# Back-compat shim. Canonical: plugins/shared/install-helpers/wolfram/_activation_parse.py
import importlib.util, os
_here = os.path.dirname(os.path.abspath(__file__))
_canon = os.path.normpath(os.path.join(_here, "..", "..", "..", "..", "shared",
                                        "install-helpers", "wolfram", "_activation_parse.py"))
spec = importlib.util.spec_from_file_location("_activation_parse_canon", _canon)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
globals().update({k: v for k, v in vars(mod).items() if not k.startswith("_")})

if __name__ == "__main__":
    mod.main()
