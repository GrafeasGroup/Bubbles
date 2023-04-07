setup:
	poetry2setup > setup.py

build: setup shiv

clean:
	rm setup.py

shiv:
	mkdir -p build
	shiv --preamble bubbles/preamble.py -c bubbles -o build/bubbles.pyz . --compressed
