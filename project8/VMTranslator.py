import os
from pathlib import Path
import sys
import argparse
from typing import List, Literal, Tuple


def parsing_error(line_number: int, line: str):
    raise ValueError((f"No idea how to parse this shit:\n" f"{line_number}: {line}"))

SEGMENT_VM_TO_HACK = {
    "temp": "5",
    "pointer": "THIS",
    "local": "LCL",
    "this": "THIS",
    "that": "THAT",
    "argument": "ARG"
}

def translate(program: str, namespace: str = "default") -> str: #lines: List[str]) -> List[str]:
    """
    Translate lines of VM code into Hack assembly.

    Args:
        program: VM code
        namespace: should be the basename of the program file, e.g. MyProgram
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
            // {token} {jump}
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
                program = f"""
                // not
                @SP
                A=M-1  // point to top of stack
                M=!M   // logical negate
                """
                out_lines.extend(program.splitlines())
            elif token == "neg":
                program = f"""
                // neg
                @SP
                A=M-1  // point to top of stack
                M=-M   // arithmetic negate
                """
                out_lines.extend(program.splitlines())
            elif token == "and":
                program = f"""
                // and
                @SP
                AM=M-1  // SP = SP-1; A = SP-1 (top of stack)
                D=M     // D = "y"
                A=A-1
                M=D&M   // new top of stack = x and y
                """
                out_lines.extend(program.splitlines())
            elif token == "or":
                program = f"""
                // or
                @SP
                AM=M-1  // SP = SP-1; A = SP-1 (top of stack)
                D=M     // D = "y"
                A=A-1   // point to "x"
                M=D|M   // new top of stack = x or y
                """
                out_lines.extend(program.splitlines())
            elif token == "add":
                program = f"""
                // add
                @SP
                AM=M-1  // SP = SP-1; A = SP-1 (top of stack)
                D=M     // D = "y"
                A=A-1   // point to "x"
                M=D+M   // new top of stack = x+y
                """
                out_lines.extend(program.splitlines())
            elif token == "sub":
                program = f"""
                // sub
                @SP
                AM=M-1  // SP = SP-1; A = SP-1 (top of stack)
                D=M     // D = "y"
                A=A-1   // point to "x"
                M=M-D   // new top of stack = x+y
                """
                out_lines.extend(program.splitlines())
            else:
                parsing_error(line_number, line)
        elif len(tokens) == 3:
            cmd, segment, num = tokens
            num = int(num) & 0xFFFF

            program = f"""
                // {cmd} {segment} {num}
            """

            if cmd == "push":

                # Set D to the value we want to push onto the stack.

                if segment == "constant":
                    program += f"""
                        @{num} // {cmd} {segment} {num}
                        D=A
                    """
                elif segment == "temp":
                    actual_num = num + 5
                    program += f"""
                        @{actual_num} // @TEMP + num
                        D=M
                    """
                elif segment == "pointer":
                    # Push the THIS or THAT pointer onto the stack.
                    assert num in (0, 1), f"num ({num}) is not what I expected"

                    segment_symbol = "THIS" if num == 0 else "THAT"

                    program += f"""
                        @{segment_symbol}
                        D=M
                    """
                elif segment == "static":
                    # Push Static.i onto the stack

                    static_var = f"{namespace}.{num}"

                    program += f"""
                        @{static_var}
                        D=M // copy value of {static_var} into D
                    """
                else:
                    assert segment in ("local", "this", "that", "argument"), f"{segment}"

                    segment_symbol = SEGMENT_VM_TO_HACK[segment]

                    program += f"""
                        @{num}
                        D=A
                        @{segment_symbol}
                        A=D+M
                        D=M
                    """

                program += """
                    @SP // push D onto the stack
                    A=M
                    M=D
                    @SP
                    M=M+1
                """

                out_lines.extend(program.splitlines())

            elif cmd == "pop":
                # Write top of stack into a memory location (segment base + offset)

                assert segment in ("temp", "local", "this", "that", "pointer", "argument", "static"), f"{segment}"

                program = f"""
                // pop {segment} {num}
                """

                if segment == "temp":
                    # Write directly into RAM[temp+num]
                    segment_symbol = SEGMENT_VM_TO_HACK[segment]
                    assert segment_symbol == "5"

                    actual_num = num + 5
                    program += f"""
                        // Pop from stack
                        @SP
                        AM=M-1  // SP = SP-1, A = addr of top
                        D=M     // D = value at top

                        // Write to saved location
                        @{actual_num}
                        M=D
                    """
                elif segment == "pointer":
                    # Write to RAM[THIS] or RAM[THAT]

                    assert num in (0, 1), f"num = {num} unexpected for pointer"
                    seg = "THIS" if num == 0 else "THAT"

                    program += f"""
                        @{seg} // Save the write address
                        D=A
                        @R15
                        M=D // save write addr in R15

                        @SP     // Pop from stack
                        AM=M-1  // SP = SP-1, A = addr of top
                        D=M     // D = value at top

                        @R15    // Write to saved location
                        A=M
                        M=D
                    """
                elif segment == "static":
                    # Pop from Static.{num}

                    static_var = f"{namespace}.{num}"

                    program += f"""
                        @SP    // pop from stack
                        AM=M-1 // SP = SP-1, A = addr of top
                        D=M    // D = value at top

                        @{static_var} // write to static var
                        M=D
                    """
                else:
                    segment_symbol = SEGMENT_VM_TO_HACK[segment]

                    # I used this first
                    # @{segment_symbol}
                    # D=M
                    # @{num}
                    # D=D+A

                    program += f"""
                        // Save the write address
                        @{num}
                        D=A
                        @{segment_symbol}
                        D=D+M
                        @R15
                        M=D // save write addr in R15

                        // Pop from stack
                        @SP
                        AM=M-1 // SP = SP-1; A points to top of stack
                        D=M    // D = value at top of stack

                        // Write to saved location
                        @R15
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


def normalize_arguments(argv: List[str]) -> Tuple[List[Path], Path, bool]:
    """
    Args:
        argv: list of arguments from sys.argv. First arg is program name,
            second arg is vm file path or directory containing vm files,
            third arg (optional) is output file path
    Returns:
        list of input file paths
        output file path
        bool, True if input was a directory, False otherwise
    """
    path = Path(argv[1])

    if path.is_dir():
        input_files = sorted([p for p in path.iterdir() if p.suffix == ".vm"])
        do_init = True
    else:
        input_files = [path]
        do_init = False

    output_file = Path(argv[2]) if len(argv) >= 3 else path.with_suffix(".asm")

    return input_files, output_file, do_init


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("> VMTranslator")
        print("Compile .vm files in current directory to .asm files")
        print("> VMTranslator path/to/file.vm [output/file.asm]")
        print(("Compile single .vm file to a .asm file in same directory or "
            "at custom path"
        ))
        print("> VMTranslator path/to/directory [output/file.asm]")
        print((
            "Compile all files in given directory to a .asm file in the "
            "same directory or at custom path"
        ))
        exit(0)

    input_files, output_file, do_init = normalize_arguments(sys.argv)

"""
Plan this one out.


"""



