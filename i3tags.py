#!/usr/bin/env python3.6

"""Emulate tags to i3wm. Run as service.

Call in following directions
 i3 <-> logic=BusinessLogic <-> gui=HighGUI -> tkinter
with no jumps, e.g. logic may call gui,
but i3 shouldn't call gui directly."""

import i3ipc
import tkinter
import time
import subprocess
import copy
import logging
import multipledispatch
import unicodedata


class BusinessLogic:
    """Central class.

    Don't call tk_root from here, call gui instead."""

    def __init__(self):
        i3.on(i3ipc.Event.BINDING, self.handle_binding)
        # i3 handles modes properly, including sequences,
        # overlapping sequences and multiple keys at once,
        # as well as japanese keys
        self._tag_tree = i3.get_tree()
        self._workspace_tree = i3.get_tree()
        self.previous_tag_name = self._tag_tree.find_focused().tag().name
        self.nop_mapping = {
            'activate': self.activate,
            'reset': gui.reset,
            'mode': gui.show_mode,
            'switch': self.switch_tag,
            'retag': self.show_retag_entry,
            'add': gui.add_mode,
            'branch': self.branch_tag,
            'title': self.show_retitle_entry
            # add to your i3 config like this:
            # bindsym Escape mode default; nop reset
        }
    @property
    def tags(self):
        return self._tag_tree.nodes[1].nodes[1].nodes

    @tags.setter
    def tags(self, list_):
        self._tag_tree.nodes[1].nodes[1].nodes = list_

    def handle_binding(self, _, binding_event):
        command = binding_event.binding.command
        if 'nop' in command:
            behind_nop = binding_event.binding.command.split('nop ', 1)[1]
            nop_list = behind_nop.split(';', 1)[0].split()
            logging.debug(nop_list)
            for comment in nop_list:
                self.nop_mapping[comment](binding_event)

    def listen_for_bindings(self):
        i3.main()

    def stop_listening(self):
        i3.main_quit()

    def activate(self, _):
        i3.command('fullscreen disable')
        self._update_tag_tree()
        gui.activate(self._tag_tree)

    def show_retitle_entry(self, _):
        self.prepare_for_entry()
        gui.show_retitle_entry()

    def show_retag_entry(self, _):
        self.prepare_for_entry()
        gui.show_tag_entry()

    def branch_tag(self, binding_event):
        tag_name = binding_event.binding.symbol
        current_tag = self._tag_tree.find_focused().tag()
        new_tag = copy.copy(current_tag)
        new_tag.name = tag_name
        self.tags.append(new_tag)
        i3.command(f'move window to workspace {tag_name}')

    def prepare_for_entry(self):
        self.stop_listening()
        i3.command('mode default')

    def find_target_name(self, key):
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
        gui.reset()
        target_name = self.find_target_name(symbol)
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

    def process_tag_entry(self, entry):
        if entry == 'quit':
            gui.quit()
            exit()
        # get variables
        current_tag = self._tag_tree.find_focused().workspace()
        current_window = self._tag_tree.find_focused()
        # remove current window from tag tree
        self._tag_tree.remove_node_by_id(current_window.id)
        #
        if entry == '':
            i3.command('kill') #kill focused window
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
            elif current_tag.name not in entry:
                i3.command('move window to workspace {}'.format(entry[0]))
        self.listen_for_bindings()

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


