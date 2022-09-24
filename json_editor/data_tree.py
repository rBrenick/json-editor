import json
import os
import re
import sys
from collections import OrderedDict
from functools import partial

from json_editor import ui_utils
from json_editor.ui_utils import QtCore, QtWidgets


class LocalConstants:
    col_key = 0
    col_value = 1
    col_type = 2

    add_types = (str, int, float, bool, dict, list)
    default_add_values = {
        str: "STRING",
        dict: {"key": "value"},
        list: ["list_item"],
    }

    root_add_values = {
        dict: {"key": "value"},
        OrderedDict: {"ordered_key": "ordered_value"},
        list: ["list_item"],
        tuple: ["tuple_item"],
    }

    default_key_name = "KEY"

    list_types = (list, tuple)
    dict_types = (dict, OrderedDict)
    list_type_names = (list.__name__, tuple.__name__)
    dict_type_names = (dict.__name__, OrderedDict.__name__)
    supports_children_types = list_types + dict_types
    supports_children_type_names = list_type_names + dict_type_names
    none_type_name = str(type(None).__name__)

    header_names = ("Key", "Value", "Type")


lk = LocalConstants


class DataTreeWidget(QtWidgets.QWidget):
    data_is_shown = QtCore.Signal(bool)

    def __init__(self, *args, **kwargs):
        super(DataTreeWidget, self).__init__(*args, **kwargs)
        self.default_expand_depth = 2
        self._root_type = None

        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setSelectionMode(QtWidgets.QTreeWidget.ExtendedSelection)

        # right click menu
        self.tree_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.build_tree_context_menu)
        self.tree_widget.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree_widget.header().customContextMenuRequested.connect(self.build_tree_context_menu)

        self.tree_widget.setHeaderLabels(lk.header_names)
        self.update_header_display()

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.tree_widget)
        self.setLayout(self.main_layout)

    #################################################################################################################
    # the two most important functions

    def set_data(self, data):
        self.tree_widget.clear()
        self.data_is_shown.emit(True)

        self._root_type = type(data)
        self.tree_widget.invisibleRootItem().setData(lk.col_type, QtCore.Qt.DisplayRole, self._root_type.__name__)

        self.add_data_to_widget(data_value=data, parent_item=self.tree_widget.invisibleRootItem(), merge=True)

        self.tree_widget.expandToDepth(self.default_expand_depth)
        self.update_header_display()

    def get_data(self):
        return self.get_widget_item_values(self.tree_widget.invisibleRootItem())

    #################################################################################################################

    def build_tree_context_menu(self):
        action_list = list()

        if self._root_type is None:
            for add_type in lk.supports_children_types:
                action_list.append({
                    "Set Root Type - {}".format(add_type.__name__): partial(self.set_root_type, add_type)
                })
        else:
            action_list.extend([
                {"Cut": self.action_cut_data_to_clipboard},
                {"Copy": self.action_copy_data_to_clipboard},
                {"Paste": self.action_paste_data_from_clipboard},
                {"Duplicate": self.action_duplicate_selected_items},
                {"Delete": self.delete_selected_items},
                "-",
                {"Move Up": self.action_move_selected_items_up},
                {"Move Down": self.action_move_selected_items_down},
                {"Sort Alphabetical": self.sort_selected_items},
                "-",
            ])

            for add_type in lk.add_types:
                action_list.append({
                    "Add - {}".format(add_type.__name__): partial(self.add_item_of_type, add_type)
                })

        ui_utils.build_menu_from_action_list(action_list)

    def set_filter(self, filter_text, search_columns=(lk.col_key,)):
        all_items = self.get_all_items()
        if not filter_text:
            for item in all_items:
                item.setHidden(False)
            return

        # search keys or values
        for item in all_items:
            item.setHidden(True)
        for item in all_items:
            if any(filter_text.lower() in item.text(col).lower() for col in search_columns):
                self.recursive_set_visible(item)

    def recursive_set_visible(self, item):
        item.setHidden(False)
        if item.parent():
            self.recursive_set_visible(item.parent())

    def get_all_items(self, widget=None, widget_list=None):
        if widget is None:
            widget = self.tree_widget.invisibleRootItem()
        if widget_list is None:
            widget_list = list()

        widgets = get_sub_widgets(widget)
        widget_list.extend(widgets)

        for sub_widget in widgets:
            self.get_all_items(sub_widget, widget_list)

        return widget_list

    def action_cut_data_to_clipboard(self):
        self.action_copy_data_to_clipboard()
        self.delete_selected_items()

    def action_copy_data_to_clipboard(self):
        selected_data = self.get_selected_data()
        if not selected_data:
            return

        # Save to clipboard
        str_data = json.dumps(selected_data)
        cb = QtWidgets.QApplication.clipboard()
        cb.setText(str_data, mode=cb.Clipboard)

    def action_paste_data_from_clipboard(self):
        cb = QtWidgets.QApplication.clipboard()
        str_data = cb.text()
        try:
            clipboard_data = json.loads(str_data, object_pairs_hook=OrderedDict)
        except ValueError:
            self.status_message("No JSON serializable data could be read from clipboard")
            return

        self.add_data_to_selected(clipboard_data, merge=True)
        self.data_is_shown.emit(True)
        
    def action_duplicate_selected_items(self):
        for item in self.get_selected_items():  # type: QtWidgets.QTreeWidgetItem
            item_data = self.get_widget_item_values(item)
            item_key = item.text(lk.col_key)
            parent = self.get_parent(item)

            new_item = self.add_data_to_widget(
                data_key=item_key,
                data_value=item_data,
                parent_item=parent,
                merge=not item_supports_children(item),
                key_safety=True
            )

            # insert next to the original
            item_index = parent.indexOfChild(item)
            parent.takeChild(parent.indexOfChild(new_item))
            parent.insertChild(item_index + 1, new_item)

            fix_list_indices(parent)

    def delete_selected_items(self):
        to_delete = self.get_selected_items()
        for item in to_delete:
            if item is self.tree_widget.invisibleRootItem():
                continue

            item_parent = self.get_parent(item)
            item_parent.removeChild(item)
            fix_list_indices(item_parent)

        if self.tree_widget.invisibleRootItem().childCount() == 0:
            # if we've gotten rid of everything do a full clear
            self.action_clear()

    def sort_selected_items(self):
        selected_items = self.get_selected_items(root_on_empty=False)
        common_parent_map = {}
        for selected_item in selected_items:
            item_parent = self.get_parent(selected_item)

            items_of_parent = common_parent_map.get(item_parent, list())
            items_of_parent.append(selected_item)
            common_parent_map[item_parent] = items_of_parent

        for parent, child_items in common_parent_map.items():
            sorted_children = sorted(child_items, key=lambda x: x.text(lk.col_key))
            first_child_index = min(parent.indexOfChild(child) for child in child_items)
            [parent.takeChild(parent.indexOfChild(child)) for child in child_items]

            sorted_children.reverse()
            [parent.insertChild(first_child_index, sorted_child) for sorted_child in sorted_children]

    def select_hierarchy(self):
        for item in self.get_selected_items():
            item_descendants = get_all_item_descendants(item)
            for item in item_descendants:
                item.setSelected(True)

    def action_clear(self):
        self._root_type = None
        self.tree_widget.clear()
        self.data_is_shown.emit(False)

    def set_root_type(self, add_type):
        root_data = lk.root_add_values.get(add_type, add_type())
        self.set_data(root_data)

    def add_item_of_type(self, add_type=str):
        data_to_add = lk.default_add_values.get(add_type, add_type())
        self.add_data_to_selected(data_to_add)

    def add_data_to_selected(self, data_to_add, merge=False):
        for selected_item in self.get_selected_items():
            if not item_supports_children(selected_item):
                continue

            self.add_data_to_widget(data_value=data_to_add, parent_item=selected_item, merge=merge, key_safety=True)
            fix_list_indices(selected_item)

    def get_selected_items(self, root_on_empty=True):
        selected_items = self.tree_widget.selectedItems()
        if not selected_items and root_on_empty:
            selected_items = [self.tree_widget.invisibleRootItem()]
        return selected_items

    def get_selected_data(self):
        """
        Gets data from all selected items

        :return:
        """
        selected_items = self.get_selected_items()
        if len(selected_items) == 1 and selected_items[0] is self.tree_widget.invisibleRootItem():
            return self.get_data()

        # find most common parent type of all selected items
        parent_data_types = []
        for item in selected_items:
            item_parent = self.get_parent(item)

            parent_data_type = get_data_type(item_parent)
            parent_data_types.append(parent_data_type)

        most_common_parent_type = max(set(parent_data_types), key=parent_data_types.count)

        # build list or dict to put selected data in
        output_data = convert_type_string_to_instance(most_common_parent_type)

        for item in selected_items:
            selected_item_data = self.get_widget_item_values(item)
            if most_common_parent_type in lk.dict_type_names:
                output_data[item.text(lk.col_key)] = selected_item_data
            else:
                output_data.append(selected_item_data)

        return output_data

    def update_header_display(self):
        tree_header = self.tree_widget.header()  # type: QtWidgets.QHeaderView
        tree_header.setStretchLastSection(False)
        tree_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tree_widget.resizeColumnToContents(lk.col_key)

    def get_widget_item_values(self, widget_item):
        data_type = get_data_type(widget_item)
        data_value = get_data_as_correct_type(widget_item)

        if data_type in lk.dict_type_names:
            for sub_widget in get_sub_widgets(widget_item):
                data_value[sub_widget.text(lk.col_key)] = self.get_widget_item_values(sub_widget)

        elif data_type in lk.list_type_names:
            for sub_widget in get_sub_widgets(widget_item):
                data_value.append(self.get_widget_item_values(sub_widget))

        return data_value

    def add_data_to_widget(self, data_key="", data_value=None, parent_item=None, merge=False, key_safety=False):
        data_type_name = type(data_value).__name__
        return_item = None

        if key_safety:
            parent_type = get_data_type(parent_item)

            if parent_type in lk.dict_type_names:
                data_key = get_unique_dict_key(parent_item, key_name=data_key)

            if parent_type in lk.list_type_names:
                data_key = "[{}]".format(parent_item.childCount())

        if isinstance(data_value, lk.dict_types):
            if not merge:
                parent_item = QtWidgets.QTreeWidgetItem(
                    parent_item,
                    [data_key, "-------- {} items --------".format(len(data_value)), data_type_name],
                )
                parent_item.setFlags(parent_item.flags() | QtCore.Qt.ItemIsEditable)
                return_item = parent_item

            for k, v in data_value.items():
                self.add_data_to_widget(
                    data_key=k,
                    data_value=v,
                    parent_item=parent_item,
                    merge=False,
                    key_safety=key_safety,
                )

        elif isinstance(data_value, lk.list_types):
            if not merge:
                parent_item = QtWidgets.QTreeWidgetItem(
                    parent_item,
                    [data_key, "-------- {} items --------".format(len(data_value)), data_type_name],
                )
                parent_item.setFlags(parent_item.flags() | QtCore.Qt.ItemIsEditable)
                return_item = parent_item

            for i, v in enumerate(data_value):
                self.add_data_to_widget(
                    data_key="[{}]".format(i),
                    data_value=v,
                    parent_item=parent_item,
                    merge=False,
                    key_safety=key_safety,
                )
        else:
            widget_item = QtWidgets.QTreeWidgetItem(parent_item, [data_key, str(data_value), data_type_name])
            # widget_item.setData(lk.col_value, QtCore.Qt.DisplayRole, data_value)
            widget_item.setFlags(widget_item.flags() | QtCore.Qt.ItemIsEditable)
            return_item = widget_item

        return return_item

    def action_move_selected_items_up(self):
        self.reorder_selected_items(direction=-1)

    def action_move_selected_items_down(self):
        self.reorder_selected_items(direction=1)

    def reorder_selected_items(self, direction=1):
        """
        This thing is a mess

        :param direction:
        :return:
        """
        resolve_parent_list_items = []
        selected_items = self.get_selected_items(root_on_empty=False)
        if direction == 1:
            selected_items.reverse()

        for i, item in enumerate(selected_items):  # Find new indices for selected items
            parent_item = self.get_parent(item)

            was_expanded = item.isExpanded()

            current_index = parent_item.indexOfChild(item)
            new_index = current_index + direction

            if new_index < 0:
                new_index = 0
            if new_index > parent_item.childCount() - 1:
                new_index = parent_item.childCount() - 1

            parent_item.takeChild(current_index)
            parent_item.insertChild(new_index, item)  # ReOrder

            resolve_parent_list_items.append(parent_item)
            item.treeWidget().setCurrentItem(item)  # Set highlight focus
            item.setExpanded(was_expanded)
            parent_item.setExpanded(True)

        if direction == 1:
            selected_items.reverse()  # reverse back

        for item in selected_items:  # ReSelect
            item.setSelected(True)

        for resolved_parent in resolve_parent_list_items:
            fix_list_indices(resolved_parent)

    def get_parent(self, item):
        item_parent = item.parent()
        if item_parent is None:
            item_parent = self.tree_widget.invisibleRootItem()
        return item_parent


