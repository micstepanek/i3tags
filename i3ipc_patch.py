"""
Monkey patch, the class used by i3ipc is i3ipc.Con

Modifies/extends i3ipc.Con. Do not want to inherit i3ipc.Con and
thus change identity as it is called by multiple i3ipc classes.
"""

import i3ipc


def apply():
    i3ipc.Con.tag = i3ipc.Con.workspace
    i3ipc.Con.tags = i3ipc.Con.workspaces
    i3ipc.Con.remove_focus = remove_focus
    i3ipc.Con.update_tag = update_tag
    i3ipc.Con.remove_nodes_by_id = remove_nodes_by_id
    i3ipc.Con.find_tag_by_name = find_tag_by_name


def remove_nodes_by_id(self, removed_id):
    self.nodes = [node for node in self.nodes if node.id != removed_id]
    for node in self.nodes:
        node.remove_nodes_by_id(removed_id)


def remove_focus(self):
    self.focused = False
    return self


def update_tag(self, workspace_tree):
    self.focused = False
    self.nodes = [
        window.remove_focus() for window
        in self.nodes
        if window.id in
           [window2.id for window2 in workspace_tree.leaves()]
    ]
    return self


def find_tag_by_name(self, name):
    for tag in self.tags():
        if tag.name == name:
            return tag
