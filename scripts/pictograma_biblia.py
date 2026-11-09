"""Bíblia de desenho e escolhas de cânone por projeto."""
from pathlib import Path

from cenas import number, only
from projeto import read

ASSET = Path(__file__).resolve().parents[1] / 'assets' / 'biblia-pictograma.json'


def for_project(project):
    bible = read(ASSET)
    choices = project.get('canon_pictograma', {})
    only(choices, ' '.join(bible['corpo']), 'Cânone Pictograma')
    body = {}
    for key, (default, lower, upper) in bible['corpo'].items():
        chosen = number(choices.get(key, default), key)
        if not lower <= chosen <= upper:
            raise ValueError(f'{key}: use um valor entre {lower:g} e {upper:g}.')
        body[key] = chosen
    if body['joelho_ao_chao'] >= body['quadril_ao_chao']:
        raise ValueError('O joelho precisa ficar entre o quadril e o chão.')
    return {**bible, 'canon': body}
