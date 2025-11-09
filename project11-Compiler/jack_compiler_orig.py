from typing import List, Optional
import logging

from jack_element import Element
from symbol_table import SymbolTable

# Element(category='classVarDec')
# Element(category='expression')
# Element(category='expressionList')
# Element(category='identifier')
# Element(category='integerConstant')
# Element(category='keyword')
# Element(category='parameterList')
# Element(category='returnStatement')
# Element(category='symbol')
# Element(category='term')

log = logging.getLogger(__name__)



class CompilerError(Exception):
    pass

class CookieMonster:
    def __init__(self, elements: List[Element]):
        self.elements = elements
        self.index = 0

    def next(self, category: Optional[str] = None, content: Optional[str] = None) -> Element:
        elem = self.elements[self.index]
        log.info(f"{elem}")

        if category is not None:
            if elem.category != category:
                raise CompilerError(f"Expected category {category!r}; got {elem.category!r}\nelem = {elem}")
        if content is not None:
            if isinstance(elem.content, str) and elem.content != content:
                raise CompilerError(f"Expected content {content!r}; got {elem.content!r}\nelem = {elem}")
            elif isinstance(elem.content, list):
                raise CompilerError(f"Expected content {content!r}; got a list of length {len(elem.content)}")
            else:
                assert elem.content == content

        self.index += 1

        return elem

    def peek(self, category: Optional[str] = None, content: Optional[str] = None, ahead: int = 1) -> Optional[Element]:
        elem = self.elements[self.index + (ahead-1)]

        if category is not None:
            if elem.category != category:
                return None
        if content is not None:
            if isinstance(elem.content, str) and elem.content != content:
                return None
            elif isinstance(elem.content, list):
                return None
            else:
                assert elem.content == content

        return elem

    def done(self) -> bool:
        return self.index < len(self.elements)


class JackCompiler:
    def __init__(self, elements: List[Element]):
        self.elements = elements
        self.static_table = SymbolTable()
        self.local_table = SymbolTable()

    def compile_class(self, element: Element):
        """
        Compile a class. The first token should be the 'class' keyword.

        'class' className '{' classVarDec* subroutineDec* '}'
        """
        assert element.category == "class"
        assert isinstance(element.content, list)

        munch = CookieMonster(element.content)
        munch.next(content="class")
        class_elem = munch.next("identifier") # NAME OF CLASS
        munch.next("symbol", "{")

        while munch.peek("classVarDec"):
            self.compile_class_var_dec(munch.next("classVarDec"))

        while munch.peek("subroutineDec"):
            self.compile_subroutine_dec(munch.next("subroutineDec"))


    def compile_class_var_dec(self, element: Element):
        """
        Compile a classVarDec:

        ('static' | 'field') type varName (',', varName)* ';'
        """
        assert element.category == "classVarDec"
        assert isinstance(element.content, list)

        munch = CookieMonster(element.content)

        while not munch.done() and munch.peek("classVarDec"):
            pass
            


    def compile_subroutine_dec(self, element: Element):
        """
        Compile a subroutineDec:

        ('constructor' | 'function' | 'method') ('void' | type) subroutineName
        '(' parameterList ')' subroutineBody
        """
        pass

    def compile_parameter_list(self, element: Element):
        """
        ( (type varName) (',' type varName)* )?
        """
        pass

    def compile_subroutine_body(self, element: Element):
        """
        '{' varDec* statements '}'
        """
        pass

    def compile_var_dec(self, element: Element):
        """
        'var' type varName (',' varName)* ';'
        """
        pass

    def compile_statements(self, element: Element):
        """
        statement*
        """
        pass



    def compile_expression(self, element: Element):
        """
        term (op term)*
        """
        pass

    def compile_statement(self, element: Element):
        """
        letStatement | ifStatement | whileStatement | doStatement | returnStatement
        """
        pass



def compile_elements(elements: List[Element]):
    assert len(elements) == 1
    jack_compiler = JackCompiler(elements)
    jack_compiler.compile_class(elements[0])