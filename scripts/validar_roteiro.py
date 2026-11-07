#!/usr/bin/env python3
"""Conferência textual local. Não gera áudio nem acessa ElevenLabs."""
import argparse
import html
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET
from fala import KNOWN, strip_voice, compare_speech, paragraphs as spoken_paragraphs

MODELS = {
    'eleven_v4': {'audio_tags': True, 'reference_limit': 10000},
    'eleven_v3': {'audio_tags': True, 'reference_limit': 5000},
    'eleven_multilingual_v2': {'audio_tags': False, 'reference_limit': 10000},
}
DOCUMENTED = {'curious', 'thoughtful', 'surprised', 'whispers', 'sighs',
              'short pause', 'long pause'}
TAG = re.compile(r'\[([^\[\]\n]+)\]')
XML_TAG = re.compile(r'<[^>]+>')
WORDS = re.compile(r"[^\W_]+(?:[-’'][^\W_]+)*", re.UNICODE)
VISUAL = re.compile(r'^(?:zoom\b|c[âa]mera\b|corte\b|cena\b|trilha\b|m[úu]sica\b|fade\b|[PC]\d+$)', re.I)


def normalize(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


def strip_controls(text):
    """Para comparar a fala, sem interpretar a intenção das marcações."""
    return normalize(strip_voice(text))


def validate(text, model, clean=None, wpm_min=125, wpm_max=160, audio_tags=(), literal_tags=()):
    if model not in MODELS:
        raise ValueError('Modelo não coberto: consultar a documentação antes de validar.')
    if not all(math.isfinite(n) and n > 0 for n in (wpm_min, wpm_max)) or wpm_min > wpm_max:
        raise ValueError('A faixa de palavras/minuto deve ser positiva e ordenada.')
    profile = MODELS[model]
    errors, warnings = [], []
    literals={t.casefold().strip() for t in literal_tags}
    controls=(KNOWN|{t.casefold().strip() for t in audio_tags})-literals
    brackets=TAG.findall(text)
    tags=[t for t in brackets if t.casefold().strip() in controls]
    if '[]' in text or re.search(r'\[(?:'+ '|'.join(re.escape(t) for t in controls)+r')\b[^\]\n]*(?:$|\n)',text,re.I):
        errors.append('Colchetes de controle vazios ou incompletos: conferir marcações.')
    for tag in brackets:
        if VISUAL.search(tag.strip()):errors.append('Direção de edição/ID no texto de voz: ['+tag+'].')
        elif tag.casefold().strip() not in controls|literals and re.fullmatch(r'[A-Za-z -]+',tag):
            warnings.append('Colchete não removido: se for direção auditiva experimental, declarar --audio-tag '+tag+'.')
    if tags and not profile['audio_tags']:
        errors.append('Tags expressivas em colchetes não pertencem ao perfil Multilingual v2.')
    for tag in tags:
        if VISUAL.search(tag.strip()):
            errors.append('Direção de edição/ID no texto de voz: [' + tag + '].')
        elif profile['audio_tags'] and tag.strip().lower() not in DOCUMENTED:
            warnings.append('Tag fora dos exemplos documentados desta skill; registrar como experimental: [' + tag + '].')

    requested_breaks = 0.0
    markup = XML_TAG.findall(text)
    if markup and profile['audio_tags']:
        errors.append('SSML/markup XML não é aceito pelo perfil v4/v3.')
    if not profile['audio_tags']:
        for raw in markup:
            try:
                node = ET.fromstring(raw)
                match = re.fullmatch(r'(\d+(?:\.\d+)?)s', node.attrib.get('time', ''))
                if node.tag != 'break' or set(node.attrib) != {'time'} or not match or list(node) or node.text:
                    raise ValueError
                seconds = float(match.group(1))
                if not 0 < seconds <= 3:
                    raise ValueError
                requested_breaks += seconds
            except (ET.ParseError, ValueError):
                errors.append('Pausa/markup inválido neste perfil: ' + raw)
    without_markup = XML_TAG.sub('', text)
    if '<' in without_markup or '>' in without_markup:
        errors.append('Sinal angular ou markup incompleto: escrever a expressão para fala.')

    spoken = normalize(strip_voice(text,audio_tags,literal_tags))
    word_count = len(WORDS.findall(spoken))
    if not word_count:
        errors.append('Não há fala no roteiro.')
    if re.search(r'^\s*(?:#{1,6}\s|\d{1,2}:\d{2}\b|(?:CENA|P\d{2})\s*[:—-])', text, re.M):
        warnings.append('Possível cabeçalho/tempo/ID de produção no arquivo de voz; conferir.')
    if re.search(r'https?://|www\.', spoken, re.I):
        warnings.append('URL na fala: preferir a descrição e manter no áudio apenas se intencional.')
    if re.search(r'\d', spoken):
        warnings.append('Há algarismos na fala: conferir leitura de datas, números e unidades.')

    paragraphs = [p for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]
    limit = profile['reference_limit']
    oversized = [i for i, p in enumerate(paragraphs, 1) if len(p) > limit]
    if oversized:
        errors.append('Blocos acima do limite de referência por geração: ' + ', '.join(map(str, oversized)) + '.')
    if len(text) > limit and not oversized:
        warnings.append('Arquivo acima do limite por geração; usar os blocos separados do Studio e reconferir o limite vigente.')
    controls_only = [i for i, p in enumerate(paragraphs, 1) if not WORDS.search(strip_controls(p))]
    if controls_only:
        warnings.append('Parágrafo só de controles; conferir contexto no Studio: ' + ', '.join(map(str, controls_only)) + '.')

    equal = None
    if clean is not None:
        if any(t.casefold().strip() in controls for t in TAG.findall(clean)) or re.search(r'<break\b',clean):
            errors.append('A versão limpa ainda contém controles.')
        equal = compare_speech(text, clean, audio_tags, literal_tags)
        if not equal:
            errors.append('A fala da versão limpa difere da versão marcada após retirar controles.')

    qualitative = sum('pause' in t.lower() for t in tags)
    if qualitative:
        warnings.append('Pausas qualitativas sem duração medida; a estimativa não lhes atribui segundos.')
    return {
        'status': 'erro' if errors else ('apto_com_avisos' if warnings else 'apto_textual'),
        'model_target': model,
        'model_confirmed_in_account': False,
        'characters_input': len(text),
        'characters_spoken': len(spoken),
        'spoken_words': word_count,
        'paragraphs': len(paragraphs),
        'audio_tags': tags,
        'spoken_text_equal_to_clean': equal,
        'duration_estimate': {
            'wpm_assumption': [wpm_min, wpm_max],
            'seconds_without_unmeasured_tag_pauses': [round(word_count/wpm_max*60+requested_breaks, 1), round(word_count/wpm_min*60+requested_breaks, 1)],
            'requested_ssml_pause_seconds': round(requested_breaks, 3),
            'qualitative_pause_tags': qualitative,
            'audio_measured': False,
        },
        'reference_limits_checked_on': '2026-11-06',
        'errors': errors,
        'warnings': warnings,
        'limitations': ['Verificação textual, não auditoria factual ou de fidelidade autoral.',
                        'Sem geração/escuta de áudio, teste de identidade vocal ou sincronização.'],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('script', type=Path)
    parser.add_argument('--model', required=True, choices=sorted(MODELS))
    parser.add_argument('--clean', type=Path)
    parser.add_argument('--audio-tag',action='append',default=[])
    parser.add_argument('--literal-tag',action='append',default=[])
    parser.add_argument('--wpm-min', type=float, default=125)
    parser.add_argument('--wpm-max', type=float, default=160)
    args = parser.parse_args(argv)
    try:
        result = validate(args.script.read_text(encoding='utf-8'), args.model,
                          args.clean.read_text(encoding='utf-8') if args.clean else None,
                          args.wpm_min, args.wpm_max, args.audio_tag, args.literal_tag)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({'status': 'erro_entrada', 'error': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
