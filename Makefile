
test: pdftitle.py test.sh test_max2.sh test_eliot.sh testc.sh
	pylint pdftitle.py
	bash test.sh
	bash test_max2.sh
	bash test_eliot.sh
	bash testc.sh

upload: pdftitle.py setup.py
	rm -rf dist
	python setup.py sdist
	twine upload dist/*
