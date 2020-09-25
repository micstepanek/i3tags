import time

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLineEdit


class MainWindow(QDialog):
    def __init__(self, tag_tree, parent=None):
        super(MainWindow, self).__init__(parent)
        time_ = time.asctime(time.localtime())
        self.setWindowTitle(time_)
        self.layout_ = QVBoxLayout()
        self.setLayout(self.layout_)

    # override Escape key behavior
    def reject(self):
        self.destroy()

    def clear(self):
        for i in reversed(range(self.layout_.count())):
            self.layout_.takeAt(i).widget().deleteLater()

    def move_above_focused_window(self, workspace_tree):
        focused_window = workspace_tree.find_focused()
        try:
            self.move(focused_window.rect.x, focused_window.rect.y + 75)
        except OverflowError:
            pass

    def show_entry(self, callback):
        self.entry = QLineEdit()
        self.entry.returnPressed.connect(callback)
        self.layout_.addWidget(self.entry)
        self.entry.setFocus()
