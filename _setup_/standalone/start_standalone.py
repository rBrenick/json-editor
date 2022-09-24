import os
import sys

import json_editor
win = json_editor.main()

if len(sys.argv) > 1:
    json_path = os.path.abspath(sys.argv[1])
    if os.path.exists(json_path):
        win.ui.load_json(json_path)
