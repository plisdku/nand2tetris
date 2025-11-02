from __future__ import annotations
import dataclasses
from typing import List

@dataclasses.dataclass
class Element:
    category: str
    content: str | List[Element]

    def __bool__(self):
        return True