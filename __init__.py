#!BPY
# -*- coding: utf-8 -*-

import os.path
from math import radians
import bpy, mathutils
from bpy_extras.io_utils import ImportHelper
from . import valkyria

bl_info = {
        "name": "Valkyria Chronicles (.MLX, .HMD)", # ABR, MMF to come?
        "description": "Imports model files from Valkyria Chronicles (PS3)",
        "author": "Chrrox, Gomtuu",
        "version": (0, 5),
        "blender": (2, 63, 0),
        "location": "File > Import",
        "warning": "",
        "category": "Import-Export",
        }


class Texture_Pack:
    def __init__(self):
        self.htsf_images = []

    def add_image(self, htsf, filename):
        image = HTSF_Image(htsf)
        image.filename = filename + ".dds"
        self.htsf_images.append(image)
        return image

    def build_blender(self):
        for image in self.htsf_images:
            image.build_blender()


class HTEX_Pack:
    def __init__(self, source_file, htex_id):
        self.F = source_file
        self.htex_id = htex_id
        self.htsf_images = []

    def add_image(self, htsf):
        htsf_id = len(self.htsf_images)
        image = HTSF_Image(htsf)
        image.filename = "HTEX-{:03}-HTSF-{:03}.dds".format(self.htex_id, htsf_id)
        self.htsf_images.append(image)
        return image

    def read_data(self):
        for htsf in self.F.HTSF:
            image = self.add_image(htsf)
            image.read_data()

    def build_blender(self):
        for image in self.htsf_images:
            image.build_blender()


class HTSF_Image:
    def __init__(self, source_file):
        self.F = source_file
        assert len(self.F.DDS) == 1
        self.dds = self.F.DDS[0]
        self.dds_data = None

    def write_tmp_dds(self, dds_path):
        tmp_dds = open(dds_path, 'wb')
        tmp_dds.write(self.dds.data)
        tmp_dds.close()

    def build_blender(self):
        from bpy_extras.image_utils import load_image
        tempdir = bpy.app.tempdir
        dds_path = os.path.join(tempdir, self.filename)
        self.write_tmp_dds(dds_path)
        # TODO: Create alpha and non-alpha versions
        self.image = load_image(dds_path)
        self.image.pack()
        os.remove(dds_path)

    def read_data(self):
        self.dds.read_data()


class MXTL_List:
    def __init__(self, source_file):
        self.F = source_file
        self.texture_packs = []

    def read_data(self):
        self.F.read_data()
        self.texture_lists = self.F.texture_lists


class IZCA_Model:
    def __init__(self, source_file):
        self.F = source_file
        self.texture_packs = []
        self.shape_key_sets = []
        self.hmdl_models = []

    def add_hshp(self, hshp):
        hshp_id = len(self.shape_key_sets)
        shape_key_set = HSHP_Key_Set(hshp, hshp_id)
        self.shape_key_sets.append(shape_key_set)
        return shape_key_set

    def add_htex(self, htex):
        htex_id = len(self.texture_packs)
        htex_pack = HTEX_Pack(htex, htex_id)
        self.texture_packs.append(htex_pack)
        return htex_pack

    def add_model(self, hmdl):
        model_id = len(self.hmdl_models)
        model = HMDL_Model(hmdl, model_id)
        self.hmdl_models.append(model)
        return model

    def read_data(self):
        if hasattr(self.F, 'HSHP'):
            for hshp in self.F.HSHP:
                shape_key_set = self.add_hshp(hshp)
                shape_key_set.read_data()
        if getattr(self.F, 'MXTL', False):
            # read HMDL/HTSF associations from MXTL
            mxtl = MXTL_List(self.F.MXTL[0])
            mxtl.read_data()
            for model_i, texture_list in enumerate(mxtl.texture_lists):
                texture_pack = Texture_Pack()
                for htsf_i, filename in texture_list:
                    htsf = texture_pack.add_image(self.F.HTSF[htsf_i], filename)
                    htsf.read_data()
                self.texture_packs.append(texture_pack)
                model = self.add_model(self.F.HMDL[model_i])
                model.read_data()
        else:
            # deduce HMDL/HTEX associations
            for hmd, htx in zip(self.F.HMDL, self.F.HTEX):
                htex_pack = self.add_htex(htx)
                htex_pack.read_data()
                model = self.add_model(hmd)
                model.read_data()

    def build_blender(self):
        for texture_pack, model in zip(self.texture_packs, self.hmdl_models):
            texture_pack.build_blender()
            model.build_blender()
            model.assign_materials(texture_pack.htsf_images)
        # Messed up: 3 6 8 9 11 13 25
        for shape_key_set in self.shape_key_sets:
            self.hmdl_models[1].build_shape_keys(shape_key_set)

    def finalize_blender(self):
        for model in self.hmdl_models:
            model.finalize_blender()


