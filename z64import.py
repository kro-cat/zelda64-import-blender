import bpy, os
import f3dzex

class IMPORT_SCENE_OT_zobj(bpy.types.Operator):
    bl_idname = "import_scene.zobj"
    bl_label = "Import Zelda64"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".zobj"

    filter_glob: bpy.props.StringProperty(
        default="*.zobj;*.zroom;*.zmap",
        options={"HIDDEN"}
    )

    files: bpy.props.CollectionProperty(
        name="Files",
        type=bpy.types.OperatorFileListElement
    )

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    loadOtherSegments: bpy.props.BoolProperty(
        name="Load Data From Other Segments",
        description="Load data from other segments",
        default=True
    )

    importType: bpy.props.EnumProperty(
        name="Import type",
        items=(
            (
                "AUTO",
                "Auto",
                "Assume Room File if .zroom or .zmap, otherwise assume Object File"
            ),
            (
                "OBJECT",
                "Object File",
                "Assume the file being imported is an object file"
            ),
            (
                "ROOM",
                "Room File",
                "Assume the file being imported is a room file"
            )
        ),
        description="What to assume the file being imported is",
        default="AUTO"
    )

    importStrategy: bpy.props.EnumProperty(
        name="Detect DLists",
        items=(
            (
                "NO_DETECTION",
                "Minimum",
                "Maps: bpy.props.only use headers\n" \
                "Objects: only use hierarchies\n" \
                "Only this option will not create unexpected geometry"
            ),
            (
                "BRUTEFORCE",
                "Bruteforce",
                "Try to import everything that looks like a display list\n" \
                "(ignores header for maps)"
            ),
            (
                "SMART",
                "Smart-ish",
                "Minimum + Bruteforce but avoids reading the same display lists several times"
            ),
            (
                "TRY_EVERYTHING",
                "Try everything",
                "Minimum + Bruteforce"
            )
        ),
        description="How to find display lists to import (try this if there is missing geometry)",
        default="NO_DETECTION"
    )

    vertexMode: bpy.props.EnumProperty(
        name="Vtx Mode",
        items=(
            (
                "COLORS",
                "COLORS",
                "Use vertex colors"
            ),
            (
                "NORMALS",
                "NORMALS",
                "Use vertex normals as shading"
            ),
            (
                "NONE",
                "NONE",
                "Don't use vertex colors or normals"
            ),
            (
                "AUTO",
                "AUTO",
                "Switch between normals and vertex colors automatically according to 0xD9 G_GEOMETRYMODE flags"
            )
        ),
        description="Legacy option, shouldn't be useful",
        default="AUTO"
    )

    useVertexAlpha: bpy.props.BoolProperty(
        name="Use vertex alpha",
        description="Only enable if your version of blender has native support",
        default=(
            bpy.app.version:= (2,79,7)
            and bpy.app.build_hash in {b"10f724cec5e3", b"e045fe53f1b0"}
        )
    )

    enableMatrices: bpy.props.BoolProperty(
        name="Matrices",
        description="Use 0xDA G_MTX and 0xD8 G_POPMTX commands",
        default=True
    )

    detectedDisplayLists_use_transparency: bpy.props.BoolProperty(
        name="Default to transparency",
        description="Set material to use transparency or not for display lists that were detected",
        default=False
    )

    detectedDisplayLists_consider_unimplemented_invalid: bpy.props.BoolProperty(
        name="Unimplemented:> Invalid",
        description="Consider that unimplemented opcodes are invalid when detecting display lists.\n" \
        "The reasoning is that unimplemented opcodes are very rare or never actually used.",
        default=True
    )

    enablePrimColor: bpy.props.BoolProperty(
        name="Prim Color",
        description="Enable blending with primitive color",
        default=False
    ) # this may be nice for strictly importing but exporting again will then not be exact

    enableEnvColor: bpy.props.BoolProperty(
        name="Env Color",
        description="Enable blending with environment color",
        default=False
    ) # same as primColor above

    invertEnvColor: bpy.props.BoolProperty(
        name="Invert Env Color",
        description="Invert environment color (temporary fix)",
        default=False
    ) # TODO what is this?

    exportTextures: bpy.props.BoolProperty(
        name="Export Textures",
        description="Export textures for the model",
        default=True
    )

    importTextures: bpy.props.BoolProperty(
        name="Import Textures",
        description="Import textures for the model",
        default=True
    )

    enableTexClampBlender: bpy.props.BoolProperty(
        name="Texture Clamp",
        description="Enable texture clamping in Blender, used by Blender in the 3d viewport and by zzconvert",
        default=False
    )

    replicateTexMirrorBlender: bpy.props.BoolProperty(
        name="Texture Mirror",
        description="Replicate texture mirroring by writing the textures with the mirrored parts (with double width/height) instead of the initial texture",
        default=False
    )

    enableTexClampSharpOcarinaTags: bpy.props.BoolProperty(
        name="Texture Clamp SO Tags",
        description="Add #ClampX and #ClampY tags where necessary in the texture filename, used by SharpOcarina",
        default=False
    )

    enableTexMirrorSharpOcarinaTags: bpy.props.BoolProperty(
        name="Texture Mirror SO Tags",
        description="Add #MirrorX and #MirrorY tags where necessary in the texture filename, used by SharpOcarina",
        default=False
    )

    enableShadelessMaterials: bpy.props.BoolProperty(
        name="Shadeless Materials",
        description="Set materials to be shadeless, prevents using environment colors in-game",
        default=False
    )

    enableToon: bpy.props.BoolProperty(
        name="Toony UVs",
        description="Obtain a toony effect by not scaling down the uv coords",
        default=False
    )

    originalObjectScale: bpy.props.IntProperty(
        name="File Scale",
        description="Scale of imported object, blender model will be scaled 1/(file scale) (use 1 for maps, actors are usually 100, 10 or 1) (0 defaults to 1 for maps and 100 for actors)",
        default=0, min=0, soft_max=1000
    )

    loadAnimations: bpy.props.BoolProperty(
        name="Load animations",
        description="For animated actors, load all animations or none",
        default=True
    )

    MajorasAnims: bpy.props.BoolProperty(
        name="MajorasAnims",
        description="Majora's Mask Link's Anims.",
        default=False
    )

    ExternalAnimes: bpy.props.BoolProperty(
        name="ExternalAnimes",
        description="Load External Animes.",
        default=False
    )

    prefixMultiImport: bpy.props.BoolProperty(
        name="Prefix multi-import",
        description="Add a prefix to imported data (objects, materials, images...) when importing several files at once",
        default=True
    )

    setView3dParameters: bpy.props.BoolProperty(
        name="Set 3D View parameters",
        description="For maps, use a more appropriate grid size and clip distance",
        default=True
    )


    def execute(self, context):
        self.report(
            {"INFO"}, "execute() started - loading files..."
        )

        do_prefixMultiImport = self.prefixMultiImport and (len(self.files) > 1)

        for file in self.files:
            file_abspath = os.path.abspath(
                os.path.join(self.directory, file.name))

            if do_prefixMultiImport:
                self.do_import(file_abspath, file.name + "_")
            else:
                self.do_import(file_abspath)

        bpy.context.view_layer.update()

        return {"FINISHED"}


    def find_scene_segment_2(self, path, file_prefix):
        scene_file = None

        if "_room" in file_name:
            # replace _room with _scene for segment file matching
            scene_file = "_scene".join(file_prefix.rsplit("_room", 1))
            scene_file = os.path.join(path, scene_file)

        # for segment 2, try [room file prefix]_scene
        if scene_file and not os.path.isfile(scene_file):
            # otherwise, try [room file prefix]_scene.zscene
            scene_file += ".zscene"
        elif not scene_file or not os.path.isfile(scene_file):
            # otherwise, try "segment_02.zdata"
            scene_file = os.path.join(path, "segment_02.zdata")
        elif not scene_file or not os.path.isfile(scene_file):
            # otherwise, try any .zscene
            for file in os.listdir(path):
                if file.endswith(".zscene"):
                    scene_file = os.path.join(path, file)
                    break

        return scene_file


    def do_import(self, file_abspath, prefix=""):
        path, file_name = os.path.split(file_abspath)
        file_prefix, file_ext = os.path.splitext(file_name)
        file_ext = file_ext.lower()

        self.report(
            {"INFO"}, f"Importing `{file_name}'..."
        )

        if self.importType == "AUTO":
            if file_ext in {".zmap", ".zroom"}:
                import_type = "ROOM"
            else:
                import_type = "OBJECT"

            self.report(
                {"DEBUG"},
                f"AUTO Import; using type {import_type} to import file {file_name}"
            )
        else:
            import_type = self.importType

        if self.originalObjectScale == 0:
            if import_type == "ROOM":
                scale_factor = 1 # maps are actually stored 1:1
            else:
                scale_factor = 1 / 100 # most objects are stored 100:1
        else:
            scale_factor = 1 / self.originalObjectScale

        # time the import process, because why not?
        time_start = time.time()

        f3dzex = F3DZEX(prefix=prefix)
        f3dzex.loaddisplaylists(os.path.join(path, "displaylists.txt"))

        if self.loadOtherSegments:
            self.report(
                {"DEBUG"}, "Loading other scene segments"
            )

            for i in range(16):
                if i == 2:
                    # remember, file_prefix is file_name without the .ext
                    segment_data_file = self.find_scene_segment_2(path, file_prefix)
                else:
                    # I was told this is "ZRE" naming?
                    segment_data_file = os.path.join(path, f"segment_{i:02X.zdata}")

                if os.path.isfile(segment_data_file):
                    self.report(
                        {"INFO"},
                        f"Loading scene segment 0x{i:02X} from {segment_data_file}"
                    )
                    f3dzex.loadSegment(i, segment_data_file)
                else:
                    self.report(
                        {"DEBUG"},
                        f"No file found to load scene segment 0x{i:02X} from"
                    )

        if import_type == "ROOM":
            self.report(
                {"DEBUG"},
                "Importing room"
            )
            f3dzex.loadSegment(0x03, filepath)
            f3dzex.importMap()
        else:
            self.report(
                {"DEBUG"},
                "Importing object"
            )
            f3dzex.loadSegment(0x06, filepath)
            f3dzex.importObj()

        # TODO: use a map here...
        if self.setView3dParameters:
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type == "VIEW_3D":
                        if importType == "ROOM":
                            area.spaces.active.grid_lines = 500
                            area.spaces.active.grid_scale = 10
                            area.spaces.active.grid_subdivisions = 10
                            area.spaces.active.clip_end = 900000
                        area.spaces.active.viewport_shade = "TEXTURED"

        time_elapsed = time.time() - time_start
        self.report(
            {"INFO"},
            f"SUCCESS:  Elapsed time {time_elapsed:.4f} sec"
        )


    def draw(self, context):
        pass

