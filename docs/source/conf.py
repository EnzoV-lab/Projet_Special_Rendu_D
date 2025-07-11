import os
import sys
sys.path.insert(0, os.path.abspath('../../Itineraire-aérien-package'))
sys.path.insert(0, os.path.abspath('../../ItineraireAerien'))
sys.path.insert(0, os.path.abspath('../../Avion'))
sys.path.insert(0, os.path.abspath('../../coordonnees'))
sys.path.insert(0, os.path.abspath('../../Meteo'))
sys.path.insert(0, os.path.abspath('../../Visualisation'))
sys.path.insert(0, os.path.abspath('../..'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ITINÉRAIRE AÉRIEN SÉCURISÉ PAR METEO'
copyright = '2025, Romuald TIAKO - Elsa KUPFER - Enzo VILLAMANDOS - Lucas BONNEAUD'
author = 'Romuald TIAKO - Elsa KUPFER - Enzo VILLAMANDOS - Lucas BONNEAUD'
release = '27/06/2025'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = []

language = 'fr'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
