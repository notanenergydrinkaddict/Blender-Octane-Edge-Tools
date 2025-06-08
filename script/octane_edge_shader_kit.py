def update_asset_path(self, context):
    save_asset_path(self.asset_blend_path)


def ensure_edge_assets_are_present():
    import bpy
    import os

    scene = bpy.context.scene
    input_path = bpy.path.abspath(scene.asset_blend_path)

    # Support both file or directory
    if input_path.lower().endswith(".blend") and os.path.isfile(input_path):
        blend_path = input_path
    else:
        blend_path = os.path.join(input_path, "Octane_Edge_Tools_Assets.blend")

    if not os.path.isfile(blend_path):
        print(f"❌ Asset file not found: {blend_path}")
        return False

    collection_name = 'GeoEdges'
    object_name = 'GeoNodeTemplate'

    # Append collection if not already present
    if collection_name not in bpy.data.collections:
        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
            if collection_name in data_from.collections:
                data_to.collections.append(collection_name)
                print(f'✅ Collection {collection_name} appended.')
            else:
                print(f'❌ Collection {collection_name} not found in .blend.')

    coll = bpy.data.collections.get(collection_name)

    # Check if collection is already linked to scene
    def is_collection_linked_recursively(parent, target):
        if any(child is target for child in parent.children):
            return True
        return any(is_collection_linked_recursively(child, target) for child in parent.children)

    if coll and not is_collection_linked_recursively(bpy.context.scene.collection, coll):
        bpy.context.scene.collection.children.link(coll)
        print(f"📦 Collection '{collection_name}' linked to scene.")

    # Append object if missing
    if object_name not in bpy.data.objects:
        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
            if object_name in data_from.objects:
                data_to.objects = [object_name]
                print(f'✅ Object {object_name} appended.')
    else:
        print(f'ℹ️ Object {object_name} already exists. Skipping import.')

    # Link object to collection
    obj = bpy.data.objects.get(object_name)
    if obj and coll and obj.name not in coll.objects:
        coll.objects.link(obj)
        print(f'🔗 Linked object {obj.name} to collection {collection_name}')

    # === Cleanup: remove unused duplicated scenes (e.g. Scene.001, Scene.002, etc.)
    current_scene = bpy.context.scene
    to_remove = [
        scene for scene in bpy.data.scenes
        if scene != current_scene and scene.users == 0 and scene.name.startswith("Scene")
    ]
    for scene in to_remove:
        bpy.data.scenes.remove(scene)
        print(f"🧹 Removed unused scene: {scene.name}")

    # === Reassign drivers to current scene (after cleanup)
    all_blocks = (
        list(bpy.data.node_groups) +
        list(bpy.data.materials) +
        list(bpy.data.objects)
    )
    for datablock in all_blocks:
        if datablock.animation_data:
            for driver in datablock.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE' and target.id != current_scene:
                            target.id = current_scene
                            print(f"🔁 Driver in '{datablock.name}' reassigned to scene: {current_scene.name}")

    return True



import bpy

