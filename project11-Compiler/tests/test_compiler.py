from jack_compiler import compile_jack, Compiler, CompilerError
from textwrap import dedent
from symbol_table import Symbol

def test_var_dec_two_ints():
    """
    
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
    
    """

    jack = dedent("""
        var char alfalfa;
    """)

    c = Compiler(code=jack)
    out = c.compile_var_dec()

    # assert out is None

    assert len(c.local_symbols) == 1
    assert len(c.static_symbols) == 0

    assert c.local_symbols["alfalfa"] == Symbol("alfalfa", "var", "char", 0)

def test_var_dec_class():
    jack = dedent("""
        var Unicorn xyzzy;
    """)

    c = Compiler(code=jack)
    out = c.compile_var_dec()

    # assert out is None

    assert len(c.local_symbols) == 1
    assert len(c.static_symbols) == 0

    assert c.local_symbols["xyzzy"] == Symbol("xyzzy", "var", "Unicorn", 0)

