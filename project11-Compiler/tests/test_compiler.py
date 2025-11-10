import pytest
from jack_compiler import compile_jack, Compiler, CompilerError
from textwrap import dedent
from symbol_table import Symbol

def test_var_dec_two_ints():
    """
    Declaer two int-valued local variables.
    """

    jack = dedent("""
        var int x, y;
    """)

    c = Compiler(code=jack)
    out = c.compile_var_dec()

    # assert out is None

    assert len(c.local_symbols) == 2
    assert len(c.static_symbols) == 0

    assert c.local_symbols["x"] == Symbol("x", "var", "int", 0)
    assert c.local_symbols["y"] == Symbol("y", "var", "int", 1)


def test_var_dec_char():
    """
    Declare a char local variable.
    """

    jack = dedent("""
        var char alfalfa;
    """)

    c = Compiler(code=jack)
    out = c.compile_var_dec()

    assert out == []

    assert len(c.local_symbols) == 1
    assert len(c.static_symbols) == 0

    assert c.local_symbols["alfalfa"] == Symbol("alfalfa", "var", "char", 0)


def test_var_dec_class():
    """
    Declare a local variable of type Unicorn.
    """
    jack = dedent("""
        var Unicorn xyzzy;
    """)

    c = Compiler(code=jack)
    out = c.compile_var_dec()

    assert out == []

    assert len(c.local_symbols) == 1
    assert len(c.static_symbols) == 0

    assert c.local_symbols["xyzzy"] == Symbol("xyzzy", "var", "Unicorn", 0)


def test_class_var_dec_two_fields():
    """
    Declare two char-valued fields.
    """
    jack = dedent("""
        field char ww, zz;
    """)

    c = Compiler(code=jack)
    out = c.compile_class_var_dec()

    assert out == []

    assert len(c.local_symbols) == 0
    assert len(c.static_symbols) == 2

    assert c.static_symbols["ww"] == Symbol("ww", "field", "char", 0)
    assert c.static_symbols["zz"] == Symbol("zz", "field", "char", 1)

def test_class_var_dec_static():
    """
    Declare a static variable of type Orb.
    """

    jack = dedent("""
        static Orb round_guy;
    """)

    c = Compiler(code=jack)
    out = c.compile_class_var_dec()

    assert out == []

    assert len(c.local_symbols) == 0
    assert len(c.static_symbols) == 1

    assert c.static_symbols["round_guy"] == Symbol("round_guy", "static", "Orb", 0)


def test_expression_arithmetic():
    """
    Test some simple arithmetic expressions.
    """

    jack = "1+2"

    c = Compiler(code=jack)
    out = "\n".join(c.compile_expression())
    expected = dedent("""
        push constant 1
        push constant 2
        add
    """).strip()

    assert out == expected


def test_expression_string():
    """
    A string all by itself
    """

    jack = '"hello"'   # codes: 104 101 108 108 111

    c = Compiler(code=jack)
    out = "\n".join(c.compile_expression())
    expected = dedent(f"""
        push constant {len('hello')}
        call String.new 1
        push constant 104
        call String.appendChar 1
        push constant 101
        call String.appendChar 1
        push constant 108
        call String.appendChar 1
        push constant 108
        call String.appendChar 1
        push constant 111
        call String.appendChar 1
    """).strip()

    assert out == expected


def test_expression_parens():
    """
    Math expression using parentheses
    """

    jack = "(x+y)-(1+2)"

    c = Compiler(code=jack)
    c.local_symbols.insert("x", "local", "int")
    c.local_symbols.insert("y", "local", "int")

    out = "\n".join(c.compile_expression())

    expected = dedent(f"""
        push local 0
        push local 1
        add
        push constant 1
        push constant 2
        add
        sub
    """).strip()

    assert out == expected

def test_expression_multiply_divide():
    """
    Math expression with * and /, which are OS functions.
    """

    jack = "3 * 2 / 4"

    c = Compiler(code=jack)

    out = "\n".join(c.compile_expression())

    expected = dedent(f"""
        push constant 3
        push constant 2
        call Math.multiply 2
        push constant 4
        call Math.divide 2
    """).strip()

    assert out == expected


@pytest.mark.parametrize(
    "jack,expected",
    [
        ("true", "push constant 0\nnot"),
        ("false", "push constant 0"),
        ("null", "push constant 0"),
        ("this", "push pointer 0"),
    ],
)
def test_keyword_expression(jack: str, expected: str):
    c = Compiler(code=jack)
    out = "\n".join(c.compile_expression())
    assert out == expected













#