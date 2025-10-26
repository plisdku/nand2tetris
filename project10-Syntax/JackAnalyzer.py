import argparse
import pathlib

from jack_analyzer import handle_paths, tokenize

def main():

    parser = argparse.ArgumentParser("JackAnalyzer")
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