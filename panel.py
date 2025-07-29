import bpy
import os

# Глобальное имя последнего объекта для таймера
_last_checked_obj = None


class BC_PT_CompressionPanel(bpy.types.Panel):
    bl_label = "BC Сжатие текстур"
    bl_idname = "BC_PT_compression_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Texture Tools'

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        props = context.scene.bc_compression_props

        layout.prop(props, "auto_format")

        row = layout.row()
        row.enabled = not props.auto_format
        row.prop(props, "compression_format")

        layout.label(text="Текстуры для сжатия:")
        box = layout.box()
        if not props.texture_list:
            box.label(text="Нет текстур")
        else:
            for item in props.texture_list:
                row = box.row()
                row.prop(item, "use", text=item.name)

        show_quality = (not props.auto_format) and props.compression_format in {"BC7_UNORM", "BC6H_UF16"}
        row = layout.row()
        row.enabled = show_quality
        row.prop(props, "compression_quality")

        layout.prop(props, "generate_mipmaps")
        layout.prop(props, "output_path")
        layout.operator("bc.compress_textures", icon='FILE_TICK')

        output_dir = bpy.path.abspath(props.output_path.strip()) if props.output_path.strip() else ""
        if not output_dir or not os.path.exists(output_dir):
            obj = context.object
            if obj and obj.active_material:
                mats = obj.active_material
                image_nodes = [n for n in mats.node_tree.nodes if n.type == 'TEX_IMAGE']
                if image_nodes and image_nodes[0].image and image_nodes[0].image.filepath:
                    base_path = bpy.path.abspath(image_nodes[0].image.filepath_raw)
                    base_dir = os.path.dirname(base_path)
                    output_dir = os.path.join(base_dir, "Compressed_DDS")
                elif bpy.data.filepath:
                    base_dir = os.path.dirname(bpy.data.filepath)
                    output_dir = os.path.join(base_dir, "Compressed_DDS")

        if output_dir and os.path.exists(output_dir):
            op = layout.operator("wm.path_open", text="Открыть папку вывода", icon='FILE_FOLDER')
            op.filepath = output_dir

        layout.operator("bc.batch_select_textures", icon='FILEBROWSER', text="Пакетный выбор текстур")


class BC_OT_RefreshTextures(bpy.types.Operator):
    bl_idname = "bc.refresh_textures"
    bl_label = "Обновить список текстур"
    bl_description = "Сканировать текстуры активного объекта"

    def execute(self, context):
        obj = context.object
        if obj:
            update_texture_list(context.scene, obj)
            self.report({'INFO'}, "Список текстур обновлён")
        else:
            self.report({'WARNING'}, "Нет активного объекта")
        return {'FINISHED'}


def update_texture_list(scene, obj):
    props = scene.bc_compression_props

    if not props or props.use_batch_selection or not obj:
        return

    if props.last_obj_name == obj.name:
        return

    props.last_obj_name = obj.name

    new_textures = []
    if obj.active_material and obj.active_material.use_nodes:
        mat = obj.active_material
        image_nodes = [n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE']
        for node in image_nodes:
            image = node.image
            if image and image.filepath:
                path_abs = bpy.path.abspath(image.filepath_raw)
                name = os.path.basename(path_abs)
                new_textures.append((name, path_abs))

    old_set = {(item.name, item.filepath) for item in props.texture_list}
    new_set = set(new_textures)

    if old_set == new_set:
        return

    old_uses = {(item.name, item.filepath): item.use for item in props.texture_list}

    props.texture_list.clear()
    for name, filepath in new_textures:
        item = props.texture_list.add()
        item.name = name
        item.filepath = filepath
        item.use = old_uses.get((name, filepath), True)


def monitor_active_object():
    global _last_checked_obj

    scene = bpy.context.scene
    if not scene:
        return 0.1

    props = scene.bc_compression_props
    if not props or props.use_batch_selection:
        return 0.1

    obj = bpy.context.view_layer.objects.active
    if obj and obj != _last_checked_obj:
        update_texture_list(scene, obj)
        _last_checked_obj = obj

    return 0.1


def register():
    bpy.utils.register_class(BC_PT_CompressionPanel)
    bpy.utils.register_class(BC_OT_RefreshTextures)

    bpy.app.timers.register(monitor_active_object, persistent=True)


def unregister():
    bpy.utils.unregister_class(BC_PT_CompressionPanel)
    bpy.utils.unregister_class(BC_OT_RefreshTextures)
