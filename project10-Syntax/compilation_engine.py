def main():
    import argparse
    import pathlib
    import rich
    from jack_paths import handle_xml_paths
    from jack_tokenizer import read_xml

    parser = argparse.ArgumentParser("JackCompiler")
    parser.add_argument(
        "input",
        type=pathlib.Path
    )

    args = parser.parse_args()

    in_paths = handle_xml_paths(args.input)

    for path in in_paths:
        content = path.read_text()
        tokens = read_xml(content)
        rich.print(tokens)

if __name__ == '__main__':
    main()