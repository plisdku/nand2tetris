import sys
from typing import List


def parsing_error(line_number: int, line: str):
    raise ValueError((f"No idea how to parse this shit:\n" f"{line_number}: {line}"))


def translate(lines: List[str]) -> List[str]:
    for line_number, line in enumerate(lines):
        # Discard comment if any
        idx_comment = line.find("//")
        if idx_comment != -1:
            line = line[:idx_comment]

        # Split into tokens. Expect one or three.
        tokens = line.split()

        if len(tokens) == 1:
            token = tokens[0]
            if token == "eq":
                # @SP   point to top of stack
                # D=M   put value at top of stack into D
                # M=A   put value of A into M
                # M=M-1 decrement M
                # A=M   point to new top of stack
                # D=D-M D <- difference of D and M
                # M=!D  write !D to new top of stack
                # D=A   D <- addr of top of stack
                # @SP   point to top of stack
                # M=D   write new addr to top of stack
                pass
            elif token == "gt":
                pass
            elif token == "lt":
                pass
            elif token == "not":
                pass
            elif token == "and":
                pass
            elif token == "or":
                pass
            elif token == "add":
                # @SP     a = &sp
                # D=M     d = *a
                # M=A     *a = a
                # M=M-1   *a = *a - 1
                # A=M     a = *a       point to new top
                # M=D+M   *a = d + *a  add new top and old top into new top
                # D=A     d = a
                # @SP     a = &sp
                # M=D     sp = d       sp points to new top of stack
                pass
            else:
                parsing_error(line_number, line)
        elif len(tokens) == 3:
            cmd, segment, num = tokens

            if cmd == "push":
                print(cmd, segment, num)
                pass
            elif cmd == "pop":
                pass
            else:
                parsing_error(line_number, line)
        elif len(tokens) == 0:
            pass
        else:
            parsing_error(line_number, line)

    return lines


if __name__ == "__main__":
    print(sys.argv)

    if len(sys.argv) < 2:
        raise Exception("Usage: VMTranslator <filename>")

    translate(open(sys.argv[1]).readlines())


# Some example lines:
#
# push constant [n]
# pop local [n]
# pop argument [n]
# pop this [n]
# pop that [n]
# push local [n]
# push pointer [n]
# pop pointer [n]
# add
# sub
# and
# or
# not
# eq
# gt
# lt
