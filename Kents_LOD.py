import bpy
import bmesh
import webbrowser

bl_info = {
    "name": "Kent's LOD Maker",
    "author": "Kent Espejon",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "View3D",
    "description": "A tool for creating LOD (Level of Detail) models in Blender.",
    "warning": "",
    "wiki_url": "",
    "category": "Mesh"
}

# Properties for decimation ratios



bpy.types.Scene.lod1_ratio = bpy.props.FloatProperty(
    name="LOD1 Ratio",
    description="The lower the number, the more face will dissolve. Default value for LOD 1 is 0.2",
    default=0.2,
    min=0.0,
    max=1.0
)

bpy.types.Scene.lod2_ratio = bpy.props.FloatProperty(
    name="LOD2 Ratio",
    description="The lower the number, the more face will dissolve. Default value for LOD 1 is 0.5",
    default=0.5,
    min=0.0,
    max=1.0
)

bpy.types.Scene.lod3_ratio = bpy.props.FloatProperty(
    name="LOD3 Ratio",
    description="The lower the number, the more face will dissolve. Default value for LOD 1 is 0.7",
    default=0.7,
    min=0.0,
    max=1.0
)


class LODMaker(bpy.types.Operator):
    """Create an LOD out of the object selected"""
    bl_idname = "mesh.lod_operator"
    bl_label = "LOD"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = bpy.context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}

        obj = selected_objects[0]  # Get the first selected object
        bpy.ops.object.shade_smooth(use_auto_smooth=True)

        # Check if LOD already exists
        existing_lod_suffixes = ["_LOD0", "_LOD1", "_LOD2", "_LOD3"]
        for suffix in existing_lod_suffixes:
            if obj.name.endswith(suffix):
                self.report({'WARNING'}, "Object already has LOD")
                return {'CANCELLED'}

        # Check the point count of the object
        point_count = len(obj.data.vertices)
        if point_count < 10:
            self.report({'WARNING'}, "Object cannot be decimated further")
            return {'CANCELLED'}

        # Rename the original object with "_LOD0" suffix
        obj.name += "_LOD0"

        original_points = point_count  # Store the total point count

        # Copy and paste the original object for LOD1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.duplicate(linked=False)
        copied_obj = bpy.context.active_object
        copied_obj.name = obj.name.replace("_LOD0", "_LOD1")

        # Get the decimation ratios from the scene properties
        lod1_ratio = context.scene.lod1_ratio
        lod2_ratio = context.scene.lod2_ratio
        lod3_ratio = context.scene.lod3_ratio

        # Calculate point counts for LOD2 and LOD3 based on the remaining points
        lod2_points = int(original_points * (1 - lod1_ratio))
        lod3_points = int(original_points * (1 - lod2_ratio))

        # Apply decimate modifier to LOD1 object
        bpy.context.view_layer.objects.active = copied_obj
        bpy.ops.object.modifier_add(type='DECIMATE')
        bpy.context.object.modifiers["Decimate"].ratio = lod1_ratio
        bpy.ops.object.modifier_apply(modifier="Decimate")
        bpy.ops.object.shade_smooth(use_auto_smooth=True)

        # Copy and paste LOD1 object for LOD2
        bpy.context.view_layer.objects.active = copied_obj
        bpy.ops.object.select_all(action='DESELECT')
        copied_obj.select_set(True)
        bpy.ops.object.duplicate(linked=False)
        copied_obj2 = bpy.context.active_object
        copied_obj2.name = copied_obj.name.replace("_LOD1", "_LOD2")

        # Apply decimate modifier to LOD2 object
        bpy.context.view_layer.objects.active = copied_obj2
        bpy.ops.object.modifier_add(type='DECIMATE')
        bpy.context.object.modifiers["Decimate"].ratio = 1 - (lod2_points / original_points)
        bpy.ops.object.modifier_apply(modifier="Decimate")
        bpy.ops.object.shade_smooth(use_auto_smooth=True)

        # Copy and paste LOD2 object for LOD3
        bpy.context.view_layer.objects.active = copied_obj2
        bpy.ops.object.select_all(action='DESELECT')
        copied_obj2.select_set(True)
        bpy.ops.object.duplicate(linked=False)
        copied_obj3 = bpy.context.active_object
        copied_obj3.name = copied_obj2.name.replace("_LOD2", "_LOD3")

        # Apply decimate modifier to LOD3 object
        bpy.context.view_layer.objects.active = copied_obj3
        bpy.ops.object.modifier_add(type='DECIMATE')
        bpy.context.object.modifiers["Decimate"].ratio = 1 - (lod3_points / original_points)
        bpy.ops.object.modifier_apply(modifier="Decimate")
        bpy.ops.object.shade_smooth(use_auto_smooth=True)

        # Check face count of each LOD and perform necessary actions
        lods = [copied_obj, copied_obj2, copied_obj3]
        delete_lods = False
        for lod in lods:
            face_count = len(lod.data.polygons)
            if face_count < 4:
                self.report({'WARNING'}, f"Face count of {lod.name} is less than 4. Try Adjusting the LOD Ratio or change the object")
                delete_lods = True
                break

        if delete_lods:
            obj.name = obj.name.replace("_LOD0", "")
            bpy.data.objects.remove(copied_obj, do_unlink=True)
            bpy.data.objects.remove(copied_obj2, do_unlink=True)
            bpy.data.objects.remove(copied_obj3, do_unlink=True)
        else:
            # Hide LOD1, LOD2, and LOD3
            copied_obj.hide_set(True)
            copied_obj2.hide_set(True)
            copied_obj3.hide_set(True)
            
        
            self.report({'INFO'}, "LOD creation successful")


        return {'FINISHED'}


