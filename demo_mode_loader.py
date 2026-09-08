"""Load `demo-mode/` so `import demo_mode.*` works (hyphen folder → Python package alias)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REG = Path(__file__).resolve().parent / 'demo-mode' / 'register_pkg.py'
_SPEC = importlib.util.spec_from_file_location('_demo_mode_register_pkg', _REG)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f'Cannot load demo package register from {_REG}')
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)
_MOD.ensure_demo_mode_package()
