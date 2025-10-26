import pathlib
import pytest
import sys
import rich

from jack_analyzer import handle_paths

def test_input_directory(tmp_path: pathlib.Path):
    """
    Input is a directory with files in it
    """

    file1 = tmp_path / "file1.jack"
    file2 = tmp_path / "file2.jack"
    file3 = tmp_path / "file3.csv"

    file1.write_text("aoeu")
    file2.write_text("aoeu")
    file3.write_text("aoeu")

    in_paths, out_paths = handle_paths(tmp_path, None)

    assert {p.name for p in in_paths} == {"file1.jack", "file2.jack"}
    assert {p.name for p in out_paths} == {"file1T.xml", "file2T.xml"}

def test_input_output_directory(tmp_path: pathlib.Path):
    """
    Input is a directory with files in it.
    Output is a directory.
    """

    src_dir = tmp_path / "src"
    src_dir.mkdir()

    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()

    file1 = src_dir / "file1.jack"
    file2 = src_dir / "file2.jack"
    file3 = src_dir / "file3.csv"

    file1.write_text("aoeu")
    file2.write_text("aoeu")
    file3.write_text("aoeu")

    in_paths, out_paths = handle_paths(src_dir, xml_dir)

    assert {p.name for p in in_paths} == {"file1.jack", "file2.jack"}
    assert {p.name for p in out_paths} == {"file1T.xml", "file2T.xml"}
    assert {p.parent.stem for p in out_paths} == {"xml", "xml"}

def test_input_file(tmp_path: pathlib.Path):
    """
    Input is a file
    """

    file = tmp_path / "file.jack"
    file.write_text("aoeu")

    in_paths, out_paths = handle_paths(file, None)

    assert {p.name for p in in_paths} == {"file.jack"}
    assert {p.name for p in out_paths} == {"fileT.xml"}
    assert in_paths[0].parent == out_paths[0].parent


def test_input_output_file(tmp_path: pathlib.Path):

    file = tmp_path / "file.jack"
    file.write_text("aoeu")

    out_dir = tmp_path / "lazy" / "hazy" / "crazy"
    out_file = out_dir / "blah.xml"

    in_paths, out_paths = handle_paths(file, out_file)

    assert {p.name for p in in_paths} == {"file.jack"}
    assert {p.name for p in out_paths} == {"fileT.xml"}
    assert in_paths[0].parent == tmp_path
    assert out_paths[0].parent == out_dir



