import bpy
from bpy.props import (
    EnumProperty,
    StringProperty,
    PointerProperty,
    BoolProperty,
    CollectionProperty,
)


class BC_TextureItem(bpy.types.PropertyGroup):
    name: StringProperty()
    filepath: StringProperty()
    use: BoolProperty(name="Выбирать", default=True)


class BC_CompressionProperties(bpy.types.PropertyGroup):
    compression_format: EnumProperty(
        name="Формат сжатия",
        items=[
            ('BC1_UNORM', "BC1 (без альфы)", ""),
            ('BC3_UNORM', "BC3 (с альфой)", ""),
            ('BC5_UNORM', "BC5 (Normals)", ""),
            ('BC6H_UF16', "BC6H (HDRI)", ""),
            ('BC7_UNORM', "BC7", "")
        ],
        default='BC7_UNORM'
    )

    compression_quality: EnumProperty(
        name="Качество",
        items=[
            ('q', "Быстрое (q)", "Минимальное качество, максимальная скорость"),
            ('x', "Высокое (x)", "Оптимальное качество, стандартный режим"),
            ('xd', "С dither (xd)", "Высокое качество + дизеринг"),
            ('xdu', "С dither + uniform (xdu)", "Макс. качество + дизеринг + равномерный вес")
        ],
        default='x'
    )

    auto_format: BoolProperty(
        name="Автоматически выбирать формат",
        description="Определять формат сжатия на основе типа текстуры",
        default=False
    )

    generate_mipmaps: BoolProperty(
        name="Генерировать Mipmaps",
        default=True
    )

    output_path: StringProperty(
        name="Папка вывода",
        description="Куда сохранять сжатые DDS",
        subtype='DIR_PATH',
        default=""
    )

    texture_list: CollectionProperty(type=BC_TextureItem)
    last_obj_name: StringProperty(default="")

    use_batch_selection: BoolProperty(default=False)


def register():
    bpy.utils.register_class(BC_TextureItem)
    bpy.utils.register_class(BC_CompressionProperties)
    bpy.types.Scene.bc_compression_props = PointerProperty(type=BC_CompressionProperties)


def unregister():
    if hasattr(bpy.types.Scene, "bc_compression_props"):
        del bpy.types.Scene.bc_compression_props
    bpy.utils.unregister_class(BC_CompressionProperties)
    bpy.utils.unregister_class(BC_TextureItem)
