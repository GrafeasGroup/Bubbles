# import pytest

import bubbles.plugins as indirect_base
import bubbles.plugins.__base__ as specific_base
import bubbles.plugins.__base_command__ as cmd_base


def test_import_path_convenience():
    assert hasattr(indirect_base, 'ChatPluginManager')
    assert hasattr(indirect_base, 'EventLoop')
    assert hasattr(cmd_base, 'ChatPluginManager')
    assert not hasattr(specific_base, 'ChatPluginManager')
    assert hasattr(specific_base, 'EventLoop')