def get_sub_widgets(tree_widget_item):
    return [tree_widget_item.child(i) for i in range(tree_widget_item.childCount())]


def get_all_item_descendants(tree_widget_item, item_list=None):
    if item_list is None:
        item_list = []

    item_children = get_sub_widgets(tree_widget_item)

    # This list is recursively extended. So mutability comes into play here.
    item_list.extend(item_children)

    for item_child in item_children:
        get_all_item_descendants(item_child, item_list)

    return item_list


def get_data_as_correct_type(tree_widget_item):
    data_value = tree_widget_item.text(lk.col_value)
    data_type = tree_widget_item.text(lk.col_type)

    if data_type == "NoneType":
        return None

    if data_type in ("int", "float"):
        try:  # This is kinda dumb, but check if the values in the fields are valid
            if data_type == "int":
                int(data_value)
            if data_type == "float":
                float(data_value)
        except ValueError:
            data_value = "".join([s for s in str(data_value) if not s.isalpha()])  # remove letters

    if data_type == "bool":
        # I let you be really sloppy with typing here
        if data_value.lower().startswith("t"):
            return True
        elif data_value.lower() in ["1", "y"]:
            return True
        elif data_value.lower().startswith("f"):
            return False
        else:
            return False

    if data_type in lk.supports_children_type_names:
        eval_statement = "{}()".format(data_type)
    else:
        eval_statement = "{}('{}')".format(data_type, data_value)

    data_of_correct_type = eval(eval_statement)

    return data_of_correct_type


