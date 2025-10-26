
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



def tokenize(content: str) -> str:
    """
    Read .jack code and output tokens as XML.
    """

    return "haha"