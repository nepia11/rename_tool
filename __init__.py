import bpy
import traceback
import pprint

bl_info = {
    "name": "Rename Tool",
    "author": "nepia",
    "version": (0, 1, 0),
    "blender": (2, 93, 0),
    "location": "view3d > ui > RN",
    "description": "非ascii文字を一括置換",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Tools",
}


def ShowMessageBox(message="", title="Message Box", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def get_non_ascii_items():
    bdata = bpy.data
    attr = [getattr(bdata, attr_name) for attr_name in dir(bdata)]

    items: list[tuple[str, any]] = []

    for a in attr:
        try:
            items.extend(a.items())  # [(name_str, data_refs),,,]
        except:
            pass

    for v in items:
        item = v[1]

        if isinstance(item, bpy.types.Object):
            item: bpy.types.Object
            items.extend(item.modifiers.items())
            items.extend(item.constraints.items())
            items.extend(item.vertex_groups.items())

        if isinstance(item, bpy.types.Mesh):
            item: bpy.types.Mesh
            if not item.shape_keys is None:
                items.extend(item.shape_keys.key_blocks.items())
            items.extend(item.uv_layers.items())
            items.extend(item.vertex_colors.items())

    # str.isascii()は文字列がascii文字のみの場合Trueを返す
    non_ascii_items = [item for item in items if not item[0].isascii()]
    return non_ascii_items


def extract_word_set(non_ascii_items):
    words = []
    for items in non_ascii_items:
        name = items[0]
        sp_name = name.split(".")
        for n in sp_name:
            if not n.isascii():
                words.append(n)

    word_set = set(words)
    return word_set


def replace_item_names(replace_words):
    # replace_words = [(old,new),,,]
    non_ascii_items = get_non_ascii_items()
    for item in non_ascii_items:
        for word in replace_words:
            if word[0] in item[0]:
                new_name = item[1].name.replace(word[0], word[1])
                item[1].name = new_name


# OPS
class RN_OT_CheckItems(bpy.types.Operator):
    bl_idname = "util.check_item_name"
    bl_label = "check item name"
    bl_description = (
        "Extract words and phrases that contain non-ascii characters in item names."
    )
    bl_options = {"MACRO"}

    def execute(self, context):
        non_ascii_items = get_non_ascii_items()
        word_set = extract_word_set(non_ascii_items)

        rn_list = context.scene.rn_list
        rn_list.clear()
        for word in word_set:
            key = rn_list.add()
            key.old = word
            key.new = word

        msg = str(word_set) + pprint.pformat(non_ascii_items)
        ShowMessageBox(message=msg)
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class RN_OT_RenameItems(bpy.types.Operator):
    bl_idname = "util.rename_item"
    bl_label = "batch rename item"
    bl_description = "Replace item names that contain extracted words and phrases."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        rn_list = context.scene.rn_list
        rename_list = [(v.old, v.new) for v in rn_list]
        non_ascii_items = get_non_ascii_items()
        replace_item_names(rename_list)
        bpy.ops.util.check_item_name()

        return {"FINISHED"}


# PROP
class RNProp(bpy.types.PropertyGroup):

    old: bpy.props.StringProperty(name="old", default="")
    new: bpy.props.StringProperty(name="new", default="")


# UI
class RN_PT_Panel(bpy.types.Panel):
    bl_label = "rename panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RN"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.operator(RN_OT_CheckItems.bl_idname)
        props = context.scene.rn_list

        grid = layout.grid_flow(row_major=True, columns=2)
        for p in props:
            grid.prop(p, "old")
            grid.prop(p, "new")

        layout.label(text="debug")
        layout.operator(RN_OT_RenameItems.bl_idname)


classes = [
    RN_OT_CheckItems,
    RN_OT_RenameItems,
    RN_PT_Panel,
    RNProp,
]


def register():
    for c in classes:
        try:
            bpy.utils.register_class(c)
        except:
            traceback.print_exc()

    bpy.types.Scene.rn_list = bpy.props.CollectionProperty(type=RNProp)


def unregister():
    for c in classes:
        try:
            bpy.utils.unregister_class(c)
        except:
            traceback.print_exc()

    del bpy.types.Scene.rn_list


if __name__ == "__main__":
    register()
