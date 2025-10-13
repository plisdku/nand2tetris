from functools import wraps
import os
from pathlib import Path
import sys
from typing import Callable, List, Literal, Tuple
import textwrap


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


def remove_comments(program: str) -> str:
    """
    Strip out all comments from a hack program or VM program
    """

    out_lines = [line.split("//")[0] for line in program.splitlines()]
    return "\n".join(out_lines)

def strip(func: Callable):
    @wraps(func)
    def f(*args, **kwargs) -> str:
        gross_str = func(*args, **kwargs)

        lines = [l.strip() for l in gross_str.splitlines()]
        return "\n".join(lines)
    return f

@strip
def write_cmp(token: Literal["eq", "gt", "lt"], jump: Literal["JNE", "JLE", "JGE"], label_count: dict[str,int]):
    """
    Hack implementation for "eq", "gt" and "lt".
    """
    label = f"{token}_{label_count.setdefault(token, 0)}"
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

@strip
def write_not():
    program = f"""
    @SP
    A=M-1  // point to top of stack
    M=!M   // logical negate
    """
    return program

@strip
def write_neg():
    program = f"""
    @SP
    A=M-1  // point to top of stack
    M=-M   // arithmetic negate
    """
    return program

@strip
def write_and():
    program = f"""
    @SP
    AM=M-1  // SP = SP-1; A = SP-1 (top of stack)
    D=M     // D = "y"
    A=A-1
    M=D&M   // new top of stack = x and y
    """
    return program

@strip
def write_or():
    program = f"""
    @SP
    AM=M-1  // SP = SP-1; A = SP-1 (top of stack)
    D=M     // D = "y"
    A=A-1   // point to "x"
    M=D|M   // new top of stack = x or y
    """
    return program

@strip
def write_add():
    program = f"""
    @SP
    AM=M-1  // SP = SP-1; A = SP-1 (top of stack)
    D=M     // D = "y"
    A=A-1   // point to "x"
    M=D+M   // new top of stack = x+y
    """
    return program

@strip
def write_sub():
    program = f"""
    @SP
    AM=M-1  // SP = SP-1; A = SP-1 (top of stack)
    D=M     // D = "y"
    A=A-1   // point to "x"
    M=M-D   // new top of stack = x+y
    """
    return program

@strip
def write_push(cmd: str, segment: str, num_str: str, namespace: str) -> str:
    # Set D to the value we want to push onto the stack.

    num = int(num_str) & 0xFFFF

    program = ""

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
    return program

@strip
def write_pop(cmd: str, segment: str, num_str: str, namespace: str) -> str:
    # Write top of stack into a memory location (segment base + offset)

    num = int(num_str) & 0xFFFF

    assert segment in ("temp", "local", "this", "that", "pointer", "argument", "static"), f"{segment}"

    program = ""

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
    return program


@strip
def write_label(cmd: str, label_name: str, namespace: str) -> str:
    program = f"""
        ({namespace}.{label_name})
    """
    return program

@strip
def write_goto(cmd: str, label_name: str, namespace: str) -> str:
    program = f"""
        @{namespace}.{label_name}
        0;JMP
    """
    return program

@strip
def write_if_goto(cmd: str, label_name: str, namespace: str) -> str:
    """
    If the top element of the stack is nonzero, jump to the label.
    """

    # push condition
    # if-goto LABEL   <-- implement this
    
    program = f"""
        @SP
        AM=M-1 // SP = SP-1; A = address of prev top
        D=M    // save the address to jump to
        @{namespace}.{label_name}
        D;JNE  // 
    """


    pass
    

# For each file:
#  program += translate()


def translate(program: str, namespace: str = "default") -> str:
    """
    Translate lines of VM code into Hack assembly.

    Args:
        program: VM code
        namespace: should be the basename of the program file, e.g. MyProgram
    """

    lines = [line.strip() for line in program.splitlines()]

    out_paragraphs: list[str] = []

    label_count: dict[str,int] = {}

    for line_number, line in enumerate(lines):
        # Remove extra whitespace

        # Discard comment if any
        idx_comment = line.find("//")
        if idx_comment != -1:
            line = line[:idx_comment]

        # Split into tokens. Expect one or three.
        tokens = line.split()
        if not tokens:
            continue

        cmd = tokens[0]

        program = ""

        if cmd == "eq":
            program = write_cmp("eq", "JNE", label_count)
        elif cmd == "gt":
            program = write_cmp("gt", "JLE", label_count)
        elif cmd == "lt":
            program = write_cmp("lt", "JGE", label_count)
        elif cmd == "not":
            program = write_not()
        elif cmd == "neg":
            program = write_neg()
        elif cmd == "and":
            program = write_and()
        elif cmd == "or":
            program = write_or()
        elif cmd == "add":
            program = write_add()
        elif cmd == "sub":
            program = write_sub()
        elif cmd == "push":
            program = write_push(cmd, tokens[1], tokens[2], namespace)
        elif cmd == "pop":
            program = write_pop(cmd, tokens[1], tokens[2], namespace)
        elif cmd == "label":
            program = write_label(cmd, tokens[1], namespace)
            pass
        elif cmd == "goto":
            program = ""
            pass
        elif cmd == "if-goto":
            program = ""
            pass
        elif cmd == "function":
            program = ""
            pass
        elif cmd == "call":
            program = ""
            pass
        elif cmd == "return":
            program = ""
            pass
        else:
            parsing_error(line_number, line)

        out_paragraphs.append(f"// {' '.join(tokens)}")
        out_paragraphs.append(program)

    return "\n".join(out_paragraphs)


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

    asm_chapters: list[str] = []

    for file in input_files:
        with open(file) as fh:
            contents = fh.read()
            asm_code = translate(contents, file.stem)
            asm_chapters.append(asm_code)

    with open(output_file, "w") as fh:
        fh.write("\n".join(asm_chapters))


