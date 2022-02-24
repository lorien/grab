.PHONY: build venv deps clean release test check install_codecov_binary coveralls

build: venv deps develop

venv:
	virtualenv -p python3 .env
	
deps:
	.env/bin/pip install -r requirements_dev.txt
	.env/bin/pip install -r requirements_dev_backend.txt

clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete
	find -name '__pycache__' -delete

release:
	git push; git push --tags; rm dist/*; python3 setup.py clean sdist; twine upload dist/*


test:
	coverage run runtest.py --test-all --backend-redis --backend-mongodb \
		&& coverage report -i -m --include "grab/*"

check:
	python setup.py check -s \
		&& pylint setup.py grab tests \
		&& flake8 setup.py grab tests \
		&& pytype setup.py grab tests

coveralls:
	bash -c "source var/coveralls.env && coveralls"
