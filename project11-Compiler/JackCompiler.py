import argparse
import pathlib
import logging

from jack_paths import handle_jack_vm_paths
from jack_tokenizer import tokenize, read_xml
from jack_analyzer import write_element_xml_lines, analyze
from jack_compiler import compile_elements, compile_jack

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(levelname)s:%(funcName)s: %(message)s"
# )
# log = logging.getLogger(__name__)

logging.getLogger("jack_compiler_orig").setLevel(logging.INFO)
logging.getLogger("jack_analyzer").setLevel(logging.ERROR)

def main():
    parser = argparse.ArgumentParser("JackCompiler")
    parser.add_argument(
        "input",
        type=pathlib.Path
    )
    parser.add_argument(
        "output",
        type=pathlib.Path,
        nargs="?",
        # default="out"
    )

    args = parser.parse_args()
    
    in_paths, out_paths = handle_jack_vm_paths(args.input, args.output, in_suffixes=(".jack",))

    for _in, _out in zip(in_paths, out_paths):
        logging.info(f"Analyze {str(_in)} => {str(_out)}")
        _out.parent.mkdir(parents=True, exist_ok=True)

        if _in.suffix == ".jack":
            vm_code = compile_jack(_in.read_text())
            _out.write_text(vm_code)
        else:
            tokens = None
            print("Unimplemented weirdness")


if __name__ == '__main__':
    main()
    