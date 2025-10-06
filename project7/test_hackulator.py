import itertools
from typing import Literal
import pytest
from hackulator import Compy386, Parser


# Computes R2 = max(R0, R1)  (R0,R1,R2 refer to RAM[0],RAM[1],RAM[2])
# Usage: Before executing, put two values in R0 and R1.
MAX = """
  @R0
  D=M
  @R1
  D=D-M
  // If (D > 0) goto ITSR0
  @ITSR0
  D;JGT
  // Its R1
  @R1
  D=M
  @OUTPUT_D
  0;JMP
(ITSR0)
  @R0 // 10
  D=M
(OUTPUT_D)
  @R2 // 12
  M=D
(END)
  @END // 14
  0;JMP
"""


def test_push_pop():
    compy = Compy386()

    assert compy.sp == compy.stack_ptr

    compy.run()

    assert compy.depth() == 0
    compy.push(1)
    assert compy.depth() == 1
    compy.push(-2)
    assert compy.depth() == 2
    compy.push(3)
    assert compy.depth() == 3

    assert compy.pop() == 3
    assert compy.depth() == 2
    assert compy.pop() == -2
    assert compy.depth() == 1
    assert compy.pop() == 1
    assert compy.depth() == 0



def test_max_labels():
    """
    Check that labels are resolved to the correct instructions
    """
    parser = Parser()
    parser.parse(MAX.splitlines())

    assert parser.symbol_table["ITSR0"] == 10
    assert parser.symbol_table["OUTPUT_D"] == 12
    assert parser.symbol_table["END"] == 14


def test_user_symbols():
    """
    Check the construction of the symbol table for user-defined variables
    """
    # nonsensical test
    program = """
    (PARIS)
    @x
    (BERLIN)
    0;JMP
    @BERLIN
    @y
    0;JMP
    """

    parser = Parser()
    parser.parse(program.splitlines())

    assert parser.symbol_table["x"] == 16
    assert parser.symbol_table["y"] == 17


def test_run_max():
    """
    Spot check the max program
    """
    for x, y in [(0, 1), (1, 0), (100, 10), (10, 100), (-1 & 0xFFFF, -10 & 0xFFFF)]:
        compy = Compy386(MAX, init_sp=False)
        compy.ram[0] = x
        compy.ram[1] = y

        for step in range(100):
            compy.step()

        assert compy.ram[2] == max(x, y)


def test_noop():
    """
    Verify that the 'D' command can function as a noop.
    """

    program = """
    D
    """
    compy = Compy386(program, init_sp=False)
    compy.step()
    assert compy.pc == 1

    # Verify that nothing happened
    compy2 = Compy386(program, init_sp=False)
    assert compy.register_d == compy2.register_d

    for r1, r2 in zip(compy.ram, compy2.ram):
        assert r1 == r2


@pytest.mark.parametrize(
    "segment, base_addr", [("LCL", 40), ("THIS", 50), ("THAT", 60), ("ARG", 70)]
)
def test_get_set_segment_base(segment: Literal["LCL", "THIS", "THAT", "ARG"], base_addr: int):
    compy = Compy386()
    compy.set_segment_base(segment, base_addr)
    assert compy.segment_base(segment) == base_addr

@pytest.mark.parametrize(
    "segment, base_addr, offset, value",
    [("LCL", 100, 10, 1), ("THIS", 200, 20, -2), ("THAT", 300, 30, -3), ("ARG", 400, 0, 4)]
)
def test_get_set_segment(segment: Literal["LCL", "THIS", "THAT", "ARG"], base_addr: int, offset: int, value: int):
    compy = Compy386()
    compy.set_segment_base(segment, base_addr)
    compy.set_in_segment(segment, offset, value & 0xFFFF)
    assert compy.get_in_segment(segment, offset) == value & 0xFFFF


@pytest.mark.parametrize(
    "jump_command, does_goto_dest",
    [
        ("-1;JGT", False),
        ("0;JGT", False),
        ("1;JGT", True),
        ("-1;JEQ", False),
        ("0;JEQ", True),
        ("1;JEQ", False),
        ("-1;JGE", False),
        ("0;JGE", True),
        ("1;JGE", True),
        ("-1;JLT", True),
        ("0;JLT", False),
        ("1;JLT", False),
        ("-1;JNE", True),
        ("0;JNE", False),
        ("1;JNE", True),
        ("-1;JLE", True),
        ("0;JLE", True),
        ("1;JLE", False),
        ("-1;JMP", True),
        ("0;JMP", True),
        ("1;JMP", True),
    ],
)
def test_jumps(jump_command: str, does_goto_dest: bool):
    """
    Test that the jump commands move the program counter as expected
    """
    dest = 3
    program = f"@DEST\n{jump_command}\n" + "D\n" * (dest - 2) + "(DEST)\nD"

    compy = Compy386(program, init_sp=False)

    compy.step()  # @DEST
    compy.step()  # jump

    if does_goto_dest:
        assert compy.pc == dest
    else:
        assert compy.pc == 2


_COMMANDS = [
    "0",
    "1",
    "-1",
    "D",
    "A",
    "M",
    "!D",
    "!M",
    "!A",
    "-D",
    "-A",
    "-M",
    "D+1",
    "A+1",
    "M+1",
    "D-1",
    "A-1",
    "M-1",
    "D+A",
    "D+M",
    "D-A",
    "D-M",
    "A-D",
    "M-D",
    "D&A",
    "D&M",
    "D|A",
    "D|M",
]
_DESTS = ["M", "D", "A"]
_TESTS = list(itertools.product(_DESTS, _COMMANDS))


@pytest.mark.parametrize("dest, command", _TESTS)
def test_comps(dest, command):
    """
    Test the commands of the form dest=comp.

    Hack allows the dest to be _multiple_ registers, e.g. 'DM=0'.
    I don't test this because I'm being super lazy and using eval().
    """

    a_value = 10
    m_value = 3
    d_value = 4

    program = f"@{a_value}\n{dest}={command}"

    compy = Compy386(program, init_sp=False)
    compy.ram[a_value] = m_value
    compy.register_d = d_value

    expected = eval(
        command.replace("!", "~"), locals={"D": d_value, "A": a_value, "M": m_value}
    )
    expected = expected & 0xFFFF
    compy.step()
    compy.step()
    got = eval(
        dest,
        locals={
            "D": compy.register_d,
            "A": compy.register_a,
            "M": compy.ram[compy.register_a]
            if compy.register_a < len(compy.ram)
            else None,
        },
    )
    got = got & 0xFFFF

    assert got == expected
