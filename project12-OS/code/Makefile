# Simple Makefile for Nand2Tetris Project 12 - OS Implementation

test:
	cp Array.jack ../ArrayTest/
	cp Keyboard.jack ../KeyboardTest/
	cp Math.jack ../MathTest/
	cp Memory.jack ../MemoryTest/
	cp Output.jack ../OutputTest/
	cp Screen.jack ../ScreenTest/
	cp String.jack ../StringTest/
	cp Sys.jack ../SysTest/

unittest:
	mkdir -p unit_tests/string
	cp String.jack unit_tests/string/
	mkdir -p unit_tests/memory
	cp Memory.jack unit_tests/memory/
	mkdir -p unit_tests/math
	cp Math.jack unit_tests/math/

submission:
	mkdir -p ../submission
	rm -f ../submission/Archive.zip
	cp Array.jack ../submission/
	cp Keyboard.jack ../submission/
	cp Math.jack ../submission/
	cp Memory.jack ../submission/
	cp Output.jack ../submission/
	cp Screen.jack ../submission/
	cp String.jack ../submission/
	cp Sys.jack ../submission/
	cp lang.txt ../submission/
	cd ../submission && zip Archive.zip *.jack lang.txt

clean:
	rm -f ../ArrayTest/Array.jack
	rm -f ../KeyboardTest/Keyboard.jack
	rm -f ../MathTest/Math.jack
	rm -f ../MemoryTest/Memory.jack
	rm -f ../OutputTest/Output.jack
	rm -f ../ScreenTest/Screen.jack
	rm -f ../StringTest/String.jack
	rm -f ../SysTest/Sys.jack

	rm -f unit_tests/string/String.jack
	rm -f unit_tests/memory/Memory.jack
	rm -f unit_tests/math/Math.jack

	# Remove any generated submission artifacts
	rm -rf ../submission

.PHONY: test submission clean
