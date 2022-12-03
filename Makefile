
.PHONY: help

## List of makefile targets
## help         : shows this help documentation
help: makefile
	@sed -n 's/^##[ ]//p' $<

## autopep8     : runs 'autopep8 --in-place src/grony/*.py'
autopep8:
	autopep8 --in-place src/grony/*.py

## mypy         : runs 'mypy src/'
mypy:
	mypy src/

## flake8       : runs 'flake8 src/'
flake8:
	flake8 src/