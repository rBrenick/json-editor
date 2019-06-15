# ---------------------------------- common startup site handling -----------------------------------
import os
import sys
import site
import inspect

def common_startup():
    # Add site-packages to sys.path
    package_dir = os.path.dirname(os.path.dirname(os.path.dirname(inspect.getfile(inspect.currentframe())))) # my god
    
    if package_dir not in sys.path:
        site.addsitedir(package_dir)

common_startup()

# ---------------------------------- !common startup site handling -----------------------------------

try:
    import json_editor.json_editor_dcc_setup
    json_editor.json_editor_dcc_setup.startup()
except StandardError as e:
    print(e)
    
    