def open_survey():
    survey_url = "https://docs.google.com/forms/d/e/1FAIpQLSclA-ubyspCmOJmyd8byfgmtxlVYSwtsq03zFIGf-9dmzZk8A/viewform?usp=sf_link"  # Replace with the actual URL of your survey
    webbrowser.open(survey_url)


class CreateLODPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kent LOD"
    bl_label = "Create LOD"

    def draw(self, context):
        layout = self.layout

        # Create LOD button
        box = layout.box()
        box.operator("mesh.lod_operator", text="Create LOD")

        # LOD ratio inputs
        box = layout.box()
        box.prop(context.scene, "lod1_ratio", text="LOD1 Ratio", slider=False)
        box.prop(context.scene, "lod2_ratio", text="LOD2 Ratio", slider=False)
        box.prop(context.scene, "lod3_ratio", text="LOD3 Ratio", slider=False)
        
        box = layout.box()
        box.operator("mesh.revert_lod_operator", text="Revert Mesh")

class ShowLODPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kent LOD"
    bl_label = "Show LOD"

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()

        # Show LOD buttons
        row = box.row()
        row.operator("mesh.show_lod0_operator", text="LOD0")
        row.operator("mesh.show_lod1_operator", text="LOD1")


        row = box.row()
        row.operator("mesh.show_lod2_operator", text="LOD2")
        row.operator("mesh.show_lod3_operator", text="LOD3")

        
class SurveyPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kent LOD"
    bl_label = "Survey"

    def draw(self, context):
        layout = self.layout

        # Open survey button
        layout.operator("mesh.open_survey_operator", text="Rate this Add-on")




class ShowLOD0Operator(bpy.types.Operator):
    """Show LOD"""
    bl_idname = "mesh.show_lod0_operator"
    bl_label = "Show LOD0"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Find LOD0 object
        lod0_obj = None
        for obj in bpy.data.objects:
            if obj.name.endswith("_LOD0"):
                lod0_obj = obj
                break

        if lod0_obj is None:
            self.report({'WARNING'}, "No LOD0 object found")
            return {'CANCELLED'}

        # Hide LOD1, LOD2, and LOD3 objects
        for obj in bpy.data.objects:
            if obj.name.endswith("_LOD1") or obj.name.endswith("_LOD2") or obj.name.endswith("_LOD3"):
                obj.hide_set(True)

        # Show LOD0 object
        lod0_obj.hide_set(False)

        return {'FINISHED'}


