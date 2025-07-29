import bpy
import os


class BC_OT_BatchSelectTextures(bpy.types.Operator):
    bl_idname = "bc.batch_select_textures"
    bl_label = "Пакетный выбор текстур"
    bl_description = "Выбрать несколько текстур вручную для пакетной обработки"

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        scene = context.scene
        props = scene.bc_compression_props

        context.view_layer.objects.active = None
        props.last_obj_name = ""

        props.texture_list.clear()

        selected_paths = [os.path.join(self.directory, f.name) for f in self.files]
        textures = []

        for path in selected_paths:
            if os.path.isfile(path):
                name = os.path.basename(path)
                item = props.texture_list.add()
                item.name = name
                item.filepath = path
                item.use = True

        scene.use_batch_selection = True

        self.report({'INFO'}, f"Выбрано текстур: {len(props.texture_list)}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(BC_OT_BatchSelectTextures)


def unregister():
    bpy.utils.unregister_class(BC_OT_BatchSelectTextures)
