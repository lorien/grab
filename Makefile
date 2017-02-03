.PHONY: build venv deps develop flake flake_verbose test coverage_nobackend coverage coverage_missing clean upload doc doc_ru

build: venv deps develop

venv:
	virtualenv --no-site-packages --python=python3.4 .env
	
deps:
	.env/bin/pip install -r requirements.txt
	.env/bin/pip install -r requirements_dev.txt
	.env/bin/pip install -r requirements_dev_backend.txt

develop:
	.env/bin/python setup.py develop

flake:
	flake8 grab test setup.py

flake_verbose:
	flake8 grab test setup.py --show-pep8

test:
	tox -e py34

coverage_nobackend:
	coverage erase
	coverage run --source=grab ./runtest.py --test-all
	coverage report -m

coverage:
	coverage erase
	coverage run --source=grab ./runtest.py --test-all --backend-mongo --backend-mysql --backend-redis --backend-postgres
	coverage report -m

coverage_missing:
	coverage erase
	coverage run --source=grab ./runtest.py --test-all --backend-mongo --backend-mysql --backend-redis --backend-postgres
	coverage report -m | grep -v '100%' | grep -v Missing | grep -v -- '----' | sort -k 3 -nr

clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete
	find -name '__pycache__' -delete

upload:
	python setup.py sdist upload

doc:
	sh -c 'cd docs/en; make html'

doc_open:
	x-www-browser docs/en/build/html/index.html

doc_ru:
	sh -c 'cd docs/ru; make html'
