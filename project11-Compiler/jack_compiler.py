from __future__ import annotations

import logging
from typing import Collection, List, Optional, Tuple, cast
from jack_element import Element
from jack_tokenizer import escape_token, tokenize
from symbol_table import SymbolTable, KIND, Symbol

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(funcName)s: %(message)s"
)
log = logging.getLogger(__name__)


def remove_whitespace(program: str) -> str:
    """
    Remove leading and trailing whitespace from each line, and remove empty lines.
    """

    out_lines = []

    for line in program.splitlines():
        stript = line.strip()
        if stript:
            out_lines.append(stript)
    return "\n".join(out_lines)


class CompilerError(Exception):
    pass


def compile_jack(code: str) -> str:
    tokens = tokenize(code)
    return compile_elements(tokens)

def compile_elements(tokens: List[Element]) -> str:
    compiler = Compiler(tokens)
    return "\n".join(compiler.compile_elements())


"""
VM command reference:

push [segment] [index]
pop [segment] [index]

segments are (argument, local, static, constant, this, that, pointer, temp)

add, sub, neg
eq, gt, lt
and, or, not

label [label]
goto [label]
if-goto [label]

function [functionName] [nVars]
call [functionName] [nArgs]
return
"""


SEGMENT_FOR_KIND = {
    "arg": "argument",
    "var": "local",
    "field": "this",
    "static": "static"
}


BINARY_OPS_MAP = {
    "+": "add",
    "*": "call Math.multiply 2",
    "/": "call Math.divide 2",
    "-": "sub",
    "=": "eq",
    ">": "gt",
    "<": "lt",
    "&": "and",
    "|": "or",
}

UNARY_OPS_MAP = {
    "-": "neg",
    "~": "not"
}


class Labeler:
    def __init__(self, prefix: str):
        self.prefix: str = prefix
        self.count: int = 0

    def new(self) -> str:
        label = f"{self.prefix}_{self.count}"
        self.count += 1
        return label