def convert_type_string_to_instance(data_type):
    eval_statement = "{}()".format(data_type)
    data_of_correct_type = eval(eval_statement)
    return data_of_correct_type


def get_data_type(tree_widget_item):
    return tree_widget_item.text(lk.col_type)


def item_supports_children(item):
    return get_data_type(item) in lk.supports_children_type_names


def get_unique_dict_key(parent_item, key_name=""):
    """
    Creates a unique key to use in a dictionary
    +1 to end of name if key already exists

    :param parent_item:
    :param key_name:
    :return:
    """
    if key_name == "":
        key_name = "KEY_0"

    existing_keys = [i.text(lk.col_key) for i in get_sub_widgets(parent_item)]
    if key_name and key_name not in existing_keys:
        return key_name

    if not key_name[-1].isdigit():
        key_name += "_0"

    while key_name in existing_keys:
        old_index = re.findall(r'\d+', key_name)[-1]
        key_name_without_last_number = key_name[:-len(str(old_index))]
        key_name = key_name_without_last_number + str(int(old_index) + 1)

    return key_name


def fix_list_indices(parent_item):
    """
    Sets the list indices on a list tree widget item

    :param parent_item:
    :return:
    """
    if get_data_type(parent_item) in lk.supports_children_type_names:
        parent_item.setText(lk.col_value, "-------- {} items --------".format(parent_item.childCount()))

    if get_data_type(parent_item) in lk.list_type_names:
        children = get_sub_widgets(parent_item)
        for i, child_item in enumerate(children):
            child_item.setData(lk.col_key, QtCore.Qt.DisplayRole, "[{}]".format(i))


def test_data_tree():
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow()

    tree = DataTreeWidget()

    win.setCentralWidget(tree)
    win.show()
    win.resize(1000, 1000)

    example_json_path = os.path.join(os.path.dirname(__file__), "resources", "example_json_data.json")
    with open(example_json_path, "r") as fp:
        test_data = json.load(fp, object_pairs_hook=OrderedDict)

    tree.set_data(test_data)
    ui_data = tree.get_data()

    # round trip through the UI, should be identical
    print("TEST_DATA", test_data)
    print("UI_DATA  ", ui_data)
    assert (ui_data == test_data)

    sys.exit(app.exec_())


if __name__ == '__main__':
    test_data_tree()
