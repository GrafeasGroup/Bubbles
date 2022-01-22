# import pytest

import pathlib

import bubbles.commands


def test_module_importer():
    base_dir = pathlib.Path(__file__).parent

    for module in bubbles.commands.__all__:
        assert base_dir.joinpath(f'{module}.py').is_file
        assert '.' not in module
