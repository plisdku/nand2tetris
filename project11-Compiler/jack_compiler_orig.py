from typing import List

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


class CompilerError(Exception):
    pass

class CookieMonster:
    def __init__(self, elements: list[Element]):
        self.elements = elements
        self.index = 0

    def next(self, category: str | None = None, content: str | None = None) -> Element:
        elem = self.peek(category, content)
        self.index += 1
        return elem

    def peek(self, category: str | None = None, content: str | None = None) -> Element:
        elem = self.elements[self.index]

        if category is not None:
            if elem.category != category:
                raise CompilerError(f"Expected category {category!r}; got {elem.category!r}")
        if content is not None:
            if isinstance(elem.content, str) and elem.content != content:
                raise CompilerError(f"Expected content {content!r}; got {elem.content!r}")
            elif isinstance(elem.content, list):
                raise CompilerError(f"Expected content {content!r}; got a list of length {len(elem.content)}")
            else:
                raise CompilerError(f"Unexpected error, expected content {content!r}; got {elem.content!r}")

        self.index += 1

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

        while munch.peek("classVarDec"):
            self.compile_class_var_dec(munch.next("classVarDec"))


    def compile_class_var_dec(self, element: Element):
        assert element.category == "classVarDec"
        assert isinstance(element.content, list)

        munch = CookieMonster(element.content)

        while not munch.done() and munch.peek("classVarDec"):
            


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