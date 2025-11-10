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

    assert out == []

    assert len(c.local_symbols) == 1
    assert len(c.static_symbols) == 0

    assert c.local_symbols["alfalfa"] == Symbol("alfalfa", "var", "char", 0)


def test_var_dec_class():
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

    jack = dedent("""
        static Orb round_guy;
    """)

    c = Compiler(code=jack)
    out = c.compile_class_var_dec()

    assert out == []

    assert len(c.local_symbols) == 0
    assert len(c.static_symbols) == 1

    assert c.static_symbols["round_guy"] == Symbol("round_guy", "static", "Orb", 0)


