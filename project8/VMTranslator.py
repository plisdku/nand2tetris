import argparse
from functools import wraps
import os
from pathlib import Path
import sys
from typing import Callable, List, Literal, Optional, Tuple, TypeVar
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

def remove_whitespace(program: str) -> str:
    """
    Remove leading and trailing whitespace from each line, and remove empty lines.
    """

    out_lines = []

    for line in program.splitlines():
        stript = line.strip()
        if stript:
            out_lines.append(stript)
    return "\n".join(out_lines)

T = TypeVar("T", bound=Callable) #[.., str])

def strip(func: T) -> T:
    """
    Decorator to remove leading and trailing whitespace from output of function.
    """
    @wraps(func)
    def f(*args, **kwargs) -> str:
        gross_str = func(*args, **kwargs)

        lines = [l.strip() for l in gross_str.splitlines()]
        return "\n".join(lines)
    return f # type:ignore

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
        # Push a constant onto the stack
        program += f"""
            @{num} // {cmd} {segment} {num}
            D=A
        """
    elif segment == "temp":
        # Push *(temp + num) onto the stack
        actual_num = num + 5
        program += f"""
            @{actual_num} // @TEMP + num
            D=M
        """
    elif segment == "pointer":
        # Push the THIS or THAT pointer onto the stack
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
        # Push RAM[RAM[SEGMENT] + num] to the stack,
        # where SEGMENT is local, this, that, or argument.

        assert segment in ("local", "this", "that", "argument"), f"{segment}"

        segment_symbol = SEGMENT_VM_TO_HACK[segment]

        program += f"""
            @{num}
            D=A
            @{segment_symbol}
            A=D+M
            D=M
        """

    program += write_push_d()
    return program

@strip
def write_push_d() -> str:
    """Push D onto the stack. This is called in common by all the push commands."""
    program = """
        @SP // push D onto the stack
        A=M
        M=D
        @SP
        M=M+1
    """
    return program


@strip
def write_pop(segment: str, num_str: str, namespace: str) -> str:
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
def write_label(label_name: str, namespace: Optional[str]) -> str:

    if namespace is None:
        program = f"({label_name})"
    else:
        program = f"({namespace}.{label_name})"

    return program

@strip
def write_goto(label_name: str, namespace: Optional[str]) -> str:

    if namespace is None:
        program = f"""
            @{label_name}
            0;JMP
        """
    else:
        program = f"""
            @{namespace}.{label_name}
            0;JMP
        """
    return program

@strip
def write_if_goto(label_name: str, namespace: str) -> str:
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

    return program

@strip
def write_function(function_name: str, num_vars: int) -> str:
    """
    Function definition. Pushes a label, then initializes the local
    variables to zero.
    
    Pseudocode:
        (function_name)
        push constant 0
        ...
        push constant 0   // num_vars times
    """

    program_chunks = [write_label(function_name, None)]

    for nn in range(num_vars):
        program_chunks.append(write_push("push", "constant", "0", ""))

    program = "\n".join(program_chunks)
    return program

@strip
def write_push_label(label: str) -> str:
    """
    Push the value of a label onto the stack.

    Pseudocode:
        @{label}
        D=A
        push D
    """
    program = f"@{label}\nD=A\n" + write_push_d()
    return program

@strip
def write_push_pointer(symbol: Literal["LCL", "ARG", "THIS", "THAT"]) -> str:
    """
    Push the base address of a segment onto the stack.

    Pseudocode:
        @{symbol}
        D=M
        push D
    """
    program = f"@{symbol}\nD=M\n" + write_push_d()
    return program

@strip
def write_call(function_name: str, num_args: int, label_count: dict[str,int]) -> str:
    """
    Pseudocode:
        push returnAddress
        push LCL
        push ARG
        push THIS
        push THAT
        ARG = SP-5-nArgs
        LCL = SP
        goto f
        (returnAddress)

    The return address is something I haven't dealt with yet.
    I can add a label, then @label it.
    """

    return_address_prefix = f"{function_name}.call"
    idx_call = label_count.setdefault(return_address_prefix, 0)
    return_address_label = f"{return_address_prefix}.{idx_call}"
    label_count[return_address_prefix] += 1
    
    program_chunks = [
        write_push_label(return_address_label),
        write_push_pointer("LCL"),
        write_push_pointer("ARG"),
        write_push_pointer("THIS"),
        write_push_pointer("THAT"),
        # ARG = SP-5-num_args
        f"""
            // ARG = SP - 5 - num_args
            @SP
            D=M
            @5
            D=D-A
            @{num_args}
            D=D-A
            @ARG
            M=D
        """,
        # LCL = SP
        f"""
            // LCL = SP
            @SP
            D=M
            @LCL
            M=D
        """,
        write_goto(function_name, None),
        write_label(return_address_label, None)
    ]
    return "\n".join(program_chunks)

