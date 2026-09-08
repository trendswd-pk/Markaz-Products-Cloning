"""Register the hyphenated `demo-mode/` folder as importable package name `demo_mode`.

Python identifiers cannot contain hyphens, so production/demo code still uses
`import demo_mode…` while the on-disk (and Streamlit) folder name is `demo-mode/`.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path


def ensure_demo_mode_package():
    existing = sys.modules.get('demo_mode')
    if existing is not None and getattr(existing, '__path__', None):
        return existing

    pkg_dir = Path(__file__).resolve().parent
    pkg = types.ModuleType('demo_mode')
    pkg.__path__ = [str(pkg_dir)]
    pkg.__file__ = str(pkg_dir / '__init__.py')
    pkg.__package__ = 'demo_mode'
    sys.modules['demo_mode'] = pkg
    return pkg


ensure_demo_mode_package()
