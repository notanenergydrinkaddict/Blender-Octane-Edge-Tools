bl_info = {
    "name": "Octane Copy Active Material to All Slots (_Toon)",
    "author": "Lino Grandi",
    "version": (1, 1, 0),
    "blender": (3, 0, 0),
    "location": "Properties > Material > Right-click menu",
    "description": "Copies the active material to all slots of selected objects and adds '_Toon' suffix, skipping slots already suffixed",
    "category": "Material",
}

import bpy
from bpy.types import Operator, Menu

class MATERIAL_OT_CopyActiveMaterialToon(Operator):
    bl_idname = "material.copy_active_to_all_slots_toon"
    bl_label = "Copy Active Material to All Slots (_Toon)"
    bl_description = "Copies the active material to all slots of selected objects and adds a _Toon suffix"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.object

        if not active_obj or active_obj.type != 'MESH' or not active_obj.material_slots:
            self.report({'ERROR'}, "Active object must be a mesh with material slots")
            return {'CANCELLED'}

        active_index = active_obj.active_material_index
        source_mat = active_obj.material_slots[active_index].material

        if not source_mat:
            self.report({'ERROR'}, "No material in active slot")
            return {'CANCELLED'}

        total_slots = 0
        affected_objects = 0

        for obj in context.selected_objects:
            if obj.type != 'MESH' or not obj.material_slots:
                continue
            affected_objects += 1

            for i, slot in enumerate(obj.material_slots):
                if obj == active_obj and i == active_index:
                    continue
                if slot.material:
                    old_name = slot.material.name
                    if "_Toon" in old_name:
                        continue  # Skip if already has _Toon
                    new_name = f"{old_name}_Toon"

                    if new_name in bpy.data.materials:
                        slot.material = bpy.data.materials[new_name]
                        continue

                    new_mat = source_mat.copy()
                    new_mat.name = new_name
                    slot.material = new_mat
                    total_slots += 1

        self.report({'INFO'}, f"Copied material to {total_slots} slot(s) across {affected_objects} object(s), skipping existing _Toon materials.")
        return {'FINISHED'}


class MATERIAL_MT_slot_context_menu(Menu):
    bl_label = "Material Slot Specials"
    bl_idname = "MATERIAL_MT_slot_context_menu"

    def draw(self, context):
        self.layout.operator("material.copy_active_to_all_slots_toon", icon='COPYDOWN')


def draw_material_slot_menu(self, context):
    self.layout.separator()
    self.layout.menu(MATERIAL_MT_slot_context_menu.bl_idname)


def register():
    bpy.utils.register_class(MATERIAL_OT_CopyActiveMaterialToon)
    bpy.utils.register_class(MATERIAL_MT_slot_context_menu)
    bpy.types.MATERIAL_MT_context_menu.append(draw_material_slot_menu)


def unregister():
    bpy.types.MATERIAL_MT_context_menu.remove(draw_material_slot_menu)
    bpy.utils.unregister_class(MATERIAL_MT_slot_context_menu)
    bpy.utils.unregister_class(MATERIAL_OT_CopyActiveMaterialToon)


if __name__ == "__main__":
    register()
