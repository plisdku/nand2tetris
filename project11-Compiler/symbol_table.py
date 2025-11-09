import dataclasses
from typing import Any, Dict, Iterator, Literal

KIND = Literal["static", "field", "arg", "var"]

@dataclasses.dataclass
class Symbol:
    name: str
    kind: KIND
    type: str
    index: int
    """Index of the symbol within its kind"""


# NOTE: each symbol NOT FOUND in the symbol table can be assumed to be a CLASS NAME
# or a SUBROUTINE NAME according to the lecture.
#
# So, I conclude, class names and subroutine names don't go into the table. Hrm.

@dataclasses.dataclass
class SymbolTable:

    count_by_kind: Dict[str, int] = dataclasses.field(default_factory=dict)
    symbols: Dict[str, Symbol] = dataclasses.field(default_factory=dict)
        
    def __init__(self):
        """Initialize new symbol table"""
        self.reset()

    def reset(self):
        """Reset symbol table and counters"""
        self.count_by_kind = dict()
        self.symbols = dict()

    def __len__(self) -> int:
        return len(self.symbols)

    def __getitem__(self, name: str) -> Symbol:
        """Get a symbol by name"""
        try:
            return self.symbols[name]
        except KeyError as exc:
            raise KeyError(f"No symbol named {name} is in the table") from exc

    def __iter__(self) -> Iterator[Symbol]:
        return iter(self.symbols.values())

    def __contains__(self, name: str) -> bool:
        """
        Return True if `name` refers to a known symbol.

        Examples:
            >>> table = SymbolTable()
            >>> table.insert("x", "static", "int")
            Symbol(name='x', kind='static', type='int', index=0)
            >>> "x" in table
            True
            >>> "y" in table
            False
        """
        return name in self.symbols

    def insert(self, name: str, kind: KIND, type: str) -> Symbol:
        """
        Create a new symbol.

        Examples:
            >>> table = SymbolTable()
            >>> table.insert("x", "static", "int")
            Symbol(name='x', kind='static', type='int', index=0)
            >>> table.insert("y", "static", "char")
            Symbol(name='y', kind='static', type='char', index=1)
            >>> table.insert("z", "field", "int")
            Symbol(name='z', kind='field', type='int', index=0)
        """

        if name in self.symbols:
            raise ValueError(f"A symbol named {name} is already in the table")

        index = self.count_by_kind.setdefault(kind, 0)
        self.count_by_kind[kind] += 1

        symbol = Symbol(name, kind, type, index)
        self.symbols[name] = symbol
        return symbol

    def count(self, kind: str) -> int:
        """
        Return the number of symbols of a given kind in the table.

        Examples:
            >>> table = SymbolTable()
            >>> symbol = table.insert("x", "static", "int")
            >>> table.count("static")
            1
            >>> table.count("field")
            0
        """
        return self.count_by_kind.get(kind, 0)

