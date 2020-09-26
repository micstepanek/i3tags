#!/usr/bin/env python3.8

"""Emulate tags to i3wm. Run as service.

"""

import copy
import i3ipc
import logging
import multipledispatch
import subprocess
import threading
from PySide2.QtCore import QObject, Signal, Slot
from PySide2.QtWidgets import QApplication
# modules
from graphical_elements import MainWindow
import i3ipc_patch


class GUIControl:
    def __init__(self):
        self.window = MainWindow()

    @Slot()
    def add_retag_entry(self):
        self.window.show_entry(self.process_retag_entry)

    @Slot()
    def process_retag_entry(self):
        entry = self.window.entry.text()
        self.window.reset()
        logic.process_retag_entry(entry)

    @Slot()
    def reset(self):
        self.window.reset()

    @Slot()
    def show_mode(self, binding_event):
        self.window.clear()
        self.add_mode(binding_event)

    def add_mode(self, binding_event):
        behind_mode = binding_event.binding.command.split('mode ', 1)[-1]
        mode_hints = behind_mode.split(';', 1)[0].split('|')
        for hint in mode_hints:
            self.window.add_label(hint)

    @Slot()
    def show_tags(self, tag_tree):
        self._prepare_tags(tag_tree)
        self.prepare_position(tag_tree)
        self.window.show()

    def prepare_position(self, tag_tree):
        focused_window = tag_tree.find_focused()
        self.window.move_(focused_window.rect.x,
                          focused_window.rect.y + 75)

    def _prepare_tags(self, tag_tree):
        for tag in tag_tree.tags():
            if tag.name == 'hidden':
                continue
            windows = tag.nodes
            if not windows:
                try:
                    windows = tag.floating_nodes[0].nodes
                except IndexError:  # no widows at all, label tag name
                    self.window.add_label(f'''{tag.name} 
''')
            for window in windows:
                self.label_i3_window(tag, window)

    def label_i3_window(self, tag, window):
        self.window.add_label(f'''{tag.name}           {window.window_class}
{window.name}''',
                              window.focused,
                              not window.urgent)

class Signals(QObject):
    show_tags = Signal(object)
    reset = Signal()
    show_mode = Signal(object)
    add_retag_entry = Signal()

class Connections:
    def __init__(self):
        signals.show_tags.connect(gui.show_tags)
        signals.reset.connect(gui.window.reset)
        signals.show_mode.connect(gui.show_mode)
        signals.add_retag_entry.connect(gui.add_retag_entry)


