from typing import List, Literal

import dataclasses

import re

SYMBOLS = "{}()[].,;+-*/&|<>=~"
KEYWORDS = [
    "class", "method", "function", "constructor", "int", "boolean", "char",
    "void", "var", "static", "field", "let", "do", "if", "else", "while",
    "return", "true", "false", "null", "this"
]


def remove_block_comments(content: str) -> str:
    """
    Remove /* */ style comments.

    Example:
        >>> remove_block_comments("hello /* there */")
        'hello '

        # Test nested blocks, which shouldn't happen
        >>> remove_block_comments("hi /*/*/**/ there")
        'hi  there'
    """
    pattern = re.compile(r"/\*(.*)\*/", flags=re.DOTALL)
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
) -> Literal['keyword', 'symbol', 'identifier', 'int_const', 'string_const']:
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
        'string_const'
    """
    
    if token[0] in SYMBOLS:
        return "symbol"
    elif token[0].isdecimal():
        return 'int_const'
    elif token[0] in ('"', "'"):
        # I forget which quote we use, it's whatever
        return 'string_const'
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

def tokenize(content: str) -> str:
    """
    Read .jack code and output tokens as XML.

    The outermost XML element is <tokens>. Then on separate lines,
    each token is written <{category}> {token} </{category}>, including
    the whitespace around the token.

    Args:
        content: Jack program text
    Returns:
        XML string
    """

    # Remove comments
    content = remove_block_comments(content)
    content = remove_line_comments(content)

    tokens = []

    for chunk in content.split():
        # Now chunk is one or more tokens, and there is no whitespace.
        # I think if I cut out the symbols, everything else is whole tokens.
        tokens.extend(match_tokens(chunk))

    # Now categorize the tokens and write the xml digest

    xml_lines = []

    xml_lines.append("<tokens>")
    for token in tokens:
        category = token_category(token)
        xml_lines.append(f"<{category}> {escape_token(token)} </{category}>")
    xml_lines.append("</tokens>")

    return "\n".join(xml_lines)

@dataclasses.dataclass
class Token:
    category: str
    token: str


def parse_token_xml(xml: str) -> Token:
    """
    Parse an XML element and return the token category and content.

    Examples:
        # >>> parse_token_xml("<")
    """
    pat = re.compile(r"<(\w+)> (.*?) </\1>")
    matches = re.findall(pat, xml)

    return matches


# def read_xml(content: str) -> List[Token]:
#     lines = content.splitlines()



def main():
    import argparse
    import pathlib
    from jack_paths import handle_paths

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

    in_paths, out_paths = handle_paths(args.input, args.output)

    for _in, _out in zip(in_paths, out_paths):
        _out.parent.mkdir(parents=True, exist_ok=True)
        _out.write_text(tokenize(_in.read_text()))

if __name__ == '__main__':
    main()
