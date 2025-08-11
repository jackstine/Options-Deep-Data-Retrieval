# used to install the requirements.txt
PHONY: install-r
install-r:
	pip install -r requirements.txt

# run all unit tests
PHONY: unit-test
unit-test:
	PYTHONPATH=. python -m unittest discover -s tests -p "test_*.py" -v