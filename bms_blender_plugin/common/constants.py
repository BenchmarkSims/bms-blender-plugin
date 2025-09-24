"""Acts as a header for constants, etc

Purpose:
- Avoid literals... :)

Notes:

"""

# Maximum allowable (inclusive) identifier values for DOFs and Switches.
# Previously 255. Used in __init__.py (object intproperty limits) and export_parent_dat.py (cap highest number)
BMS_MAX_SWITCH_NUMBER: int = 2048
BMS_MAX_SWITCH_BRANCH: int = 2048  # Branch uses same bound currently
BMS_MAX_DOF_NUMBER: int = 2048

# Not recommended but available if someone were to import with wildcard eg. from bms_blender_plugin.common.constants import *
# If adding above, also add them here if they should be available as if "public"
__all__ = [
    "BMS_MAX_SWITCH_NUMBER",
    "BMS_MAX_SWITCH_BRANCH",
    "BMS_MAX_DOF_NUMBER",
]
