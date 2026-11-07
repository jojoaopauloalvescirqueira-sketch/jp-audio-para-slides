"""Catálogo local e preferências de direção vocal."""
import json
from pathlib import Path
from unicodedata import normalize


CATEGORIES = ('entrega', 'emocao', 'vocalizacoes', 'voz', 'efeitos-sonoros')
DEFAULT_CATEGORIES = CATEGORIES[:3]
REQUIRES_PERMISSION = set(CATEGORIES[3:])
DENSITIES = {'leve': 60, 'moderada': 35, 'expressiva': 20}
TAG_FIELDS = ('idioma_tags', 'densidade_tags', 'categorias_tags')


def tag_key(value):
    return normalize('NFC', value.strip()).casefold()


path = Path(__file__).resolve().parents[1] / 'assets/tags_elevenlabs.json'
with path.open(encoding='utf-8') as source:
    CATALOG = json.load(source)['tags']


def preference(direction, key, default=None):
    return (direction or {}).get(key, {}).get('valor', default)


def allowed_categories(direction):
    entry = (direction or {}).get('categorias_tags', {})
    choices = set(entry.get('valor', DEFAULT_CATEGORIES))
    return choices if entry.get('origem') == 'usuario' else choices - REQUIRES_PERMISSION