def ensure_octane_edge_assets():
    import bpy
    import os
    
    # === CONFIGURATION ===

    LIBRARY_PATH = bpy.path.abspath(bpy.bpy.context.scene.asset_blend_path)
    if not LIBRARY_PATH or not os.path.exists(LIBRARY_PATH):
        print("❌ Invalid asset path. Please set it in the addon preferences.")
        return
    
    assets = {
        "materials": ["Edge Material", "Inverted Hull Edges"],
        "objects": ["GeoNodeTemplate"],
        "node_groups": ["GeoEdgesTemplate"],
        "node_trees": ["Octane_Toon_AOVs", "Octane Toon Compositor"]
    }
    
    def append_from_library(path, category, names):
        try:
            with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
                existing = getattr(bpy.data, category)
                to_load = [name for name in names if name not in existing]
                if to_load:
                    setattr(data_to, category, to_load)
                    print(f"📦 Imported {category}: {to_load}")
                else:
                    print(f"✅ Already present: {category}")
        except Exception as e:
            print(f"❌ Failed to load category '{category}' from {path}. Error: {e}")


    
    # === ESECUZIONE DELL'IMPORT ===
    append_from_library(LIBRARY_PATH, "materials", assets["materials"])
    append_from_library(LIBRARY_PATH, "objects", assets["objects"])
    append_from_library(LIBRARY_PATH, "node_groups", assets["node_groups"])
    append_from_library(LIBRARY_PATH, "node_groups", assets["node_trees"])
    
    # === REMOVAL OF STRAY SCENES (e.g. Scene.001) ===
    for scene in bpy.data.scenes:
        if scene != bpy.context.scene and scene.name.startswith("Scene."):
            bpy.data.scenes.remove(scene)
    scene = bpy.context.scene
    
    # === DRIVER SETUP ===
    def apply_driver(target, path, prop_name):
        try:
            target.driver_remove(path)
        except:
            pass
        fcurve = target.driver_add(path)
        driver = fcurve.driver
        driver.type = 'AVERAGE'
        var = driver.variables.new()
        var.name = "var"
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = scene
        var.targets[0].data_path = f'["{prop_name}"]'
        driver.expression = "var"
    
    # === DRIVER sul materiale "Edge Material"
    mat = bpy.data.materials.get("Edge Material")
    if mat and mat.node_tree:
        node = mat.node_tree.nodes.get("Multiply texture")
        if node and node.inputs[1]:
            apply_driver(node.inputs[1], "default_value", "Outline Thickness")
            print("🎯 Driver set on Edge Material")
    
    # === DRIVER on the GeoNodeTemplate
    geo_obj = bpy.data.objects.get("GeoNodeTemplate")
    if geo_obj:
        for mod in geo_obj.modifiers:
            if mod.type == 'NODES' and mod.node_group and mod.node_group.name == "GeoEdgesTemplate":
                inputs = mod.node_group.interface.items_tree
                for i, input_socket in enumerate(inputs):
                    if input_socket.name == "Thickness":
                        input_id = f"Input_{i}"
                        geo_obj.modifiers[mod.name][input_id] = 1.0  # default init
                        apply_driver(geo_obj, f'modifiers["{mod.name}"]["{input_id}"]', "Edge Thickness")
                        print("🎯 Driver set on GeoNodeTemplate")
    
    print("✅ All assets imported and drivers applied.")
    
    
    # === FIX: forza la scena corretta come target dei driver ===
    def force_driver_scene_binding(node_group_name):
        node_group = bpy.data.node_groups.get(node_group_name)
        if node_group and node_group.animation_data:
            for driver in node_group.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE':
                            target.id = bpy.context.scene
                            print(f"🔗 Driver in '{node_group_name}' ricollegato a scena attiva.")
    
    force_driver_scene_binding("GeoEdgesTemplate")
    
    
    # === FIX: also force the correct scene for the material's node group ===
    def force_driver_scene_binding_for_material(node_group_name):
        node_group = bpy.data.node_groups.get(node_group_name)
        if node_group and node_group.animation_data:
            for driver in node_group.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE':
                            target.id = bpy.context.scene
                            print(f"🔗 Driver in '{node_group_name}' ricollegato a scena attiva (material).")
    
    force_driver_scene_binding_for_material("Edge Thickness Multiplier")



    def execute(self, context):
        ensure_octane_edge_assets()
        self.report({'INFO'}, "Edge Tools assets imported.")
        return {'FINISHED'}
        ensure_edge_assets_are_present()  # Ensure asset availability



    # === CONFIGURATION ===
    blend_path = os.path.join(bpy.path.abspath(bpy.context.scene.asset_blend_path), "Octane_Edge_Tools_Assets.blend")
    LIBRARY_PATH = os.path.join(bpy.path.abspath(context.scene.asset_blend_path), "Octane_Edge_Tools_Assets.blend")
    
    assets = {
        "materials": ["Edge Material", "Inverted Hull Edges"],
        "objects": ["GeoNodeTemplate"],
        "node_groups": ["GeoEdgesTemplate"],
        "node_trees": ["Octane_Toon_AOVs", "Octane Toon Compositor"]
    }
    
    # === FUNCTION: import a category from a blend file ===
    def append_from_library(path, category, names):
        try:
            with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
                existing = getattr(bpy.data, category)
                to_load = [name for name in names if name not in existing]
                if to_load:
                    setattr(data_to, category, to_load)
                    print(f"📦 Imported {category}: {to_load}")
                else:
                    print(f"✅ Already present: {category}")
        except Exception as e:
            print(f"❌ Failed to load category '{category}' from {path}. Error: {e}")

    
    # === ESECUZIONE DELL'IMPORT ===
    append_from_library(LIBRARY_PATH, "materials", assets["materials"])
    append_from_library(LIBRARY_PATH, "objects", assets["objects"])
    append_from_library(LIBRARY_PATH, "node_groups", assets["node_groups"])
    append_from_library(LIBRARY_PATH, "node_groups", assets["node_trees"])
    
    # === REMOVAL OF STRAY SCENES (e.g. Scene.001) ===
    for scene in bpy.data.scenes:
        if scene != bpy.context.scene and scene.name.startswith("Scene."):
            bpy.data.scenes.remove(scene)
    scene = bpy.context.scene
    
    # === DRIVER SETUP ===
    def apply_driver(target, path, prop_name):
        try:
            target.driver_remove(path)
        except:
            pass
        fcurve = target.driver_add(path)
        driver = fcurve.driver
        driver.type = 'AVERAGE'
        var = driver.variables.new()
        var.name = "var"
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = scene
        var.targets[0].data_path = f'["{prop_name}"]'
        driver.expression = "var"
    
    # === DRIVER sul materiale "Edge Material"
    mat = bpy.data.materials.get("Edge Material")
    if mat and mat.node_tree:
        node = mat.node_tree.nodes.get("Multiply texture")
        if node and node.inputs[1]:
            apply_driver(node.inputs[1], "default_value", "Outline Thickness")
            print("🎯 Driver set on Edge Material")
    
    # === DRIVER on the GeoNodeTemplate
    geo_obj = bpy.data.objects.get("GeoNodeTemplate")
    if geo_obj:
        for mod in geo_obj.modifiers:
            if mod.type == 'NODES' and mod.node_group and mod.node_group.name == "GeoEdgesTemplate":
                inputs = mod.node_group.interface.items_tree
                for i, input_socket in enumerate(inputs):
                    if input_socket.name == "Thickness":
                        input_id = f"Input_{i}"
                        geo_obj.modifiers[mod.name][input_id] = 1.0  # default init
                        apply_driver(geo_obj, f'modifiers["{mod.name}"]["{input_id}"]', "Edge Thickness")
                        print("🎯 Driver set on GeoNodeTemplate")
    
    print("✅ All assets imported and drivers applied.")
    
    
    # === FIX: forza la scena corretta come target dei driver ===
    def force_driver_scene_binding(node_group_name):
        node_group = bpy.data.node_groups.get(node_group_name)
        if node_group and node_group.animation_data:
            for driver in node_group.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE':
                            target.id = bpy.context.scene
                            print(f"🔗 Driver in '{node_group_name}' ricollegato a scena attiva.")
    
    force_driver_scene_binding("GeoEdgesTemplate")
    
    
    # === FIX: also force the correct scene for the material's node group ===
    def force_driver_scene_binding_for_material(node_group_name):
        node_group = bpy.data.node_groups.get(node_group_name)
        if node_group and node_group.animation_data:
            for driver in node_group.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE':
                            target.id = bpy.context.scene
                            print(f"🔗 Driver in '{node_group_name}' ricollegato a scena attiva (material).")
    
    force_driver_scene_binding_for_material("Edge Thickness Multiplier")

    # === CONFIGURATION ===
    addon = bpy.context.preferences.addons.get(__name__)
    prefs = addon.preferences
    LIBRARY_PATH = os.path.join(bpy.path.abspath(bpy.context.scene.asset_blend_path), "Octane_Edge_Tools_Assets.blend")
    
    assets = {
        "materials": ["Edge Material", "Inverted Hull Edges"],
        "objects": ["GeoNodeTemplate"],
        "node_groups": ["GeoEdgesTemplate"],
        "node_trees": ["Octane_Toon_AOVs", "Octane Toon Compositor"]
    }
    
    # === FUNCTION: import a category from a blend file ===
    def append_from_library(path, category, names):
        try:
            with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
                existing = getattr(bpy.data, category)
                to_load = [name for name in names if name not in existing]
                if to_load:
                    setattr(data_to, category, to_load)
                    print(f"📦 Imported {category}: {to_load}")
                else:
                    print(f"✅ Already present: {category}")
        except Exception as e:
            print(f"❌ Failed to load category '{category}' from {path}. Error: {e}")

    
    # === ESECUZIONE DELL'IMPORT ===
    append_from_library(LIBRARY_PATH, "materials", assets["materials"])
    append_from_library(LIBRARY_PATH, "objects", assets["objects"])
    append_from_library(LIBRARY_PATH, "node_groups", assets["node_groups"])
    append_from_library(LIBRARY_PATH, "node_groups", assets["node_trees"])
    
    # === REMOVAL OF STRAY SCENES (e.g. Scene.001) ===
    for scene in bpy.data.scenes:
        if scene != bpy.context.scene and scene.name.startswith("Scene."):
            bpy.data.scenes.remove(scene)
    scene = bpy.context.scene
    
    # === DRIVER SETUP ===
    def apply_driver(target, path, prop_name):
        try:
            target.driver_remove(path)
        except:
            pass
        fcurve = target.driver_add(path)
        driver = fcurve.driver
        driver.type = 'AVERAGE'
        var = driver.variables.new()
        var.name = "var"
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = scene
        var.targets[0].data_path = f'["{prop_name}"]'
        driver.expression = "var"
    
    # === DRIVER sul materiale "Edge Material"
    mat = bpy.data.materials.get("Edge Material")
    if mat and mat.node_tree:
        node = mat.node_tree.nodes.get("Multiply texture")
        if node and node.inputs[1]:
            apply_driver(node.inputs[1], "default_value", "Outline Thickness")
            print("🎯 Driver set on Edge Material")
    
    # === DRIVER on the GeoNodeTemplate
    geo_obj = bpy.data.objects.get("GeoNodeTemplate")
    if geo_obj:
        for mod in geo_obj.modifiers:
            if mod.type == 'NODES' and mod.node_group and mod.node_group.name == "GeoEdgesTemplate":
                inputs = mod.node_group.interface.items_tree
                for i, input_socket in enumerate(inputs):
                    if input_socket.name == "Thickness":
                        input_id = f"Input_{i}"
                        geo_obj.modifiers[mod.name][input_id] = 1.0  # default init
                        apply_driver(geo_obj, f'modifiers["{mod.name}"]["{input_id}"]', "Edge Thickness")
                        print("🎯 Driver set on GeoNodeTemplate")
    
    print("✅ All assets imported and drivers applied.")
    
    
    # === FIX: forza la scena corretta come target dei driver ===
    def force_driver_scene_binding(node_group_name):
        node_group = bpy.data.node_groups.get(node_group_name)
        if node_group and node_group.animation_data:
            for driver in node_group.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE':
                            target.id = bpy.context.scene
                            print(f"🔗 Driver in '{node_group_name}' ricollegato a scena attiva.")
    
    force_driver_scene_binding("GeoEdgesTemplate")
    
    
    # === FIX: also force the correct scene for the material's node group ===
    def force_driver_scene_binding_for_material(node_group_name):
        node_group = bpy.data.node_groups.get(node_group_name)
        if node_group and node_group.animation_data:
            for driver in node_group.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE':
                            target.id = bpy.context.scene
                            print(f"🔗 Driver in '{node_group_name}' ricollegato a scena attiva (material).")
    
    force_driver_scene_binding_for_material("Edge Thickness Multiplier")


