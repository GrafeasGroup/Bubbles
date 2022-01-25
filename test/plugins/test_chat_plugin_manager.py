import pytest

import importlib
from unittest.mock import patch

from bubbles.plugins import BaseCommand, ChatPluginManager
from bubbles.plugins.__base__ import import_subclasses


@pytest.mark.skip(reason='Really hard to test, given pytest and using importlib in the code. Just test manually instead')
def test_load_subclasses(helpers):
    helpers.clear_subclasses(BaseCommand)
    importlib.invalidate_caches()

    initial_commands = set(BaseCommand._subclasses)
    import_subclasses()
    assert len(BaseCommand._subclasses) > len(initial_commands)


@patch('bubbles.plugins.__base_command__.import_subclasses')
def test_route_unknown_message(import_subclasses, helpers):
    helpers.clear_subclasses(BaseCommand)
    import_subclasses.side_effect = lambda *_: helpers.new_command_class()

    assert len(BaseCommand._subclasses) == 0
    with ChatPluginManager() as mgr:
        assert len(BaseCommand._subclasses) > 0
        assert len(mgr.commands) > 0

    import_subclasses.assert_called()
