import collections
import json
import os
import sys

active_dcc_is_maya = "maya" in os.path.basename(sys.executable)

if active_dcc_is_maya:
    from . import json_editor_dcc_maya as dcc_module

    dcc = dcc_module.JsonEditorMaya()
else:
    from . import json_editor_dcc_core as dcc_module

    dcc = dcc_module.JsonEditorCoreInterface()


def load_json(json_path):
    if not os.path.exists(json_path):
        return

    with open(json_path, "r") as fp:
        json_data = json.load(fp, object_pairs_hook=collections.OrderedDict)
    return json_data


def get_json_indent_level(json_path):
    with open(json_path, "r") as fp:
        first_couple_of_characters = fp.readline(8)

    if len(first_couple_of_characters) > 2:
        return None

    with open(json_path, "r") as fp:
        fp.readline()  # read first line so we can get to the second one

        next_line = fp.readline()
        indent_number = len(next_line) - len(next_line.lstrip())
    return indent_number


def save_json(json_data, json_path, indent=2):
    with open(json_path, "w+") as fp:
        json.dump(json_data, fp, indent=indent)
