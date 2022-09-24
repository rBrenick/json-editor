from functools import partial

from .ui_utils import QtWidgets


class BatchNameWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(BatchNameWidget, self).__init__(*args, **kwargs)

        self._search_replace_widgets = []

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.prefix_line_edit = QtWidgets.QLineEdit()
        self.prefix_line_edit.setPlaceholderText("Prefix")
        self.prefix_line_edit.setClearButtonEnabled(True)
        self.suffix_line_edit = QtWidgets.QLineEdit()
        self.suffix_line_edit.setPlaceholderText("Suffix")
        self.suffix_line_edit.setClearButtonEnabled(True)

        self.add_search_replace_button = QtWidgets.QPushButton("+")
        self.add_search_replace_button.clicked.connect(self.add_search_replace_line)

        self.search_replace_layout = QtWidgets.QVBoxLayout()
        self.search_replace_layout.setContentsMargins(0, 0, 0, 0)

        default_items_layout = QtWidgets.QHBoxLayout()
        default_items_layout.setContentsMargins(0, 0, 0, 0)
        default_items_layout.addWidget(self.prefix_line_edit)
        default_items_layout.addWidget(self.suffix_line_edit)
        default_items_layout.addWidget(self.add_search_replace_button)

        self.main_layout.addLayout(self.search_replace_layout)
        self.main_layout.addLayout(default_items_layout)

        self.setLayout(self.main_layout)

    def add_search_replace_line(self):
        widget = SearchReplaceWidget()
        widget.remove_button.clicked.connect(partial(self.remove_sr_widget, widget))
        self.search_replace_layout.addWidget(widget)
        self._search_replace_widgets.append(widget)

    def remove_sr_widget(self, widget):
        self.search_replace_layout.removeWidget(widget)
        self._search_replace_widgets.remove(widget)
        widget.deleteLater()

    def modify_string(self, input_string):
        output_string = input_string
        for sr_widget in self._search_replace_widgets:  # type: SearchReplaceWidget
            output_string = output_string.replace(
                sr_widget.search_line.text(),
                sr_widget.replace_line.text()
            )
        return "{}{}{}".format(self.prefix_line_edit.text(), output_string, self.suffix_line_edit.text())


class SearchReplaceWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(SearchReplaceWidget, self).__init__(*args, **kwargs)
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText("Search")
        self.replace_line = QtWidgets.QLineEdit()
        self.replace_line.setPlaceholderText("Replace")
        main_layout.addWidget(self.search_line)
        main_layout.addWidget(self.replace_line)

        self.remove_button = QtWidgets.QPushButton("-")
        main_layout.addWidget(self.remove_button)
        self.setLayout(main_layout)
