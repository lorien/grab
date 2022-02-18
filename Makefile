.PHONY: build venv deps clean upload upload_docs test check

build: venv deps develop

venv:
	virtualenv --python=python3 .env
	
deps:
	.env/bin/pip install -r requirements_dev.txt
	.env/bin/pip install -r requirements_dev_backend.txt

clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete
	find -name '__pycache__' -delete

upload:
	git push --tags; python setup.py clean sdist upload

upload_docs:
	tox -e doc && rsync -azhP docs/build/html/ web@sam:/web/grablab/docs/

test:
	./runtest.py --test-all --backend-redis --backend-mongodb

check:
	python setup.py check -s \
		&& pylint setup.py grab tests \
		&& flake8 setup.py grab tests \
		&& pytype setup.py grab tests
