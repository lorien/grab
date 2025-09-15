.PHONY: py3 py3-venv py3-deps py2 py2-venv py2-deps dirs test coverage_nobackend coverage coverage_missing clean build yaml release

PY2_ROOT = /home/user/.pyenv/versions/2.7.18
PY2_VENV = .venv-py2
PY3_VENV = .venv-py3
COVERAGE_TARGET = grab

# PY3
py3: py3-venv py3-deps dirs

py3-venv:
	virtualenv -p python3 $(PY3_VENV)

py3-deps:
	$(PY3_VENV)/bin/pip install -r requirements_dev.txt
	$(PY3_VENV)/bin/pip install -r requirements_dev_backend.txt
	$(PY3_VENV)/bin/pip install .[urllib3,pyquery]

# PY2
py2: py2-venv py2-deps dirs

py2-venv:
	$(PY2_ROOT)/bin/pip install virtualenv
	$(PY2_ROOT)/bin/virtualenv --python=$(PY2_ROOT)/bin/python2.7 $(PY2_VENV)
	
py2-deps:
	$(PY2_VENV)/bin/pip install -r requirements_dev.txt
	$(PY2_VENV)/bin/pip install -r requirements_dev_backend.txt
	$(PY2_VENV)/bin/pip install .[urllib3,pyquery]

dirs:
	if [ ! -e var/run ]; then mkdir -p var/run; fi
	if [ ! -e var/log ]; then mkdir -p var/log; fi
	if [ ! -e var/bin ]; then mkdir -p var/bin; fi

test:
	./runtest.py --test-all --backend-mongo --backend-mysql --backend-redis --backend-postgres

coverage_nobackend:
	coverage erase
	coverage run --source=$(COVERAGE_TARGET) ./runtest.py --test-all
	coverage report -m

coverage:
	coverage erase
	coverage run --source=$(COVERAGE_TARGET) ./runtest.py --test-all --backend-mongo --backend-mysql --backend-redis --backend-postgres
	coverage report -m

coverage_missing:
	coverage erase
	coverage run --source=$(COVERAGE_TARGET) ./runtest.py --test-all --backend-mongo --backend-mysql --backend-redis --backend-postgres
	coverage report -m | grep -v '100%' | grep -v Missing | grep -v -- '----' | sort -k 3 -nr

clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete
	find -name '__pycache__' -delete

build:
	rm -rf *.egg-info
	rm -rf dist/*
	python -m build

yaml:
	yamllint .github

release:
	git push \
	&& git push --tags \
	&& make build \
	&& twine upload dist/*
