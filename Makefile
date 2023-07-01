.PHONY: bootstrap venv deps dirs clean pytest test release mypy pylint flake8 bandit check build docs eradicate

SHELL := /bin/bash
FILES_CHECK_MYPY = grab tests
FILES_CHECK_ALL = $(FILES_CHECK_MYPY)

init: venv deps dirs

venv:
	virtualenv -p python3 .env

deps:
	.env/bin/pip install -r requirements_dev.txt
	.env/bin/pip install -r requirements_backend.txt
	.env/bin/pip install -e .[cssselect,pyquery]

dirs:
	if [ ! -e var/run ]; then mkdir -p var/run; fi
	if [ ! -e var/log ]; then mkdir -p var/log; fi

clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete
	find -name '__pycache__' -delete

pytest:
	pytest -n30 -x --cov grab --cov-report term-missing

test: check pytest
	tox -e python38-check

#release:
#	git push \
#	&& git push --tags \
#	&& make build \
#	&& twine upload dist/*

mypy:
	mypy --python-version=3.8 --strict $(FILES_CHECK_MYPY)

pylint:
	pylint -j0  $(FILES_CHECK_ALL)

flake8:
	flake8 -j auto --isolated --select CCR --max-cognitive-complexity=17 $(FILES_CHECK_ALL)

ruff:
	ruff $(FILES_CHECK_ALL)

eradicate:
	tox -e eradicate -- flake8 -j auto --eradicate-whitelist-extend="License:" $(FILES_CHECK_ALL)

bandit:
	bandit -qc pyproject.toml -r $(FILES_CHECK_ALL)

check: ruff mypy pylint flake8 bandit

build:
	rm -rf *.egg-info
	rm -rf dist/*
	python -m build --sdist

docs:
	rm -rf docs/_build/html 
	sphinx-build -j auto docs docs/_build/html