class ZOBJ_PT_import_config(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Config"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_zobj"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "import_type", text="Type")
        layout.prop(operator, "import_strategy", text="Strategy")
        if operator.import_strategy != "NO_DETECTION":
            layout.prop(operator, "detected_display_lists_use_transparency")
            layout.prop(operator, "detected_display_lists_consider_unimplemented_invalid")
        layout.prop(operator, "vertex_mode")
        layout.prop(operator, "load_other_segments")
        layout.prop(operator, "original_object_scale")
        layout.prop(operator, "enable_matrices")
        layout.prop(operator, "enable_toon")
        layout.prop(operator, "prefix_multi_import")
        layout.prop(operator, "set_view_3d_parameters")

class ZOBJ_PT_import_texture(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Textures"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_zobj"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "enable_tex_clamp_blender")
        layout.prop(operator, "replicate_tex_mirror_blender")
        if operator.replicate_tex_mirror_blender:
            wBox = layout.box()
            wBox.label(text="Enabling texture mirroring", icon="ERROR")
            wBox.label(text="will break exporting with", icon="BLANK1")
            wBox.label(text="SharpOcarina, and may break", icon="BLANK1")
            wBox.label(text="exporting in general with", icon="BLANK1")
            wBox.label(text="other tools.", icon="BLANK1")
        layout.prop(operator, "enable_tex_clamp_sharp_ocarina_tags")
        layout.prop(operator, "enable_tex_mirror_sharp_ocarina_tags")

        layout.separator()

        layout.prop(operator, "enable_prim_color")
        layout.prop(operator, "enable_env_color")
        layout.prop(operator, "invert_env_color")
        layout.prop(operator, "export_textures")
        layout.prop(operator, "import_textures")

class ZOBJ_PT_import_animation(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Animations"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_zobj"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "load_animations")
        layout.prop(operator, "majora_anims")
        layout.prop(operator, "external_animes") 
