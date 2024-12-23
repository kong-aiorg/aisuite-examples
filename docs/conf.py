"""Sphinx configuration."""
project = "Aisuite Examples"
author = "kongyew"
copyright = "2024, kongyew"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
