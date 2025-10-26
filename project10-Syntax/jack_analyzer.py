
import re
from typing import List, Optional, Tuple

import pathlib


def handle_paths(
    in_path: pathlib.Path,
    out_path: Optional[pathlib.Path]
) -> Tuple[List[pathlib.Path], List[pathlib.Path]]:
    """
    Return corresponding lists of input .jack files and output .xml files.

    For each input file, if its name is 'Xxx.jack', the output file name will
    be 'XxxT.xml'. out_path can adjust the directory for the output but will
    not change the name of the XML file.

    Args:
        in_path: path to directory containing .jack files; or a .jack file
        out_path: path to a directory to put .xml files; or None
    Returns:
        list of input file paths
        list of output file paths corresponding to input file paths
    """
    if in_path.is_dir():
        in_paths = [path for path in in_path.iterdir() if path.suffix == ".jack"]

        if out_path is None:
            # in_path is directory; put outputs in same directory
            out_paths = [path.with_name(path.stem + "T").with_suffix(".xml") for path in in_paths]
        else:
            # in_path is directory; out_path is directory
            assert isinstance(out_path, pathlib.Path)

            if not out_path.exists:
                out_path.mkdir(parents=True, exist_ok=True)

            out_paths = [(out_path / (path.stem + "T")).with_suffix(".xml") for path in in_paths]

        return in_paths, out_paths
    else:
        if out_path is None:
            # in_path is file; put output next to it
            out_path = in_path.with_name(in_path.stem + "T").with_suffix(".xml")
        else:
            out_path = out_path.with_name(in_path.stem + "T").with_suffix(".xml")
        
        return [in_path], [out_path]


SYMBOLS = "{}()[].,;+-*/&|<>=~"


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
    """

    symbol_pat = r"[{}\(\)\[\]\.,;\+\-\*/&\|<>=~]"
    word_pat = r"\w+"
    pattern = re.compile(f"({symbol_pat}|{word_pat})")

    matches = re.findall(pattern, content)

    return matches


def tokenize(content: str) -> str:
    """
    Read .jack code and output tokens as XML.
    """

    # Remove comments
    content = remove_block_comments(content)
    content = remove_line_comments(content)

    tokens = []

    for chunk in content.split():
        # Now chunk is one or more tokens, and there is no whitespace.
        # I think if I cut out the symbols, everything else is whole tokens.
        tokens.extend(match_tokens(chunk))

    import rich
    rich.print(tokens)

    return "haha"

