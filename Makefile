setup:
	poetry2setup > setup.py

build: setup shiv

clean:
	rm setup.py

shiv:
	mkdir -p build
	shiv -c bubbles -o build/bubbles.pyz . --compressed -p "python3.10"