# === AUTO-ASSET LOADER FOR EDGE TOOLS ===
    # === CONFIGURATION ===
    addon = bpy.context.preferences.addons.get(__name__)
    prefs = addon.preferences
    LIBRARY_PATH = os.path.join(bpy.path.abspath(bpy.context.scene.asset_blend_path), "Octane_Edge_Tools_Assets.blend")
    
    assets = {
        "materials": ["Edge Material", "Inverted Hull Edges"],
        "objects": ["GeoNodeTemplate"],
        "node_groups": ["GeoEdgesTemplate"],
        "node_trees": ["Octane_Toon_AOVs", "Octane Toon Compositor"]
    }
    
    # === FUNCTION: import a category from a blend file ===
    def append_from_library(path, category, names):
        try:
            with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
                existing = getattr(bpy.data, category)
                to_load = [name for name in names if name not in existing]
                if to_load:
                    setattr(data_to, category, to_load)
                    print(f"📦 Imported {category}: {to_load}")
                else:
                    print(f"✅ Already present: {category}")
        except Exception as e:
            print(f"❌ Failed to load category '{category}' from {path}. Error: {e}")

    
    # === ESECUZIONE DELL'IMPORT ===
    append_from_library(LIBRARY_PATH, "materials", assets["materials"])
    append_from_library(LIBRARY_PATH, "objects", assets["objects"])
    append_from_library(LIBRARY_PATH, "node_groups", assets["node_groups"])
    append_from_library(LIBRARY_PATH, "node_groups", assets["node_trees"])
    
    # === REMOVAL OF STRAY SCENES (e.g. Scene.001) ===
    for scene in bpy.data.scenes:
        if scene != bpy.context.scene and scene.name.startswith("Scene."):
            bpy.data.scenes.remove(scene)
    scene = bpy.context.scene
    
    # === DRIVER SETUP ===
    def apply_driver(target, path, prop_name):
        try:
            target.driver_remove(path)
        except:
            pass
        fcurve = target.driver_add(path)
        driver = fcurve.driver
        driver.type = 'AVERAGE'
        var = driver.variables.new()
        var.name = "var"
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = scene
        var.targets[0].data_path = f'["{prop_name}"]'
        driver.expression = "var"
    
    # === DRIVER sul materiale "Edge Material"
    mat = bpy.data.materials.get("Edge Material")
    if mat and mat.node_tree:
        node = mat.node_tree.nodes.get("Multiply texture")
        if node and node.inputs[1]:
            apply_driver(node.inputs[1], "default_value", "Outline Thickness")
            print("🎯 Driver set on Edge Material")
    
    # === DRIVER on the GeoNodeTemplate
    geo_obj = bpy.data.objects.get("GeoNodeTemplate")
    if geo_obj:
        for mod in geo_obj.modifiers:
            if mod.type == 'NODES' and mod.node_group and mod.node_group.name == "GeoEdgesTemplate":
                inputs = mod.node_group.interface.items_tree
                for i, input_socket in enumerate(inputs):
                    if input_socket.name == "Thickness":
                        input_id = f"Input_{i}"
                        geo_obj.modifiers[mod.name][input_id] = 1.0  # default init
                        apply_driver(geo_obj, f'modifiers["{mod.name}"]["{input_id}"]', "Edge Thickness")
                        print("🎯 Driver set on GeoNodeTemplate")
    
    print("✅ All assets imported and drivers applied.")
    
    
    # === FIX: forza la scena corretta come target dei driver ===
    def force_driver_scene_binding(node_group_name):
        node_group = bpy.data.node_groups.get(node_group_name)
        if node_group and node_group.animation_data:
            for driver in node_group.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE':
                            target.id = bpy.context.scene
                            print(f"🔗 Driver in '{node_group_name}' ricollegato a scena attiva.")
    
    force_driver_scene_binding("GeoEdgesTemplate")
    
    
    # === FIX: also force the correct scene for the material's node group ===
    def force_driver_scene_binding_for_material(node_group_name):
        node_group = bpy.data.node_groups.get(node_group_name)
        if node_group and node_group.animation_data:
            for driver in node_group.animation_data.drivers:
                for var in driver.driver.variables:
                    for target in var.targets:
                        if target.id_type == 'SCENE':
                            target.id = bpy.context.scene
                            print(f"🔗 Driver in '{node_group_name}' ricollegato a scena attiva (material).")
    
    force_driver_scene_binding_for_material("Edge Thickness Multiplier")
    
    
