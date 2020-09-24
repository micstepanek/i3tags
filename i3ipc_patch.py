import i3ipc


class ConPatch():
    """Monkey patch, the class used by i3ipc is i3ipc.Con.

    This class
    modifies/extends i3ipc.Con. Don't want to inherit i3ipc.Con and
    thus change identity as it is called by multiple i3ipc classes.
    Methods must be assigned to i3ipc.Con
    class, see the end of class. Call self only."""

    def remove_node_by_id(self, removed_id):
        self.nodes = [node for node in self.nodes if node.id != removed_id]
        for node in self.nodes:
            node.remove_node_by_id(removed_id)

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

    Con = i3ipc.Con
    Con.tag = Con.workspace
    Con.tags = Con.workspaces
    Con.remove_focus = remove_focus
    Con.update_tag = update_tag
    Con.remove_node_by_id = remove_node_by_id
    Con.find_tag_by_name = find_tag_by_name