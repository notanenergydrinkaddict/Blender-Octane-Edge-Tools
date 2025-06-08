
import bpy

bl_info = {
    "name": "Octane Toon & Edge Suffix Manager",
    "blender": (2, 80, 0),
    "category": "Object",
}

class SuffixManagerProperties(bpy.types.PropertyGroup):
    target_collection: bpy.props.PointerProperty(
        name="Collection to Rename",
        type=bpy.types.Collection,
    )

    suffix: bpy.props.StringProperty(
        name="Suffix",
        description="Suffix to add or remove",
        default="_CharA"
    )

    remove_suffix: bpy.props.BoolProperty(
        name="Remove Suffix",
        description="Remove the suffix instead of adding it",
        default=False
    )

    skip_if_exists: bpy.props.BoolProperty(
        name="Skip if Suffix Exists",
        description="Skip renaming items that already have the suffix",
        default=True
    )


class OBJECT_OT_apply_suffix_to_collection(bpy.types.Operator):
    bl_idname = "object.apply_suffix_to_collection"
    bl_label = "Apply or Remove Suffix"
    bl_description = "Apply or remove a suffix to all objects and assets in a collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.suffix_manager_props
        collection = props.target_collection
        suffix = props.suffix
        remove_suffix = props.remove_suffix
        skip_if_exists = props.skip_if_exists

        excluded_object_names = {"GeoNodeTemplate"}

        if not collection:
            self.report({'ERROR'}, "No collection selected.")
            return {'CANCELLED'}

        for obj in collection.all_objects:
            if obj.name in excluded_object_names:
                continue

            if remove_suffix:
                if obj.name.endswith(suffix):
                    obj.name = obj.name[:-len(suffix)]
            elif not skip_if_exists or not obj.name.endswith(suffix):
                obj.name += suffix

            for slot in obj.material_slots:
                mat = slot.material
                if not mat:
                    continue

                if remove_suffix:
                    if mat.name.endswith(suffix):
                        mat.name = mat.name[:-len(suffix)]
                elif not skip_if_exists or not mat.name.endswith(suffix):
                    if mat.name + suffix not in bpy.data.materials:
                        mat.name += suffix

                if mat.use_nodes:
                    for node in mat.node_tree.nodes:
                        if node.type == 'GROUP' and node.node_tree:
                            ng = node.node_tree
                            if remove_suffix:
                                if ng.name.endswith(suffix):
                                    ng.name = ng.name[:-len(suffix)]
                            elif not skip_if_exists or not ng.name.endswith(suffix):
                                if ng.name + suffix not in bpy.data.node_groups:
                                    ng.name += suffix

            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    ng = mod.node_group
                    if remove_suffix:
                        if ng.name.endswith(suffix):
                            ng.name = ng.name[:-len(suffix)]
                    elif not skip_if_exists or not ng.name.endswith(suffix):
                        if ng.name + suffix not in bpy.data.node_groups:
                            ng.name += suffix

            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    for node in mod.node_group.nodes:
                        if node.type == 'OBJECT_INFO':
                            input_obj = node.inputs[0].default_value
                            if not input_obj or input_obj.name in excluded_object_names:
                                continue

                            if remove_suffix:
                                if input_obj.name.endswith(suffix):
                                    input_obj.name = input_obj.name[:-len(suffix)]
                            elif not skip_if_exists or not input_obj.name.endswith(suffix):
                                if input_obj.name + suffix not in bpy.data.objects:
                                    input_obj.name += suffix

        return {'FINISHED'}


class VIEW3D_PT_octane_toon_edge_suffix_manager(bpy.types.Panel):
    bl_label = "Toon & Edge Suffix Manager"
    bl_category = "Octane"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        props = context.scene.suffix_manager_props

        layout.prop(props, "target_collection")
        layout.prop(props, "suffix")
        layout.prop(props, "remove_suffix")
        layout.prop(props, "skip_if_exists")
        layout.operator("object.apply_suffix_to_collection")


classes = (
    SuffixManagerProperties,
    OBJECT_OT_apply_suffix_to_collection,
    VIEW3D_PT_octane_toon_edge_suffix_manager,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.suffix_manager_props = bpy.props.PointerProperty(type=SuffixManagerProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.suffix_manager_props

if __name__ == "__main__":
    register()