# === FINE BLOCCO AUTO-ASSET ===



bl_info = {
    "name": "Octane Edge Shader Kit",
    "author": "Lino Grandi – 3D Artist at OTOY",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Octane",
    "description": "Tools to set up toon edges and compositing for OctaneRender",
    "category": "Object"
}

import bpy
import os

class OBJECT_OT_remove_toon_edges(bpy.types.Operator):
    bl_idname = "object.remove_toon_edges"
    bl_label = "Remove Toon Edges"
    bl_description = "Remove associated GeoEdges objects and clean modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not ensure_edge_assets_are_present():
            self.report({'ERROR'}, "Missing assets.")
            return {'CANCELLED'}

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            self.report({'WARNING'}, "No mesh selected.")
            return {'CANCELLED'}

        removed = 0
        for obj in selected_meshes:
            geo_name = f"GeoEdges_{obj.name}"
            geo_obj = bpy.data.objects.get(geo_name)

            # 1. Remove associated GeoEdges duplicate object
            if geo_obj:
                for coll in geo_obj.users_collection:
                    coll.objects.unlink(geo_obj)

                geo_mod = geo_obj.modifiers.get("GeometryNodes")
                if geo_mod and geo_mod.node_group:
                    ng = geo_mod.node_group
                    if ng.users == 1:
                        ng_name = ng.name
                        bpy.data.node_groups.remove(ng)
                        print(f"🧹 Removed node group: {ng_name}")

                bpy.data.objects.remove(geo_obj)
                removed += 1
                print(f"🧹 Removed edge object: {geo_name}")
            else:
                print(f"⚠️ Edge object '{geo_name}' not found.")

            # 2. Remove only the "GeometryNodes" modifier
            mod = obj.modifiers.get("GeometryNodes")
            if mod and mod.type == 'NODES':
                obj.modifiers.remove(mod)
                print(f"🧽 Removed 'GeometryNodes' modifier from: {obj.name}")

            # 3. Remove EdgeThickness vertex group
            if "EdgeThickness" in obj.vertex_groups:
                obj.vertex_groups.remove(obj.vertex_groups["EdgeThickness"])
                print(f"🧽 Removed vertex group 'EdgeThickness' from: {obj.name}")

        self.report({'INFO'}, f"Toon Edges removed from {removed} object(s).")
        return {'FINISHED'}