class HSHP_Key_Set:
    def __init__(self, source_file, shape_key_set_id):
        self.F = source_file
        self.shape_key_set_id = shape_key_set_id

    def read_data(self):
        self.F.read_data()
        self.shape_keys = self.F.shape_keys


class HMDL_Model:
    def __init__(self, source_file, model_id):
        self.F = source_file
        self.model_id = model_id
        self.kfmd_models = []

    def add_model(self, kfmd):
        model_id = len(self.kfmd_models)
        model = KFMD_Model(kfmd, model_id)
        self.kfmd_models.append(model)
        return model

    def read_data(self):
        for kfmd in self.F.KFMD:
            model = self.add_model(kfmd)
            model.read_data()

    def build_blender(self):
        self.empty = bpy.data.objects.new("HMDL-{:03d}".format(self.model_id), None)
        bpy.context.scene.objects.link(self.empty)
        for model in self.kfmd_models:
            model.build_blender()
            model.empty.parent = self.empty

    def assign_materials(self, texture_pack):
        for model in self.kfmd_models:
            model.build_materials(texture_pack)
            model.assign_materials()

    def build_shape_keys(self, shape_key_set):
        for model in self.kfmd_models:
            model.build_shape_keys(shape_key_set)

    def finalize_blender(self):
        for model in self.kfmd_models:
            model.finalize_blender()


