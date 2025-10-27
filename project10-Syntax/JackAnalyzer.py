import argparse
import pathlib
import logging

from jack_paths import handle_jack_xml_paths
from jack_tokenizer import tokenize, read_xml
from jack_analyzer import write_element_xml_lines, analyze

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s:%(funcName)s: %(message)s"
)
log = logging.getLogger(__name__)

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
    )

    args = parser.parse_args()

    in_paths, out_paths = handle_jack_xml_paths(args.input, args.output, add_T=False, in_suffixes=(".jack",))

    for _in, _out in zip(in_paths, out_paths):
        logging.info(f"Analyze {str(_in)} => {str(_out)}")
        _out.parent.mkdir(parents=True, exist_ok=True)

        if _in.suffix == ".jack":
            # Tokenize the jack
            tokens = tokenize(_in.read_text())
        elif _in.stem.endswith("T") and _in.suffix == ".xml":
            # It's a token file
            tokens = read_xml(_in.read_text())
        else:
            tokens = None

        if tokens is not None:
            xml_lines = write_element_xml_lines(analyze(tokens))
            _out.write_text("\n".join(xml_lines))


if __name__ == '__main__':
    main()
    