bl_info = {
    "name":         "Apply modifiers for object with shape keys",
    "author":       "Przemysław Bągard, Fin O'Riordan",
    "blender":      (2,80,0),
    "version":      (0,1,1),
    "location":     "3D View",
    "description":  "Allows to apply modifiers for objects with Shape Keys.",
    "category":     "Edit"
}

import bpy, math
from bpy.props import *

# Algorithm:
# - Duplicate active object as many times as the number of shape keys
# - For each copy remove all shape keys except one
# - Removing last shape does not change geometry data of object
# - Apply modifier for each copy
# - Join objects as shapes and restore shape keys names
# - Delete all duplicated object except one
# - Delete old object
# - Restore name of object and object data

def find_collection(context, item):
    collections = item.users_collection
    if len(collections) > 0:
        return collections[0]
    return context.scene.collection

def make_collection(collection_name, parent_collection):
    if collection_name in bpy.data.collections:
        return bpy.data.collections[collection_name]
    else:
        new_collection = bpy.data.collections.new(collection_name)
        parent_collection.children.link(new_collection)
        return new_collection

def apply_modifiers(context, modifierName):
    list_names = []
    list = []
    list_shapes = []
    basename = bpy.context.object.name

    if context.object.data.shape_keys:
        list_shapes = [o for o in context.object.data.shape_keys.key_blocks]

    if(list_shapes == []):
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifierName)
        return context.view_layer.objects.active

    list.append(context.view_layer.objects.active)

    for i in range(1, len(list_shapes)):
        bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')

        list.append(context.view_layer.objects.active)

    for i, o in enumerate(list):
        context.view_layer.objects.active = o
        list_names.append(o.data.shape_keys.key_blocks[i].name)
        for j in range(i+1, len(list))[::-1]:
            context.object.active_shape_key_index = j
            bpy.ops.object.shape_key_remove()
        for j in range(0, i):
            context.object.active_shape_key_index = 0

            bpy.ops.object.shape_key_remove()
        # last deleted shape doesn't change object shape
        context.object.active_shape_key_index = 0
        bpy.ops.object.shape_key_remove()
        # time to apply modifiers
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifierName)

        if i>0:
            bpy.context.object.name = f'{basename}_{list_names[i]}'
            # time to apply modifiers
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifierName)
            old_collection = find_collection(bpy.context, o)
            new_collection = make_collection(f'{basename} Shapekeys', old_collection)
            new_collection.objects.link(o)
            old_collection.objects.unlink(o)


    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = list[0]
    list[0].select_set(True)
    bpy.ops.object.shape_key_add(from_mix=False)
    context.object.data.shape_keys.key_blocks[0].name = list_names[0]

    for i in range(1, len(list)):
        list[i].select_set(state=True)
        bpy.ops.object.join_shapes()
        list[i].select_set(state=False)
        context.object.data.shape_keys.key_blocks[i].name = list_names[i]

    bpy.ops.object.select_all(action='DESELECT')

    for o in list[1:]:
        o.select_set(True)

    bpy.ops.object.delete(use_global=False)
    context.view_layer.objects.active = list[0]
    context.view_layer.objects.active.select_set(state=True)
    return context.view_layer.objects.active

class AWS_OT_operator(bpy.types.Operator):
    bl_idname = "aws.operator"
    bl_label = "Apply Modifiers w/ Shape Keys"
    bl_description = ("Apply Modifiers for objects with Shape Keys")
    bl_options = {'REGISTER', 'UNDO'}

    def item_list(self, context):
        return [(modifier.name, modifier.name, modifier.name)
                for modifier in bpy.context.view_layer.objects.active.modifiers]

    my_enum : EnumProperty(name="Modifier name",
                            items = item_list)

    def execute(self, context):

        ob = context.view_layer.objects.active
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        context.view_layer.objects.active = ob
        apply_modifiers(context, self.my_enum)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AWS_PT_panel(bpy.types.Panel):
    bl_label = "Apply Modifiers w/ Shape Keys"
    bl_idname = "AWS_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"


    # def draw(self, context):
    #     self.layout.operator("AWS_OT_operator")

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.operator("aws.operator", icon="SHAPEKEY_DATA")
        row.scale_y = 1.5


# def menu_func(self, context):
#     self.layout.operator("AWS_OT_operator",
#         text="Apply Modifiers w/ Shape Keys")

classes = (AWS_OT_operator, AWS_PT_panel)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
