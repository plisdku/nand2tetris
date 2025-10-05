import hackulator


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

# nonsensical test
JUMPS = """
(PARIS)
@x
(BERLIN)
0;JMP
@BERLIN
@y
0;JMP
"""

def test_max_labels():
    """
    Check that labels are resolved to the correct instructions
    """
    parser = hackulator.Parser()
    parser.parse(MAX.splitlines())

    assert parser.symbol_table["ITSR0"] == 10
    assert parser.symbol_table["OUTPUT_D"] == 12
    assert parser.symbol_table["END"] == 14

def test_user_symbols():
    parser = hackulator.Parser()
    parser.parse(JUMPS.splitlines())

    assert parser.symbol_table["x"] == 16
    assert parser.symbol_table["y"] == 17

def test_run_max():
    for (x,y) in [(0, 1), (1, 0), (100, 10), (10, 100), (-1 & 0xFFFF, -10 & 0xFFFF)]:

        compy = hackulator.Compy386(MAX)
        compy.ram[0] = x
        compy.ram[1] = y

        for step in range(100):
            compy.step()

        assert compy.ram[2] == max(x,y)

def test_noop():
    """
    Verify that the 'D' command can function as a noop.
    """

    program = """
    D
    """
    compy = hackulator.Compy386(program)
    compy.step()
    assert compy.pc == 1

    # Verify that nothing happened
    compy2 = hackulator.Compy386(program)
    assert compy.register_d == compy2.register_d

    for r1,r2 in zip(compy.ram, compy2.ram):
        assert r1 == r2
import pytest

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
    ]
)
def test_jumps(jump_command: str, does_goto_dest: bool):
    """
    Test that the jump commands move the program counter as expected
    """
    dest = 3
    program = f"@DEST\n{jump_command}\n" + "D\n" * (dest - 2) + "(DEST)\nD"

    compy = hackulator.Compy386(program)
    compy.step()  # @DEST
    compy.step()  # jump

    if does_goto_dest:
        assert compy.pc == dest
    else:
        assert compy.pc == 2




