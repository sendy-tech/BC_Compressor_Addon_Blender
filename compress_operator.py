import bpy
import os
import subprocess
from bpy.types import Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, CollectionProperty


class FileConflictItem(PropertyGroup):
    name: StringProperty()
    filepath: StringProperty()
    overwrite: BoolProperty(default=True)


class BC_OT_ConfirmOverwrite(Operator):
    bl_idname = "bc.confirm_overwrite"
    bl_label = "Конфликты файлов"
    bl_description = "Выберите, какие файлы перезаписать"

    conflicts: CollectionProperty(type=FileConflictItem)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Следующие файлы уже существуют. Перезаписать?")
        box = layout.box()
        for item in context.window_manager.bc_conflicts:
            row = box.row()
            row.prop(item, "overwrite", text=item.name)

    def execute(self, context):
        return bpy.ops.bc.compress_textures('EXEC_DEFAULT')


class BC_OT_CompressTextures(Operator):
    bl_idname = "bc.compress_textures"
    bl_label = "Сжать текстуры"
    bl_description = "Сжимает выбранные текстуры активного объекта в .DDS с помощью texconv.exe"

    def invoke(self, context, event):
        props = context.scene.bc_compression_props
        obj = context.object

        if not obj or not obj.active_material:
            self.report({'WARNING'}, "Нет активного объекта или материала")
            return {'CANCELLED'}

        if not props.texture_list:
            mat = obj.active_material
            image_nodes = [n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE']
            for node in image_nodes:
                image = node.image
                if not image or not image.filepath:
                    continue
                item = props.texture_list.add()
                item.name = os.path.basename(image.filepath)
                item.filepath = bpy.path.abspath(image.filepath_raw)
                item.use = True

        selected = [item for item in props.texture_list if item.use]
        if not selected:
            self.report({'ERROR'}, "Не выбрано ни одной текстуры для сжатия")
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(props.output_path.strip()) if props.output_path.strip() else os.path.join(os.path.dirname(bpy.data.filepath), "DDS_Output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        wm = context.window_manager
        if hasattr(wm, "bc_conflicts"):
            wm.bc_conflicts.clear()

        for item in selected:
            dds_name = os.path.splitext(item.name)[0] + ".DDS"
            output_file = os.path.join(output_dir, dds_name)
            if os.path.exists(output_file):
                conflict = wm.bc_conflicts.add()
                conflict.name = dds_name
                conflict.filepath = output_file
                conflict.overwrite = True

        if len(wm.bc_conflicts) > 0:
            return bpy.ops.bc.confirm_overwrite('INVOKE_DEFAULT')
        else:
            return self.execute(context)

    def execute(self, context):
        props = context.scene.bc_compression_props
        obj = context.object
        if not obj or not obj.active_material:
            self.report({'WARNING'}, "Нет активного объекта или материала")
            return {'CANCELLED'}

        mat = obj.active_material
        image_nodes = [n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE']

        addon_dir = os.path.dirname(os.path.abspath(__file__))
        texconv_path = os.path.join(addon_dir, "bin", "texconv.exe")

        if not os.path.exists(texconv_path):
            self.report({'ERROR'}, "texconv.exe не найден")
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(props.output_path.strip()) if props.output_path.strip() else os.path.join(os.path.dirname(bpy.data.filepath), "DDS_Output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        selected_textures = {item.filepath for item in props.texture_list if item.use}

        wm = context.window_manager
        conflict_overwrite = {}
        if hasattr(wm, "bc_conflicts"):
            conflict_overwrite = {item.name: item.overwrite for item in wm.bc_conflicts}

        for node in image_nodes:
            image = node.image
            if not image or not image.filepath:
                continue

            input_path = bpy.path.abspath(image.filepath_raw)
            if input_path not in selected_textures:
                continue

            base_name = os.path.splitext(os.path.basename(image.filepath))[0]
            dds_name = base_name + ".DDS"
            output_file = os.path.join(output_dir, dds_name)

            if os.path.exists(output_file):
                if dds_name in conflict_overwrite and not conflict_overwrite[dds_name]:
                    self.report({'INFO'}, f"Пропущено: {dds_name} (перезапись не разрешена)")
                    continue
                try:
                    os.remove(output_file)
                except Exception:
                    self.report({'WARNING'}, f"Не удалось удалить: {output_file}")
                    continue

            format_to_use = props.compression_format
            if props.auto_format:
                format_to_use = self.get_format_from_connection(mat, node)

            args = [
                texconv_path,
                "-f", format_to_use,
                "-o", output_dir
            ]

            if not props.auto_format and format_to_use in {"BC7_UNORM", "BC6H_UF16"}:
                args += ["-bc", props.compression_quality]
            elif props.auto_format and format_to_use == "BC7_UNORM":
                args += ["-bc", "q"]

            if not props.generate_mipmaps:
                args += ["-m", "1"]

            args.append(input_path)

            try:
                subprocess.run(args, check=True)
                self.report({'INFO'}, f"Сжато: {dds_name}")
            except subprocess.CalledProcessError as e:
                self.report({'ERROR'}, f"Ошибка при сжатии {image.name}: {e}")

        self.report({'INFO'}, "Сжатие завершено")
        return {'FINISHED'}

    def get_format_from_connection(self, material, tex_node):
        def trace_output(node, depth=0):
            if depth > 10:
                return None
            for link in material.node_tree.links:
                if link.from_node == node:
                    to_node = link.to_node
                    to_socket = link.to_socket
                    socket_name = to_socket.name.lower()
                    if "base color" in socket_name or "albedo" in socket_name:
                        return "BC7_UNORM"
                    elif "normal" in socket_name or isinstance(to_node, bpy.types.ShaderNodeNormalMap):
                        return "BC5_UNORM"
                    elif socket_name in ["roughness", "metallic", "ao", "specular", "height", "displacement"]:
                        return "BC1_UNORM"
                    elif "emission" in socket_name or "emissive" in socket_name:
                        return "BC6H_UF16"
                    result = trace_output(to_node, depth + 1)
                    if result:
                        return result
            return None

        result = trace_output(tex_node)
        return result if result else "BC7_UNORM"


def register():
    bpy.utils.register_class(FileConflictItem)
    bpy.utils.register_class(BC_OT_ConfirmOverwrite)
    bpy.utils.register_class(BC_OT_CompressTextures)


def unregister():
    bpy.utils.unregister_class(BC_OT_CompressTextures)
    bpy.utils.unregister_class(BC_OT_ConfirmOverwrite)
    bpy.utils.unregister_class(FileConflictItem)
