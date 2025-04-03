import importlib
import sys
import os
from itertools import groupby

from bms_blender_plugin.ext.blender_dds_addon.directx.texconv import unload_texconv

bl_info = {
    "name": "Falcon BMS Plugin",
    "author": "Benchmark Sims",
    "version": (0, 0, 20250403),
    "blender": (3, 6, 0),
    "location": "File > Export",
    "description": "Export as Falcon BMS BML",
    "warning": "",
    "doc_url": "https://github.com/BenchmarkSims/bms-blender-plugin",
    "tracker_url": "https://github.com/BenchmarkSims/bms-blender-plugin/issues",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

# get folder name
__folder_name__ = __name__
__dict__ = {}
addon_dir = os.path.dirname(__file__)

# get all .py file paths
py_paths = [
    os.path.join(root, f)
    for root, dirs, files in os.walk(addon_dir)
    for f in files
    if f.endswith(".py") and f != "__init__.py" and f != "test.py"
]

for path in py_paths:
    name = os.path.basename(path)[:-3]
    correct_path = path.replace("\\", "/")
    # split path with folder name
    dir_list = [
        list(g)
        for k, g in groupby(correct_path.split("/"), lambda x: x == __folder_name__)
        if not k
    ]
    # combine path and make dict like this: 'name:folder.name'
    if "preset" not in dir_list[-1]:
        r_name_raw = __folder_name__ + "." + ".".join(dir_list[-1])
        __dict__[name] = r_name_raw[:-3]

# auto reload
for name in __dict__.values():
    if name in sys.modules:
        importlib.reload(sys.modules[name])
    else:
        globals()[name] = importlib.import_module(name)
        setattr(globals()[name], "modules", __dict__)


def register():
    for module_name in __dict__.values():
        if module_name in sys.modules and hasattr(sys.modules[module_name], "register"):
            try:
                sys.modules[module_name].register()
            except ValueError:  # open template file may cause this problem
                pass


def unregister():
    unload_texconv()
    for module_name in __dict__.values():
        if module_name in sys.modules and hasattr(sys.modules[module_name], "unregister"):
            sys.modules[module_name].unregister()


if __name__ == "__main__":
    register()
