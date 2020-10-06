#!/usr/bin/env python3.8

"""Emulate tags to i3wm. Run as service.

"""

import copy
import i3ipc
import logging
import multipledispatch
import subprocess
import threading
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QApplication
# modules
import graphical_elements
import i3ipc_patch
from qt_signals import Signals


class GUIControl:
    def __init__(self):
        self.window = graphical_elements.MainWindow()

    @Slot()
    def add_retag_entry(self):
        self.window.show_entry(self.preprocess_retag_entry)

    def preprocess_retag_entry(self,entry):
        if entry == 'exit':
            app.exit()
        else:
            data.process_retag_entry(entry)

    @Slot()
    def reset(self):
        self.window.reset()

    @Slot()
    def show_mode(self, binding_event):
        self.window.clear()
        self.add_mode(binding_event)
        self.window.show_()

    def add_mode(self, binding_event):
        behind_mode = binding_event.binding.command.split('mode ', 1)[-1]
        mode_hints = behind_mode.split(';', 1)[0].split('|')
        for hint in mode_hints:
            self.window.add_label(hint)

    @Slot()
    def show_tags(self, tag_tree):
        self._prepare_tags(tag_tree)
        self.prepare_position(tag_tree)
        self.window.show_()

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


class QtConnections:
    def __init__(self):
        signals.show_tags.connect(gui.show_tags)
        signals.reset.connect(gui.window.reset)
        signals.show_mode.connect(gui.show_mode)
        signals.add_retag_entry.connect(gui.add_retag_entry)


class I3Input:
    """
    i3 handles keystrokes properly, including sequences,
    overlapping sequences, multiple keys at once,
    japanese keys and ISO_Level keys
    """
    def i3_loop(self):
        i3.on(i3ipc.Event.BINDING, self.handle_binding)
        i3.main()

    def handle_binding(self, _, binding_event):
        i3tags_commands = self.extract_i3tags_commands(binding_event)
        logging.debug(i3tags_commands)
        for c in i3tags_commands:
            if c == 'reset'   : signals.reset.emit()
            # add to your ~/.config/i3/config like this:
            # bindsym Escape mode default; nop reset
            elif c == 'tags'  : self.show_tags()
            elif c == 'mode'  : signals.show_mode.emit(binding_event)
            elif c == 'switch': data.switch_tag(binding_event)
            elif c == 'retag' : signals.add_retag_entry.emit()
            elif c == 'add'   : signals.add_mode.emit(binding_event)
            elif c == 'branch': data.branch_tag(binding_event)
            elif c == 'title' : signals.add_retitle_entry.emit()

    def extract_i3tags_commands(self, binding_event):
        i3_command = binding_event.binding.command
        try:
            behind_nop = i3_command.split('nop ', 1)[1]
        except IndexError:
            return []
        return behind_nop.split(';', 1)[0].split()

    def show_tags(self):
        data.update_tag_tree()
        signals.show_tags.emit(data.tag_tree)


class Data:

    def __init__(self):
        self.tag_tree = i3.get_tree()
        self._workspace_tree = i3.get_tree()
        self.previous_tag_name = self.tag_tree.find_focused().tag().name

    @property
    def tags(self):
        return self.tag_tree.nodes[1].nodes[1].nodes

    @tags.setter
    def tags(self, list_):
        self.tag_tree.nodes[1].nodes[1].nodes = list_

    def branch_tag(self, binding_event):
        tag_name = binding_event.binding.symbol
        current_tag = self.tag_tree.find_focused().tag()
        new_tag = copy.copy(current_tag)
        new_tag.name = tag_name
        self.tags.append(new_tag)
        i3.command(f'move window to workspace {tag_name}')

    def find_target_workspace_name(self, key):
        current_tag_name = self.tag_tree.find_focused().workspace().name
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
        target_tag = self.tag_tree.find_tag_by_name(target_name)
        if target_tag:
            for i, window in enumerate(target_tag.nodes):
                try:
                    if window.id == target_workspace.nodes[i].id:
                        continue
                except (IndexError, AttributeError):
                    pass
                # if anything goes wrong with the window being in
                # workspace on correct position
                self._reload_window_to_workspace(window, target_name)

        # self.command(f'workspace {target_name}')
        # - blocked by PyCharm if going to empty workspace
        # subprocess with i3-msg works
        subprocess.run(['i3-msg', 'workspace', target_name])

    def _reload_window_to_workspace(self, window, target_name):
        # if you uncomment the next code line you get stable window
        # positions in
        # tagged workspaces, but modified layout will be impossible
        # to keep. i3tags will reset them.
        # i3.command(f'[con_id={window.id}]move window to workspace tmp')
        i3.command(f'[con_id={window.id}] move window to workspace {target_name}')

    def update_tag_tree(self):
        self._workspace_tree = i3.get_tree()
        self._inspect_tag_tree()
        self._inspect_workspaces()
        self._inspect_windows()
        self.tags.sort(key=lambda x: x.name)

    def process_retag_entry(self, entry):
        current_window = self.tag_tree.find_focused()
        if entry == '':
            i3.command(f'[con_id={current_window.id}] kill')
            return

        # remove current window from current positions in tag tree
        self.tag_tree.remove_nodes_by_id(current_window.id)

        existing_tag_names = [tag.name for tag in self.tags]
        for char in entry:
            if char == '.':
                continue
            if char in existing_tag_names:
                self.add_to_existing_tag(char)
            else:
                new_tag = i3.get_tree().workspaces()[0]
                new_tag.name = char
                new_tag.nodes = [i3.get_tree().find_focused()]
                self.tags.append(new_tag)

        current_tag = self.tag_tree.find_focused().tag()
        if current_tag.name not in entry:
            i3.command(
                f'[con_id={current_window.id}] move window to workspace {entry[0]}')
        if '.' in entry:
            self.switch_tag(entry[0])

    def add_to_existing_tag(self, char):
        for tag in self.tags:
            if char == tag.name:
                tag.nodes.append(i3.get_tree().find_focused())

    def retitle_focused_window(self, title):
        focused_window = self.tag_tree.find_focused()
        for window in self.tag_tree.leaves():
            if focused_window.id == window.id:
                window.name = title
                window.window_title = title
        subprocess.run(['xdotool',
                        'set_window',
                        '--name',
                        title,
                        str(self.tag_tree.find_focused().window)
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
        tagged_window_ids = [window.id for window in self.tag_tree.leaves()]
        for window in self._workspace_tree.leaves():
            if window.id not in tagged_window_ids:
                # copy window from workspace to tag
                workspace_id = (self._workspace_tree
                                .find_by_id(window.id)
                                .workspace().id)
                self.tag_tree.find_by_id(workspace_id).nodes.append(window)


i3 = i3ipc.Connection(auto_reconnect=True)
i3ipc_patch.apply()
data = Data()
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication()
    gui = GUIControl()
    signals = Signals()
    connections = QtConnections()
    i3input = I3Input()
    i3_thread = threading.Thread(target=i3input.i3_loop)
    i3_thread.start()
    app.exec_()
    # this will run after app.exit()
    i3.main_quit()
