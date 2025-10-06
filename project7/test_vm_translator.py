from os import initgroups
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
    # Initialize SP = 256.
    # Write something to an offset at each segment
    # and push it to the stack.

    vm_program = """
    push constant -1
    push constant 0
    push constant 1
    """

    compy = Compy386(translate(vm_program))
    compy.run() #print_line=True)

    assert compy.depth() == 2
    assert compy.peek() == 1
    assert compy.peek(1) == 0
    assert compy.peek(2) == (-1 & 0xFFFF)

def test_pop():
    pass