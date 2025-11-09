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
        elem = self.peek(category, content)
        log.info(f"{elem}")
        self.index += 1
        return elem

    def peek(self, category: Optional[str] = None, content: Optional[str] = None, ahead: int = 1) -> Element:
        elem = self.elements[self.index + (ahead-1)]

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

        return elem

    def done(self) -> bool:
        return self.index < len(self.elements)


class JackCompiler:
    def __init__(self, elements: List[Element]):
        self.elements = elements
        self.static_table = SymbolTable()
        self.local_table = SymbolTable()

    def compile_class(self, element: Element):
        assert element.category == "class"
        assert isinstance(element.content, list)

        munch = CookieMonster(element.content)
        munch.next(content="class")
        class_elem = munch.next("identifier")
        munch.next("symbol", "{")

        while munch.peek().category == "classVarDec":
            self.compile_class_var_dec(munch.next("classVarDec"))


    def compile_class_var_dec(self, element: Element):
        assert element.category == "classVarDec"
        assert isinstance(element.content, list)

        munch = CookieMonster(element.content)

        while not munch.done() and munch.peek("classVarDec"):
            pass
            


    def compile_subroutine_dec(self, element: Element):
        pass

    def compile_parameter_list(self, element: Element):
        pass

    def compile_subroutine_body(self, element: Element):
        pass

    def compile_var_dec(self, element: Element):
        pass

    def compile_statements(self, element: Element):
        pass



    def compile_expression(self, element: Element):
        pass

    def compile_statement(self, element: Element):
        pass



def compile_elements(elements: List[Element]):
    assert len(elements) == 1
    jack_compiler = JackCompiler(elements)
    jack_compiler.compile_class(elements[0])