.PHONY: bootstrap venv deps dirs clean test release mypy pylint flake8 bandit check build quick

SHELL := /bin/bash
FILES_CHECK_MYPY = grab
FILES_CHECK_ALL = $(FILES_CHECK_MYPY) tests

#coverage:
#	pytest --cov grab --cov-report term-missing
#
#coveralls:
#	bash -c "source var/coveralls.env && coveralls"
#
#docs:
#	if [ -e docs/_build ]; then rm -r docs/_build; fi \
#		&& sphinx-build -b html docs docs/_build

bootstrap: venv deps dirs

venv:
	virtualenv -p python3 .env

deps:
	.env/bin/pip install -r requirements.txt
	.env/bin/pip install -r requirements_backend.txt
	.env/bin/pip install -e .[cssselect,pyquery]

dirs:
	if [ ! -e var/run ]; then mkdir -p var/run; fi
	if [ ! -e var/log ]; then mkdir -p var/log; fi

clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete
	find -name '__pycache__' -delete

test:
	tox -e py3-test

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
	flake8 -j auto --max-cognitive-complexity=17 $(FILES_CHECK_ALL)

bandit:
	bandit -qc pyproject.toml -r $(FILES_CHECK_ALL)

check:
	tox -e py3-check \
	&& tox -e py38-check

build:
	rm -rf *.egg-info
	rm -rf dist/*
	python -m build --sdist

demo:
	tox -e py3-demo \
	&& tox -e py38-demo

quick:
	pytest -n30 -x