class Compiler:
    def __init__(self, tokens: Optional[List[Element]] = None, code: Optional[str] = None):
        self.idx = 0

        if tokens is None:
            assert code is not None
            tokens = tokenize(code)
        else:
            assert code is None

        self.tokens: List[Element] = tokens
        self.static_symbols: SymbolTable = SymbolTable()
        self.local_symbols: SymbolTable = SymbolTable()

        self.if_true = Labeler("IF_TRUE")
        self.if_false = Labeler("IF_FALSE")
        self.if_end = Labeler("IF_END")
        self.while_start = Labeler("WHILE_START")
        self.while_end = Labeler("WHILE_END")


    def get_symbol(self, name: str) -> Symbol:
        if name in self.local_symbols:
            return self.local_symbols[name]
        else:
            return self.static_symbols[name]

    def compile_elements(self):
        self.idx = 0
        return self.compile_class() 

    def peek(
        self,
        category: str | Collection[str] | None = None,
        value: str | Collection[str] | None = None,
        ahead: int = 1
    ) -> Element | None:
        """
        Get the next element without advancing the cursor.
        """
        if self.idx + ahead > len(self.tokens):
            return None

        token = self.tokens[self.idx + ahead - 1]

        if category is not None:
            if isinstance(category, str):
                if token.category != category:
                    return None
            else:
                if token.category not in category:
                    return None
        if value is not None:
            if isinstance(value, str):
                if token.content != value:
                    return None
            else:
                if token.content not in value:
                    return None

        return token

    def next(self, category: str | Collection[str] | None = None, value: str | Collection[str] | None = None) -> Element:
        token = self.tokens[self.idx]

        if category is not None:
            if isinstance(category, str):
                if token.category != category:
                    raise CompilerError(f"Expected ({category!r}, {value!r}); got {token}")
            else:
                if token.category not in category:
                    raise CompilerError(f"Expected ({category!r}, {value!r}); got {token}")
        if value is not None:
            if isinstance(value, str):
                if token.content != value:
                    raise CompilerError(f"Expected ({category!r}, {value!r}); got {token}")
            else:
                if token.content not in value:
                    raise CompilerError(f"Expected ({category!r}, {value!r}); got {token}")

        self.idx += 1

        logging.info(f"{token}")
        return token

    def compile_class(self) -> List[str]:
        """
        Compile a class. The first token should be the 'class' keyword.

        'class' className '{' classVarDec* subroutineDec* '}'
        """
        logging.info("class")
        lines: List[str] = []

        # 'class'
        self.next("keyword", "class")

        # className
        class_name = self.next("identifier")
        assert isinstance(class_name.content, str)

        # '{'
        self.next("symbol", "{")

        while self.peek("keyword", ("static", "field")):
            self.compile_class_var_dec()

        log.info("Static symbols:")
        for symbol in self.static_symbols:
            log.info(f"\t{symbol.index}: {SEGMENT_FOR_KIND[symbol.kind]} {symbol.type} {symbol.name}")

        while self.peek("keyword", ("constructor", "function", "method")):
            lines.extend(self.compile_subroutine_dec(class_name.content))

        # '}'
        self.next("symbol", "}")

        # return Element("class", elems)
        return lines


    def compile_class_var_dec(self) -> List[str]:  # TESTED
        """
        Compile a classVarDec:

        ('static' | 'field') type varName (',', varName)* ';'
        """
        logging.info("classVarDec")
        lines: List[str] = []

        # 'static' | 'field'
        var_kind = self.next("keyword", ("static", "field"))

        # type
        if self.peek("keyword", ("int", "char", "boolean")):
            var_type = self.next()
        else:
            var_type = self.next("identifier") # custom type 

        var_name = self.next("identifier")

        assert isinstance(var_name.content, str)
        assert isinstance(var_kind.content, str)
        assert isinstance(var_type.content, str)
        kind = cast(KIND, var_kind.content)
        self.static_symbols.insert(var_name.content, kind, var_type.content)

        # (',', varName)* ';'
        while self.peek("symbol", ","):
            self.next("symbol", ",")
            var_name = self.next("identifier")

            assert isinstance(var_name.content, str)
            self.static_symbols.insert(var_name.content, kind, var_type.content)


        # ';'
        self.next("symbol", ";")


        # return Element("classVarDec", elems)
        return lines

    def compile_subroutine_dec(self, class_name: str) -> List[str]:
        """
        Compile a subroutineDec:

        ('constructor' | 'function' | 'method') ('void' | type) subroutineName
        '(' parameterList ')' subroutineBody
        """
        logging.info("subroutineDec")

        self.local_symbols.reset()

        if self.peek("keyword", "constructor"):
            return self.compile_constructor_dec(class_name)
        elif self.peek("keyword", "function"):
            return self.compile_function_dec(class_name)
        else:
            assert self.peek("keyword", "method")
            return self.compile_method_dec(class_name)

        # log.info("Local symbols:")
        # for symbol in self.local_symbols:
        #     log.info(f"\t{symbol.index}: {SEGMENT_FOR_KIND[symbol.kind]} {symbol.type} {symbol.name}")

    def compile_constructor_dec(self, class_name: str) -> List[str]:
        """
        'constructor' type subroutineName '(' parameterList ')' subroutineBody
        """
        lines: List[str] = []

        self.next("keyword", "constructor")
        return_type = self.next("identifier")
        assert isinstance(return_type.content, str)
        assert return_type.content == class_name

        subroutine_name = self.next("identifier")
        assert isinstance(subroutine_name.content, str)

        # parameters
        self.next("symbol", "(")
        parameters = self.compile_parameter_list()
        assert parameters == [] # no code, just symbol creation
        self.next("symbol", ")")

        body = self.compile_subroutine_body()

        # Determine how many fields to allocate
        num_fields = self.static_symbols.count("field")

        lines.append(f"function {class_name}.{subroutine_name.content} {len(parameters)}")
        lines.append(f"push constant {num_fields}")
        lines.append("call Memory.alloc 1")
        lines.append("pop pointer 0") # set "this" to whatever came back from alloc()
        lines.extend(body)

        return lines

    def compile_method_dec(self, class_name: str) -> List[str]:
        """
        'method' ('void' | type) subroutineName '(' parameterList ')' subroutineBody
        """
        lines: List[str] = []
        self.next("keyword", "method")
        self.next("keyword", ("void", "int", "char", "boolean")) # return type

        subroutine_name = self.next("identifier")
        assert isinstance(subroutine_name.content, str)

        # parameters
        self.next("symbol", "(")
        parameters = self.compile_parameter_list()
        assert parameters == [] # no code, just symbol creation
        self.next("symbol", ")")

        body = self.compile_subroutine_body()

        lines.append(f"function {class_name}.{subroutine_name.content} {self.local_symbols.count('arg')}")
        lines.extend(body)
        return lines

    def compile_function_dec(self, class_name) -> List[str]:
        """
        'function' ('void' | type) subroutineName '(' parameterList ')' subroutineBody
        """
        lines: List[str] = []
        self.next("keyword", "function")
        self.next("keyword", ("void", "int", "char", "boolean")) # return type

        subroutine_name = self.next("identifier")
        assert isinstance(subroutine_name.content, str)

        # parameters
        self.next("symbol", "(")
        parameters = self.compile_parameter_list()
        assert parameters == [] # no code, just symbol creation
        self.next("symbol", ")")

        body = self.compile_subroutine_body()

        lines.append(f"function {class_name}.{subroutine_name.content} {self.local_symbols.count('arg')}")
        lines.extend(body)
        return lines

    def compile_parameter_list(self) -> List[str]:
        """
        ( (type varName) (',' type varName)* )?
        """
        logging.info("parameterList")
        lines: List[str] = []

        # Zero or one

        if self.peek("keyword", ("int", "char", "boolean")):
            var_type = self.next()
            var_name = self.next("identifier")

            assert isinstance(var_type.content, str)
            assert isinstance(var_name.content, str)
            self.local_symbols.insert(var_name.content, "arg", var_type.content)

            # (',' type varName)*
            while self.peek("symbol", ","):
                self.next()
                var_type = self.next("keyword", ("int", "char", "boolean"))
                var_name = self.next("identifier")

                assert isinstance(var_type.content, str)
                assert isinstance(var_name.content, str)
                self.local_symbols.insert(var_name.content, "arg", var_type.content)

        assert lines == []
        return lines

    def compile_subroutine_body(self) -> List[str]:
        """
        '{' varDec* statements '}'
        
        Generates VM code for the body of a subroutine.
        """
        logging.info("subroutineBody")
        lines: List[str] = []

        self.next("symbol", "{")

        while self.peek("keyword", "var"):
            self.compile_var_dec()

        lines.extend(self.compile_statements())

        self.next("symbol", "}")

        # return Element("subroutineBody", elems)
        return lines


    def compile_var_dec(self) -> List[str]:  # TESTED
        """
        'var' type varName (',' varName)* ';'
        
        Insert a variable into the symbol table.

        Returns:
            None
        """
        logging.info("varDec")
        lines: List[str] = []

        self.next("keyword", "var")
        var_type = self.next(("keyword", "identifier")) # type

        var_name = self.next("identifier") # var name

        assert isinstance(var_type.content, str)
        assert isinstance(var_name.content, str)
        self.local_symbols.insert(var_name.content, "var", var_type.content)

        while self.peek("symbol", ","):
            self.next() # ",
            var_name = self.next("identifier")

            assert isinstance(var_name.content, str)
            self.local_symbols.insert(var_name.content, "var", var_type.content)

        self.next("symbol", ";")

        # return Element("varDec", elems)
        return lines

    def compile_statements(self) -> List[str]: # TESTED
        """
        statement*
        """
        logging.info("statements")
        lines: List[str] = []

        while self.peek("keyword", ("let", "if", "while", "do", "return")):
            lines.extend(self.compile_statement())

        # return Element("statements", elems)
        return lines

    def compile_statement(self) -> List[str]:
        """
        letStatement | ifStatement | whileStatement | doStatement | returnStatement
        """
        logging.info("statement")
        if self.peek("keyword", "let"): # TESTED
            return self.compile_let_statement()
        elif self.peek("keyword", "if"): # TESTED
            return self.compile_if_statement()
        elif self.peek("keyword", "while"): # TESTED
            return self.compile_while_statement()
        elif self.peek("keyword", "do"):
            assert False
            return self.compile_do_statement()
        else:
            return self.compile_return_statement()

    def compile_let_statement(self) -> List[str]: # TESTED
        """
        'let' varName ('[' expression ']')? '=' expression ';'
        """
        logging.info("let")
        lines: List[str] = []

        self.next("keyword", "let")
        var_name = self.next("identifier")
        assert isinstance(var_name.content, str)

        assert isinstance(var_name.content, str)
        log.info(f"let {var_name.content}: {self.get_symbol(var_name.content)}")

        if self.peek("symbol", "["):
            # set array: x[y] = z
            self.next()
            indexing_expression = self.compile_expression()

            self.next("symbol", "]")
            self.next("symbol", "=")
            value_expression = self.compile_expression()
            self.next("symbol", ";")

            symbol = self.get_symbol(var_name.content)
            lines.append(f"push {SEGMENT_FOR_KIND[symbol.kind]} {symbol.index}")
            lines.extend(indexing_expression)
            lines.append("add")
            # address to write to is at the top of the stack

            lines.extend(value_expression)
            lines.append("pop temp 0")

            # now the address to write to is at the top of the stack again
            lines.append("pop pointer 1")
            lines.append("push temp 0")
            lines.append("pop that 0")
        else:
            # set scalar: x = y

            self.next("symbol", "=")
            value_expression = self.compile_expression()
            self.next("symbol", ";")

            symbol = self.get_symbol(var_name.content)
            lines.extend(value_expression)

            # kind, segment
            #
            # var, local
            # static, static
            # field, this
            # arg, argument
            lines.append(f"pop {SEGMENT_FOR_KIND[symbol.kind]} {symbol.index}")

        return lines

    def compile_if_statement(self) -> List[str]: # TESTED
        """
        'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        """
        logging.info("if")
        lines: List[str] = []

        self.next("keyword", "if")
        self.next("symbol", "(")
        condition = self.compile_expression()
        self.next("symbol", ")")

        self.next("symbol", "{")
        if_statements = self.compile_statements()
        self.next("symbol", "}")

        if_true = self.if_true.new()
        if_end = self.if_end.new()

        if self.peek("keyword", "else"):
            self.next()
            self.next("symbol", "{")
            else_statements = self.compile_statements()
            self.next("symbol", "}")

            lines.extend(condition)
            lines.append(f"if-goto {if_true}")
            lines.extend(else_statements)
            lines.append(f"goto {if_end}")
            lines.append(f"label {if_true}")
            lines.extend(if_statements)
            lines.append(f"label {if_end}")
        else:
            lines.extend(condition)
            lines.append(f"if-goto {if_true}")
            lines.append(f"goto {if_end}")
            lines.append(f"label {if_true}")
            lines.extend(if_statements)
            lines.append(f"label {if_end}")

        return lines

    def compile_while_statement(self) -> List[str]: # TESTED
        """
        'while' '(' expression ')' '{' statements '}'
        """
        logging.info("while")
        lines: List[str] = []

        self.next("keyword", "while")
        self.next("symbol", "(")
        condition = self.compile_expression()
        self.next("symbol", ")")
        self.next("symbol", "{")
        while_statements = self.compile_statements()
        self.next("symbol", "}")

        while_start = self.while_start.new()
        while_end = self.while_end.new()

        lines.append(f"label {while_start}")
        lines.extend(condition)
        lines.append("not")
        lines.append(f"if-goto {while_end}")
        lines.extend(while_statements)
        lines.append(f"goto {while_start}")
        lines.append(f"label {while_end}")

        return lines

    def compile_do_statement(self) -> List[str]:
        """
        'do' subroutineCall ';'
        """
        assert False
        logging.info("do")
        lines: List[str] = []

        self.next("keyword", "do")
        subroutine = self.compile_subroutine_call()
        self.next("symbol", ";")

        lines.extend(subroutine)
        lines.append("pop temp 0")  # dump the unwanted result

        return lines

    def compile_return_statement(self) -> List[str]: # TESTED
        """
        'return' expression? ';'
        """
        logging.info("return")
        lines: List[str] = []

        self.next("keyword", "return")

        if self.peek("symbol", ";"):
            # by convention, void functions still return 0
            lines.append("push constant 0")
            self.next()
        else:
            lines.extend(self.compile_expression())
            self.next("symbol", ";")

        lines.append("return")


        return lines

    def compile_expression(self) -> List[str]: # TESTED
        """
        term (op term)*
        """
        logging.info("expression")
        lines: List[str] = []

        lines.extend(self.compile_term())

        # something should be on the stack

        while self.peek("symbol", ("+", "-", "*", "/", "&", "|", "<", ">", "=")):
            operator = self.next()
            lines.extend(self.compile_term())

            # put the term's value on the stack
            # do the correct operation

            assert isinstance(operator.content, str)
            lines.append(BINARY_OPS_MAP[operator.content])

        return lines

    def compile_term(self) -> List[str]:  # TESTED
        """
        integerConstant | stringConstant | keywordConstant | varName |
        varName '[' expression ']' | '(' expression ')' | (unaryOp term) | subroutineCall

        This will push a value onto the stack.
        """

        logging.info("term")
        lines: List[str] = []

        if self.peek(("integerConstant", "stringConstant")):
            constant = self.next()
            assert isinstance(constant.content, str)

            if constant.category == "integerConstant":
                lines.append(f"push constant {constant.content}")
            else:
                assert isinstance(constant.content, str)
                # the constructor pushes the address of the allocated
                # memory block.
                lines.append(remove_whitespace(f"""
                    push constant {len(constant.content)}
                    call String.new 1
                """))

                for char in constant.content:
                    # TODO: implement proper Hack character set, which isn't extended ASCII
                    hack_code = ord(char)
                    lines.append(remove_whitespace(f"""
                        push constant {hack_code}
                        call String.appendChar 1
                    """))

        elif self.peek("keyword", ("true", "false", "null", "this")): # TESTED
            constant = self.next()
            assert isinstance(constant.content, str)

            if constant.content == "true":
                lines.extend(["push constant 0", "not"])
            elif constant.content in ("false", "null"):
                lines.append("push constant 0")
            else:
                assert constant.content == "this"
                lines.append("push pointer 0")

        elif self.peek("identifier"):
            # Could be varName, varName[expression], or subroutineCall

            if self.peek("symbol", ("(", "."), ahead=2):
                # subroutineCall

                subroutine_lines = self.compile_subroutine_call()
                lines.extend(subroutine_lines)
            elif self.peek("symbol", "[", ahead=2): # TESTED
                # varName[expression]

                var_name = self.next("identifier")
                assert isinstance(var_name.content, str)
                symbol = self.get_symbol(var_name.content)
                log.info(f"var [] reference: {symbol}")

                lines.append(f"push {SEGMENT_FOR_KIND[symbol.kind]} {symbol.index}")

                self.next("symbol", "[")
                lines.extend(self.compile_expression())
                self.next("symbol", "]")

                lines.append("add") # add array base address to expression result
                lines.append("pop pointer 1")
                lines.append("push that 0")
            else: # TESTED
                # varName
                var_name = self.next("identifier")
                assert isinstance(var_name.content, str)
                symbol = self.get_symbol(var_name.content)
                log.info(f"var reference: {symbol}")

                lines.append(f"push {SEGMENT_FOR_KIND[symbol.kind]} {symbol.index}")

        elif self.peek("symbol", "("): # TESTED
            self.next()
            lines.extend(self.compile_expression())
            self.next("symbol", ")")
        else:
            # tested
            operator = self.next("symbol", ("-", "~"))
            assert isinstance(operator.content, str)
            lines.extend(self.compile_term())
            lines.append(f"{UNARY_OPS_MAP[operator.content]}")

        return lines

    def compile_subroutine_call(self) -> List[str]:
        """
        subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName
        '(' expressionList ')'

        Jack features two kinds of method call:

            varName.method(...)
            method(...)

        The second one has "this" implicitly as the variable.
        """
        logging.info("subroutine")
        lines: List[str] = []

        if self.peek("symbol", "(", ahead=2):
            # subroutineName

            # This one implicitly calls this.something().
            # We push "this" manually as an argument, and add one
            # to the number of args in the call statement.

            func_name = self.next("identifier")
            assert isinstance(func_name.content, str)

            self.next("symbol", "(")
            expressions, num_expressions = self.compile_expression_list()
            self.next("symbol", ")")

            lines.append("push argument 0")  # arg 0 is "this"
            lines.extend(expressions)
            lines.append(f"call {func_name.content} {num_expressions+1}")

        else:
            # (className | varName) . subroutineName ( expressionList )

            assert self.peek("symbol", ".", ahead=2)

            obj = self.next("identifier")
            assert isinstance(obj.content, str)
            self.next("symbol", ".")
            func_name = self.next("identifier")
            assert isinstance(func_name.content, str)

            self.next("symbol", "(")
            expressions, num_expressions = self.compile_expression_list()
            self.next("symbol", ")")

            # Is this a function or method?
            if obj.content in self.local_symbols or obj.content in self.static_symbols:
                # It's a method being called on a specific object.
                # We have to push that object as the first argument.

                # Example: `my_str.len()` becomes `call String.len 0`

                symbol = self.get_symbol(obj.content)
                lines.append(f"push {SEGMENT_FOR_KIND[symbol.kind]} {symbol.index}")
                lines.extend(expressions)
                lines.append(f"call {symbol.type}.{func_name.content} {num_expressions+1}")
            else:
                # It's a function; obj.content is a class name like String.

                lines.extend(expressions)
                lines.append(f"call {obj.content}.{func_name.content} {num_expressions}")

        return lines

    def compile_expression_list(self) -> Tuple[List[str], int]:
        """
        (expression (',' expression)* )?

        Returns:
            list of VM code lines
            number of expressions
        """
        logging.info("expressionList")
        lines: List[str] = []

        num_expressions: int = 0

        if self.peek("symbol", ")"):
            return [], 0
            # return Element("expressionList", elems)

        lines.extend(self.compile_expression())
        num_expressions += 1

        while self.peek("symbol", ","):
            self.next()
            lines.extend(self.compile_expression())
            num_expressions += 1

        return lines, num_expressions



