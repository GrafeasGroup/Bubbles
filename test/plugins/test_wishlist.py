# import pytest

from unittest.mock import patch

import bubbles.plugins.wishlist as base


@patch('bubbles.plugins.wishlist.new_project_note')
def test_responds_to_trigger_word(new_project_note):
    cmd = base.WishlistCommand()
    cmd