class HighGUI:
    """High-level domain specific graphical user interface commands.

    Commnads are implemented in tkinter. Call only logic, tk_root and
    tkinter."""

    _FOCUS_COLOR = '#cfc'
    _URGENT_COLOR = 'yellow'
    _COLOR_0 = 'white'
    _COLOR_1 = '#fafafa'
    _TAG_PADDING = 40

    def __init__(self):
        tk_root.attributes('-type', 'dialog')
        self.frame = tkinter.Frame(tk_root)
        self.frame.pack()
        self.color_generator = self.color_generator_function()
        self.update = tk_root.update

    def activate(self, tag_tree):
        self._prepare_tags(tag_tree)
        self._set_position(tag_tree)
        self._set_time()
        tk_root.update() # fixes position
        tk_root.deiconify()
        tk_root.update() # fixes content

    def _prepare_tags(self, tag_tree):
        for tag in tag_tree.tags():
            if tag.name == 'hidden':
                continue
            windows = tag.nodes
            if not windows:
                try:
                    windows = tag.floating_nodes[0].nodes
                except IndexError: # no widows at all, label tag name
                    self.add_label(tag.name,
                                   self._FOCUS_COLOR,
                                   self._TAG_PADDING)
            for window in windows:
                self.label_i3_window(tag, window)

    def label_i3_window(self, tag, window):
        if window.focused:
            color = self._FOCUS_COLOR
        elif window.urgent:
            color = self._URGENT_COLOR
        else:
            color = next(self.color_generator)
        self.add_label(f'{tag.name}           {window.window_class}',
                       color,
                       self._TAG_PADDING)
        self.add_label(window.name, color)

    def add_label(self, text, background_color=None, left_padding=None):
        deunicoded = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
        label = tkinter.Label(self.frame, #parent
                              anchor = 'w', #left
                              text = deunicoded,
                              padx = left_padding,
                              bg = background_color)
        label.pack(expand=True, fill='x')

    def color_generator_function(self):
        while True:
            yield self._COLOR_0
            yield self._COLOR_1

    def _set_position(self, tag_tree):
        windows = tag_tree.leaves()
        for window in windows:
            if window.focused:
                tk_root.geometry(f'+{window.rect.x}+{window.rect.y + 75}')
                break

    def _set_time(self):
        tk_root.title(time.asctime(time.localtime()))

    def show_entry(self, on_return_key):
        self.entry = tkinter.Entry(self.frame)
        self.entry.focus()
        self.entry.bind('<Escape>', self._escape_from_entry)
        self.entry.bind('<Return>', on_return_key)
        self.entry.pack()

    def show_retitle_entry(self):
        self.show_entry(self._handle_retitle_entry)

    def show_tag_entry(self):
        self.show_entry(self._handle_tag_entry)

    def _handle_retitle_entry(self, _):
        entry = self.entry.get()
        self.reset()
        logic.retitle_focused_window(entry)
        logic.listen_for_bindings()

    def _handle_tag_entry(self, _):
        entry = self.entry.get()
        self.reset()
        logic.process_tag_entry(entry)

    def _escape_from_entry(self, _=None):
        self.reset()
        logic.listen_for_bindings()

    def reset(self, _=None):
        self.clear()
        tk_root.update()
        tk_root.withdraw()

    def clear(self):
        self.frame.destroy()
        self.frame = tkinter.Frame(tk_root)
        self.frame.pack()

    def show_mode(self, binding_event):
        self.clear()
        self.add_mode(binding_event)

    def add_mode(self, binding_event):
        behind_mode = binding_event.binding.command.split('mode ', 1)[-1]
        mode_hints = behind_mode.split(';', 1)[0].split('|')
        for hint in mode_hints:
            self.add_label(hint)
        tk_root.update()

    def quit(self):
        """Use to avoid calling tk_root from logic."""
        tk_root.destroy()


class I3ipcConMonkeyPatch():
    """Monkey patch, the class used by i3ipc is i3ipc.Con.

    This class
    modifies/extends i3ipc.Con. Don't want to inherit i3ipc.Con and
    thus change identity as it is called by multiple i3ipc classes.
    Methods must be assigned to i3ipc.Con
    class, see the end of class. Call self only."""
    Con = i3ipc.Con
    Con.tag = Con.workspace
    Con.tags = Con.workspaces

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


    Con.remove_focus = remove_focus
    Con.update_tag = update_tag
    Con.remove_node_by_id = remove_node_by_id
    Con.find_tag_by_name = find_tag_by_name


i3 = i3ipc.Connection(auto_reconnect = True)
tk_root = tkinter.Tk()
gui = HighGUI()
logic = BusinessLogic()
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logic.listen_for_bindings() #start hidden
    tk_root.mainloop()
