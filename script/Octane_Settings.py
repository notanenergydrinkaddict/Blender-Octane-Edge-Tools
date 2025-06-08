bl_info = {
    "name": "Set Octane Options",
    "blender": (4, 0, 2),
    "category": "3D View",
    "description": "Sets Octane Render options quickly.",
    "author": "Your Name",
    "version": (1, 0, 0),
    "location": "View3D > UI panel",
}

import bpy


class SetOctaneOptionsPanel(bpy.types.Panel):
    """Creates a Panel in the 3D view"""
    bl_label = "Set Octane Options"
    bl_idname = "VIEW3D_PT_set_octane_options"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Octane'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Create a custom button
        layout.operator("wm.set_octane_options", text="Set Octane Options")


class WM_OT_SetOctaneOptions(bpy.types.Operator):
    """Set Octane Options"""
    bl_label = "Set Octane Options"
    bl_idname = "wm.set_octane_options"

    def execute(self, context):
        set_octane_color_management_settings()
        set_octane_output_settings()
        set_video_output_settings()
        self.report({'INFO'}, "Octane Color Management and Output options set")
        set_octane_kernel()
        set_octane_environment()
        self.report({'INFO'}, "Octane Color Management, Output options, Octane Kernel and World set")
        return {'FINISHED'}


def set_octane_color_management_settings():

    # Set Render Engine to Octane
    bpy.context.scene.render.engine = 'octane'

    # Set the Display Device to sRGB
    bpy.context.scene.display_settings.display_device = 'sRGB'

    # Set the View Transform to Raw
    bpy.context.scene.view_settings.view_transform = 'Raw'

    # Set the Look to None
    bpy.context.scene.view_settings.look = 'None'

    # Set the Exposure to 0.0
    bpy.context.scene.view_settings.exposure = 0.0

    # Set the Gamma to 1.0
    bpy.context.scene.view_settings.gamma = 1.0

    # Set the Sequencer color space to sRGB
    bpy.context.scene.sequencer_colorspace_settings.name = 'sRGB'


def set_video_output_settings():
    # Set the output path
    bpy.context.scene.render.filepath = "/tmp"

    # Set the output format to FFmpeg Video
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'

    # Set the container format to MPEG4
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'

    # Set the video codec to H.264
    bpy.context.scene.render.ffmpeg.codec = 'H264'

    # Set the video quality to Medium
    bpy.context.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'

    # Set the encoding speed to Good
    bpy.context.scene.render.ffmpeg.ffmpeg_preset = 'GOOD'

    # Set the keyframe interval
    bpy.context.scene.render.ffmpeg.gopsize = 18

    # Set the maximum number of B-frames
    bpy.context.scene.render.ffmpeg.max_b_frames = 0


def set_octane_output_settings():
    # Set Octane pre and post-production options
    bpy.context.scene.octane.octane_export_prefix_tag = "FileName_"
    bpy.context.scene.octane.octane_export_postfix_tag = "$OCTANE_PASS$_$VIEW_LAYER$_###"

    # Set the type of image export
    bpy.context.scene.octane.export_type = 'EXPORT_SEPARATE_IMAGE_FILES'

    # Set the file type to PNG
    bpy.context.scene.render.image_settings.file_format = 'PNG'

    # Set the bit depth to 8-bit
    bpy.context.scene.render.image_settings.color_depth = '8'

    # Set the color space (this is an example, adjust as necessary)
    bpy.context.scene.render.image_settings.color_mode = 'RGB'

    # The following line is commented out because the property might be different or might not exist.
    # Please verify the correct property for Octane in Blender's Python API.
    # bpy.context.scene.octane_render_passes.beauty_pass = False


def set_octane_kernel():
    from octane.utils import consts, utility
    scene = bpy.context.scene
    octane_scene = scene.octane
    node_tree = bpy.data.node_groups.new(
        name=consts.OctanePresetNodeTreeNames.KERNEL,
        type=consts.OctaneNodeTreeIDName.KERNEL)
    node_tree.use_fake_user = True
    nodes = node_tree.nodes
    output = nodes.new("OctaneKernelOutputNode")
    kernel_node = nodes.new("OctanePathTracingKernel")
    output.location = (0, 0)
    if kernel_node:
        kernel_node.location = (-300, 0)
        node_tree.links.new(kernel_node.outputs[0], output.inputs[0])
    utility.beautifier_nodetree_layout_with_nodetree(node_tree, consts.OctaneNodeTreeIDName.KERNEL)
    octane_scene.kernel_data_mode = "NODETREE"
    octane_scene.kernel_node_graph_property.node_tree = node_tree


def set_octane_environment():
    from octane.nodes.base_node_tree import NodeTreeHandler
    scene = bpy.context.scene
    active_world = scene.world
    if active_world is None:
        active_world = bpy.data.worlds.new("OctaneWorld")
    if not active_world.use_nodes:
        active_world.use_nodes = True
    node_tree = active_world.node_tree
    NodeTreeHandler._on_world_new(node_tree, active_world, None, "OctaneDaylightEnvironment")


def register():
    bpy.utils.register_class(SetOctaneOptionsPanel)
    bpy.utils.register_class(WM_OT_SetOctaneOptions)


def unregister():
    bpy.utils.unregister_class(SetOctaneOptionsPanel)
    bpy.utils.unregister_class(WM_OT_SetOctaneOptions)


if __name__ == "__main__":
    register()