class ToonEdgeSettings(bpy.types.PropertyGroup):
    preserve_edge_thickness: bpy.props.BoolProperty(
        name="Preserve EdgeThickness",
        description="Preserve EdgeThickness",
        default=False
    )
    show_edge_creation_options: bpy.props.BoolProperty(name="Show Edge Creation Options", default=True)
    show_global_thickness: bpy.props.BoolProperty(name="Show Global Thickness Controls", default=True)

    global_outline_thickness: bpy.props.FloatProperty(
        name="Outline Thickness",
        description="Global Outline Thickness.",
        default=1.0,
        min=0.0,
        max=10.0
    )
    global_edge_thickness: bpy.props.FloatProperty(
        name="Edge Thickness",
        description="Global Edge Thickness",
        default=1.0,
        min=0.0,
        max=10.0
    )
    preserve_custom_normals: bpy.props.BoolProperty(
        name="Preserve Custom Normals",
        description="Do not clear custom split normals",
        default=False
    )
    edge_thickness_value: bpy.props.FloatProperty(
        name="EdgeThickness Weight",
        description="Weight value for EdgeThickness vertex group",
        default=0.5,
        min=0.0,
        max=1.0
    )
    outline_thickness_value: bpy.props.FloatProperty(
        name="Outline Thickness",
        description="Value to set on the Geometry Node modifier's Thickness input",
        default=0.5,
        min=0.0,
        max=20.0
    )
    shading_mode: bpy.props.EnumProperty(
        name="Shading Mode",
        description="Choose shading type for selected objects",
        items=[
            ('FLAT', "Flat", "Use flat shading"),
            ('SMOOTH', "Smooth", "Use smooth shading"),
            ('AUTO_SMOOTH', "Auto Smooth", "Use auto smooth shading")
        ],
        default='AUTO_SMOOTH'
    )

