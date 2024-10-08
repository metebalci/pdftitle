
run_checks:
	black --check pdftitle
	pylint pdftitle

run_cli_tests:
	cd cli_tests && bash test.sh

upload:
	rm -rf dist
	python setup.py sdist
	twine upload dist/*
