# zelda64-import-blender
# Import models from Zelda64 files into Blender
# Copyright (C) 2013 SoulofDeity
# Copyright (C) 2020 Dragorn421
# Copyright (C) 2023 StardustSauce
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>

bl_info = {
    "name":        "Zelda64 Importer",
    "description": "Import Zelda64 for Blender 2.8+",
    "version":     (3, 0),
    "author":      "SoulofDeity",
    "blender":     (2, 80, 0),
    "location":    "File > Import-Export",
    "warning":     "",
    "wiki_url":    "https://github.com/StardustSauce/zelda64-import-blender",
    "tracker_url": "https://github.com/StardustSauce/zelda64-import-blender",
    "support":     "COMMUNITY",
    "category":    "Import-Export"
}

"""Anim stuff: RodLima http://www.facebook.com/rod.lima.96?ref=tn_tnmn"""

#import bpy, os, struct, time
#import mathutils
#import re

#from bpy import ops
#from bpy.props import *
#from bpy_extras.image_utils import load_image
#from bpy_extras.io_utils import ExportHelper, ImportHelper
#from math import *
#from mathutils import *
#from struct import pack, unpack_from

#from mathutils import Vector, Euler, Matrix

import bpy
from z64import import (
    IMPORT_SCENE_OT_zobj,
    ZOBJ_PT_import_config,
    ZOBJ_PT_import_texture,
    ZOBJ_PT_import_animation
)


def menu_func_import(self, context):
    self.layout.operator(
        ImportZ64.bl_idname,
        text="Zelda64 (.zobj;.zroom;.zmap)"
    )

classes = (
    IMPORT_SCENE_OT_zobj,
    ZOBJ_PT_import_config,
    ZOBJ_PT_import_texture,
    ZOBJ_PT_import_animation
)

def register():
    bpy.utils.register_module(__name__)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
