"""Liga o verbo central de uma batida à atuação que o palco executa."""
import re

from ancoras import norm, tokens

# Construções compostas têm precedência sobre verbos isolados.
PHRASES = (
    (r'nao\s+(?:consegu\w*|pod\w*|consegui\w*)\s+(?:se\s+)?levantar', 'levantar', 'tentar_levantar'),
    (r'esperar\s+nao\s+e\s+preguica', 'esperar', 'acompanhar_espera'),
    (r'quem\s+vive\s+nao\s+sou\s+mais\s+eu', 'mudar', 'virar'),
    (r'(?:nasceu|surgiu)\s+de\s+uma\s+conversa', 'conversar', 'conversar'),
)
VERBS = (
    (r'levantar|levantou|levantaram', 'levantar'),
    (r'sentar|sentou|sentaram', 'sentar'),
    (r'esperar|esperou|esperando', 'esperar'),
    (r'ler|leu|leem|lendo', 'ler'),
    (r'orar|orou|orando', 'orar'),
    (r'entregar|entregou|entregando', 'entregar'),
    (r'receber|recebeu|recebendo', 'receber'),
    (r'conversar|conversou|conversando', 'conversar'),
    (r'cuidar|cuidou|cuidando', 'amparar'),
    (r'cair|caiu|caindo', 'cair'),
    (r'carregar|carregou|carregando', 'carregar'),
    (r'mudar|mudou|mudando', 'virar'),
    (r'comecar|comecou|comecando','começar'),
)
PAIRED = {'conversar', 'acompanhar_espera', 'amparar', 'oferecer_e_recusar'}
CONTRAST = re.compile(r'\bcomecar\s+por\s+ela\s*[,;]?\s*porque\s+seria\s+facil\s+demais\s+comecar\s+por\s+mim\b')
MODAL = re.compile(r'\b(?:nao|seria|em vez de|ao inves de)\b')
CONDITIONAL = re.compile(r'^\s*se\s+')
CLAUSE = re.compile(r'[,;:.!?]|\b(?:mas|porem|contudo)\b')


def modality(plain, start):
    previous=list(CLAUSE.finditer(plain,0,start))
    offset=previous[-1].end() if previous else 0
    before=plain[offset:start]
    marker=MODAL.search(before)
    if marker:
        return {'nao':'negada','seria':'hipotetica'}.get(marker[0],'rejeitada')
    if CONDITIONAL.match(before):
        return 'hipotetica'
    return 'afirmativa'


def find_cue(phrase):
    plain = norm(phrase)
    contrast=CONTRAST.search(plain)
    if contrast:
        return {'verbo':'começar','acao':'oferecer_e_recusar','modalidade':'rejeitada',
                'deslocamento':len(tokens(plain[:contrast.start()])),
                'secundario':len(tokens(plain[:plain.index('facil',contrast.start())])),
                'precisa_opcoes':True}
    for pattern, verb, kind in (*PHRASES, *((expr, key, key) for expr, key in VERBS)):
        match = re.search(r'(?<!\w)(?:' + pattern + r')(?!\w)', plain)
        if not match:
            continue
        start = match.start()
        if kind == 'tentar_levantar':
            start = plain.rfind('levantar', match.start(), match.end())
        if kind == 'conversar' and 'conversa' in match[0] and 'uma ' in match[0]:
            start = plain.rfind('conversa', match.start(), match.end())
        state=modality(plain,start)
        if state!='afirmativa':
            kind='tentar_levantar' if verb=='levantar' and state=='negada' else 'recusar'
        return {'verbo':verb,'acao':kind,'deslocamento':len(tokens(plain[:start])),
                'modalidade':state,'precisa_opcoes':state!='afirmativa'}
    return None


def apply_cue(row, times, fps, mode):
    cue = find_cue(row['fala'])
    if not cue:
        return
    current = row.get('movimento') or {}
    kind = cue['acao']
    pair_ok = kind not in PAIRED or current.get('alvo') == 'outro'
    if current.get('tipo') == kind and pair_ok and 'secundario' not in cue:
        row['verbo_chave'] = cue
        return
    if mode == 'validar' and (current.get('tipo')!=kind or not pair_ok):
        code='EC-098' if cue['precisa_opcoes'] else 'EC-097'
        raise ValueError(f'{code} · {row["id"]} · {cue["verbo"]} exige a ação {kind}.')
    word = row['palavra'] + cue['deslocamento']
    action = {'tipo': kind, 'ator': 'principal', 'palavra': word, 'pouso': round(times[word]*fps)}
    if 'secundario' in cue:
        action['segunda_palavra']=row['palavra']+cue['secundario']
        action['segundo_pouso']=round(times[action['segunda_palavra']]*fps)
    if kind in PAIRED:
        action['alvo'] = 'outro'
        row['layout'] = 'dupla'
    if kind == 'acompanhar_espera':
        action['figura'] = 'idoso'
    row.update(movimento=action, verbo_chave=cue, pausa=None)