class KFMD_Model:
    def __init__(self, source_file, model_id):
        self.F = source_file
        self.model_id = model_id
        self.kfms = self.F.KFMS[0]
        self.kfmg = self.F.KFMG[0]
        self.empty = None
        self.oneside = None

    def build_armature(self):
        armature = bpy.data.objects.new("Armature",
            bpy.data.armatures.new("ArmatureData"))
        scene = bpy.context.scene
        scene.objects.link(armature)
        scene.objects.active = armature
        armature.select = True
        bpy.ops.object.mode_set(mode = 'EDIT')
        for bone in self.bones:
            if 'deform_id' in bone:
                bone['name'] = "Bone-{:02x}".format(bone['deform_id'])
            else:
                bone['name'] = "Bone-{:02x}".format(bone['id'])
            if bone["parent"]:
                bone["accum_rotation"] = bone["parent"]["accum_rotation"]
                bone["head"] = bone["parent"]["head"] + bone["accum_rotation"] * mathutils.Vector(bone["location"])
                bone["accum_rotation"] *= mathutils.Quaternion(bone["rotation"])
            else:
                bone["accum_rotation"] = mathutils.Quaternion(bone["rotation"])
                bone["head"] = mathutils.Vector(bone["location"])
        for bone in self.bones:
            if bone["fav_child"]:
                bone["tail"] = bone["fav_child"]["head"]
            else:
                bone["tail"] = bone["head"] + bone["accum_rotation"] * mathutils.Vector((0.5, 0, 0))
            if bone["object_ptr1"] and bone["parent"]:
                bone["tail"] = bone["head"]
                bone["head"] = bone["parent"]["head"]
            bone["edit_bpy"] = armature.data.edit_bones.new(bone["name"])
            bone["edit_bpy"].use_connect = False
            if bone["parent"]:
                bone["edit_bpy"].parent = bone["parent"]["edit_bpy"]
            bone["edit_bpy"].head = bone["head"]
            bone["edit_bpy"].tail = bone["tail"]
        bpy.ops.object.mode_set(mode = 'OBJECT')
        return armature

    def build_meshes(self):
        for i, mesh_dict in enumerate(self.meshes):
            # Create mesh object
            mesh = bpy.data.meshes.new("MeshData-{:03d}".format(i))
            mesh_dict["bpy"] = bpy.data.objects.new("Mesh-{:03d}".format(i), mesh)
            bpy.context.scene.objects.link(mesh_dict['bpy'])
            mesh_dict["bpy"].parent = self.armature
            # Create vertices
            mesh.vertices.add(len(mesh_dict['vertices']))
            vertex_array = []
            for vertex in mesh_dict["vertices"]:
                vertex_array.append(vertex["location_x"])
                vertex_array.append(vertex["location_y"])
                vertex_array.append(vertex["location_z"])
            mesh.vertices.foreach_set("co", vertex_array)
            # Create faces
            mesh.tessfaces.add(len(mesh_dict['faces']))
            face_array = []
            for face in mesh_dict["faces"]:
                face_array.extend(face)
            mesh.tessfaces.foreach_set("vertices_raw", face_array)
            # Move accessories to proper places
            parent_bone_id = mesh_dict["object"]["parent_bone_id"]
            if parent_bone_id:
                parent_bone = self.bones[parent_bone_id]
                if parent_bone["name"] in self.armature.data.bones:
                    bone_quat = self.armature.data.bones[parent_bone["name"]].matrix_local.to_quaternion()
                    mesh_quat = mesh_dict["bpy"].matrix_world.to_quaternion()
                    axis_correction = bone_quat.rotation_difference(mesh_quat)
                    mesh_dict["bpy"].rotation_mode = 'QUATERNION'
                    mesh_dict["bpy"].rotation_quaternion = axis_correction * parent_bone["accum_rotation"]
                    mesh_dict["bpy"].parent_type = 'BONE'
                    mesh_dict["bpy"].parent_bone = parent_bone["name"]
            else:
                mesh_dict["bpy"].parent_type = 'ARMATURE'

    def assign_vertex_groups(self):
        for mesh in self.meshes:
            for local_id, vertex_list in mesh["vertex_groups"].items():
                global_id = mesh["vertex_group_map"][local_id]
                vgroup_name = "Bone-{:02x}".format(global_id)
                if vgroup_name in mesh["bpy"].vertex_groups:
                    vgroup = mesh["bpy"].vertex_groups[vgroup_name]
                else:
                    vgroup = mesh["bpy"].vertex_groups.new(vgroup_name)
                for vertex_id, weight in vertex_list:
                    vgroup.add([vertex_id], weight, 'ADD')

    def build_blender(self):
        self.empty = bpy.data.objects.new("KFMD-{:03d}".format(self.model_id), None)
        bpy.context.scene.objects.link(self.empty)
        self.armature = self.build_armature()
        self.armature.parent = self.empty
        self.build_meshes()
        if self.kfmg.bytes_per_vertex == 0x30:
            self.assign_vertex_groups()

    def index_vertex_groups(self):
        # TODO: This function and assign_vertex_groups might be a little
        # excessive. Consider doing this all directly when building the mesh.
        for mesh in self.meshes:
            vertex_groups = {}
            for i, vertex in enumerate(mesh["vertices"]):
                if vertex["vertex_group_1"] not in vertex_groups:
                    vertex_groups[vertex["vertex_group_1"]] = []
                vertex_groups[vertex["vertex_group_1"]].append([i, vertex["vertex_group_weight_1"]])
                if vertex["vertex_group_2"] not in vertex_groups:
                    vertex_groups[vertex["vertex_group_2"]] = []
                vertex_groups[vertex["vertex_group_2"]].append([i, vertex["vertex_group_weight_2"]])
            mesh["vertex_groups"] = vertex_groups

    def read_data(self):
        self.F.read_data()
        self.bones = self.F.bones
        self.materials = self.F.materials
        self.meshes = self.F.meshes
        self.textures = self.F.textures
        if self.kfmg.bytes_per_vertex == 0x30:
            self.index_vertex_groups()

    def create_oneside(self):
        self.oneside = bpy.data.textures.new("OneSide", type='BLEND')
        self.oneside.use_color_ramp = True
        self.oneside.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        self.oneside.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        element0 = self.oneside.color_ramp.elements.new(0.5)
        element0.color = (0.0, 0.0, 0.0, 1.0)
        element1 = self.oneside.color_ramp.elements.new(0.501)
        element1.color = (1.0, 1.0, 1.0, 1.0)

    def build_materials(self, texture_pack):
        for ptr, texture_dict in self.textures.items():
            # TODO: Consider doing this another way.
            name = "Texture-{:04x}".format(ptr)
            texture_dict["bpy"] = bpy.data.textures.new(name, type = 'IMAGE')
            texture_dict["bpy"].image = texture_pack[texture_dict["image"]].image
            texture_dict["bpy"].use_alpha = False
            texture_dict["bpy_alpha"] = bpy.data.textures.new(name + "-alpha", type = 'IMAGE')
            texture_dict["bpy_alpha"].image = texture_pack[texture_dict["image"]].image
            texture_dict["bpy_alpha"].use_alpha = True
            texture_dict["bpy_normal"] = bpy.data.textures.new(name + "-normal", type = 'IMAGE')
            texture_dict["bpy_normal"].image = texture_pack[texture_dict["image"]].image
            texture_dict["bpy_normal"].use_alpha = False
            texture_dict["bpy_normal"].use_normal_map = True
        for ptr, material_dict in self.materials.items():
            name = "Material-{:04x}".format(ptr)
            material_dict["bpy"] = material = bpy.data.materials.new(name)
            material.game_settings.use_backface_culling = material_dict["use_backface_culling"]
            material.specular_intensity = 0.0
            if material_dict["texture_ptr"]:
                slot0 = material.texture_slots.add()
                slot0.texture_coords = 'UV'
                if material_dict["use_alpha"]:
                    slot0.texture = material_dict["texture"]["bpy_alpha"]
                    slot0.use_map_alpha = True
                    slot0.alpha_factor = 1.0
                else:
                    slot0.texture = material_dict["texture"]["bpy"]
            if material_dict["use_alpha"]:
                material.use_transparency = True
                material.transparency_method = 'Z_TRANSPARENCY'
                material.alpha = 0.0
            if material_dict["normal_ptr"]:
                slot1 = material.texture_slots.add()
                slot1.texture_coords = 'UV'
                slot1.texture = material_dict["normal"]["bpy_normal"]
                slot1.use_map_color_diffuse = False
                slot1.use_map_normal = True
            if material_dict["use_backface_culling"]:
                slot2 = material.texture_slots.add()
                if self.oneside is None:
                    self.create_oneside()
                slot2.texture = self.oneside
                slot2.texture_coords = 'NORMAL'
                slot2.use_map_color_diffuse = False
                slot2.use_map_alpha = True
                slot2.mapping_x = 'Z'
                slot2.mapping_y = 'NONE'
                slot2.mapping_z = 'NONE'
                slot2.default_value = 0.0
                slot2.use_rgb_to_intensity = True

    def assign_materials(self):
        for mesh in self.meshes:
            material = self.materials[mesh["object"]["material_ptr"]]["bpy"]
            mesh["bpy"].data.materials.append(material)
            if hasattr(material.texture_slots[0], "texture"):
                mesh["bpy"].data.uv_textures.new()
                uv_faces = mesh["bpy"].data.tessface_uv_textures.active.data[:]
                image = material.texture_slots[0].texture.image
                for i, face in enumerate(mesh["faces"]):
                    mesh["bpy"].data.tessfaces[i].use_smooth = 1
                    uv_faces[i].uv1 = (mesh["vertices"][face[0]]["u"], mesh["vertices"][face[0]]["v"] + 1)
                    uv_faces[i].uv2 = (mesh["vertices"][face[1]]["u"], mesh["vertices"][face[1]]["v"] + 1)
                    uv_faces[i].uv3 = (mesh["vertices"][face[2]]["u"], mesh["vertices"][face[2]]["v"] + 1)
                    uv_faces[i].image = image

    def build_shape_keys(self, shape_key_set):
        scene = bpy.context.scene
        for mesh, shape_key in zip(self.meshes, shape_key_set.shape_keys):
            vertex_shift = len(mesh["bpy"].data.vertices) - len(shape_key["vertices"])
            if "bpy_dup_base" not in mesh:
                bpy.ops.object.select_all(action='DESELECT')
                scene.objects.active = mesh["bpy"]
                mesh["bpy"].select = True
                bpy.ops.object.duplicate()
                mesh["bpy_dup_base"] = scene.objects.active
            bpy.ops.object.select_all(action='DESELECT')
            scene.objects.active = mesh["bpy_dup_base"]
            mesh["bpy_dup_base"].select = True
            bpy.ops.object.duplicate()
            temp_object = scene.objects.active
            temp_object.name = "HSHP-{:02d}".format(shape_key_set.shape_key_set_id)
            for i, vertex in enumerate(shape_key["vertices"]):
                j = i + vertex_shift
                old = temp_object.data.vertices[j].co
                new = [old[0] + vertex["translate_x"],
                    old[1] + vertex["translate_y"],
                    old[2] + vertex["translate_z"],
                    ]
                temp_object.data.vertices[j].co = new
            scene.objects.active = mesh["bpy"]
            temp_object.select = True
            bpy.ops.object.join_shapes()
            bpy.ops.object.select_all(action='DESELECT')
            temp_object.select = True
            bpy.ops.object.delete()

    def finalize_blender(self):
        for mesh in self.meshes:
            mesh["bpy"].data.update()
            for i, mesh_vertex in enumerate(mesh["bpy"].data.vertices):
                dict_vertex = mesh["vertices"][i]
                mesh_vertex.normal = [dict_vertex["normal_x"], dict_vertex["normal_y"], dict_vertex["normal_z"]]
            if "bpy_dup_base" in mesh:
                bpy.ops.object.select_all(action='DESELECT')
                mesh["bpy_dup_base"].select = True
                bpy.ops.object.delete()


