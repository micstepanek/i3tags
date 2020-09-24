import time

from PySide2.QtWidgets import QDialog, QVBoxLayout


class MainWindow(QDialog):
    def __init__(self, tag_tree, parent=None):
        super(MainWindow, self).__init__(parent)
        time_ = time.asctime(time.localtime())
        self.setWindowTitle(time_)
        self.layout_ = QVBoxLayout()
        self.setLayout(self.layout_)

    def clear(self):
        for i in reversed(range(self.layout_.count())):
            self.layout_.takeAt(i).widget().deleteLater()

    def move_above_focused_window(self, tag_tree):
        windows = tag_tree.leaves()
        for window in windows:
            if window.focused:
                self.move(window.rect.x, window.rect.y + 75)
                break
