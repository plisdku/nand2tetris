from typing import Callable, Literal
import pytest
from hackulator import Compy386
from VMTranslator import translate
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



def test_pop():
    pass