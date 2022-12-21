extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "autoapi.extension",
    "myst_nb",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "Grab"
copyright = "2015 – 2023, Gregory Petukhov"
version = "0.6.41"
release = "0.6.41"
exclude_patterns = []
pygments_style = "sphinx"
html_static_path = []  #'_static']
htmlhelp_basename = "Grabdoc"
latex_elements = {}
latex_documents = [
    ("index", "Grab.tex", "Grab Documentation", "Gregory Petukhov", "manual"),
]
man_pages = [("index", "grab", "Grab Documentation", ["Gregory Petukhov"], 1)]
texinfo_documents = [
    (
        "index",
        "Grab",
        "Grab Documentation",
        "Gregory Petukhov",
        "Grab",
        "One line description of project.",
        "Miscellaneous",
    ),
]
html_theme = "sphinx_rtd_theme"
autoapi_dirs = ["../grab"]  # location to parse for API reference