class OBJECT_OT_setup_toon_edges(bpy.types.Operator):
    bl_idname = "object.setup_toon_edges"
    bl_label = "Set Up Toon Edges"
    bl_description = "Set up toon edge tracing with Geometry Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        # ✅ Step 1: Controlla presenza asset file
        if not ensure_edge_assets_are_present():
            self.report({'ERROR'}, "Asset blend file not found or missing required data. Check Add-on Preferences.")
            return {'CANCELLED'}
        
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            self.report({'WARNING'}, 'No mesh objects selected.')
            return {'CANCELLED'}

        props = context.scene.toon_edge_settings
        VERTEX_GROUP_NAME = "EdgeThickness"
        EDGE_MAT_NAME = "Edge Material"
        TEMPLATE_OBJ_NAME = "GeoNodeTemplate"
        TEMPLATE_GROUP_NAME = "GeoEdgesTemplate"
        TARGET_COLLECTION_NAME = "GeoEdges"

        ensure_edge_assets_are_present()  # Ensure asset availability

        source_object = bpy.data.objects.get(TEMPLATE_OBJ_NAME)
        node_group = bpy.data.node_groups.get(TEMPLATE_GROUP_NAME)
        target_collection = bpy.data.collections.get(TARGET_COLLECTION_NAME)

        if source_object is None or node_group is None or target_collection is None:
            self.report({'ERROR'}, "GeoNodeTemplate, GeoEdgesTemplate, or GeoEdges collection not found.")
            return {'CANCELLED'}

        edge_mat = bpy.data.materials.get(EDGE_MAT_NAME)

        for obj in selected_meshes:
            mesh = obj.data

            if props.preserve_edge_thickness and VERTEX_GROUP_NAME in obj.vertex_groups:
                pass
            else:
                if VERTEX_GROUP_NAME in obj.vertex_groups:
                    obj.vertex_groups.remove(obj.vertex_groups[VERTEX_GROUP_NAME])
                vg = obj.vertex_groups.new(name=VERTEX_GROUP_NAME)
                vg.add(range(len(mesh.vertices)), props.edge_thickness_value, 'REPLACE')
                obj.vertex_groups.active_index = vg.index
                while obj.vertex_groups.active_index > 0:
                    bpy.ops.object.vertex_group_move(direction='UP')

            while obj.vertex_groups.active_index > 0:
                bpy.ops.object.vertex_group_move(direction='UP')

            context.view_layer.objects.active = obj
            if props.shading_mode == 'FLAT':
                bpy.ops.object.shade_flat()
            elif props.shading_mode == 'SMOOTH':
                bpy.ops.object.shade_smooth()
            elif props.shading_mode == 'AUTO_SMOOTH':
                bpy.ops.object.shade_auto_smooth()

            if not props.preserve_custom_normals:
                try:
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
                except:
                    pass

            if edge_mat and edge_mat.name not in [m.name for m in mesh.materials]:
                mesh.materials.append(edge_mat)

            geo_name = f"GeoEdges_{obj.name}"
            if geo_name in bpy.data.objects:
                self.report({'INFO'}, f"{geo_name} already exists, skipping.")
                continue

            new_obj = source_object.copy()
            new_obj.hide_select = True
            new_obj.data = source_object.data.copy()
            target_collection.objects.link(new_obj)

            for coll in new_obj.users_collection:
                if coll != target_collection:
                    coll.objects.unlink(new_obj)

            new_obj.name = geo_name
            new_obj.data.name = f"GeoEdges_{obj.data.name}"

            unique_group = node_group.copy()
            unique_group.name = f"{geo_name}_NG"

            modifier = new_obj.modifiers.get("GeometryNodes")
            if not modifier:
                modifier = new_obj.modifiers.new("GeometryNodes", 'NODES')
            modifier.node_group = unique_group

            for node in unique_group.nodes:
                if node.type == 'OBJECT_INFO':
                    node.inputs['Object'].default_value = obj
                    break

            try:
                modifier["Socket_2"] = props.outline_thickness_value
                print(f"✔️ {new_obj.name}: Socket_2 set to {props.outline_thickness_value}")
            except:
                print(f"⚠️ {new_obj.name}: Could not set Socket_2")

        # Assegna Edge Material alla selezione finale
        if selected_meshes:
            last_obj = selected_meshes[-1]
            bpy.context.view_layer.objects.active = last_obj

            edge_material = None
            for mat in bpy.data.materials:
                if "Edge Material" in mat.name:
                    edge_material = mat
                    break

            if edge_material:
                if not last_obj.data.materials:
                    last_obj.data.materials.append(edge_material)
                else:
                    found_index = -1
                    for index, mat in enumerate(last_obj.data.materials):
                        if mat and "Edge Material" in mat.name:
                            last_obj.active_material_index = index
                            found_index = index
                            break

                    if found_index == -1:
                        last_obj.material_slots[0].material = edge_material
                        last_obj.active_material_index = 0

                if last_obj.type == 'MESH' and last_obj.material_slots:
                    try:
                        bpy.ops.material.copy_active_to_all_slots_toon()
                        print("🎨 Copied active material to all slots.")
                    except Exception as e:
                        print(f"❌ Failed to copy material: {e}")
            else:
                print("❌ No 'Edge Material' found in the scene.")

        # ✅ Cleanup scene duplicata (Scene.001, Scene.002, ecc.)
        stray_scenes = [
            scene.name for scene in bpy.data.scenes
            if scene != bpy.context.scene and scene.name.startswith("Scene.")
        ]
        for name in stray_scenes:
            scene_to_remove = bpy.data.scenes.get(name)
            if scene_to_remove:
                bpy.data.scenes.remove(scene_to_remove)
                print(f"🧹 Removed stray scene: {name}")

        self.report({'INFO'}, "Toon edge setup complete.")
        return {'FINISHED'}





class OBJECT_OT_set_thickness_on_selected(bpy.types.Operator):
    bl_idname = "object.set_thickness_on_selected"
    bl_label = "Set Outline Thickness on Selected"
    bl_description = "Set Outline Thickness value on all selected objects."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        props = context.scene.toon_edge_settings
        value = props.outline_thickness_value
        count = 0
        view_layer = context.view_layer
        ensure_edge_assets_are_present()  # Ensure asset availability

        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']
        for obj in selected:
            if obj.name.startswith("GeoEdges_"):
                continue

            geo_name = f"GeoEdges_{obj.name}"
            geo_obj = bpy.data.objects.get(geo_name)
            if not geo_obj:
                self.report({'WARNING'}, f"No GeoEdges object found for {obj.name}")
                continue

            geo_obj.hide_select = True
            view_layer.objects.active = geo_obj
            bpy.context.view_layer.update()

            mod = geo_obj.modifiers.get("GeometryNodes")
            if mod and "Socket_2" in mod:
                mod["Socket_2"] = value
                mod.node_group = mod.node_group
                obj.update_tag()
                bpy.context.view_layer.update()
                count += 1
            else:
                self.report({'WARNING'}, f"{obj.name}: GeometryNodes modifier or Socket_2 not found.")

        self.report({'INFO'}, f"Set Outline Thickness = {value} on {count} objects.")
        # ✅ Selects the slot containing "Edge Material" in the last selected object
        if selected_meshes:
            last_obj = selected_meshes[-1]
            bpy.context.view_layer.objects.active = last_obj
            for index, mat in enumerate(last_obj.data.materials):
                if mat and mat.name == "Edge Material":
                    last_obj.active_material_index = index
                    print(f"🎯 Selected 'Edge Material' in slot {index} on: {last_obj.name}")
                return {'FINISHED'}  # replaced break to exit operator
        return {'FINISHED'}


