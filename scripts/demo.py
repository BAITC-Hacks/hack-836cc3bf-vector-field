"""One-command local demo after dependency installation and frontend build."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--skip-pipeline', action='store_true', help='Serve the existing verified outputs')
    parser.add_argument('--no-ai', action='store_true', help='Disable optional AI even if a key is configured')
    parser.add_argument('--env-file', type=Path, help='Explicit local file with OPENAI_API_KEY / OPENAI_MODEL only')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be in 1..65535')
    if not (ROOT / 'frontend/dist/index.html').is_file():
        parser.error('Frontend build missing. Run npm ci and npm run build in frontend first.')
    env = os.environ.copy()
    if args.env_file:
        if not args.env_file.is_file():
            parser.error('The specified environment file does not exist.')
        for line in args.env_file.read_text(encoding='utf-8-sig').splitlines():
            key, separator, value = line.strip().partition('=')
            if separator and key.strip() in ('OPENAI_API_KEY', 'OPENAI_MODEL'):
                env[key.strip()] = value.strip().strip('\"').strip("'")
    if args.no_ai:
        env.pop('OPENAI_API_KEY', None)
    if not args.skip_pipeline:
        pipeline_env = env.copy()
        pipeline_env.pop('OPENAI_API_KEY', None)
        result = subprocess.run([sys.executable, '-m', 'pipeline', '--data',
                                 str(ROOT / 'case/data (1)/data'), '--out', str(ROOT / 'pipeline/out')],
                                cwd=ROOT, env=pipeline_env)
        if result.returncode:
            return result.returncode
    required = ('snapshot.json', 'nodes_roles.csv', 'clusters.csv', 'top_nodes.csv')
    if any(not (ROOT / 'pipeline/out' / name).is_file() for name in required):
        parser.error('Snapshot/CSV missing. Run without --skip-pipeline, or restore submission/backup.zip.')
    print(f'Demo: http://127.0.0.1:{args.port} | AI: ' +
          ('configured' if env.get('OPENAI_API_KEY', '').strip() else 'unavailable (core works)'), flush=True)
    try:
        return subprocess.call([sys.executable, '-m', 'uvicorn', 'backend.app:app',
                                '--host', '127.0.0.1', '--port', str(args.port)], cwd=ROOT, env=env)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
