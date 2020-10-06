from PySide2.QtCore import QObject, Signal


class Signals(QObject):
    show_tags = Signal(object)
    reset = Signal()
    show_mode = Signal(object)
    add_retag_entry = Signal()