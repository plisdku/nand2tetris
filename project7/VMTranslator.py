import os
import sys
from typing import List, Literal


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

    label_count: dict[str,int] = dict(((k,0) for k in ("eq", "gt", "lt", "not", "and", "or", "add")))

    for line_number, line in enumerate(lines):
        # Remove extra whitespace

        # Discard comment if any
        idx_comment = line.find("//")
        if idx_comment != -1:
            line = line[:idx_comment]

        # Split into tokens. Expect one or three.
        tokens = line.split()

        def _compare(token: Literal["eq", "gt", "lt"], jump: Literal["JNE", "JLE", "JGE"] ):
            """
            Hack implementation for "eq", "gt" and "lt".
            """
            label = f"{token}_{label_count[token]}"
            label_count[token] += 1

            # Compare top two items on stack.
            #
            # Strategy stolen from StackTest.asm.
            
            program = f"""
            @SP
            AM=M-1 // SP = SP - 1; A = SP - 1
            D=M    // D = "y"
            A=A-1  // point to "x"
            D=M-D  // D = "x-y"
            M=0    // top of stack = 0 in case
            @{label}
            D;{jump}  // if we're done, exit
            @SP
            A=M-1  // point to new top of stack
            M=-1   // top of stack = 0xFFFF
            ({label})
            """
            return program

        if len(tokens) == 1:
            token = tokens[0]
            if token == "eq":
                program = _compare("eq", "JNE")
                out_lines.extend(program.splitlines())
            elif token == "gt":
                program = _compare("gt", "JLE")
                out_lines.extend(program.splitlines())
            elif token == "lt":
                program = _compare("lt", "JGE")
                out_lines.extend(program.splitlines())
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
                        @{num} // {cmd} {segment} {num}
                        D=A
                    """
                else:
                    assert segment in ("temp", "local", "this", "that", "arg")
                    segment_symbol = SEGMENT_VM_TO_HACK[segment]

                    program = f"""
                        @{num}
                        D=A
                        @{segment_symbol}
                        A=M
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

                program = f"""
                    // {cmd} {segment} {num}
                """

                if segment == "temp":
                    # we'll directly write into RAM[temp + num],
                    # i.e. *(&temp + num).

                    assert segment_symbol == "5"

                    program += f"""
                        @{num} // Set write address to 5 + num and save to D
                        D=A
                        @{segment_symbol}
                        D=D+A // sole difference between temp and other segments
                    """
                else:
                    # we'll write into RAM[RAM[sp] + num],
                    # i.e. *(sp + num)

                    program += f"""
                        @{num} // Set write address to segment_ptr + num and save to D
                        D=A
                        @{segment_symbol}
                        D=D+M
                    """

                # Write address is in D. Save to R13
                program += """
                    @R13 // Save write address to R13
                    M=D
                """

                program += """
                    @SP // Decrement stack pointer and save top of stack to R13
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

    hack_code = translate(open(sys.argv[1]).read())

    print(hack_code)

    with open(os.path.splitext(sys.argv[1])[0] + ".asm") as fh:
        fh.write(hack_code)


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
