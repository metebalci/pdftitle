
test:
	black --check pdftitle
	pylint pdftitle
	cd cli_tests && bash test.sh

upload:
	rm -rf build
	rm -rf dist
	python -m build
	python -m twine upload dist/*
