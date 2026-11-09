#!/usr/bin/env python3
"""Execute a suíte local e destaque cobertura incompleta do catálogo."""
import argparse
from pathlib import Path
import sys
import unittest


def linked_tests():
    from catalogo_erros import catalogo
    return {row['teste'] for row in catalogo() if row.get('teste')}


def test_cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_cases(item)
        else:
            yield item


def catalog_skips(result):
    linked=linked_tests()
    return [(item.id(), reason) for item,reason in result.skipped
            if item.id() in linked or item.id().startswith('test_catalogo_erros.')]


class CatalogRunner(unittest.TextTestRunner):
    def run(self, test):
        result = super().run(test)
        skips = catalog_skips(result)
        if skips:
            self.stream.writeln(f'*** ATENÇÃO: {len(skips)} TESTE(S) DO CATÁLOGO PULADO(S) ***')
            for name, reason in skips:
                self.stream.writeln(f'  {name}: {reason}')
        else:
            self.stream.writeln('CATÁLOGO: 0 testes pulados.')
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogo', action='store_true', help='execute somente o catálogo')
    parser.add_argument('--exigir-catalogo', action='store_true', help='falhe se algum teste do catálogo for pulado')
    args = parser.parse_args()
    path = Path(__file__).resolve().parent
    discovered=unittest.defaultTestLoader.discover(str(path), 'test_*.py')
    cases=list(test_cases(discovered))
    linked=linked_tests()
    missing=linked-{item.id() for item in cases}
    if missing:
        print('CATÁLOGO: testes vinculados não descobertos: '+', '.join(sorted(missing)),file=sys.stderr)
    tests=unittest.TestSuite(item for item in cases if not args.catalogo or item.id() in linked
                            or item.id().startswith('test_catalogo_erros.'))
    result = CatalogRunner(verbosity=2).run(tests)
    return int(not result.wasSuccessful() or (args.exigir_catalogo and (bool(missing) or bool(catalog_skips(result)))))


if __name__ == '__main__':
    sys.exit(main())