class I3LogicExtension:
    """Central class.

    """

    def __init__(self):
        # i3 handles modes properly, including sequences,
        # overlapping sequences and multiple keys at once,
        # as well as japanese keys
        self._tag_tree = i3.get_tree()
        self._workspace_tree = i3.get_tree()
        self.previous_tag_name = self._tag_tree.find_focused().tag().name

    def i3_loop(self):
        i3.on(i3ipc.Event.BINDING, self.handle_binding)
        i3.main()

    @property
    def tags(self):
        return self._tag_tree.nodes[1].nodes[1].nodes

    @tags.setter
    def tags(self, list_):
        self._tag_tree.nodes[1].nodes[1].nodes = list_

    def extract_i3tags_commands(self, i3_command):
        behind_nop = i3_command.split('nop ', 1)[1]
        return behind_nop.split(';', 1)[0].split()

    def handle_binding(self, _, binding_event):
        i3_command = binding_event.binding.command
        if 'nop' in i3_command:
            self_commands = self.extract_i3tags_commands(i3_command)
            logging.debug(self_commands)
            for c in self_commands:
                if c == 'reset'   : signals.reset.emit()
                # add to your ~/.config/i3/config like this:
                # bindsym Escape mode default; nop reset
                elif c == 'tags'  : self.show_tags()
                elif c == 'mode'  : signals.show_mode.emit(binding_event)
                elif c == 'switch': self.switch_tag(binding_event)
                elif c == 'retag' : signals.add_retag_entry.emit()
                elif c == 'add'   : signals.add_mode.emit(binding_event)
                elif c == 'branch': self.branch_tag(binding_event)
                elif c == 'title' : self.show_retitle_entry()

    def show_tags(self):
        self._update_tag_tree()
        signals.show_tags.emit(self._tag_tree)


    def branch_tag(self, binding_event):
        tag_name = binding_event.binding.symbol
        current_tag = self._tag_tree.find_focused().tag()
        new_tag = copy.copy(current_tag)
        new_tag.name = tag_name
        self.tags.append(new_tag)
        i3.command(f'move window to workspace {tag_name}')

    def find_target_workspace_name(self, key):
        current_tag_name = self._tag_tree.find_focused().workspace().name
        if current_tag_name == key:
            target = self.previous_tag_name
        else:
            target = key
        self.previous_tag_name = current_tag_name
        return target

    @multipledispatch.dispatch(object)
    def switch_tag(self, binding_event):
        self.switch_tag(binding_event.binding.symbol)

    @multipledispatch.dispatch(str)
    def switch_tag(self, symbol):
        signals.reset.emit()
        target_name = self.find_target_workspace_name(symbol)
        target_workspace = self._workspace_tree.find_tag_by_name(target_name)
        target_tag = self._tag_tree.find_tag_by_name(target_name)
        if target_tag:
            for i, window in enumerate(target_tag.nodes):
                try:
                    if window.id == target_workspace.nodes[i].id:
                        pass
                    else:
                        self._reload_window_to_workspace(window, target_name)
                except:
                    self._reload_window_to_workspace(window, target_name)

        #self.command(f'workspace {target_name}')
        # - blocked by PyCharm if going to empty workspace
        # subprocess with i3-msg works
        subprocess.run(['i3-msg', 'workspace', target_name])

    def _reload_window_to_workspace(self, window, target_name):
        #i3.command(f'[con_id={window.id}]move window to workspace tmp')
        i3.command(f'[con_id={window.id}] move window to workspace {target_name}')

    def _update_tag_tree(self):
        self._workspace_tree = i3.get_tree()
        self._inspect_tag_tree()
        self._inspect_workspaces()
        self._inspect_windows()
        self.tags.sort(key=lambda x: x.name)

    def process_retag_entry(self, entry):
        if entry == 'exit':
            app.exit()
            # app.exit is not immediate, we have to stop function too
            return
        # get variables
        current_tag = self._tag_tree.find_focused().workspace()
        current_window = self._tag_tree.find_focused()
        # remove current window from tag tree
        self._tag_tree.remove_node_by_id(current_window.id)
        #
        if entry == '':
            i3.command(f'[con_id={current_window.id}] kill')
        else:
            change_workspace_after_retagging = False
            for char in entry:
                if char == '.':
                    change_workspace_after_retagging = True
                    break
                else:
                    placed = self._add_to_existing_tag(char, current_window)
                if not placed:
                    new_tag = copy.copy(current_tag)
                    new_tag.name = char
                    new_tag.nodes = [current_window]
                    self.tags.append(new_tag)
            if change_workspace_after_retagging == True:
                self.switch_tag(entry[0])
            if current_tag.name not in entry:
                i3.command(
                    f'[con_id={current_window.id}] move window to workspace {entry[0]}')

    def _add_to_existing_tag(self, char, current_window):
        for tag in self.tags:
            if char == tag.name:
                tag.nodes.append(current_window)
                return True
        return False

    def retitle_focused_window(self, title):
        focused_window = self._tag_tree.find_focused()
        for window in self._tag_tree.leaves():
            if focused_window.id == window.id:
                window.name = title
                window.window_title = title
        subprocess.run(['xdotool',
                        'set_window',
                        '--name',
                        title,
                        str(self._tag_tree.find_focused().window)
                        ])

    def _inspect_tag_tree(self):
        current_workspace = self._workspace_tree.find_focused().workspace()
        tags = [
                current_workspace if current_workspace.name == tag.name else
                tag.update_tag(self._workspace_tree)
                for tag in self.tags
                    ]
        self.tags = [tag for tag in tags if tag.nodes]

    def _inspect_workspaces(self):
        tag_names = [tag.name for tag in self.tags]
        for workspace in self._workspace_tree.workspaces():
            if workspace.name not in tag_names:
                self.tags.append(workspace)

    def _inspect_windows(self):
        tagged_window_IDs = [window.id for window in self._tag_tree.leaves()]
        for window in self._workspace_tree.leaves():
            if window.id not in tagged_window_IDs:
                #copy window frow workspace to tag
                workspace_id = (self._workspace_tree
                                .find_by_id(window.id)
                                .workspace().id)
                self._tag_tree.find_by_id(workspace_id).nodes.append(window)


i3 = i3ipc.Connection(auto_reconnect=True)
i3ipc_patch.apply()
logic = I3LogicExtension()
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication()
    gui = GUIControl()
    signals = Signals()
    connections = Connections()
    i3_thread = threading.Thread(target=logic.i3_loop)
    i3_thread.start()
    app.exec_()
    # this will run after app.exit()
    i3.main_quit()
