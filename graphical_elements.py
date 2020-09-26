import time
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QFrame,\
    QLabel


class MainWindow(QDialog):
    def __init__(self, parent=None):
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

    def move_(self, x, y):
        try:
            self.move(x, y)
        except OverflowError:
            pass

    def show_entry(self, callback):
        self.entry = QLineEdit()
        self.entry.returnPressed.connect(callback)
        self.layout_.addWidget(self.entry)
        self.entry.setFocus()

    def add_label(self, text, sunken=False, raised=False):
        label = QLabel(text, self)
        if sunken:
            label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        elif raised:
            label.setFrameStyle(QFrame.Panel | QFrame.Raised)
        label.setLineWidth(2)
        self.layout_.addWidget(label)
