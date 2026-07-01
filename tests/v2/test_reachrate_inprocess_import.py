"""
Regression test for: launching Reach Rate Calculator in-process failed with
"No module named 'ReachRateCalculatorUI_v2'".

Root cause: tool_launcher._launch_reachrate_inprocess() does a bare
`import ReachRateCalculatorUI_v2`, which requires the "Reach Rate Calculator"
directory to already be on sys.path. The old subprocess launcher got this
for free (Python auto-adds a script's own directory when run directly via
`python some_script.py`). In-process launching has no script boundary, so
nothing added that directory to sys.path in dev mode — only the frozen
build's PyInstaller spec did (via pathex). ensure_runtime_paths() now
includes the Reach Rate Calculator directory alongside ART Q Control.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)


def test_reachrate_module_importable_after_ensure_runtime_paths():
    from utils.runtime import ensure_runtime_paths

    ensure_runtime_paths()

    sys.modules.pop("ReachRateCalculatorUI_v2", None)

    import ReachRateCalculatorUI_v2

    assert hasattr(ReachRateCalculatorUI_v2, "ReachRateCalculatorWindow")


if __name__ == "__main__":
    test_reachrate_module_importable_after_ensure_runtime_paths()
    print("OK: ReachRateCalculatorUI_v2 imports correctly after ensure_runtime_paths()")
