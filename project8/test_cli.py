import os
from os.path import basename
import pathlib
from pathlib import Path
from VMTranslator import normalize_arguments

def _sys_argv(input_path: Path, output_path: Path | None = None) -> list[str]:
    """Get pretend sys.argv"""

    argv = ["VMTranslator", str(input_path)]

    if output_path is not None:
        argv += [str(output_path)]

    return argv

def test_single_file_no_output(tmp_path: Path):

    file = tmp_path / "test.vm"
    file.touch()

    in_files, out_file, do_init = normalize_arguments(str(file))

    assert in_files == [file]
    assert out_file == tmp_path/"test.asm"
    assert not do_init

def test_multi_file_no_output(tmp_path: Path):

    file1 = tmp_path/"test1.vm"
    file2 = tmp_path/"test2.vm"

    file1.touch()
    file2.touch()

    in_files, out_file, do_init = normalize_arguments(str(tmp_path))

    assert sorted(in_files) == sorted([file1, file2])
    assert out_file == (tmp_path / tmp_path.stem).with_suffix(".asm")
    assert do_init


def test_single_file_with_output(tmp_path: Path):

    file = tmp_path / "test.vm"
    file.touch()

    out = tmp_path / "out.asm"

    in_files, out_file, do_init = normalize_arguments(str(file), str(out))

    assert in_files == [file]
    assert out_file == out
    assert not do_init


def test_multi_file_with_output(tmp_path: Path):

    file1 = tmp_path/"test1.vm"
    file2 = tmp_path/"test2.vm"

    out = tmp_path / "out.asm"

    file1.touch()
    file2.touch()

    in_files, out_file, do_init = normalize_arguments(str(tmp_path), str(out))

    assert sorted(in_files) == sorted([file1, file2])
    assert out_file == out
    assert do_init
