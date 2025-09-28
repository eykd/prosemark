.PHONY: clean build publish

clean:
	rm -rf dist/

build: clean
	uv build

publish: build
	uv publish
