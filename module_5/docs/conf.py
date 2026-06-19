import os
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
MODULE_4_DIR = DOCS_DIR.parent
REPO_ROOT = MODULE_4_DIR.parent

sys.path.insert(0, str(REPO_ROOT))

project = "Grad Cafe Analytics Module 4"
author = "Jonah Thomas"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]