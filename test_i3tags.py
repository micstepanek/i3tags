#pytest
from i3tags import *

def test_tags():
    assert i3.tags is i3._tag_tree.nodes[1].nodes[1].nodes
