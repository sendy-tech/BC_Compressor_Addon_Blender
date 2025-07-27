import bpy
import os

class BC_PT_CompressionPanel(bpy.types.Panel):
    bl_label = "BC Сжатие текстур"
    bl_idname = "BC_PT_compression_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Texture Tools'

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.active_material is not None

    def draw(self, context):
        layout = self.layout
        props = context.scene.bc_compression_props

        layout.label(text="Текстуры активного объекта:")
        box = layout.box()

        if len(props.texture_list) == 0:
            box.label(text="Нет текстур")
        else:
            for item in props.texture_list:
                row = box.row()
                row.prop(item, "use", text=item.name)

        layout.separator()
        layout.prop(props, "auto_format")

        row = layout.row()
        row.enabled = not props.auto_format
        row.prop(props, "compression_format")

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
                    base_path = bpy.path.abspath(image_nodes[0].image.filepath)
                    base_dir = os.path.dirname(base_path)
                    output_dir = os.path.join(base_dir, "Compressed_DDS")
                elif bpy.data.filepath:
                    base_dir = os.path.dirname(bpy.data.filepath)
                    output_dir = os.path.join(base_dir, "Compressed_DDS")

        if output_dir and os.path.exists(output_dir):
            op = layout.operator("wm.path_open", text="Открыть папку вывода", icon='FILE_FOLDER')
            op.filepath = output_dir


def update_texture_list(scene):
    props = scene.bc_compression_props
    obj = bpy.context.object

    if not props or not obj:
        return

    current_obj_name = obj.name
    if props.last_obj_name == current_obj_name:
        return

    props.last_obj_name = current_obj_name

    new_textures = []
    if obj.active_material and obj.active_material.use_nodes:
        mat = obj.active_material
        image_nodes = [n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE']
        for node in image_nodes:
            image = node.image
            if image and image.filepath:
                new_textures.append((os.path.basename(image.filepath), bpy.path.abspath(image.filepath_raw)))

    old_set = {(item.name, item.filepath) for item in props.texture_list}
    new_set = set(new_textures)

    if old_set == new_set:
        return 

    props.texture_list.clear()
    for name, filepath in new_textures:
        item = props.texture_list.add()
        item.name = name
        item.filepath = filepath
        item.use = True


def register():
    bpy.utils.register_class(BC_PT_CompressionPanel)
    bpy.app.handlers.depsgraph_update_post.append(update_texture_list)


def unregister():
    bpy.utils.unregister_class(BC_PT_CompressionPanel)
    if update_texture_list in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(update_texture_list)
