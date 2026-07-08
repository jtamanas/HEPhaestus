# Repo-root pytest config helper.
#
# eval/test_slate_style.py is a standalone matplotlib-style verification SCRIPT
# (run directly: `python eval/test_slate_style.py`), not a pytest module. It
# calls sys.exit() at import time, which raises SystemExit during collection and
# aborts the whole session with an INTERNALERROR. Exclude it from collection.
collect_ignore = ["eval/test_slate_style.py"]
