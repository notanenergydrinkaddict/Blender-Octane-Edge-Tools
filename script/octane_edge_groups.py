import bpy

bl_info = {
    "name": "Octane Edge Tools",
    "author": "Lino Grandi",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "Object Data Properties > Vertex Groups",
    "description": "Adds buttons to create specific vertex groups for Octane NPR projects",
    "category": "Object",
}

EDGE_GROUPS = {
    "EdgeThickness": 1.0,
    "Traced_Edges_01": 0.0,
    "Traced_Edges_02": 0.0,
    "Traced_Edges_03": 0.0,
}


class AddVertexGroupOperator(bpy.types.Operator):
    """Add a Vertex Group with a specific name and weight"""
    bl_idname = "object.add_vertex_group"
    bl_label = "Add Vertex Group"
    bl_options = {'REGISTER', 'UNDO'}

    vertex_group_name: bpy.props.StringProperty()
    default_weight: bpy.props.FloatProperty()

    def execute(self, context):
        initial_mode = context.object.mode

        for obj in context.selected_objects:
            if obj.type == 'MESH':
                if obj.mode == 'EDIT':
                    bpy.ops.object.mode_set(mode='OBJECT')

                vg = obj.vertex_groups.get(self.vertex_group_name)
                if vg is None:
                    vg = obj.vertex_groups.new(name=self.vertex_group_name)

                all_verts = [v.index for v in obj.data.vertices]
                vg.add(all_verts, self.default_weight, 'REPLACE')

        if initial_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


class AddAllEdgeGroupsOperator(bpy.types.Operator):
    """Adds all required vertex groups, skipping existing ones"""
    bl_idname = "object.add_all_edge_groups"
    bl_label = "Add All Edge Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        initial_mode = context.object.mode

        for obj in context.selected_objects:
            if obj.type == 'MESH':
                if obj.mode == 'EDIT':
                    bpy.ops.object.mode_set(mode='OBJECT')

                existing_groups = {vg.name for vg in obj.vertex_groups}

                for group_name, weight in EDGE_GROUPS.items():
                    if group_name not in existing_groups:
                        vg = obj.vertex_groups.new(name=group_name)
                        all_verts = [v.index for v in obj.data.vertices]
                        vg.add(all_verts, weight, 'REPLACE')

        if initial_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


class OctaneEdgeToolsPanel(bpy.types.Panel):
    """Panel for Octane Edge Tools"""
    bl_label = "Octane Edge Tools"
    bl_idname = "DATA_PT_octane_edge_tools"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = "DATA_PT_vertex_groups"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Input value for EdgeThickness
        layout.prop(scene, "edge_thickness_value", text="EdgeThickness Value")

        # Add/Modify EdgeThickness with custom weight
        op = layout.operator("object.add_vertex_group", text="Add/Modify EdgeThickness", icon='GROUP_VERTEX')
        op.vertex_group_name = "EdgeThickness"
        op.default_weight = scene.edge_thickness_value

        # Other traced edge groups (fixed weights)
        for group_name in ["Traced_Edges_01", "Traced_Edges_02", "Traced_Edges_03"]:
            op = layout.operator("object.add_vertex_group", text=f"Add {group_name}", icon='GROUP_VERTEX')
            op.vertex_group_name = group_name
            op.default_weight = EDGE_GROUPS[group_name]

        layout.separator()
        layout.operator("object.add_all_edge_groups", text="Add All Edge Groups", icon='GROUP_VERTEX')


def register():
    bpy.utils.register_class(AddVertexGroupOperator)
    bpy.utils.register_class(AddAllEdgeGroupsOperator)
    bpy.utils.register_class(OctaneEdgeToolsPanel)

    bpy.types.Scene.edge_thickness_value = bpy.props.FloatProperty(
        name="EdgeThickness Value",
        description="Default weight value for EdgeThickness vertex group",
        default=0.5,
        min=0.0,
        max=1.0
    )


def unregister():
    bpy.utils.unregister_class(AddVertexGroupOperator)
    bpy.utils.unregister_class(AddAllEdgeGroupsOperator)
    bpy.utils.unregister_class(OctaneEdgeToolsPanel)

    del bpy.types.Scene.edge_thickness_value


if __name__ == "__main__":
    register()
