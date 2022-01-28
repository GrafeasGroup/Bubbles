# import pytest

from unittest.mock import MagicMock, patch

from bubbles.plugins.__base_command__ import BaseCommand, ChatPluginManager


@patch('bubbles.plugins.__base_command__.import_subclasses')
def test_route_unknown_message(import_subclasses, helpers, slack_utils):
    process = MagicMock()
    is_relevant = MagicMock()
    is_relevant.return_value = False

    helpers.new_command_class(methods={
        'process': process,
        'is_relevant': is_relevant,
        'trigger_words': ['lorem'],
        'help_text': "Hello world",
    })

    with ChatPluginManager(reddit=MagicMock()) as mgr:
        mgr.process({'text': '@Bubbles ipsum dolor sit amet'}, slack_utils)

    is_relevant.assert_called_once()
    assert not process.called
    import_subclasses.assert_called_once()


@patch('bubbles.plugins.__base_command__.import_subclasses')
def test_routable_message(import_subclasses, helpers, slack_utils):
    process = MagicMock()
    is_relevant = MagicMock()
    is_relevant.return_value = True  # I said it was routable...

    helpers.new_command_class(methods={
        'process': process,
        'is_relevant': is_relevant,
        'trigger_words': ['lorem'],
    })

    with ChatPluginManager(reddit=MagicMock()) as mgr:
        assert len(BaseCommand._subclasses) == 1
        assert len(mgr.commands) == 1
        mgr.process({'text': '@Bubbles lorem ipsum dolor'}, slack_utils)

    is_relevant.assert_called()
    process.assert_called_once()
    import_subclasses.assert_called()

    assert not slack_utils.respond.called
    assert not slack_utils.say.called
