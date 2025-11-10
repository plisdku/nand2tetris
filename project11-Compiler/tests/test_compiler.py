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
    c.local_symbols.insert("x", "var", "int")
    c.local_symbols.insert("y", "var", "int")

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
    """
    Test true, false, null, this.
    """
    c = Compiler(code=jack)
    out = "\n".join(c.compile_expression())
    assert out == expected


def test_array_expression():
    """
    Test array indexing, e.g. x[10]
    """

    c = Compiler(code="x[10]")
    c.static_symbols.insert("x", "static", "int")
    out = "\n".join(c.compile_expression())

    expected = dedent("""
        push static 0
        push constant 10
        add
        pop pointer 1
        push that 0
    """).strip()

    assert out == expected


@pytest.mark.parametrize("op,vm_op", [
    ("-", "neg"),
    ("~", "not"),
])
def test_unary_expression(op: str, vm_op: str):
    """
    Unary expressions like -1, ~1
    """
    c = Compiler(code=f"{op}1")
    out = "\n".join(c.compile_expression())
    expected = dedent(f"""
        push constant 1
        {vm_op}
    """).strip()
    assert out == expected


def test_let_statement_vector():
    """
    Test set value to array, x[10] = 1
    """

    c = Compiler(code="let x[10] = 1;")
    c.local_symbols.insert("x", "var", "int")
    out = "\n".join(c.compile_statement())

    expected = dedent("""
        push local 0
        push constant 10
        add
        push constant 1
        pop temp 0
        pop pointer 1
        push temp 0
        pop that 0
    """).strip()

    assert out == expected


def test_let_statement_scalar():
    """
    Test set value to scalar, z = 10
    """

    c = Compiler(code="let z = 10;")
    c.local_symbols.insert("z", "var", "int")
    out = "\n".join(c.compile_statement())

    expected = dedent("""
        push constant 10
        pop local 0
    """).strip()

    assert out == expected


def test_if_statement_without_else():
    """
    Test if statement.
    """

    jack = dedent("""
        if (1) {
            let x = 3;
        }
    """)

    c = Compiler(code = jack)
    c.local_symbols.insert("x", "var", "int")
    out = "\n".join(c.compile_statement())

    expected = dedent("""
        push constant 1
        if-goto IF_TRUE_0
        goto IF_END_0
        label IF_TRUE_0
        push constant 3
        pop local 0
        label IF_END_0
    """).strip()

    assert out == expected


def test_if_else_statement():
    """
    Test if-else statement.
    """

    jack = dedent("""
        if (1) {
            let x = 3;
        }
        else {
            let x = 4;
        }
    """)

    c = Compiler(code = jack)
    c.local_symbols.insert("x", "var", "int")
    out = "\n".join(c.compile_statement())

    expected = dedent("""
        push constant 1
        if-goto IF_TRUE_0
        push constant 4
        pop local 0
        goto IF_END_0
        label IF_TRUE_0
        push constant 3
        pop local 0
        label IF_END_0
    """).strip()

    assert out == expected

def test_while_statement():
    """
    Test while statement
    """

    jack = dedent("""
        while (1) {
            let x = 3;
        }
    """)

    c = Compiler(code=jack)
    c.local_symbols.insert("x", "var", "int")
    out = "\n".join(c.compile_statement())

    expected = dedent("""
        label WHILE_START_0
        push constant 1
        not
        if-goto WHILE_END_0
        push constant 3
        pop local 0
        goto WHILE_START_0
        label WHILE_END_0
    """).strip()

    assert out == expected







#