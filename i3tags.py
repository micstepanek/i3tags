#!/usr/bin/env python3

import i3ipc
import tkinter
import subprocess
import os

'''Run as service, run once'''

class ConnectionToI3WindowManager(i3ipc.Connection):
    def __init__(self):
        super().__init__()
        self.on(i3ipc.Event.BINDING, self.handle_hotkey)
        self._tag_tree = self.get_tree()
        self.listen_for_hotkey = self.main
        self._stop_listening_for_hotkey = self.main_quit
        self.tags = self._tag_tree.nodes[1].nodes[1].nodes

    @property
    def tags(self):
        return self._tag_tree.nodes[1].nodes[1].nodes

    @tags.setter
    def tags(self, list_):
        self._tag_tree.nodes[1].nodes[1].nodes = list_

    def handle_hotkey(self, _, key_event):
        if key_event.binding.symbol == 'Muhenkan':
            self._stop_listening_for_hotkey()
            self.update_tag_tree()
            widget.activate(self._tag_tree)

    def update_tag_tree(self):
        self.workspace_tree = self.get_tree()
        self.inspect_tag_tree()
        self.inspect_workspaces()
        self.inspect_windows()
        self.tags.sort(key=lambda x: x.name)

    def inspect_tag_tree(self):
        current_workspace = self.workspace_tree.find_focused().workspace()
        current_workspace.focused = True
        'tag is now focused if it has focus or focused window'
        self.tags = [
                current_workspace if current_workspace.name == tag.name else
                tag.update_tag(self.workspace_tree)
                for tag in self.tags
                if tag.nodes
                    ]

    def inspect_workspaces(self):
        tag_names = [tag.name for tag in self.tags]
        for workspace in self.workspace_tree.workspaces():
            if workspace.name not in tag_names:
                self.tags.append(workspace)

    def inspect_windows(self):
        tagged_window_IDs = [window.id for window in self._tag_tree.leaves()]
        for window in self.workspace_tree.leaves():
            if window.id not in tagged_window_IDs:
                #copy window frow workspace to tag
                workspace_id = (self.workspace_tree
                                .find_by_id(window.id)
                                .workspace().id)
                self._tag_tree.find_by_id(workspace_id).nodes.append(window)



    def switch_tags(self, key_event):
        widget.reset()
        # TODO if self.workspace_not_as_tag():
        # TODO self.rearrange_workspace
        self.go_to_workspace(key_event)
        self.listen_for_hotkey()

    def go_to_workspace(self, key_event):
        print(f'workspace {key_event.keysym}')
        self.command(f'workspace {key_event.keysym}')

    def do(self, command):
        widget.reset()
        self.command(command)
        self.listen_for_hotkey()

