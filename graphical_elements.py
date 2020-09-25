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

    def reject(self):
        self.destroy()

    def clear(self):
        for i in reversed(range(self.layout_.count())):
            self.layout_.takeAt(i).widget().deleteLater()

    def move_above_focused_window(self, tag_tree):
        windows = tag_tree.leaves()
        for window in windows:
            if window.focused:
                try:
                    self.move(window.rect.x, window.rect.y + 75)
                except OverflowError:
                    pass
                break

    def show_entry(self, callback):
        self.entry = QLineEdit()
        self.entry.returnPressed.connect(callback)
        self.layout_.addWidget(self.entry)
        self.entry.setFocus()
