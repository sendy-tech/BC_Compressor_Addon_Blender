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
from . import batch_select_operator
from bpy.props import CollectionProperty, BoolProperty
from .compress_operator import FileConflictItem


def register():
    properties.register()
    compress_operator.register()
    panel.register()
    batch_select_operator.register() 

    bpy.types.WindowManager.bc_conflicts = CollectionProperty(type=FileConflictItem)
    bpy.types.WindowManager.bc_skip_conflict_dialog = BoolProperty(default=False)

    bpy.types.Scene.use_batch_selection = bpy.props.BoolProperty(
        name="Пакетная обработка активна",
        default=False
    )

    addon_dir = os.path.dirname(os.path.abspath(__file__))
    if not compress_downloader.download_and_extract_texconv(addon_dir):
        print("[BC Compressor] texconv.exe не удалось загрузить. Проверьте подключение к интернету.")

def unregister():
    panel.unregister()
    compress_operator.unregister()
    properties.unregister()
    batch_select_operator.unregister()

    del bpy.types.WindowManager.bc_conflicts
    del bpy.types.WindowManager.bc_skip_conflict_dialog

    if hasattr(bpy.types.Scene, "use_batch_selection"):
        del bpy.types.Scene.use_batch_selection