class OBJECT_OT_setup_aov_compositing(bpy.types.Operator):
    bl_idname = "object.setup_aov_compositing"
    bl_label = "Set Up AOV/Compositing"
    bl_description = "Assign Octane AOV and compositing node trees to the current view layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            view_layer = bpy.context.view_layer
            octane_view_layer = view_layer.octane

            # Assign AOV Node Tree
            aov_name = "Octane_Toon_AOVs"
            aov_tree = bpy.data.node_groups.get(aov_name)
            if aov_tree:
                aov_prop = octane_view_layer.render_aov_node_graph_property
                aov_prop.render_pass_style = "RENDER_AOV_GRAPH"
                aov_prop.node_tree = aov_tree
                print(f"🟢 Assigned AOV node tree: {aov_name}")
            else:
                print(f"⚠️ AOV node tree '{aov_name}' not found.")

            # Assign Compositing Node Tree
            comp_name = "Octane Toon Compositor"
            comp_tree = bpy.data.node_groups.get(comp_name)
            if comp_tree:
                comp_prop = octane_view_layer.composite_node_graph_property
                comp_prop.node_tree = comp_tree
                print(f"🟢 Assigned Compositing node tree: {comp_name}")
            else:
                print(f"⚠️ Compositing node tree '{comp_name}' not found.")
                
            # Enable Alpha Channel
            enable_alpha_channel_from_socket()
        
            # Force GUI update
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == "PROPERTIES":
                        area.tag_redraw()

            self.report({'INFO'}, "AOV and Compositing node trees assigned.")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to assign AOV/Compositing: {e}")
            return {'CANCELLED'}



class OBJECT_OT_add_toon_light(bpy.types.Operator):
    bl_idname = "object.add_toon_light"
    bl_label = "Add Toon Light"
    bl_description = "Add an Octane directional toon light to the scene."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            bpy.ops.octane.quick_add_octane_toon_directional_light()
            self.report({'INFO'}, "Octane Toon Directional Light added")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add Toon Light: {e}")
        return {'FINISHED'}


class VIEW3D_PT_octane_toon_edges(bpy.types.Panel):
    bl_label = "Toon Edges"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Octane'
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        props = context.scene.toon_edge_settings

        layout.operator("object.setup_toon_edges", icon='MOD_WIREFRAME')
        layout.operator("object.remove_toon_edges", icon='TRASH')
        layout.operator("object.assign_octane_nodes", icon='NODETREE')
        layout.operator("object.add_toon_light", icon='LIGHT_SUN')
        layout.prop(context.scene, "asset_blend_path")
        layout.separator()

        box = layout.box()
        row = box.row()
        row.prop(props, "show_edge_creation_options", text="", icon="TRIA_DOWN" if props.show_edge_creation_options else "TRIA_RIGHT", emboss=False)
        row.label(text="Edge Creation Options", icon='MODIFIER')
        if props.show_edge_creation_options:
            box.prop(props, "shading_mode")
            box.prop(props, "preserve_custom_normals")
            box.prop(props, "preserve_edge_thickness")
            box.prop(props, "edge_thickness_value")
            box.operator("object.set_thickness_on_selected", icon='MOD_SOLIDIFY')
            box.prop(props, "outline_thickness_value")
        layout.separator()
        
        box = layout.box()
        row = box.row()
        row.prop(props, "show_global_thickness", text="", icon="TRIA_DOWN" if props.show_global_thickness else "TRIA_RIGHT", emboss=False)
        row.label(text="Global Thickness Controls", icon='TOOL_SETTINGS')
        if props.show_global_thickness:
            box.prop(props, "global_outline_thickness")
            box.prop(props, "global_edge_thickness")


