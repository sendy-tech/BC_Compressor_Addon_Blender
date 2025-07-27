bl_info = {
    "name": "BC Texture Compressor",
    "author": "sEndY",
    "version": (1, 0),
    "blender": (4, 5, 0),
    "location": "3D View > Sidebar > BC Compress",
    "description": "Сжимает активные текстуры объекта в DDS с помощью texconv.exe",
    "category": "Material",
}

import bpy
import os
from . import compress_operator
from . import properties
from . import panel
from . import compress_downloader


def register():
    properties.register()
    compress_operator.register()
    panel.register()

    bpy.types.WindowManager.bc_conflicts = bpy.props.CollectionProperty(type=compress_operator.FileConflictItem)

    addon_dir = os.path.dirname(os.path.abspath(__file__))
    if not compress_downloader.download_and_extract_texconv(addon_dir):
        print("[BC Compressor] texconv.exe не удалось загрузить. Проверьте подключение к интернету.")


def unregister():
    panel.unregister()
    compress_operator.unregister()
    properties.unregister()

    if hasattr(bpy.types.WindowManager, "bc_conflicts"):
        del bpy.types.WindowManager.bc_conflicts
