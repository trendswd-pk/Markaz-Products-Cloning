"""Import shim: portfolio folder is `demo-mode/`; Python package name is `demo_mode`."""

from pathlib import Path

# Submodules live in the hyphenated Streamlit entry folder.
__path__ = [str(Path(__file__).resolve().parent.parent / 'demo-mode')]
