"""Localiza o Godot assinado e executa o piloto de renderização vetorial."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ASSETS = Path(__file__).resolve().parents[1] / 'assets'
PUBLISHER = 'Prehensile Tales B.V. (6K46PWY5DM)'
INSTALL = ('Use o Godot fora do iCloud, por exemplo em ~/Applications/Godot.app. '
           'Extraia o ZIP oficial com ditto numa pasta local e verifique a assinatura e o Gatekeeper.')


def local_path(path):
    original = Path(os.path.abspath(Path(path).expanduser()))
    resolved = original.resolve()
    if any(part.casefold() == 'mobile documents'
           for p in (original, resolved) for part in p.parts):
        raise ValueError(f'O executável do Godot está dentro do iCloud (Mobile Documents). {INSTALL}')
    return resolved


def locate(environ=None, home=None):
    env = os.environ if environ is None else environ
    home = Path.home() if home is None else home
    explicit = env.get('JP_GODOT')
    candidates = (Path(explicit),) if explicit else (
        Path('/Applications/Godot.app'), home / 'Applications/Godot.app')
    for candidate in candidates:
        path = local_path(candidate)
        if path.suffix == '.app':
            path = local_path(path / 'Contents/MacOS/Godot')
        if path.is_file() and os.access(path, os.X_OK):
            return path
    raise ValueError(f'Godot indisponível. {INSTALL} O navegador continua disponível.')


def verify(executable):
    executable = local_path(executable)
    app = next((p for p in executable.parents if p.suffix == '.app'), None)
    if app is None:
        raise ValueError(f'O piloto no macOS exige um Godot.app assinado. {INSTALL}')
    if executable != local_path(app / 'Contents/MacOS/Godot'):
        raise ValueError('JP_GODOT deve indicar o executável oficial dentro de Godot.app.')
    checks = {
        'codesign': ['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', str(app)],
        'gatekeeper': ['/usr/sbin/spctl', '--assess', '--type', 'execute', '-vv', str(app)],
    }
    evidence = {}
    for name, command in checks.items():
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        evidence[name] = {'codigo': result.returncode, 'saida': result.stdout.strip()}
    if (any(item['codigo'] for item in evidence.values())
            or f'origin=Developer ID Application: {PUBLISHER}' not in evidence['gatekeeper']['saida']):
        raise ValueError('Assinatura ou Gatekeeper não confirmou o Godot oficial. ' +
                         json.dumps(evidence, ensure_ascii=False))
    version = subprocess.check_output([str(executable), '--version'], text=True, timeout=30).strip()
    if not re.match(r'^4\.\d+(?:\.\d+)?\.', version):
        raise ValueError(f'O piloto requer Godot 4.x. Versão encontrada: {version}.')
    return {'executavel': str(executable), 'versao': version, **evidence}


def identity(source, version):
    digest = hashlib.sha256()
    files = (source, *sorted((ASSETS / 'godot-pictograma').iterdir()),
             *sorted((ASSETS / 'pictograma-fontes').glob('*.ttf')))
    for path in files:
        digest.update(path.read_bytes())
    digest.update(version.encode())
    return digest.hexdigest()


def png_size(path):
    import struct
    with path.open('rb') as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise ValueError(f'PNG inválido: {path.name}')
    return struct.unpack('>II', header[16:24])


def render(source, output, evidence, limit=None):
    executable = local_path(evidence['executavel'])
    data = json.loads(source.read_text())
    width, height = data['size']
    frames = data['frames']
    count = len(frames) if limit is None else min(len(frames), limit)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'sha256': identity(source, evidence['versao']), 'quadros': count, 'fps': 30,
                'dimensoes': [width, height], 'versao': evidence['versao']}
    state = output / 'render_manifest.json'
    previous = json.loads(state.read_text()) if state.is_file() else None
    if previous == manifest:
        try:
            if all(png_size(output / f'{i:06}.png') == (width, height) for i in range(count)):
                return manifest
        except (OSError, ValueError):
            pass
    with tempfile.TemporaryDirectory(prefix='jp-godot-') as tmp:
        scratch = Path(tmp)
        shutil.copytree(ASSETS / 'godot-pictograma', scratch / 'project')
        project_config = scratch / 'project' / 'project.godot'
        project_config.write_text(project_config.read_text()
                                  .replace('viewport_width=1080', f'viewport_width={width}')
                                  .replace('viewport_height=1920', f'viewport_height={height}'))
        for font in (ASSETS / 'pictograma-fontes').glob('*.ttf'):
            shutil.copy2(font, scratch / 'project' / font.name)
        (scratch / 'frames.json').write_text(json.dumps({**data, 'frames':frames[:count]}))
        command = [str(executable), '--path', str(scratch/'project'), '--audio-driver', 'Dummy',
                   '--write-movie', str(scratch/'quadro.png'), '--fixed-fps', '30',
                   '--resolution', f'{width//2}x{height//2}', '--quit-after', str(count), '--', str(scratch/'frames.json')]
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        (output/'godot.log').write_text(result.stdout)
        if result.returncode or re.search(r'(?m)^(?:SCRIPT ERROR|ERROR):', result.stdout):
            raise ValueError(f'Godot falhou. Consulte {output / "godot.log"}')
        files = sorted(scratch.glob('quadro*.png'))
        if len(files) != count or any(png_size(p) != (width,height) for p in files):
            raise ValueError(f'Godot produziu {len(files)} quadros. Esperados: {count} em {width}×{height}.')
        for i, path in enumerate(files):
            shutil.copyfile(path, output/f'{i:06}.png')
    state.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    return manifest


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--poses', type=Path, help='JSON de geometria gerado por capturar_godot.mjs.')
    parser.add_argument('--saida', type=Path, help='Pasta de saída dos PNGs.')
    args = parser.parse_args()
    if (args.poses is None) != (args.saida is None):
        parser.error('Use --poses e --saida juntos, ou omita ambos para verificar o executável.')
    try:
        evidence = verify(locate())
        print(json.dumps(evidence, ensure_ascii=False, indent=2), flush=True)
        if args.poses is not None:
            manifest = render(args.poses.resolve(), args.saida.resolve(), evidence)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))


if __name__ == '__main__':
    main()
