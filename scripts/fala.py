"""Controles de voz identificados, sem apagar colchetes literais por padrão."""
import re,unicodedata

from tags_voz import CATALOG, tag_key

KNOWN = set(CATALOG)
BRACKET=re.compile(r'\[([^\[\]\n]+)\]')
BREAK=re.compile(r"<break\s+time\s*=\s*([\"'])(?:\d+(?:\.\d+)?)s\1\s*/>")

def normalize(text):return ' '.join(unicodedata.normalize('NFC',text).split())
def paragraphs(text):return [p.strip() for p in re.split(r'\n\s*\n',text.strip()) if p.strip()]
def strip_voice(text,audio_tags=(),literal_tags=()):
 controls=KNOWN|{tag_key(t) for t in audio_tags};literals={tag_key(t) for t in literal_tags}
 text=BRACKET.sub(lambda m:'' if tag_key(m[1]) in controls-literals else m[0],text)
 return BREAK.sub('',text)
def clean_paragraphs(text,audio_tags=(),literal_tags=()):
 # Preserve the paragraph boundaries; a controls-only block is an invalid spoken paragraph.
 result=[]
 for p in paragraphs(text):
  cleaned=' '.join(strip_voice(p,audio_tags,literal_tags).split())
  if not cleaned:raise ValueError('Parágrafo só de controles; reorganize a direção sem criar blocos sem fala.')
  result.append(cleaned)
 return result
def compare_speech(studio,clean,audio_tags=(),literal_tags=()):
 a=[normalize(strip_voice(p,audio_tags,literal_tags)) for p in paragraphs(studio)]
 b=[normalize(p) for p in paragraphs(clean)]
 return a==b
