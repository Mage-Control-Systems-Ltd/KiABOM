# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = 'KiABOM'
copyright = '2025, Yiannis Michael'
author = 'Yiannis Michael'
release = 'v1.8.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
import sys
from pathlib import Path

sys.path.insert(0, str(Path('..\\src', '.').resolve()))

extensions = [
        'sphinx.ext.autodoc',
        'sphinx.ext.autosummary'
        ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'bizstyle'
html_static_path = ['_static']
html_theme_options = {
        "rightsidebar" : True,
        "sidebarwidth" : "35em",
        }
