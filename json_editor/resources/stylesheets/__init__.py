import os

from PySide2 import QtWidgets


def apply_standalone_stylesheet():
    app = QtWidgets.QApplication.instance()

    with open(get_main_stylesheet_path()) as fp:
        app.setStyleSheet(fp.read())


def get_main_stylesheet_path():
    return os.path.join(os.path.dirname(__file__), "Combinear.qss")
