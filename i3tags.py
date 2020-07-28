#!/usr/bin/env python3

import i3ipc
import tkinter
import time
import subprocess
import copy


class TkWrapper(tkinter.Tk):
    _FOCUS_COLOR = '#cfc'
    _URGENT_COLOR = 'yellow'
    _COLOR_0 = 'white'
    _COLOR_1 = '#fafafa'
    _TAG_PADDING = 40

    def __init__(self):
        super().__init__()
        self.attributes('-type', 'dialog')
        self.frame = tkinter.Frame(self)
        self.frame.pack()
        self.color_generator = self.color_generator()

    def activate(self, tag_tree):
        self._prepare_tags(tag_tree)
        self._set_position(tag_tree)
        self._set_time()
        self.update() # fixes position
        self.deiconify()
        self.update() # fixes content

    def _prepare_tags(self, tag_tree):
        for tag in tag_tree.tags():
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
        label = tkinter.Label(self.frame, #parent
                              anchor = 'w', #left
                              text = text,
                              padx = left_padding,
                              bg = background_color)
        label.pack(expand=True, fill='x')

    def color_generator(self):
        while True:
            yield self._COLOR_0
            yield self._COLOR_1

    def _set_position(self, tag_tree):
        windows = tag_tree.leaves()
        for window in windows:
            if window.focused:
                self.geometry(f'+{window.rect.x}+{window.rect.y + 75}')
                break

    def _set_time(self):
        self.title(time.asctime(time.localtime()))

    def show_entry(self, on_return_key):
        self.entry = tkinter.Entry(self.frame)
        self.entry.focus()
        self.entry.bind('<Escape>', self.reset_after_entry)
        self.entry.bind('<Return>', on_return_key)
        self.entry.pack()

    def show_rename_entry(self):
        self.show_entry(self.process_rename_entry)

    def process_rename_entry(self, _):
        i3.retitle_focused_window(self.entry.get())
        self.reset_after_entry()

    def show_tag_entry(self):
        self.show_entry(self.redirect_tag_entry)

    def redirect_tag_entry(self, _):
        entry = self.entry.get()
        self.reset()
        i3.process_tag_entry(entry)
        i3.main()

    def reset_after_entry(self, _=None):
        self.reset()
        i3.main()

    def reset(self):
        self.clear()
        self.update()
        self.withdraw()

    def clear(self):
        self.frame.destroy()
        self.frame = tkinter.Frame(self)
        self.frame.pack()

    def show_mode(self, command):
        self.clear()
        mode_hints = command[5:].split('|')
        for hint in mode_hints:
            self.add_label(hint)
        self.update()


class I3Wrapper(i3ipc.Connection):
    def __init__(self):
        super().__init__()
        self.on(i3ipc.Event.BINDING, self.handle_mode)
        self._tag_tree = self.get_tree()
        self.previous_tag = self._tag_tree.find_focused().workspace().name

    @property
    def tags(self):
        return self._tag_tree.nodes[1].nodes[1].nodes

    @tags.setter
    def tags(self, list_):
        self._tag_tree.nodes[1].nodes[1].nodes = list_

    def handle_mode(self, _, binding_event):
        command = binding_event.binding.command
        print(command)
        key = binding_event.binding.symbol
        if 'mode default' in command:
            gui.reset()
            if command.startswith('mode tag'):
                self.switch_tag(self.find_target(key))
        elif command == 'mode henkan':
            self._update_tag_tree()
            gui.activate(self._tag_tree)
        elif command.endswith('retitle window'):
            self.prepare_for_entry()
            gui.show_rename_entry()
        elif command.endswith('retag window'):
            self.prepare_for_entry()
            gui.show_tag_entry()
        else:
            gui.show_mode(command)

    def prepare_for_entry(self):
        self.main_quit()
        self.command('mode default')

    def find_target(self, key):
        current_tag = self._tag_tree.find_focused().workspace().name
        if current_tag == key:
            target = self.previous_tag
        else:
            target = key
        self.previous_tag = current_tag
        return target

    def switch_tag(self, target):
        for tag in self.tags:
            if tag.name == target:
                for window in tag.nodes:
                    self.command(f'[con_id={window.id}]move window to workspace tmp')
                    self.command(f'[con_id={window.id}]move window to workspace {target}')
                break
        #self.command(f'workspace {target}')
        # - blocked by PyCharm if going to empty workspace
        # subprocess with i3-msg works
        subprocess.run(['i3-msg', 'workspace', target])

    def _update_tag_tree(self):
        self.workspace_tree = self.get_tree()
        self._inspect_tag_tree()
        self._inspect_workspaces()
        self._inspect_windows()
        self.tags.sort(key=lambda x: x.name)

    def process_tag_entry(self, entry):
        if entry == 'quit':
            gui.destroy()
            exit()
        current_tag = self._tag_tree.find_focused().workspace()
        current_window = self._tag_tree.find_focused()
        self._tag_tree.remove_node_by_id(current_window.id)
        if entry == '':
            self.command('kill') #kill focused window
        else:
            change_workspace_later = False
            for char in entry:
                if char == '.':
                    change_workspace_later = True
                    break
                else:
                    placed = self._add_to_existing_tag(char, current_window)
                if not placed:
                    new_tag = copy.copy(current_tag)
                    new_tag.name = char
                    new_tag.nodes = [current_window]
                    self.tags.append(new_tag)
            if change_workspace_later:
                self.switch_tag(entry[0])
            elif current_tag.name not in entry:
                self.command('move window to workspace {}'.format(entry[0]))

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
        current_workspace = self.workspace_tree.find_focused().workspace()
        tags = [
                current_workspace if current_workspace.name == tag.name else
                tag.update_tag(self.workspace_tree)
                for tag in self.tags
                    ]
        self.tags = [tag for tag in tags if tag.nodes]

    def _inspect_workspaces(self):
        tag_names = [tag.name for tag in self.tags]
        for workspace in self.workspace_tree.workspaces():
            if workspace.name not in tag_names:
                self.tags.append(workspace)

    def _inspect_windows(self):
        tagged_window_IDs = [window.id for window in self._tag_tree.leaves()]
        for window in self.workspace_tree.leaves():
            if window.id not in tagged_window_IDs:
                #copy window frow workspace to tag
                workspace_id = (self.workspace_tree
                                .find_by_id(window.id)
                                .workspace().id)
                self._tag_tree.find_by_id(workspace_id).nodes.append(window)


class I3ipcConMonkeyPatch():
    """Monkey patch, the class used by i3ipc is i3ipc.Con, this class
      modifies/extends i3ipc.Con. Do not want to inherit it and thus
      change identity as it is called by multiple i3ipc classes.
      Methods must be assigned to i3ipc.Con
      class, see the end of class"""
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

    Con.remove_focus = remove_focus
    Con.update_tag = update_tag
    Con.remove_node_by_id = remove_node_by_id


gui = TkWrapper()
i3 = I3Wrapper()
if __name__ == '__main__':
    i3.main()
    gui.mainloop()
