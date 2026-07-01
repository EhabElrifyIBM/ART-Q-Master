"""
Regression test for: `from config.manager import get_config_manager` failing
with "No module named 'config.manager'; 'config' is not a package".

Root cause: utils/runtime.py's ensure_runtime_paths() puts src_v2/utils
ahead of src_v2 root on sys.path. A leftover, unused src_v2/utils/config.py
(a plain module, not a package) then shadows the real src_v2/config/
package, so any later `from config.manager import ...` resolves to the
wrong "config" and fails.

This test reproduces the exact sys.path ordering the real app produces at
startup (via ensure_runtime_paths()) and then imports config.manager,
matching what ui/shell.py, ui/settings_dialog.py and utils/runtime.py do.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)


def test_config_manager_importable_after_ensure_runtime_paths():
    from utils.runtime import ensure_runtime_paths

    ensure_runtime_paths()

    # Force a fresh resolution of the top-level "config" name so this test
    # is not accidentally passed by an import cached from earlier in the
    # test session.
    sys.modules.pop("config", None)

    from config.manager import get_config_manager

    config_module = sys.modules["config"]
    assert config_module.__file__.replace("\\", "/").endswith("src_v2/config/__init__.py"), (
        f"'config' resolved to the wrong module: {config_module.__file__}"
    )
    assert callable(get_config_manager)


if __name__ == "__main__":
    test_config_manager_importable_after_ensure_runtime_paths()
    print("OK: config.manager imports correctly after ensure_runtime_paths()")