class OBJECT_OT_assign_octane_nodes(bpy.types.Operator):
    bl_idname = "object.assign_octane_nodes"
    bl_label = "Assign AOV/Compositing"
    bl_description = "Assign Octane AOV/Compositing trees and enable alpha in kernel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        AOV_NODE_NAME = "Octane_Toon_AOVs"
        COMP_NODE_NAME = "Octane Toon Compositor"
        KERNEL_ALPHA_INPUT_INDEX = {
            "Direct lighting kernel": 18,
            "Path tracing kernel": 17,
            "Photon tracing kernel": 24,
            "PMC kernel": 17,
        }

        try:
            view_layer = bpy.context.view_layer
            octane_view_layer = view_layer.octane
            octane_view_layer.render_pass_style = "RENDER_AOV_GRAPH"

            # === Auto-import se mancano ===
            if not bpy.data.node_groups.get(AOV_NODE_NAME) or not bpy.data.node_groups.get(COMP_NODE_NAME):
                addon = bpy.context.preferences.addons.get(__name__)
                prefs = addon.preferences
                blend_path = os.path.join(bpy.path.abspath(context.scene.asset_blend_path), "Octane_Edge_Tools_Assets.blend")
                if os.path.exists(blend_path):
                    try:
                        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                            if AOV_NODE_NAME in data_from.node_groups:
                                data_to.node_groups.append(AOV_NODE_NAME)
                                print(f"📥 Imported AOV node group: {AOV_NODE_NAME}")
                            if COMP_NODE_NAME in data_from.node_groups:
                                data_to.node_groups.append(COMP_NODE_NAME)
                                print(f"📥 Imported Compositor node group: {COMP_NODE_NAME}")
                    except Exception as e:
                        self.report({'ERROR'}, f"Error loading node trees from asset file: {e}")
                        return {'CANCELLED'}

            # === Prosegui con assegnazione
            aov_tree = bpy.data.node_groups.get(AOV_NODE_NAME)
            if aov_tree:
                octane_view_layer.render_aov_node_graph_property.node_tree = aov_tree
                self.report({'INFO'}, f"Assigned AOV: {AOV_NODE_NAME}")
            else:
                self.report({'WARNING'}, f"AOV node tree '{AOV_NODE_NAME}' not found.")

            comp_tree = bpy.data.node_groups.get(COMP_NODE_NAME)
            if comp_tree:
                octane_view_layer.composite_node_graph_property.node_tree = comp_tree
                self.report({'INFO'}, f"Assigned Compositor: {COMP_NODE_NAME}")
            else:
                self.report({'WARNING'}, f"Compositing node tree '{COMP_NODE_NAME}' not found.")

            # === Attiva Alpha Channel nel kernel
            kernel_tree = bpy.context.scene.octane.kernel_node_graph_property.node_tree
            if kernel_tree:
                for node in kernel_tree.nodes:
                    alpha_index = KERNEL_ALPHA_INPUT_INDEX.get(node.name)
                    if alpha_index is not None and len(node.inputs) > alpha_index:
                        try:
                            node.inputs[alpha_index].default_value = True
                            self.report({'INFO'}, f"Enabled alpha: {kernel_tree.name} → {node.name} (input[{alpha_index}]: '{node.inputs[alpha_index].name}')")
                            break
                        except Exception as e:
                            self.report({'WARNING'}, f"Error on '{node.name}': {e}")
                else:
                    self.report({'ERROR'}, "No valid kernel node found.")
            else:
                self.report({'ERROR'}, "No kernel node tree active.")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Unexpected error: {e}")
            return {'CANCELLED'}




classes = (
    OBJECT_OT_add_toon_light,
    ToonEdgeSettings,
    OBJECT_OT_setup_toon_edges,
    OBJECT_OT_set_thickness_on_selected,
    OBJECT_OT_remove_toon_edges,
    OBJECT_OT_assign_octane_nodes,
    VIEW3D_PT_octane_toon_edges,
)



def register():
    bpy.app.handlers.load_post.append(restore_cached_asset_path)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.toon_edge_settings = bpy.props.PointerProperty(type=ToonEdgeSettings)
    bpy.types.Scene.asset_blend_path = bpy.props.StringProperty(
    name="Asset File Path",
    subtype='FILE_PATH',
    description="Path to Octane Edge Tools asset .blend file",
    update=update_asset_path
)



import os
import json

def save_asset_path(path):
    cache_file = os.path.join(os.path.expanduser("~"), ".octane_edge_tools_path.json")
    try:
        with open(cache_file, "w") as f:
            json.dump({"asset_path": path}, f)
        print(f"✅ Saved asset path: {path}")
    except Exception as e:
        print(f"❌ Failed to save asset path: {e}")
        
def load_asset_path():
    cache_file = os.path.join(os.path.expanduser("~"), ".octane_edge_tools_path.json")
    try:
        if os.path.isfile(cache_file):
            with open(cache_file, "r") as f:
                data = json.load(f)
            return data.get("asset_path", "")
    except Exception as e:
        print(f"❌ Failed to load cached asset path: {e}")
    return ""



def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.toon_edge_settings
    del bpy.types.Scene.asset_blend_path

# Funzione utile, ma non chiamata automaticamente
def enable_alpha_channel_from_socket():
    try:
        kernel_group = bpy.data.node_groups.get("Octane Kernel")
        if not kernel_group:
            print("❌ Node group 'Octane Kernel' not found.")
            return

        for node in kernel_group.nodes:
            if "kernel" in node.name.lower():
                try:
                    node.inputs[17].default_value = True
                    print(f"✅ Alpha Channel attivato in '{node.name}' (input[17])")
                    return
                except Exception as e:
                    print(f"⚠️ Errore su nodo '{node.name}': {e}")
                    continue

        print("❌ Nessun nodo kernel compatibile trovato nel gruppo.")
    except Exception as e:
        print(f"❌ Errore durante la modifica: {e}")


import bpy
from bpy.app.handlers import persistent

@persistent
def restore_cached_asset_path(dummy):
    cached_path = load_asset_path()
    if cached_path:
        bpy.context.scene.asset_blend_path = cached_path
        print(f"📂 Cached path restored after load: {cached_path}")
