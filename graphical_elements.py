import time
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QFrame,\
    QLabel


class MainWindow(QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.layout_ = QVBoxLayout()
        self.setLayout(self.layout_)
        # override Escape key behavior
        self.reject = self.reset
        self.entry = None

    def show_(self):
        self.update_title()
        self.adjustSize()
        self.show()

    def reset(self):
        self.clear()
        self.hide()

    def clear(self):
        for i in reversed(range(self.layout_.count())):
            self.layout_.takeAt(i).widget().deleteLater()

    def move_(self, x, y):
        try:
            self.move(x, y)
        except OverflowError:
            pass

    def show_entry(self, callback):
        def on_return():
            entry = self.entry.text()
            self.reset()
            callback(entry)

        self.entry = QLineEdit()
        self.entry.returnPressed.connect(on_return)
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

    def update_title(self):
        time_ = time.asctime(time.localtime())
        self.setWindowTitle(time_)