class GUI(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.title('i3tags') # TODO display sth interesting
        self.attributes('-type', 'dialog')
        self.frame = tkinter.Frame(self)
        self.frame.pack()
        self.bind('<Key>', mode_default.handle)
        self.go_visible = self.deiconify

    def activate(self, tags_tree):
        self._update_position(tags_tree)
        self.prepare_tags(tags_tree)
        self.update()
        self.go_visible()

    def _update_position(self, tags_tree):
        windows = tags_tree.leaves()
        for window in windows:
            if window.focused:
                self.geometry(f'+{window.rect.x}+{window.rect.y + 75}')
                break

    def prepare_tags(self, tags_tree):
        tags = tags_tree.tags()
        for tag in tags:
            if tag.focused:
                Label_(f'{tag.name}', 'lightgreen')
            else:
                Label_(f'{tag.name}')
            windows = tag.nodes
            for window in windows:
                if window.focused:
                    Label_(f'  {window.window_title}', 'lightgreen')
                elif window.urgent:
                    Label_(f'  {window.window_title}', 'yellow')
                else:
                    Label_(f'  {window.window_title}')

    def reset(self):
        self.bind('<Key>', mode_default.handle)
        self.clear()
        self.update()
        self.withdraw()

    def clear(self):
        self.frame.destroy()
        self.frame = tkinter.Frame(self)
        self.frame.pack()


class Label_(tkinter.Label):
    def __init__(self, text, background_color=None):
        LEFT = 'w'
        super().__init__(
            widget.frame, anchor=LEFT, text=text, bg=background_color)
        self.pack(expand=True, fill='x')


class Mode:
    """Parent of modes, no instance"""

    def _call_key_symbol_as_method(self, key_event):
        getattr(self, f'_handle_key_{key_event.keysym}')()

    def _handle_key_Escape(self):
        widget.reset()
        i3.listen_for_hotkey()

    def _remove_keyboard_modifiers(self):
        subprocess.run(['xdotool', 'key', '--delay', '0', 'VoidSymbol'])


class ModeDefault(Mode):
    def handle(self, key_event):
        print(key_event.keysym)
        try:
            self._call_key_symbol_as_method(key_event)
        except AttributeError:
            i3.switch_tags(key_event)

    def _handle_key_ISO_Level2_Latch(self):
        mode_directory = ModeDirectory('level2')
        widget.bind('<KeyPress>', mode_directory.handle)
        self._remove_keyboard_modifiers()

    def _handle_key_ISO_Level5_Latch(self):
        self._remove_keyboard_modifiers()
        mode_entry = ModeEntry()  # mark

    def _handle_key_h(self):
        i3.do('focus left')

    def _handle_key_l(self):
        i3.do('focus right')

    def _handle_key_period(self):
        # spawn terminal
        subprocess.run(['nohup', 'urxvtc', '-cd', '/home/h/'])
        widget.reset()
        i3.listen_for_hotkey()

    def _handle_key_slash(self):
        # spawn file manager
        subprocess.run(['nohup', 'urxvtc', '-e', 'vifm'])
        widget.reset()
        i3.listen_for_hotkey()


class ModeDirectory(Mode):
    def __init__(self, relative_path):
        self.remaining_options = self._get_subdirectory_files(relative_path)
        self.compared_position = 0
        widget.clear()
        Label_('directory_mode', 'lightgreen')

    def _get_subdirectory_files(self, relative_path):
        this_file_path = os.path.realpath(__file__)
        this_file_directory = os.path.dirname(this_file_path)
        subdirectory = os.path.join(this_file_directory, relative_path)
        subdirectory_files = os.listdir(subdirectory)
        return subdirectory_files

    def handle(self, key_event):
        try:
            self._call_key_symbol_as_method(key_event)
        except AttributeError:
            self._suggest_from_remaining_options(key_event)

    def _suggest_from_remaining_options(self, key_event):
        suggestions = [option for option in self.remaining_options
                        if key_event.char == option[self.compared_position]]
        if len(suggestions) > 1:
            self.remaining_options = suggestions
            prefix = os.path.commonprefix(suggestions)
            self.compared_position = len(prefix)
            widget.clear()
            Label_(prefix, 'lightgreen')
            options_prefix_hidden = [option[len(prefix):] for option in suggestions]
            [Label_(option) for option in options_prefix_hidden]
        elif len(suggestions) == 1:
            launcher.run(suggestions[0])
            widget.reset()
            i3.listen_for_hotkey()
        elif suggestions == []:
            pass
        else:
            raise AssertionError


class ModeEntry(Mode):
    def __init__(self):
        widget.unbind('<Key>')
        self.entry = tkinter.Entry(widget.frame)
        self.entry.bind('<Return>', self.handle)
        self.entry.bind('<Escape>', self.handle)
        self.entry.focus()
        self.entry.pack()

    def handle(self, key_event):
        self._call_key_symbol_as_method(key_event)

    def _handle_key_Return(self):
        widget.withdraw()
        self._process(self.entry.get())
        widget.deiconify()
        widget.reset()
        i3.listen_for_hotkey()

    def _process(self, entry):
        if entry == '':
            i3.command('kill')
        elif entry == 'q':
            widget.quit()
        else:
            i3.command(f'move container to workspace {entry}')


class Launcher():
    def spawn_terminal(self):
        subprocess.run(['nohup', 'urxvtc', '-cd', '/home/h/'])
        widget.reset()
        i3.listen_for_hotkey()

    def urxvtc(self, command):
        subprocess.run(['urxvtc', '-e', command])

    def run(self, command):
        if command in os.listdir('/home/h/aa/bin/i3tags/urxvt'):
            subprocess.Popen(['nohup', 'urxvtc', '-e', command])
        else:
            subprocess.Popen([command])



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


if __name__ == '__main__':
    i3 = ConnectionToI3WindowManager()
    launcher = Launcher()
    mode_default = ModeDefault()
    widget = GUI()
    i3.main()
    widget.mainloop()