#!/usr/bin/env python3

import i3ipc
import tkinter
import time
import subprocess
import copy


class TkInter(tkinter.Tk):
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
        self.update()
        self.deiconify()
        self.update()

    def color_generator(self):
        while True:
            yield self._COLOR_0
            yield self._COLOR_1

    def show_entry(self, on_return_key):
        self.entry = tkinter.Entry(self.frame)
        self.entry.focus()
        self.entry.bind('<Escape>', self.reset_after_entry)
        self.entry.bind('<Return>', on_return_key)
        self.entry.pack()

    def show_rename_entry(self):
        self.show_entry(self.process_rename_entry)

    def process_rename_entry(self, _):
        i3.rename_focused_window(self.entry.get())
        self.reset_after_entry()

    def show_tag_entry(self):
        self.show_entry(self.process_tag_entry)

    def process_tag_entry(self, _):
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

    def _set_time(self):
        self.title(time.asctime(time.localtime()))

    def _set_position(self, tag_tree):
        windows = tag_tree.leaves()
        for window in windows:
            if window.focused:
                self.geometry(f'+{window.rect.x}+{window.rect.y + 75}')
                break

    def _prepare_tags(self, tag_tree):
        for tag in tag_tree.tags():
            windows = tag.nodes
            if not windows:
                try:
                    windows = tag.floating_nodes[0].nodes
                except IndexError:
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

    def clear(self):
        self.frame.destroy()
        self.frame = tkinter.Frame(self)
        self.frame.pack()

    def show_mode(self, binding_event):
        self.clear()
        mode_hints = binding_event.binding.command.split('|')
        for hint in mode_hints:
            self.add_label(hint)
        if mode_hints[0].startswith('move '):
            #top_container.add_existing_workspaces()
            #top_container.add_deprecated_workspaces()
            pass
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
        print(binding_event.binding.command)
        binding = binding_event.binding
        command = binding_event.binding.command
        key = binding_event.binding.symbol
        if 'mode default' in command:
            gui.reset()
        elif command == 'mode henkan':
            self._update_tag_tree()
            gui.activate(self._tag_tree)
        elif command.endswith('entry'):
            self.main_quit()
            self.command('mode default')
            if command.endswith('mode entry'):
                gui.show_rename_entry()
            elif command.endswith('mode tag entry'):
                gui.show_tag_entry()
        else:
            gui.show_mode(binding_event)
        if command.startswith('mode tag'):
            self.switch_tag(self.find_target(key))

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
                    self.command(f'[con_id={window.id}]move window to workspace {target}')
                break
        self.command(f'workspace {target}')

    def _update_tag_tree(self):
        self.workspace_tree = self.get_tree()
        self._inspect_tag_tree()
        self._inspect_workspaces()
        self._inspect_windows()
        self.tags.sort(key=lambda x: x.name)

    def process_tag_entry(self, entry):
        current_tag = self._tag_tree.find_focused().workspace()
        current_window = self._tag_tree.find_focused()
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

    def rename_focused_window(self, name):
        subprocess.run(['xdotool',
                        'set_window',
                        '--name',
                        name,
                        str(self._tag_tree.find_focused().window)
                        ])

    def _inspect_tag_tree(self):
        current_workspace = self.workspace_tree.find_focused().workspace()
        self.tags = [
                current_workspace if current_workspace.name == tag.name else
                tag.update_tag(self.workspace_tree)
                for tag in self.tags
                if tag.nodes
                    ]

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



class Con():
    """'monkey patch', the class used by i3ipc is i3ipc.Con, this class
      modifies/extends i3ipc.Con. The names are styled to appear as
      ordinary class, but the methods must be assigned to i3ipc.Con
      class, see the end of class"""
    self = i3ipc.Con
    self.tag = self.workspace
    self.tags = self.workspaces

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

    self.remove_focus = remove_focus
    self.update_tag = update_tag


gui = TkInter()
i3 = I3Wrapper()
if __name__ == '__main__':
    i3.main()
    gui.mainloop()
