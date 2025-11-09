from __future__ import annotations
import dataclasses
from typing import List

@dataclasses.dataclass
class Element:
    category: str
    content: str | List[Element]

    def __bool__(self):
        return True

    def __str__(self):
        if isinstance(self.content, str):
            return f"Element(category='{self.category}', content='{self.content}')"
        else:
            return f"Element(category='{self.category}', content=[{len(self.content)} items])"