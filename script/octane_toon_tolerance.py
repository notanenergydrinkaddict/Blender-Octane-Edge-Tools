bl_info = {
    "name": "Octane Set Global/Local Tolerance",
    "author": "Lino Grandi",
    "version": (1, 1),
    "blender": (3, 0, 0),
    "location": "Material Slot Specials (right-click)",
    "description": "Connect or disconnect Tolerance Group Node to Edge Tracer LG in materials",
    "category": "Material"
}

import bpy

SOURCE_NODE_NAME = "Tolerance Group Node"
SOURCE_SOCKET_NAME = "Tolerance Out (0-1)"
TARGET_NODE_NAME = "Edge Tracer LG"
TARGET_SOCKET_NAME = "Tolerance Angle"

def connect_nodes(mat):
    if not mat.use_nodes or not mat.node_tree:
        return
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    source = nodes.get(SOURCE_NODE_NAME)
    target = nodes.get(TARGET_NODE_NAME)
    if source and target:
        out_socket = source.outputs.get(SOURCE_SOCKET_NAME)
        in_socket = target.inputs.get(TARGET_SOCKET_NAME)
        if out_socket and in_socket and not in_socket.is_linked:
            links.new(out_socket, in_socket)

def disconnect_nodes(mat):
    if not mat.use_nodes or not mat.node_tree:
        return
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    target = nodes.get(TARGET_NODE_NAME)
    if target:
        in_socket = target.inputs.get(TARGET_SOCKET_NAME)
        if in_socket and in_socket.is_linked:
            for link in list(links):
                if link.to_socket == in_socket:
                    links.remove(link)

class OT_ConnectEdgeNodes(bpy.types.Operator):
    bl_idname = "material.connect_edge_nodes"
    bl_label = "Set Global Tolerance (_Toon)"
    bl_description = "Connect Tolerance Group Node to Edge Tracer LG"

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material:
                        connect_nodes(slot.material)
        return {'FINISHED'}

class OT_DisconnectEdgeNodes(bpy.types.Operator):
    bl_idname = "material.disconnect_edge_nodes"
    bl_label = "Set Local Tolerance (_Toon)"
    bl_description = "Disconnect Tolerance Group Node from Edge Tracer LG"

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material:
                        disconnect_nodes(slot.material)
        return {'FINISHED'}

def draw_func(self, context):
    layout = self.layout
    layout.separator()
    layout.label(text="Edge Shader Tools:")
    layout.operator("material.connect_edge_nodes", icon='NODE')
    layout.operator("material.disconnect_edge_nodes", icon='CANCEL')

def register():
    bpy.utils.register_class(OT_ConnectEdgeNodes)
    bpy.utils.register_class(OT_DisconnectEdgeNodes)
    bpy.types.MATERIAL_MT_context_menu.append(draw_func)

def unregister():
    bpy.utils.unregister_class(OT_ConnectEdgeNodes)
    bpy.utils.unregister_class(OT_DisconnectEdgeNodes)
    bpy.types.MATERIAL_MT_context_menu.remove(draw_func)

if __name__ == "__main__":
    register()
