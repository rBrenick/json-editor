import os
import sys

arg_json_path = None
if len(sys.argv) > 1:
    json_path = os.path.abspath(sys.argv[1])
    if os.path.exists(json_path):
        arg_json_path = json_path

import json_editor
win = json_editor.main(file_path=arg_json_path)
