
test: tests/__init__.py
	pylint src/pdftitle/pdftitle.py
	python -m unittest discover

upload: pdftitle.py setup.py
	rm -rf dist
	python setup.py sdist
	twine upload dist/*
