from __future__ import annotations

import logging
from typing import Collection, List
from jack_element import Element
from jack_tokenizer import escape_token

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s:%(funcName)s: %(message)s"
)
log = logging.getLogger(__name__)

class AnalyzerError(Exception):
    pass

def analyze(tokens: List[Element]) -> Element:
    analyzer = SyntaxAnalyzer(tokens)
    return analyzer.analyze()

class SyntaxAnalyzer:
    def __init__(self, tokens: List[Element]):
        self.idx = 0
        self.tokens: List[Element] = tokens

    def analyze(self):
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
                    raise AnalyzerError(f"Expected ({category!r}, {value!r}); got {token!r}")
            else:
                if token.category not in category:
                    raise AnalyzerError(f"Expected ({category!r}, {value!r}); got {token!r}")
        if value is not None:
            if isinstance(value, str):
                if token.content != value:
                    raise AnalyzerError(f"Expected ({category!r}, {value!r}); got {token!r}")
            else:
                if token.content not in value:
                    raise AnalyzerError(f"Expected ({category!r}, {value!r}); got {token!r}")

        self.idx += 1

        logging.info(f"{token!r}")
        return token

    def compile_class(self) -> Element:
        """
        Compile a class. The first token should be the 'class' keyword.

        'class' className '{' classVarDec* subroutineDec* '}'
        """
        logging.info("class")
        elems: List[Element] = []

        # 'class'
        elems.append(self.next("keyword", "class"))

        # className
        elems.append(self.next("identifier"))

        # '{'
        elems.append(self.next("symbol", "{"))

        while self.peek("keyword", ("static", "field")):
            elems.append(self.compile_class_var_dec())

        while self.peek("keyword", ("constructor", "function", "method")):
            elems.append(self.compile_subroutine_dec())

        # '}'
        elems.append(self.next("symbol", "}"))

        return Element("class", elems)


    def compile_class_var_dec(self) -> Element:
        """
        Compile a classVarDec:

        ('static' | 'field') type varName (',', varName)* ';'
        """
        logging.info("classVarDec")
        elems: List[Element] = []

        # 'static' | 'field'
        elems.append(self.next("keyword", ("static", "field")))

        # type
        if self.peek("keyword", ("int", "char", "boolean")):
            elems.append(self.next())
        else:
            elems.append(self.next("identifier")) # custom type 

        # varName
        elems.append(self.next("identifier"))

        # (',', varName)* ';'
        while self.peek("symbol", ","):
            elems.append(self.next("symbol", ","))
            elems.append(self.next("identifier"))

        # ';'
        elems.append(self.next("symbol", ";"))

        return Element("classVarDec", elems)

    def compile_subroutine_dec(self) -> Element:
        """
        Compile a subroutineDec:

        ('constructor' | 'function' | 'method') ('void' | type) subroutineName
        '(' parameterList ')' subroutineBody
        """
        logging.info("subroutineDec")
        elems: List[Element] = []

        if self.peek("keyword", "constructor"):
            elems.append(self.next())
            elems.append(self.next("identifier")) # class name
        else:
            elems.append(self.next("keyword", ("function", "method")))
            elems.append(self.next("keyword", ("void", "int", "char", "boolean")))

        # subroutineName
        elems.append(self.next("identifier"))

        # parameters
        elems.append(self.next("symbol", "("))
        elems.append(self.compile_parameter_list())
        elems.append(self.next("symbol", ")"))

        elems.append(self.compile_subroutine_body())

        return Element("subroutineDec", elems)

    def compile_parameter_list(self) -> Element:
        """
        ( (type varName) (',' type varName)* )?
        """
        logging.info("parameterList")
        elems: List[Element] = []

        # Zero or one

        if self.peek("keyword", ("int", "char", "boolean")):
            elems.append(self.next()) # type
            elems.append(self.next("identifier")) # varName

            # (',' type varName)*
            while self.peek("symbol", ","):
                elems.append(self.next())
                elems.append(self.next("keyword", ("int", "char", "boolean"))) # type
                elems.append(self.next("identifier")) # varName

        return Element("parameterList", elems)

    def compile_subroutine_body(self) -> Element:
        """
        '{' varDec* statements '}'
        """
        logging.info("subroutineBody")
        elems: List[Element] = []

        elems.append(self.next("symbol", "{"))

        while self.peek("keyword", "var"):
            elems.append(self.compile_var_dec())

        elems.append(self.compile_statements())

        elems.append(self.next("symbol", "}"))

        return Element("subroutineBody", elems)


    def compile_var_dec(self) -> Element:
        """
        'var' type varName (',' varName)* ';'
        """
        logging.info("varDec")
        elems: List[Element] = []

        elems.append(self.next("keyword", "var"))
        elems.append(self.next(("keyword", "identifier"))) # type
        elems.append(self.next("identifier")) # var name

        while self.peek("symbol", ","):
            elems.append(self.next())
            elems.append(self.next("identifier"))

        elems.append(self.next("symbol", ";"))

        return Element("varDec", elems)

    def compile_statements(self) -> Element:
        """
        statement*
        """
        logging.info("statements")
        elems: List[Element] = []

        while self.peek("keyword", ("let", "if", "while", "do", "return")):
            elems.append(self.compile_statement())

        return Element("statements", elems)

    def compile_statement(self) -> Element:
        """
        letStatement | ifStatement | whileStatement | doStatement | returnStatement
        """
        logging.info("statement")
        if self.peek("keyword", "let"):
            return self.compile_let_statement()
        elif self.peek("keyword", "if"):
            return self.compile_if_statement()
        elif self.peek("keyword", "while"):
            return self.compile_while_statement()
        elif self.peek("keyword", "do"):
            return self.compile_do_statement()
        else:
            return self.compile_return_statement()

    def compile_let_statement(self) -> Element:
        """
        'let' varName ('[' expression ']')? '=' expression ';'
        """
        logging.info("let")
        elems: List[Element] = []

        elems.append(self.next("keyword", "let"))
        elems.append(self.next("identifier"))

        if self.peek("symbol", "["):
            elems.append(self.next())
            elems.append(self.compile_expression())
            elems.append(self.next("symbol", "]"))

        elems.append(self.next("symbol", "="))

        elems.append(self.compile_expression())
        elems.append(self.next("symbol", ";"))

        return Element("letStatement", elems)

    def compile_if_statement(self) -> Element:
        """
        'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        """
        logging.info("if")
        elems: List[Element] = []

        elems.append(self.next("keyword", "if"))
        elems.append(self.next("symbol", "("))
        elems.append(self.compile_expression())
        elems.append(self.next("symbol", ")"))

        elems.append(self.next("symbol", "{"))
        elems.append(self.compile_statements())
        elems.append(self.next("symbol", "}"))

        if self.peek("keyword", "else"):
            elems.append(self.next())
            elems.append(self.next("symbol", "{"))
            elems.append(self.compile_statements())
            elems.append(self.next("symbol", "}"))

        return Element("ifStatement", elems)

    def compile_while_statement(self) -> Element:
        """
        'while' '(' expression ')' '{' statements '}'
        """
        logging.info("while")
        elems: List[Element] = []

        elems.append(self.next("keyword", "while"))
        elems.append(self.next("symbol", "("))
        elems.append(self.compile_expression())
        elems.append(self.next("symbol", ")"))
        elems.append(self.next("symbol", "{"))
        elems.append(self.compile_statements())
        elems.append(self.next("symbol", "}"))

        return Element("whileStatement", elems)

    def compile_do_statement(self) -> Element:
        """
        'do' subroutineCall ';'
        """
        logging.info("do")
        elems: List[Element] = []

        elems.append(self.next("keyword", "do"))
        # elems.append(self.compile_subroutine_call()) # not separate element in the grammar
        elems.extend(self.compile_subroutine_call().content)
        elems.append(self.next("symbol", ";"))

        return Element("doStatement", elems)

    def compile_return_statement(self) -> Element:
        """
        'return' expression? ';'
        """
        logging.info("return")
        elems: List[Element] = []

        elems.append(self.next("keyword", "return"))

        if self.peek("symbol", ";"):
            elems.append(self.next())
        else:
            elems.append(self.compile_expression())
            elems.append(self.next("symbol", ";"))

        return Element("returnStatement", elems)

    def compile_expression(self) -> Element:
        """
        term (op term)*
        """
        logging.info("expression")
        elems: List[Element] = []

        elems.append(self.compile_term())

        while self.peek("symbol", ("+", "-", "*", "/", "&", "|", "<", ">", "=")):
            elems.append(self.next())
            elems.append(self.compile_term())

        return Element("expression", elems)

    def compile_term(self) -> Element:
        """
        integerConstant | stringConstant | keywordConstant | varName |
        varName '[' expression ']' | '(' expression ')' | (unaryOp term) | subroutineCall
        """
        logging.info("term")
        elems: List[Element] = []

        if self.peek(("integerConstant", "stringConstant")):
            elems.append(self.next())
        elif self.peek("keyword", ("true", "false", "null", "this")):
            elems.append(self.next())
        elif self.peek("identifier"):
            # Could be varName, varName[expression], or subroutineCall

            if self.peek("symbol", ("(", "."), ahead=2):
                # subroutineCall
                # elems.append(self.compile_subroutine_call())
                elems.extend(self.compile_subroutine_call().content)
            elif self.peek("symbol", "[", ahead=2):
                # varName[expression]
                elems.append(self.next("identifier"))
                elems.append(self.next("symbol", "["))
                elems.append(self.compile_expression())
                elems.append(self.next("symbol", "]"))
            else:
                # varName
                elems.append(self.next("identifier"))
        elif self.peek("symbol", "("):
            elems.append(self.next())
            elems.append(self.compile_expression())
            elems.append(self.next("symbol", ")"))
        else:
            elems.append(self.next("symbol", ("-", "~")))
            elems.append(self.compile_term())

        return Element("term", elems)

    def compile_subroutine_call(self) -> Element:
        """
        subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName
        '(' expressionList ')'
        """
        logging.info("subroutine")
        elems: List[Element] = []

        if self.peek("symbol", "(", ahead=2):
            # subroutineName
            elems.append(self.next("identifier"))
            elems.append(self.next("symbol", "("))
            elems.append(self.compile_expression_list())
            elems.append(self.next("symbol", ")"))
        else:
            # (className | varName) . subroutineName ( expressionList )
            assert self.peek("symbol", ".", ahead=2)

            elems.append(self.next("identifier"))
            elems.append(self.next("symbol", "."))
            elems.append(self.next("identifier"))
            elems.append(self.next("symbol", "("))
            elems.append(self.compile_expression_list())
            elems.append(self.next("symbol", ")"))

        return Element("subroutineCall", elems)

    def compile_expression_list(self) -> Element:
        """
        (expression (',' expression)* )?
        """
        logging.info("expressionList")
        elems: List[Element] = []
        
        if self.peek("symbol", ")"):
            return Element("expressionList", elems)

        elems.append(self.compile_expression())

        while self.peek("symbol", ","):
            elems.append(self.next())
            elems.append(self.compile_expression())

        return Element("expressionList", elems)



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
            xml_lines = write_element_xml_lines(analyze(tokens))
            _out.write_text("\n".join(xml_lines))

if __name__ == '__main__':
    main()





