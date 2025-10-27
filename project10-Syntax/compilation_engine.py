from __future__ import annotations

import dataclasses
from typing import List
from jack_element import Element


class SyntaxAnalyzer:
    def __init__(self):
        self.idx = 0
        self.tokens: List[Element] = []
        self.root: Element | None = None

    def analyze(self, tokens: List[Element]):
        self.idx = 0
        self.tokens = tokens
        self.root = self.compile_class()

    def peek(self, ahead: int = 1) -> Element:
        return self.tokens[self.idx + ahead - 1]

    def next(self, category: str | None = None, value: str | None = None) -> Element:
        token = self.tokens[self.idx]

        if category is not None:
            assert token.category == category
        if value is not None:
            assert token.token == value

        self.idx += 1
        return token

    def compile_class(self) -> Element:
        """
        Compile a class. The first token should be the 'class' keyword.

        'class' className '{' classVarDec* subroutineDec* '}'
        """

        elems: List[Element] = []

        # 'class'
        token = self.next("keyword", "class")
        elems.append(token)

        # className
        token = self.next()

        return Element("class", elems)



    def compile_class_var_dec(self):
        """
        Compile a classVarDec:

        ('static' | 'field') type varName (',', varName)* ';'
        """

    def compile_subroutine_dec(self):
        """
        Compile a subroutineDec:

        ('constructor' | 'function' | 'method') ('void' | type) subroutineName
        """

    def compile_parameter_list(self):
        """
        ( (type varName) (',' type varName)* )?
        """

    def compile_subroutine_body(self):
        """
        '{' varDec* statements '}'
        """

    def compile_var_dec(self):
        """
        'var' type varName (',' varName)* ';'
        """

    def compile_statement(self):
        """
        letStatement | ifStatement | whileStatement | doStatement | returnStatement
        """

    def compile_let_statement(self):
        """
        'let' varName ('[' expression ']')? '=' expression ';'
        """

    def compile_if_statement(self):
        """
        'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        """

    def compile_while_statement(self):
        """
        'while' '(' expression ')' '{' statements '}'
        """

    def compile_do_statement(self):
        """
        'do' subroutineCall ';'
        """

    def compile_return_statement(self):
        """
        'return' expression? ';'
        """

    def compile_expression(self):
        """
        term (op term)*
        """

    def compile_term(self):
        """
        integerConstant | stringConstant | keywordConstart | varName |
        varName '[' expression ']' | '(' expression ')' | (unaryOp term) | subroutineCall
        """

    def compile_subroutine_call(self):
        """
        subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName
        '(' expressionList ')'
        """

    def compile_expression_list(self):
        """
        (expression (',' expression)* )?
        """


def main():
    import argparse
    import pathlib
    import rich
    from jack_paths import handle_xml_paths
    from jack_tokenizer import read_xml

    parser = argparse.ArgumentParser("JackCompiler")
    parser.add_argument(
        "input",
        type=pathlib.Path
    )

    args = parser.parse_args()

    in_paths = handle_xml_paths(args.input)

    for path in in_paths:
        content = path.read_text()
        tokens = read_xml(content)
        rich.print(tokens)

if __name__ == '__main__':
    main()