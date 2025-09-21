import sys
from typing import List


def translate(lines: List[str]) -> List[str]:
    for line in lines:
        print(line)

    return lines


if __name__ == "__main__":
    print(sys.argv)

    if len(sys.argv) < 2:
        raise Exception("Usage: VMTranslator <filename>")

    translate(open(sys.argv[1]).readlines())
