# Simple Makefile for Nand2Tetris Project 12 - OS Implementation

test:
	cp Array.jack ../tests/ArrayTest/
	cp Keyboard.jack ../tests/KeyboardTest/
	cp Math.jack ../tests/MathTest/
	cp Memory.jack ../tests/MemoryTest/
	cp Output.jack ../tests/OutputTest/
	cp Screen.jack ../tests/ScreenTest/
	cp String.jack ../tests/StringTest/
	cp Sys.jack ../tests/SysTest/

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
	rm -f ../tests/ArrayTest/Array.jack
	rm -f ../tests/KeyboardTest/Keyboard.jack
	rm -f ../tests/MathTest/Math.jack
	rm -f ../tests/MemoryTest/Memory.jack
	rm -f ../tests/OutputTest/Output.jack
	rm -f ../tests/ScreenTest/Screen.jack
	rm -f ../tests/StringTest/String.jack
	rm -f ../tests/SysTest/Sys.jack

	rm -f unit_tests/string/String.jack
	rm -f unit_tests/memory/Memory.jack
	rm -f unit_tests/math/Math.jack

	# Remove any generated submission artifacts
	rm -rf ../submission

.PHONY: test submission clean
