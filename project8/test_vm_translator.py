from typing import Callable, Literal
import pytest
from hackulator import Compy386
from VMTranslator import remove_comments, remove_whitespace, translate
from operator import and_, neg, or_, add, sub, not_, invert



@pytest.mark.parametrize(("x", "y"), [(0,0), (0,1), (1,0), (1,1), (-1,1)])
def test_eq(x: int, y: int):

    vm_code = f"""
        push constant {x}
        push constant {y}
        eq
    """

    # print(translate(vm_code))
    compy = Compy386(translate(vm_code))
    compy.run(print_stack=False, print_line=False, print_registers=False)

    assert compy.depth() == 1

    if x == y:
        assert compy.peek()
    else:
        assert not compy.peek()

def test_multi_eq():
    """Because each eq makes its own label, want to check that I can have
    several of them."""

    vm_code = f"""
        push constant 0
        push constant 0
        eq
        push constant 1
        push constant 0
        eq
        push constant 0
        push constant -1
        eq
        push constant 1
        push constant 1
        eq
    """

    compy = Compy386(translate(vm_code))
    compy.run()
    assert compy.depth() == 4

    assert compy.get_stack() == [0xFFFF, 0, 0, 0xFFFF]

@pytest.mark.parametrize(("x", "y"), [(0,0), (0,1), (1,0), (1,1), (-1,1)])
def test_gt(x: int, y: int):

    vm_code = f"""
        push constant {x}
        push constant {y}
        gt
    """

    compy = Compy386(translate(vm_code))
    compy.run()
    assert compy.depth() == 1

    print(f"{x} > {y}: {compy.peek()}")

    if x > y:
        assert compy.peek()
    else:
        assert not compy.peek()


@pytest.mark.parametrize(("x", "y"), [(0,0), (0,1), (1,0), (1,1), (-1,1)])
def test_lt(x: int, y: int):

    vm_code = f"""
        push constant {x}
        push constant {y}
        lt
    """

    compy = Compy386(translate(vm_code))
    compy.run()
    assert compy.depth() == 1

    print(f"{x} < {y}: {compy.peek()}")

    if x < y:
        assert compy.peek()
    else:
        assert not compy.peek()

@pytest.mark.parametrize(("command", "op"), [("not", invert), ("neg", neg)])
@pytest.mark.parametrize("x", (0, 1, -1, 4321))
def test_unary_op(x: int, command: str, op: Callable[[int], int]):

    vm_code = f"""
        push constant {x}
        {command}
    """
    compy = Compy386(translate(vm_code))
    compy.run(print_line=False, print_registers=False, print_stack=False)
    assert compy.depth() == 1

    assert compy.peek() == op(x) & 0xFFFF


@pytest.mark.parametrize(("command", "op"), [("and", and_), ("or", or_), ("add", add), ("sub", sub)])
@pytest.mark.parametrize(("x", "y"), [(0,0), (1,0), (0,1), (2, 32), (-2, -1)])
def test_binary_op(x: int, y: int, command: str, op: Callable[(int,int), int]):

    vm_code = f"""
        push constant {x}
        push constant {y}
        {command}
    """
    compy = Compy386(translate(vm_code))
    compy.run(print_line=False, print_registers=False, print_stack=False)
    assert compy.depth() == 1
    assert compy.peek() == op(x,y) & 0xFFFF

def test_init_stack():
    """
    Hack program to initialize SP to 256.
    """
    compy = Compy386()
    compy.run()
    assert compy.sp == 256


def test_push_static():

    vm_program = f"""
        push static 3
    """

    compy = Compy386(translate(vm_program))
    compy.ram[compy.symbol_table["default.3"]] = 100
    compy.run()

    assert "default.3" in compy.symbol_table
    assert compy.depth() == 1
    assert compy.peek() == 100


def test_push_constant():
    vm_program = """
        push constant -1
        push constant 0
        push constant 1
    """
    compy = Compy386(translate(vm_program))
    compy.run(print_line=False)

    assert compy.depth() == 3
    assert compy.peek() == 1
    assert compy.peek(1) == 0
    assert compy.peek(2) == (-1 & 0xFFFF)


def test_push_pointer():
    vm_program = """
        push pointer 0
        push pointer 1
    """

    print(translate(vm_program))

    compy = Compy386(translate(vm_program))
    compy.set_segment_base("THIS", 100)
    compy.set_segment_base("THAT", 200)
    compy.run()

    assert compy.depth() == 2
    assert compy.get_stack() == [100, 200]

