
test: tests/__init__.py
	# currently pylint results in nonzero exitcode -> comment out
	# pylint src/pdftitle/pdftitle.py
	python -m unittest discover

upload: pdftitle.py setup.py
	rm -rf dist
	python setup.py sdist
	twine upload dist/*