@strip
def write_return() -> str:
    """
    Pseudocode:
        frame = LCL           // frame is a temporary variable
        ret_addr = *(frame-5) // put return address in a temporary variable
        *ARG = pop()          // reposition the return value for the caller
        SP = ARG+1            // reposition SP for the caller
        THAT = *(frame-1)     // restore THAT
        THIS = *(frame-2)     // restore THIS
        ARG = *(frame-3)      // restore ARG
        LCL = *(frame-4)      // restore LCL
        goto ret_addr
    """

    program = f"""
        // frame = LCL
        @LCL       // A = &LCL
        D=M        // D = LCL
        @frame     // A = &frame
        M=D        // frame = LCL

        // ret_addr = *(frame-5)
        @5
        A=D-A      // A = frame-5
        D=M        // D = *(frame-5)
        @ret_addr  // A = &ret_addr
        M=D        // ret_addr = *(frame-5)

        // *ARG = pop()
        // ARG was pointing to the first argument,
        // but we want to overwrite that location with
        // the return value.
        @SP        // A = &SP
        AM=M-1     // SP = SP-1; A = SP-1
        D=M        // D = *(SP-1), value from top of stack
        @ARG       // A = &ARG
        A=M        // A = ARG
        M=D        // *ARG = *(SP-1)

        // SP = ARG+1
        @ARG       // A = &ARG
        D=M+1      // D = *A + 1 = ARG + 1
        @SP        // A = &SP
        M=D        // SP = ARG+1

        // THAT = *(frame-1)
        @frame     // A = &frame
        AM=M-1     // A = frame - 1; frame' = frame - 1
        D=M        // D = *(frame - 1)
        @THAT      // A = &THAT
        M=D        // THAT = *(frame - 1)

        // THIS = *(frame-2) = *(frame'-1)
        @frame     // A = &frame'
        AM=M-1     // A = frame'-1; frame'' = frame'-1
        D=M        // D = *(frame' - 1)
        @THIS      // A = &THIS
        M=D        // THIS = *(frame'-1)

        // ARG = *(frame-3)
        @frame     // A = &frame''
        AM=M-1     // A = frame''-1; frame''' = frame''-1
        D=M        // D = *(frame'' - 1)
        @ARG       // A = &ARG
        M=D        // ARG = *(frame''-1)

        // LCL = *(frame-4)
        @frame     // A = &frame'''
        AM=M-1     // A = frame'''-1; frame'''' = frame'''-1
        D=M        // D = *(frame''' - 1)
        @LCL       // A = &LCL
        M=D        // LCL = *(frame''' - 1)

        // goto ret_addr
        @ret_addr  // A = &ret_addr
        A=M        // A = *A = ret_addr
        0;JMP
    """
    return program


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
            program = write_pop(tokens[1], tokens[2], namespace)
        elif cmd == "label":
            program = write_label(tokens[1], namespace)
            pass
        elif cmd == "goto":
            program = write_goto(tokens[1], namespace)
            pass
        elif cmd == "if-goto":
            program = write_if_goto(tokens[1], namespace)
            pass
        elif cmd == "function":
            # namespace assumed to be part of the function name, so
            # we don't pass that in.
            program = write_function(tokens[1], int(tokens[2]))
            pass
        elif cmd == "call":
            program = write_call(tokens[1], int(tokens[2]), label_count)
            pass
        elif cmd == "return":
            program = write_return()
            pass
        else:
            parsing_error(line_number, line)

        out_paragraphs.append(f"// {' '.join(tokens)}")
        out_paragraphs.append(program)

    return "\n".join(out_paragraphs)


def normalize_arguments(input_filepath: str, output_filepath: Optional[str] = None) -> Tuple[List[Path], Path, bool]:
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
    path = Path(input_filepath)

    print(repr(input_filepath), repr(output_filepath))

    if path.is_dir():
        input_files = sorted([p for p in path.iterdir() if p.suffix == ".vm"])

        # input: program_dir/
        # default output path: program_dir/program_dir.asm

        output_file = Path(output_filepath) if isinstance(output_filepath, str) else (path/path.stem).with_suffix(".asm")
        do_init = True
    else:
        input_files = [path]

        # input: program.vm
        # default output path: program.asm

        output_file = Path(output_filepath) if isinstance(output_filepath, str) else path.with_suffix(".asm")
        do_init = False

    return input_files, output_file, do_init



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compile .vm files to Hack .asm files."
    )
    parser.add_argument(
        "input_path",
        help="VM file or directory containing .vm files"
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Optional output .asm file path"
    )
    parser.add_argument(
        "--strip",
        action="store_true",
        help="Remove comments and extra whitespace"
    )
    args = parser.parse_args()

    input_files, output_file, do_init = normalize_arguments(args.input_path, args.output_file)

    asm_chapters: list[str] = []

    if do_init:
        asm_chapters.append(remove_whitespace(f"""
            @256
            D=A
            @SP
            M=D
        """))

        asm_chapters.append(translate("""
            call Sys.init 0
        """, "init"))

    for file in input_files:
        with open(file) as fh:
            contents = fh.read()
            asm_code = translate(contents, file.stem)
            asm_chapters.append(asm_code)

    asm_program = "\n".join(asm_chapters)
    if args.strip:
        asm_program = remove_whitespace(remove_comments(asm_program))

    with open(output_file, "w") as fh:
        fh.write(asm_program)

