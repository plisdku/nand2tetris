import argparse
from os import listdir
import pathlib
from typing import List, Optional, Tuple

def main():

    parser = argparse.ArgumentParser("JackAnalyzer")
    parser.add_argument(
        "input",
        type=pathlib.Path
    )
    parser.add_argument(
        "output",
        type=pathlib.Path,
        nargs="?"
    )

    args = parser.parse_args()


    in_paths, out_paths = handle_paths(args.input, args.output)



def handle_paths(
    in_path: pathlib.Path,
    out_path: Optional[pathlib.Path]
) -> Tuple[List[pathlib.Path], List[pathlib.Path]]:
    
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


if __name__ == '__main__':
    main()