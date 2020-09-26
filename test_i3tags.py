#pytest
from i3tags import *


def test_tags():
    assert data.tags is data.tag_tree.nodes[1].nodes[1].nodes


class TestI3ipcConMonkeyPatch:
    def test_remove_focus_on_windows(self):
        windows = i3.get_tree().leaves()
        for window in windows:
            window.remove_focus()
            assert window.focused is False

    def test_remove_focus_on_tags(self):
        for tag in data.tags:
            tag.remove_focus()
            assert tag.focused is False
