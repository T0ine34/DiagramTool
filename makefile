VERSION = 1.1.0


all: build test


build:
	./env/bin/feanor --debug -pv $(VERSION)
	./testenv/bin/pip install --force-reinstall dist/DiagramTool-$(VERSION)-py3-none-any.whl

test:
	clear
	./testenv/bin/DiagramTool ./src/__main__.py local.svg