def write_element_xml_lines(element: Element, indent: int = 0) -> List[str]:
    """
    Convert a list of tokens to XML.

    The outermost XML element is <tokens>. Then on separate lines,
    each token is written <{category}> {token} </{category}>, including
    the whitespace around the token.
    """

    tab = " "*2*indent

    xml_lines: List[str] = []

    if isinstance(element.content, str):
        xml_lines.append(f"{tab}<{element.category}> {escape_token(element.content)} </{element.category}>")
    else:
        xml_lines.append(f"{tab}<{element.category}>")
        for elem in element.content:
            xml_lines.extend(write_element_xml_lines(elem, indent+1))
        xml_lines.append(f"{tab}</{element.category}>")

    return xml_lines


def main():
    import argparse
    import pathlib
    from jack_paths import handle_jack_xml_paths
    from jack_tokenizer import read_xml, tokenize

    parser = argparse.ArgumentParser("JackAnalyzer")
    parser.add_argument(
        "input",
        type=pathlib.Path
    )
    parser.add_argument(
        "output",
        type=pathlib.Path,
        nargs="?",
        default="out"
    )

    args = parser.parse_args()

    in_paths, out_paths = handle_jack_xml_paths(args.input, args.output, add_T=False, in_suffixes=(".jack",))

    for _in, _out in zip(in_paths, out_paths):
        logging.info(f"Analyze {str(_in)} => {str(_out)}")
        _out.parent.mkdir(parents=True, exist_ok=True)

        if _in.suffix == ".jack":
            # Tokenize the jack
            tokens = tokenize(_in.read_text())
        elif _in.stem.endswith("T") and _in.suffix == ".xml":
            # It's a token file
            tokens = read_xml(_in.read_text())
        else:
            tokens = None

        if tokens is not None:
            xml_lines = write_element_xml_lines(compile(tokens))
            _out.write_text("\n".join(xml_lines))

if __name__ == '__main__':
    main()