class ValkyriaScene:
    def __init__(self, source_file, name):
        self.source_file = source_file
        self.name = name
        self.layers_used = 0

    def layer_list(self, layer_num):
        max_layers = 20
        clamped_layer_num = layer_num % max_layers
        if clamped_layer_num + 1 > self.layers_used:
            self.layers_used = clamped_layer_num + 1
        layers_before = [False] * clamped_layer_num
        layers_after = [False] * (max_layers - 1 - clamped_layer_num)
        return layers_before + [True] + layers_after

    def create_scene(self, name):
        self.scene = bpy.data.scenes.new(name)
        for screen in bpy.data.screens:
            screen.scene = self.scene
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.viewport_shade = 'TEXTURED'
                            if hasattr(space, 'show_backface_culling'):
                                space.show_backface_culling = True
        self.scene.layers = self.layer_list(0)
        self.scene.game_settings.material_mode = 'GLSL'

    def create_lamp(self):
        lamp_data = bpy.data.lamps.new("Default Lamp", 'HEMI')
        lamp = bpy.data.objects.new("Default Lamp", lamp_data)
        lamp.layers = [True] * self.layers_used + [False] * (20 - self.layers_used)
        lamp.location = (0.0, 20.0, 15.0)
        lamp.rotation_mode = 'AXIS_ANGLE'
        lamp.rotation_axis_angle = (radians(-22.0), 1.0, 0.0, 0.0)
        self.scene.objects.link(lamp)
        self.scene.update()

    def read_data(self):
        self.source_file.read_data()

    def build_blender(self):
        self.create_scene(self.name)
        self.create_lamp()
        self.source_file.build_blender()
        self.source_file.finalize_blender()


class ImportValkyria(bpy.types.Operator, ImportHelper):
    bl_idname = 'import_scene.import_valkyria'
    bl_label = 'Valkyria Chronicles (.MLX, .HMD)' # ABR, MMF to come?
    filename_ext = "*.mlx"
    filter_glob = bpy.props.StringProperty(
            default = "*.mlx;*.hmd",
            options = {'HIDDEN'},
            )

    def import_file(self, filename):
        vfile = valkyria.files.valk_open(filename)[0]
        vfile.find_inner_files()
        if vfile.ftype == 'IZCA':
            model = IZCA_Model(vfile)
        elif vfile.ftype == 'HMDL':
            model = HMDL_Model(vfile, 0)
        scene_name = os.path.basename(filename)
        self.valk_scene = ValkyriaScene(model, scene_name)
        self.valk_scene.read_data()
        self.valk_scene.build_blender()

    def execute(self, context):
        self.import_file(self.filepath)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ImportValkyria.bl_idname)

def register():
    bpy.utils.register_class(ImportValkyria)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_class(ImportValkyria)
    bpy.types.INFO_MT_file_import.remove(menu_func)
