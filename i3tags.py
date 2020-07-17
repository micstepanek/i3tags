#!/usr/bin/env python3

import i3ipc
import tkinter
import time
import subprocess

class ConnectionToI3WindowManager(i3ipc.Connection):
    def __init__(self):
        super().__init__()
        self.on(i3ipc.Event.MODE, self.handle_mode)
        self.tag_tree = self.get_tree()

    @property
    def tags(self):
        return self._tag_tree.nodes[1].nodes[1].nodes

    @tags.setter
    def tags(self, list_):
        self._tag_tree.nodes[1].nodes[1].nodes = list_

    def handle_mode(self, _, mode_event):
        print(mode_event.change)
        mode = mode_event.change
        if mode == 'henkan':
            self.update_tags()
            gui.activate(self.tag_tree)
        elif mode.endswith('entry'):
            self.main_quit()
            self.command('mode default')
            if mode == 'entry':
                gui.loop_rename_entry()
            elif mode == 'tag entry':
                raise NotImplementedError
        elif mode == 'default':
            gui.clear()
            gui.withdraw()
        else:
            gui.show_mode(mode_event)


    def update_tags(self):
        self.tag_tree = self.get_tree()


class TkInter(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.attributes('-type', 'dialog')
        self.frame = tkinter.Frame(self)
        self.frame.pack()

    def activate(self, tag_tree):
        self._prepare_tags(tag_tree)
        self._set_position(tag_tree)
        self._set_time()
        self.update()
        self.deiconify()
        self.update()

    def loop_rename_entry(self):
        self.entry = tkinter.Entry(gui.frame)
        self.entry.focus()
        self.entry.bind('<Escape>', self.quit_entry)
        self.entry.bind('<Return>', self.process_rename_entry)
        self.entry.pack()

    def process_rename_entry(self, _):
        subprocess.run(['xdotool',
                        'set_window',
                        '--name',
                        self.entry.get(),
                        str(i3.tag_tree.find_focused().window)
                        ])
        self.quit_entry(_)

    def quit_entry(self, _):
        gui.clear()
        gui.update()
        gui.withdraw()
        i3.main()

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
            if tag.focused:
                self.add_label(tag.name, 'lightgreen')
            else:
                self.add_label(tag.name)
            windows = tag.nodes
            for window in windows:
                if window.focused:
                    self.add_label(f'  {window.window_title}', 'lightgreen')
                elif window.urgent:
                    self.add_label(f'  {window.window_title}', 'yellow')
                else:
                    self.add_label(f'  {window.window_title}')

    def add_label(self, text, background_color=None):
        label = tkinter.Label(self.frame,
                              anchor = 'w', #left
                              text = text,
                              bg = background_color)
        label.pack(expand=True, fill='x')

    def clear(self):
        self.frame.destroy()
        self.frame = tkinter.Frame(self)
        self.frame.pack()

    def show_mode(self, mode_event):
        gui.clear()
        mode_hints = mode_event.change.split('|')
        for hint in mode_hints:
            self.add_label(hint)
        if mode_hints[0].startswith('move '):
            #top_container.add_existing_workspaces()
            #top_container.add_deprecated_workspaces()
            pass
        self.update()

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
i3 = ConnectionToI3WindowManager()
i3.main()
gui.mainloop()