class ShowLOD1Operator(bpy.types.Operator):
    """Show LOD1"""
    bl_idname = "mesh.show_lod1_operator"
    bl_label = "Show LOD1"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Find LOD1 object
        lod1_obj = None
        for obj in bpy.data.objects:
            if obj.name.endswith("_LOD1"):
                lod1_obj = obj
                break

        if lod1_obj is None:
            self.report({'WARNING'}, "No LOD1 object found")
            return {'CANCELLED'}

        # Hide LOD0, LOD2, and LOD3 objects
        for obj in bpy.data.objects:
            if obj.name.endswith("_LOD0") or obj.name.endswith("_LOD2") or obj.name.endswith("_LOD3"):
                obj.hide_set(True)

        # Show LOD1 object
        lod1_obj.hide_set(False)

        return {'FINISHED'}


class ShowLOD2Operator(bpy.types.Operator):
    """Show LOD2"""
    bl_idname = "mesh.show_lod2_operator"
    bl_label = "Show LOD2"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Find LOD2 object
        lod2_obj = None
        for obj in bpy.data.objects:
            if obj.name.endswith("_LOD2"):
                lod2_obj = obj
                break

        if lod2_obj is None:
            self.report({'WARNING'}, "No LOD2 object found")
            return {'CANCELLED'}

        # Hide LOD0, LOD1, and LOD3 objects
        for obj in bpy.data.objects:
            if obj.name.endswith("_LOD0") or obj.name.endswith("_LOD1") or obj.name.endswith("_LOD3"):
                obj.hide_set(True)

        # Show LOD2 object
        lod2_obj.hide_set(False)

        return {'FINISHED'}


class ShowLOD3Operator(bpy.types.Operator):
    """Show LOD3"""
    bl_idname = "mesh.show_lod3_operator"
    bl_label = "Show LOD3"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Find LOD3 object
        lod3_obj = None
        for obj in bpy.data.objects:
            if obj.name.endswith("_LOD3"):
                lod3_obj = obj
                break

        if lod3_obj is None:
            self.report({'WARNING'}, "No LOD3 object found")
            return {'CANCELLED'}

        # Hide LOD0, LOD1, and LOD2 objects
        for obj in bpy.data.objects:
            if obj.name.endswith("_LOD0") or obj.name.endswith("_LOD1") or obj.name.endswith("_LOD2"):
                obj.hide_set(True)

        # Show LOD3 object
        lod3_obj.hide_set(False)

        return {'FINISHED'}

class OpenSurveyOperator(bpy.types.Operator):
    """Click to rate this plugin"""
    bl_idname = "mesh.open_survey_operator"
    bl_label = "Open Survey"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        open_survey()
        return {'FINISHED'}
    
# Operator to revert the selected object to its original state
class RevertLODOperator(bpy.types.Operator):
    """Revert the selected object to its original state"""
    bl_idname = "mesh.revert_lod_operator"
    bl_label = "Revert LOD"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = bpy.context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "No object selected. Select object with _LOD0 in it")
            return {'CANCELLED'}

        obj = selected_objects[0]  # Get the first selected object

        # Check if the object is an LOD
        if "_LOD" not in obj.name:
            self.report({'WARNING'}, "Object is not an LOD")
            return {'CANCELLED'}
        
        if "_LOD0" not in obj.name:
            self.report({'WARNING'}, "Select the LOD0 to revert")
            return {'CANCELLED'}

        # Remove the LOD suffix from the object's name
        obj.name = obj.name.replace("_LOD0", "")

        # Delete all LOD objects
        for suffix in ["_LOD0", "_LOD1", "_LOD2", "_LOD3"]:
            lod_obj = bpy.data.objects.get(obj.name + suffix)
            if lod_obj is not None:
                bpy.data.objects.remove(lod_obj, do_unlink=True)

        # Unhide the original object
        obj.hide_set(False)

        self.report({'INFO'}, "LOD reverted successfully")
        return {'FINISHED'}
    
# Registration

classes = (
    LODMaker,
    CreateLODPanel,
    ShowLODPanel,
    SurveyPanel,
    ShowLOD0Operator,
    ShowLOD1Operator,
    ShowLOD2Operator,
    ShowLOD3Operator,
    OpenSurveyOperator,
    RevertLODOperator

)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
