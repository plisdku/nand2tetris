from hackulator import Compy386
from VMTranslator import translate

def test_eq():

    vm_code = "eq"
    hack_code = translate([vm_code])

    compy = Compy386("\n".join(hack_code))
    print(compy.depth)
    compy.push(1)
    print(compy.depth)
    compy.push(2)
    assert compy.depth == 2
    compy.step()
    assert compy.depth == 1
    print(compy.peek())
    pass

test_eq()

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

def test_push():
    pass

def test_pop():
    pass