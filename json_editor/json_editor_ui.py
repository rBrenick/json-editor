import collections
import json
import sys
import time

from . import data_tree
from . import json_editor_system as system
from . import ui_utils
from .ui_utils import QtCore, QtWidgets, QtGui

standalone_app = None
if not QtWidgets.QApplication.instance():
    standalone_app = QtWidgets.QApplication(sys.argv)
    from .resources import stylesheets

    stylesheets.apply_standalone_stylesheet()


class JsonEditorWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(JsonEditorWidget, self).__init__(*args, **kwargs)

        self.main_layout = QtWidgets.QVBoxLayout()

        self.active_json_indent_level = None
        self.last_font_change_time = 1

        self.path_widget = ui_utils.QtPathWidget(
            settings_name="JsonEditor",
            file_filter="JSON (*.json)",
            recent_paths_amount=100,
            only_show_existing_recent_paths=True,
        )

        self.filter_widget = QtWidgets.QLineEdit()
        self.filter_widget.setPlaceholderText("filter")
        self.filter_widget.setClearButtonEnabled(True)
        self.filter_widget.textEdited.connect(self.filter_data)

        self.data_tree_widget = data_tree.DataTreeWidget()
        # self.batch_modify_widget = batch_name.BatchNameWidget()
        self.data_tree_widget.data_is_shown.connect(self.data_visibility_state_changed)

        self.helper_overlay = HelperMessageOverlay(self.data_tree_widget.tree_widget)

        self.data_tree_widget.tree_widget.viewport().installEventFilter(self)
        self.setAcceptDrops(True)

        ###########################################################
        # JSON editor specific ui
        self.modify_hierarchy = QtWidgets.QCheckBox("Modify Hierarchy")
        self.modify_hierarchy.setChecked(True)
        self.modify_type_chooser = QtWidgets.QComboBox()
        self.modify_type_chooser.addItems(["Keys & Values", "Keys", "Values"])
        self.modify_rename_button = QtWidgets.QPushButton("Rename")
        self.modify_duplicate_button = QtWidgets.QPushButton("Duplicate")

        # connect signals
        # self.modify_rename_button.clicked.connect(self.modify_rename)
        # self.modify_duplicate_button.clicked.connect(self.modify_duplicate)

        modify_layout = QtWidgets.QHBoxLayout()
        modify_layout.setContentsMargins(0, 0, 0, 0)
        modify_layout.addWidget(self.modify_hierarchy)
        modify_layout.addWidget(self.modify_type_chooser)
        modify_layout.addWidget(self.modify_rename_button)
        modify_layout.addWidget(self.modify_duplicate_button)
        ###########################################################

        self.main_layout.addWidget(self.path_widget)
        self.main_layout.addWidget(self.filter_widget)
        # main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        # main_splitter.addWidget(self.data_tree_widget)
        # main_splitter.addWidget(self.batch_modify_widget)
        # self.main_layout.addWidget(main_splitter)
        self.main_layout.addWidget(self.data_tree_widget)
        # self.main_layout.addWidget(self.batch_modify_widget)
        # self.main_layout.addLayout(modify_layout)
        self.setLayout(self.main_layout)

        self.path_widget.path_changed.connect(self.load_json)

    def filter_data(self):
        filter_text = self.filter_widget.text()

        self.data_tree_widget.set_filter(filter_text, search_columns=(data_tree.lk.col_key, data_tree.lk.col_value))

        if filter_text:
            self.data_tree_widget.tree_widget.expandAll()
        else:
            self.data_tree_widget.tree_widget.expandToDepth(self.data_tree_widget.default_expand_depth)

    def data_visibility_state_changed(self, state):
        self.helper_overlay.setVisible(not state)

    ###############################################################################
    # File Handling
    def load_json(self, path):
        json_data = system.load_json(path)
        if json_data is None:
            return

        self.active_json_indent_level = system.get_json_indent_level(path)
        if self.active_json_indent_level is not None:
            print("found indentation in file, setting to: {}".format(self.active_json_indent_level))

        self.data_tree_widget.set_data(json_data)
        print("Loaded Json from: {}".format(path))

    def new_file(self):
        self.path_widget.set_path("")
        self.data_tree_widget.action_clear()
        self.active_json_indent_level = None

    def save_json(self, path=None):
        data_from_ui = self.data_tree_widget.get_data()
        if data_from_ui == "":
            print("No data found in UI, please define a root type before saving")
            return

        ui_path = self.path_widget.path()
        if path is None:
            if ui_path:
                path = ui_path
            else:
                path = self.path_widget.get_dialog_path()

        system.save_json(data_from_ui, path, indent=self.active_json_indent_level)
        print("Saved Json to: {}".format(path))

        # file was newly saved, set the path in the UI
        if not ui_path:
            self.path_widget.set_path(path)

    def save_json_as(self):
        new_path = self.path_widget.get_dialog_path()
        self.save_json(new_path)
        self.path_widget.set_path(new_path)

    def reload(self):
        self.load_json(self.path_widget.path())

    ###############################################################################
    # Overrides

    def resizeEvent(self, event):
        self.helper_overlay.resize(event.size())
        event.accept()

    def eventFilter(self, qobject, event):
        if event.type() == QtCore.QEvent.Wheel:
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                if event.delta() > 0:
                    self.increment_tree_font_size(1)
                else:
                    self.increment_tree_font_size(-1)
                return True

        return False  # standard event processing

    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():  # if file or link is dropped
            url = event.mimeData().urls()[0]  # get first url
            self.path_widget.set_path(url.toLocalFile())
        else:
            try:
                text = event.mimeData().text()
                json_data = json.loads(text, object_pairs_hook=collections.OrderedDict)
                self.data_tree_widget.set_data(json_data)
            except Exception as e:
                self.status_message("No JSON serializable data could be read from string")

    ###############################################################################
    # Font Size

    def increment_tree_font_size(self, direction):
        if time.time() - self.last_font_change_time < 0.02:
            return

        current_font = self.data_tree_widget.tree_widget.font()
        new_font_size = current_font.pointSize() + direction
        self.set_tree_font_size(new_font_size)

    def set_tree_font_size(self, size=8):
        current_font = self.data_tree_widget.tree_widget.font()
        current_font.setPointSizeF(size)
        self.data_tree_widget.tree_widget.setFont(current_font)
        self.last_font_change_time = time.time()
        self.helper_overlay.font_size = size + 6


class HelperMessageOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HelperMessageOverlay, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background, QtCore.Qt.transparent)

        self.font_size = 13
        self.empty_json_message = "Drag and drop a JSON file, \n" \
                                  "or drag in JSON readable data, \n" \
                                  "or paste data from clipboard."

        self.setPalette(palette)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(100, 100, 100, 100)))
        painter.setFont(QtGui.QFont("seqoe", self.font_size))
        painter.drawText(event.rect(), QtCore.Qt.AlignCenter, self.empty_json_message)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))


class JsonEditorWindow(ui_utils.ToolWindow):
    def __init__(self):
        super(JsonEditorWindow, self).__init__()
        self.ui = JsonEditorWidget()
        self.setCentralWidget(self.ui)
        self.setWindowTitle("JSON Editor")

        menu_bar = QtWidgets.QMenuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.setTearOffEnabled(True)
        file_menu.addAction("New", self.ui.new_file, QtGui.QKeySequence("Ctrl+N"))
        file_menu.addAction("Open", self.ui.path_widget.open_dialog_and_set_path, QtGui.QKeySequence("Ctrl+O"))
        file_menu.addAction("Save", self.ui.save_json, QtGui.QKeySequence("Ctrl+S"))
        file_menu.addAction("Save As...", self.ui.save_json_as, QtGui.QKeySequence("Ctrl+Shift+S"))
        file_menu.addSeparator()
        file_menu.addAction("Reload from Disk", self.ui.reload, QtGui.QKeySequence("F5"))

        edit_menu = menu_bar.addMenu("Edit")
        edit_menu.setTearOffEnabled(True)
        edit_menu.addAction(
            "Cut",
            self.ui.data_tree_widget.action_cut_data_to_clipboard,
            QtGui.QKeySequence("Ctrl+X"),
        )

        edit_menu.addAction(
            "Copy",
            self.ui.data_tree_widget.action_copy_data_to_clipboard,
            QtGui.QKeySequence("Ctrl+C"),
        )

        edit_menu.addAction(
            "Paste",
            self.ui.data_tree_widget.action_paste_data_from_clipboard,
            QtGui.QKeySequence("Ctrl+V"),
        )

        edit_menu.addAction(
            "Duplicate",
            self.ui.data_tree_widget.action_duplicate_selected_items,
            QtGui.QKeySequence("Ctrl+D"),
        )

        edit_menu.addAction(
            "Delete",
            self.ui.data_tree_widget.delete_selected_items,
            QtGui.QKeySequence("DEL"),
        )

        edit_menu.addSeparator()
        edit_menu.addAction(
            "Move Up",
            self.ui.data_tree_widget.action_move_selected_items_up,
            QtGui.QKeySequence("Alt+Up"),
        )

        edit_menu.addAction(
            "Move Down",
            self.ui.data_tree_widget.action_move_selected_items_down,
            QtGui.QKeySequence("Alt+Down"),
        )

        display_menu = menu_bar.addMenu("Display")
        display_menu.setTearOffEnabled(True)
        display_menu.addAction(
            "Reset Font Size",
            self.ui.set_tree_font_size,
        )

        display_menu.addAction(
            "Increase Font Size",
            (lambda: self.ui.increment_tree_font_size(1)),
            QtGui.QKeySequence("Ctrl++"),
        )

        display_menu.addAction(
            "Decrease Font Size",
            (lambda: self.ui.increment_tree_font_size(-1)),
            QtGui.QKeySequence("Ctrl+-"),
        )

        self.setMenuBar(menu_bar)


def main(refresh=False):
    win = JsonEditorWindow()
    win.main(refresh=refresh)

    if standalone_app:
        ui_utils.standalone_app_window = win
        sys.exit(standalone_app.exec_())

    return win


if __name__ == "__main__":
    main()
