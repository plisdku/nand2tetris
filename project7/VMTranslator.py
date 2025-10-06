import sys
from typing import List


def parsing_error(line_number: int, line: str):
    raise ValueError((f"No idea how to parse this shit:\n" f"{line_number}: {line}"))

SEGMENT_VM_TO_HACK = {
    "temp": "5",
    "local": "LCL",
    "this": "THIS",
    "that": "THAT",
    "arg": "ARG"
}

def translate(program: str) -> str: #lines: List[str]) -> List[str]:
    """
    Translate lines of VM code into Hack assembly.
    """
    lines = [line.strip() for line in program.splitlines()]

    out_lines = []

    for line_number, line in enumerate(lines):
        # Remove extra whitespace

        # Discard comment if any
        idx_comment = line.find("//")
        if idx_comment != -1:
            line = line[:idx_comment]

        # Split into tokens. Expect one or three.
        tokens = line.split()

        if len(tokens) == 1:
            token = tokens[0]
            if token == "eq":
                # Compare top two items on stack

                program = """
                @SP
                A=M-1 // Point A to top element of stack
                D=M   // Copy top of stack to D
                A=A-1 // Point A to second element of stack
                M=D-M // Store stack[0]-stack[1] on top of stack
                M=!M  // M is True if stack[0] eq stack[1]
                @SP
                M=M-1 // SP--
                """
                out_lines.extend(program.splitlines())
            elif token == "gt":
                # Compare top two items on stack

                program = """
                @SP
                A=M-1 // Point A to stack[0]
                D=M   // D = stack[0]
                A=A-1 // Point A to stack[1]
                D=D-M // Store stack[0]-stack[1] in D

                // stack[1] > stack[0] if stack[0]-stack[1] is negative.
                // check the sign bit? And that is???
                """



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
            num = int(num) & 0xFFFF

            if cmd == "push":
                if segment == "constant":
                    program = f"""
                        @{num}
                        D=A
                    """
                else:
                    assert segment in ("temp", "local", "this", "that", "arg")
                    segment_symbol = SEGMENT_VM_TO_HACK[segment]

                    program = f"""
                        @{num}
                        D=A
                        @{segment_symbol}
                        A=D+A
                        D=M
                    """

                program += """
                    @SP
                    A=M
                    M=D
                    @SP
                    M=M+1
                """

                out_lines.extend(program.splitlines())

            elif cmd == "pop":
                # Write top of stack into a memory location.

                assert segment in ("temp", "local", "this", "that", "arg")
                segment_symbol = SEGMENT_VM_TO_HACK[segment]

                if segment == "temp":
                    # we'll directly write into RAM[temp + num],
                    # i.e. *(&temp + num).

                    assert segment_symbol == "5"

                    program = f"""
                        // Set write address to 5 + num and save to D
                        @{num}
                        D=A
                        @{segment_symbol}
                        D=D+A // sole difference between temp and other segments
                    """
                else:
                    # we'll write into RAM[RAM[sp] + num],
                    # i.e. *(sp + num)

                    program = f"""
                        // Set write address to segment_ptr + num and save to D
                        @{num}
                        D=A
                        @{segment_symbol}
                        D=D+M
                    """

                # Write address is in D. Save to R13
                program += """
                    // Save write address to R13
                    @R13
                    M=D
                """

                program += """
                    // Decrement stack pointer and save top of stack to R13
                    @SP
                    M=M-1
                    A=M
                    D=M
                    @R13
                    A=M
                    M=D
                """

                out_lines.extend(program.splitlines())

            elif cmd == "label":
                pass
            elif cmd == "goto":
                pass
            elif cmd == "if-goto":
                pass
            elif cmd == "function":
                pass
            elif cmd == "call":
                pass
            elif cmd == "return":
                pass
            else:
                parsing_error(line_number, line)
        elif len(tokens) == 0:
            pass
        else:
            parsing_error(line_number, line)

    return "\n".join([line.strip() for line in out_lines])


if __name__ == "__main__":
    print(sys.argv)

    if len(sys.argv) < 2:
        raise Exception("Usage: VMTranslator <filename>")

    translate(open(sys.argv[1]).read())


# Some example lines:
#
# push constant [n]: *sp++ = constant[n]
# pop local [n]: local[n] = *(--sp)
# pop argument [n]: argument[n] = *(--sp)
# pop this [n]: this[n] = *(--sp)
# pop that [n]: that[n] = *(--sp)
# push temp i: *sp++ = *(5+i)
# pop temp i: *(5+i) + *(--sp)
# push local [n]: *sp++ = local[n]
# push pointer 0/1: *sp++ = this/that   (any integer other than 0/1 is invalid)
# pop pointer 0/1: this/that = *(--sp)
# add
# sub
# and
# or
# not
# eq
# gt
# lt
#
#
# static symbols: each static variable i in Xxx.vm is translated
# to the assembly symbol Xxx.i
