VERSION = 1.1.0


all: build test


build:
	./env/bin/feanor --debug -pv $(VERSION)
	./testenv/bin/pip install --force-reinstall dist/DiagramTool-$(VERSION)-py3-none-any.whl

test:
	./testenv/bin/DiagramTool ../sae-s5.a.01-2024-sujet01/server/src/__main__.py ./crypto.svg --save-ast --debug --dump
