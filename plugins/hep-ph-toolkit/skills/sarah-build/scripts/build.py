"""sarah-build CLI: validates ModelSpec, renders, invokes SARAH via wolframscript."""
import argparse
import pathlib
import sys


def main(argv=None):
    p = argparse.ArgumentParser(prog='sarah-build')
    p.add_argument('spec_path')
    p.add_argument('--model-dir', required=True,
                   help='per-model state directory (e.g. ./demo_output/<model>/)')
    p.add_argument('--force', action='store_true',
                   help='bypass cache and rebuild')
    p.add_argument('--outputs', nargs='+', default=['ufo'],
                   choices=['ufo', 'spheno'],
                   help='SARAH targets to build (default: ufo)')
    args = p.parse_args(argv)

    repo_root = pathlib.Path(__file__).resolve().parents[5]
    sys.path.insert(0, str(repo_root / 'plugins' / 'hep-ph-toolkit' / 'skills' / '_shared'))
    sys.path.insert(0, str(repo_root / 'plugins' / 'shared' / 'install-helpers'))
    sys.path.insert(0, str(pathlib.Path(__file__).parent))

    from run_sarah import run

    result = run(
        spec_path=pathlib.Path(args.spec_path),
        model_dir=pathlib.Path(args.model_dir),
        force=args.force,
        outputs=args.outputs,
    )
    print(result)
    return 0


if __name__ == '__main__':
    sys.exit(main())