@pytest.mark.parametrize(("segment_vm", "segment_hack"),
    [("local", "LCL"), ("this", "THIS"), ("that", "THAT"), ("argument", "ARG")]
)
def test_push_segment(segment_vm: str, segment_hack: Literal["LCL", "ARG", "THIS", "THAT"]):
    """
    Test pushing to the local, this, that, or argument segments.
    """

    # Note that we're pushing OUT OF ORDER.
    # Just making it a little harder to be right by accident alone.

    vm_program = f"""
        push {segment_vm} 0
        push {segment_vm} 2
        push {segment_vm} 1
    """

    compy = Compy386(translate(vm_program))
    compy.set_segment_base(segment_hack, 1000)
    compy.set_in_segment(segment_hack, 0, 10)
    compy.set_in_segment(segment_hack, 1, -11 & 0xFFFF)
    compy.set_in_segment(segment_hack, 2, 12)
    compy.run(print_line=False, print_registers=False)

    assert compy.get_stack() == [10, 12, -11 & 0xFFFF]

    assert compy.depth() == 3
    assert compy.peek() == -11 & 0xFFFF
    assert compy.peek(1) == 12
    assert compy.peek(2) == 10


def test_pop_static():

    vm_program = f"""
        pop static 3
    """

    compy = Compy386(translate(vm_program))
    compy.push(100)
    compy.run()

    assert "default.3" in compy.symbol_table
    assert compy.ram[compy.symbol_table["default.3"]] == 100

def test_pop_temp():

    vm_program = f"""
        pop temp 0
        pop temp 2
        pop temp 6
    """

    # print(translate(vm_program))

    compy = Compy386(translate(vm_program))
    compy.push(100)
    compy.push(101)
    compy.push(102)
    compy.run(print_line=False, print_registers=False)

    assert compy.depth() == 0

    assert compy.symbol_table["TEMP"] == 5
    assert compy.ram[compy.symbol_table["TEMP"]+0] == 102
    assert compy.ram[compy.symbol_table["TEMP"]+2] == 101
    assert compy.ram[compy.symbol_table["TEMP"]+6] == 100

def test_pop_pointer():
    vm_program = """
        pop pointer 1
        pop pointer 0
    """

    # print(translate(vm_program))

    compy = Compy386(translate(vm_program))
    compy.push(99)
    compy.push(-99)
    compy.run(print_line=False, print_registers=False)

    # assert compy.depth() == 1
    assert compy.ram[compy.symbol_table["THAT"]] == -99 & 0xFFFF # first pop to THAT
    assert compy.ram[compy.symbol_table["THIS"]] == 99 # second pop to THIS


@pytest.mark.parametrize(("segment_vm", "segment_hack"),
    [("local", "LCL"), ("argument", "ARG"), ("this", "THIS"), ("that", "THAT") ]
)
def test_pop_segment(segment_vm: str, segment_hack: Literal["LCL", "ARG", "THIS", "THAT"]):

    vm_program = f"""
        pop {segment_vm} 0
        pop {segment_vm} 2
        pop {segment_vm} 1
    """

    compy = Compy386(translate(vm_program))
    compy.set_segment_base(segment_hack, 1000)
    compy.push(100)
    compy.push(101)
    compy.push(102)
    compy.run(print_line=False, print_registers=False)

    assert compy.depth() == 0
    assert compy.get_in_segment(segment_hack, 0) == 102
    assert compy.get_in_segment(segment_hack, 2) == 101
    assert compy.get_in_segment(segment_hack, 1) == 100


# ==== Project 8 tests

def test_strip_comments():
    program = """

        when in disgrace with fortune and men's eyes// no whitespace

        // bare comment
        // bear comment

        i all alone beweep my outcast state // extra space
    """

    expected = """

        when in disgrace with fortune and men's eyes

        
        

        i all alone beweep my outcast state 
    """

    assert remove_comments(program) == expected

def test_remove_whitespace():

    # Note that there is some trailing whitespace here
    program = """

    a = 3
    b = 4       

    """
    stript = remove_whitespace(program)

    expected = "a = 3\nb = 4"
    assert stript == expected


def test_write_label():

    vm_program = f"""
        label A
        push constant 0
        label B
    """

    # The first and last lines of the compiled program should be labels.

    hack_program = remove_whitespace(remove_comments(translate(vm_program, "default")))
    lines = hack_program.splitlines()
    assert lines[0] == "(default.A)"
    assert lines[-1] == "(default.B)"

def test_goto():
    """Check that a program with a goto skips the intervening lines."""
    vm_program = f"""
        goto B
        push constant 0
        push constant 1
        push constant 2
        label B
    """

    hack = translate(vm_program)
    
    compy = Compy386(hack)
    compy.run()

    # If we skipped the three push commands, the stack will be empty.
    assert compy.depth() == 0


test_goto()
