import pytest
from hackulator import Compy386
from VMTranslator import translate

def test_eq():

    # vm_code = "eq"
    # hack_code = translate(vm_code)

    # compy = Compy386("\n".join(hack_code))
    # print(compy.depth())
    # compy.push(1)
    # print(compy.depth())
    # compy.push(2)
    # assert compy.depth() == 2
    # compy.step()
    # assert compy.depth() == 1
    # print(compy.peek())
    pass

def test_gt():
    pass

def test_lt():
    pass

def test_not():
    pass

def test_and():
    pass

def test_or():
    pass

def test_add():
    pass

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

    assert compy.depth() == 2
    assert compy.peek() == 1
    assert compy.peek(1) == 0
    assert compy.peek(2) == (-1 & 0xFFFF)


@pytest.mark.parametrize(("segment_vm", "segment_hack"),
    [("local", "LCL"), ("this", "THIS"), ("that", "THAT"), ("arg", "ARG"), ("temp", "TEMP")]
)
def test_push(segment_vm: str, segment_hack: str):

    segment_vm = "local"
    segment_hack = "LCL"

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

    assert compy.depth() == 2
    assert compy.peek() == -11 & 0xFFFF
    assert compy.peek(1) == 12
    assert compy.peek(2) == 10



def test_pop():
    pass