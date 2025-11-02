from __future__ import annotations
from typing import List, Literal

import re

from jack_element import Element

SYMBOLS = "{}()[].,;+-*/&|<>=~"
KEYWORDS = [
    "class", "method", "function", "constructor", "int", "boolean", "char",
    "void", "var", "static", "field", "let", "do", "if", "else", "while",
    "return", "true", "false", "null", "this"
]


def from_token(content: str) -> Element:
    category = token_category(content)
    if category == "stringConstant":
        content = content.strip('"')
    return Element(category, content)

def remove_block_comments(content: str) -> str:
    """
    Remove /* */ style comments.

    Example:
        >>> remove_block_comments("hello /* there */")
        'hello '

        # Test infix block
        >>> remove_block_comments("hi /* yo */ there")
        'hi  there'
    """
    pattern = re.compile(r"/\*(.*?)\*/", flags=re.DOTALL)
    return re.sub(pattern, "", content)

def remove_line_comments(content: str) -> str:
    """
    Remove // style comments.

    Example:
        >>> remove_line_comments("this // is a comment")
        'this '
    """
    pattern = re.compile(r"//.*$", flags=re.MULTILINE)
    return re.sub(pattern, "", content)

def match_tokens(content: str) -> List[str]:
    """
    Match all occurrences of either a symbol or contiguous non-whitespace.
    Assumes that the input string already has no whitespace.

    Args:
        content: a string without whitespace
    Returns:
        list of tokens

    Example:
        >>> match_tokens("int main() { return 0; }")
        ['int', 'main', '(', ')', '{', 'return', '0', ';', '}']

        >>> match_tokens('" this is " + " a string "')
        ['" this is "', '+', '" a string "']
    """

    symbol_pat = r"[{}\(\)\[\]\.,;\+\-\*/&\|<>=~]"
    word_pat = r"\w+"
    quoted_string_pat = r'".*?"' # lazy matching
    pattern = re.compile(f"({quoted_string_pat}|{symbol_pat}|{word_pat})")

    matches = re.findall(pattern, content)

    return matches


def token_category(
    token: str
) -> Literal['keyword', 'symbol', 'identifier', 'integerConstant', 'stringConstant']:
    """
    Categorize a token.

    Args:
        token: a string without whitespace; should be a valid token.
    Returns:
        category of token

    Examples:
        >>> token_category("+")
        'symbol'
        >>> token_category("-")
        'symbol'
        >>> token_category("{")
        'symbol'
        >>> token_category('"hello')
        'stringConstant'
    """
    if token[0] in SYMBOLS:
        return "symbol"
    elif token[0].isdecimal():
        return 'integerConstant'
    elif token[0] in ('"', "'"):
        # I forget which quote we use, it's whatever
        return 'stringConstant'
    elif token in KEYWORDS:
        return "keyword"
    else:
        return "identifier"

def escape_token(token: str) -> str:
    """
    Escape <, >, " and & for XML.

    Examples:
        >>> escape_token('"<hello>" &c.')
        '&quot;&lt;hello&gt;&quot; &amp;c.'
    """

    token = token.replace("&", "&amp;") # do first lol
    token = token.replace("<", "&lt;")
    token = token.replace(">", "&gt;")
    token = token.replace('"', "&quot;")

    return token

def un_escape_token(token: str) -> str:
    """
    Un-escape &lt;, &gt;, &quot; and &amp;.

    Examples:
        >>> un_escape_token('&quot;&lt;hello&gt;&quot; &amp;c.')
        '"<hello>" &c.'
    """

    token = token.replace("&quot;", '"')
    token = token.replace("&gt;", ">")
    token = token.replace("&lt;", "<")
    token = token.replace("&amp;", "&")

    return token

def tokenize(content: str) -> List[Element]:
    """
    Read .jack code and output list of tokens.

    Args:
        content: Jack program text
    Returns:
        XML string
    """

    # Remove comments
    content = remove_block_comments(content)
    content = remove_line_comments(content)

    raw_tokens: List[str] = []

    # Separate quoted strings.

    # pat = re.compile('".*?"')

    raw_tokens.extend(match_tokens(content))

    # for chunk in content.split():
    #     # Now chunk is one or more tokens, and there is no whitespace.
    #     # I think if I cut out the symbols, everything else is whole tokens.
    #     raw_tokens.extend(match_tokens(chunk))

    # Now categorize the tokens and convert to list of Element objects

    return [from_token(tok) for tok in raw_tokens]

def write_token_xml(tokens: List[Element]) -> str:
    """
    Convert a list of tokens to XML.

    The outermost XML element is <tokens>. Then on separate lines,
    each token is written <{category}> {token} </{category}>, including
    the whitespace around the token.
    """

    xml_lines = []

    xml_lines.append("<tokens>")
    for token in tokens:
        xml_lines.append(f"<{token.category}> {escape_token(token.content)} </{token.category}>")
    xml_lines.append("</tokens>")

    return "\n".join(xml_lines)


def parse_token_xml(xml: str) -> Element:
    """
    Parse an XML element and return the token category and content.

    Args:
        xml: one XML element like "<keyword> var </keyword>"
    Returns:
        category (the tag)
        token (the content, less the two spaces around it)

    Examples:
        >>> parse_token_xml("<symbol> &amp; </symbol>")
        Element(category='symbol', content='&')

        >>> parse_token_xml("<stringConstant> &quot;Oh yeah&quot; </stringConstant>")
        Element(category='stringConstant', content='"Oh yeah"')
    """
    pat = re.compile(r"<(\w+)> (.*?) </\1>")
    matches = re.findall(pat, xml)

    category = matches[0][0]
    token = un_escape_token(matches[0][1])

    return Element(category, token)


def read_xml(content: str) -> List[Element]:
    """
    Parse an XML file of Jack tokens and return a list of Element objects.

    Args:
        content: an XML file beginning with <token>, then one element per line, then </token>
    Returns:
        list of Element objects
    """
    lines = content.splitlines()
    return [parse_token_xml(xml) for xml in lines[1:-1]]


def main():
    import argparse
    import pathlib
    from jack_paths import handle_jack_xml_paths

    parser = argparse.ArgumentParser("JackTokenizer")
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

    in_paths, out_paths = handle_jack_xml_paths(args.input, args.output, add_T=True)

    for _in, _out in zip(in_paths, out_paths):
        _out.parent.mkdir(parents=True, exist_ok=True)
        _out.write_text(write_token_xml(tokenize(_in.read_text())))

if __name__ == '__main__':
    main()
