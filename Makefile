.PHONY: bootstrap venv deps dirs clean test release mypy pylint flake8 bandit check build coverage

SHELL := /bin/bash
FILES_CHECK_MYPY = grab
FILES_CHECK_ALL = $(FILES_CHECK_MYPY) tests

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
	coverage run runtest.py --test-all --backend-redis --backend-mongodb \
		&& coverage report -i -m --include "grab/*"

#release:
#	git push \
#	&& git push --tags \
#	&& make build \
#	&& twine upload dist/*

mypy:
	mypy --strict $(FILES_CHECK_MYPY)

pylint:
	pylint -j0 $(FILES_CHECK_ALL)

flake8:
	flake8 -j auto --max-cognitive-complexity=17 $(FILES_CHECK_ALL)

bandit:
	bandit -qc pyproject.toml -r $(FILES_CHECK_ALL)

check:
	echo "pylint" \
	&& make pylint \
	&& echo "flake8" \
	&& make flake8 \

build:
	rm -rf *.egg-info
	rm -rf dist/*
	python -m build --sdist

pyversion:
	python -V

#coverage:
#	pytest --cov grab --cov-report term-missing
#
#coveralls:
#	bash -c "source var/coveralls.env && coveralls"
#
#docs:
#	if [ -e docs/_build ]; then rm -r docs/_build; fi \
#		&& sphinx-build -b html docs docs/_build
