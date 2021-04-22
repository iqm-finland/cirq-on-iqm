# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys


# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

# Find the path to the source files we want to to document, relative to the location of this file,
# convert it to an absolute path.
py_path = os.path.join(os.getcwd(), os.path.dirname(__file__), '../src')
sys.path.insert(0, os.path.abspath(py_path))


# -- Project information -----------------------------------------------------

project = 'Cirq on IQM'
copyright = '2020–2021, Cirq on IQM developers'
author = 'Cirq on IQM developers'

# The short X.Y version.
version = ''
# The full version, including alpha/beta/rc tags.
release = ''
try:
    from cirq_iqm import __version__ as version
except ImportError:
    pass
else:
    release = version


# -- General configuration ---------------------------------------------------

# require a recent version of Sphinx
needs_sphinx = '3.5'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.todo',
    'sphinx.ext.extlinks',
    'sphinx_automodapi.automodapi',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.*']

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%Y-%m-%d'

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
show_authors = True


# directory for the automodapi generated doc files
automodapi_toctreedirnm = 'api/api'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'nature'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Output file base name for HTML help builder.
htmlhelp_basename = 'cirq_iqm-doc'


# -- MathJax options ----------------------------------------------------------

# Here we configure MathJax, mostly to define LaTeX macros.
mathjax_config = {
    'TeX': {
        'Macros': {
            'vr': r'\vec{r}',  # no arguments
            'ket': [r'\left| #1 \right\rangle', 1],  # one argument
            'iprod': [r'\left\langle #1 | #2 \right\rangle', 2],  # two arguments
        }
    }
}


# -- External mapping ------------------------------------------------------------

extlinks = {
    'issue': ('https://github.com/iqm-finland/cirq-on-iqm/issues/%s', 'issue '),
    'mr': ('https://github.com/iqm-finland/cirq-on-iqm/pull/%s', 'MR '),
}


# -- Options for sphinxcontrib.bibtex -------------------------------------------------

# List of all bibliography files used.
#bibtex_bibfiles = ['references.bib']
