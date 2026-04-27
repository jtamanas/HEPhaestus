"""ModelSpec v3 CLI."""
import argparse
import pathlib
import sys
from .loader import load_spec, SpecLoadError
from .validate import validate
from .emit import emit_json, emit_pretty


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog='modelspec-v3')
    sub = p.add_subparsers(dest='cmd', required=True)

    v = sub.add_parser('validate')
    v.add_argument('path')
    v.add_argument('--format', choices=['pretty', 'json'], default='pretty')
    v.add_argument('--strict', action='store_true',
                   help='warnings become errors')

    r = sub.add_parser('render')
    r.add_argument('path')
    r.add_argument('--out', required=True, help='output directory')

    args = p.parse_args(argv)

    if args.cmd == 'validate':
        try:
            spec = load_spec(args.path)
        except SpecLoadError as e:
            print(f'load error: {e}', file=sys.stderr)
            return 3
        result = validate(spec)
        out = (emit_json if args.format == 'json' else emit_pretty)(result.all)
        print(out)
        if result.errors:
            return 2
        if args.strict and result.warnings:
            return 1
        return 0

    elif args.cmd == 'render':
        try:
            spec = load_spec(args.path)
        except SpecLoadError as e:
            print(f'load error: {e}', file=sys.stderr)
            return 3
        result = validate(spec)
        if result.errors:
            print(emit_pretty(result.errors), file=sys.stderr)
            print('refusing to render: spec has validation errors', file=sys.stderr)
            return 2
        from .render import render_all
        files = render_all(spec)
        out_dir = pathlib.Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (out_dir / name).write_text(content)
        print(f'wrote {len(files)} files to {out_dir}')
        return 0


if __name__ == '__main__':
    sys.exit(main())
