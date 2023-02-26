import bpy, os

class FILE_OT_z64_import(bpy.types.Operator, ImportHelper):
    bl_idname = "file.zobj2023"
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
        default=False) # todo what is this?

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
        default=False)

    enableShadelessMaterials: bpy.props.BoolProperty(
        name="Shadeless Materials",
        description="Set materials to be shadeless, prevents using environment colors in-game",
        default=False)

    enableToon: bpy.props.BoolProperty(
        name="Toony UVs",
        description="Obtain a toony effect by not scaling down the uv coords",
        default=False)

    originalObjectScale: bpy.props.IntProperty(
        name="File Scale",
        description="Scale of imported object, blender model will be scaled 1/(file scale) (use 1 for maps, actors are usually 100, 10 or 1) (0 defaults to 1 for maps and 100 for actors)",
        default=0, min=0, soft_max=1000)

    loadAnimations: bpy.props.BoolProperty(
        name="Load animations",
        description="For animated actors, load all animations or none",
        default=True)

    MajorasAnims: bpy.props.BoolProperty(
        name="MajorasAnims",
        description="Majora"s Mask Link"s Anims.",
        default=False)

    ExternalAnimes: bpy.props.BoolProperty(
        name="ExternalAnimes",
        description="Load External Animes.",
        default=False)

    prefixMultiImport: bpy.props.BoolProperty(
        name="Prefix multi-import",
        description="Add a prefix to imported data (objects, materials, images...) when importing several files at once",
        default=True)

    setView3dParameters: bpy.props.BoolProperty(
        name="Set 3D View parameters",
        description="For maps, use a more appropriate grid size and clip distance",
        default=True)

    logging_level: bpy.props.IntProperty(
        name="Log level",
        description="(logs in the system console) The lower, the more logs. trace=%d debug=%d info=%d" \
        % (logging_trace_level,logging.DEBUG,logging.INFO),
        default=logging.INFO, min=1, max=51)

    report_logging_level: bpy.props.IntProperty(
        name="Report level",
        description="What logs to report to Blender. When the import is done, warnings and errors are shown, if any. trace=%d debug=%d info=%d" \
        % (logging_trace_level,logging.DEBUG,logging.INFO),
        default=logging.INFO, min=1, max=51)

    logging_logfile_enable: bpy.props.BoolProperty(
        name="Log to file",
        description="Log everything (all levels) to a file",
        default=False)

    logging_logfile_path: bpy.props.StringProperty(
        name="Log file path",
        #subtype="FILE_PATH", # cannot use two FILE_PATH at the same time
        description="File to write logs to\nPath can be relative (to imported file) or absolute",
        default="log_io_import_z64.txt"
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
        
        bpy.context.scene.update()
        
        return {'FINISHED'}


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
                if file.endswith('.zscene'):
                    scene_file = os.path.join(path, file)
                    break

        return scene_file


    def load_other_scene_segments(self, path, file_prefix):
        self.report(
            {"DEBUG"}, "Loading other scene segments"
        )

        for i in range(16):
            if i == 2:
                segment_data_file = self.find_scene_segment_2(path, file_prefix)
            else:
                # I was told this is "ZRE" naming?
                segment_data_file = os.path.join(path, "segment_%02X.zdata" % i)

            if os.path.isfile(segment_data_file):
                self.report(
                    {"INFO"},
                    'Loading scene segment 0x%02X from %s' \
                    % (i, segment_data_file)
                )
                f3dzex.loadSegment(i, segment_data_file)
            else:
                self.report(
                    {"DEBUG"},
                    'No file found to load scene segment 0x%02X from' % i
                )


    def do_import(self, file_abspath, prefix=""):
        path, file_name = os.path.split(file_abspath)
        file_prefix, file_ext = os.path.splitext(file_name)
        file_ext = file_ext.lower()

        self.report(
            {"INFO"}, "Importing '%s'..." % file_name
        )

        if self.importType == "AUTO":
            if file_ext in {'.zmap', '.zroom'}:
                import_type = "ROOM"
            else:
                import_type = "OBJECT"

            self.report(
                {"DEBUG"},
                "AUTO Import; using type %s to import file %s" \
                % (import_type, file_name)
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
            # remember, file_prefix is file_name without the .ext
            self.load_other_scene_segments(path, file_prefix)

        if import_type == "ROOM":
            self.report(
                {"DEBUG"},
                'Importing room'
            )
            f3dzex.loadSegment(0x03, filepath)
            f3dzex.importMap()
        else:
            self.report(
                {"DEBUG"},
                'Importing object')
            )
            f3dzex.loadSegment(0x06, filepath)
            f3dzex.importObj()

        # TODO: use a map here...
        if self.setView3dParameters:
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        if importType == "ROOM":
                            area.spaces.active.grid_lines = 500
                            area.spaces.active.grid_scale = 10
                            area.spaces.active.grid_subdivisions = 10
                            area.spaces.active.clip_end = 900000
                        area.spaces.active.viewport_shade = "TEXTURED"

        self.report(
            {"INFO"}, "SUCCESS:  Elapsed time %.4f sec" % (time.time() - time_start)
        )


    def draw(self, context):
        # TODO: what even is this
        l = self.layout
        l.prop(self, 'importType', text='Type')
        l.prop(self, 'importStrategy', text='Strategy')
        if self.importStrategy != 'NO_DETECTION':
            l.prop(self, 'detectedDisplayLists_use_transparency')
            l.prop(self, 'detectedDisplayLists_consider_unimplemented_invalid')
        l.prop(self, "vertexMode")
        l.prop(self, 'useVertexAlpha')
        l.prop(self, "loadOtherSegments")
        l.prop(self, "originalObjectScale")
        box = l.box()
        box.prop(self, "enableTexClampBlender")
        box.prop(self, "replicateTexMirrorBlender")
        if self.replicateTexMirrorBlender:
            wBox = box.box()
            wBox.label(text='Enabling texture mirroring', icon='ERROR')
            wBox.label(text='will break exporting with', icon='ERROR')
            wBox.label(text='SharpOcarina, and may break', icon='ERROR')
            wBox.label(text='exporting in general with', icon='ERROR')
            wBox.label(text='other tools.', icon='ERROR')
        box.prop(self, "enableTexClampSharpOcarinaTags")
        box.prop(self, "enableTexMirrorSharpOcarinaTags")
        l.prop(self, "enableMatrices")
        l.prop(self, "enablePrimColor")
        l.prop(self, "enableEnvColor")
        l.prop(self, "invertEnvColor")
        l.prop(self, "exportTextures")
        l.prop(self, "importTextures")
        l.prop(self, "enableShadelessMaterials")
        l.prop(self, "enableToon")
        l.separator()
        l.prop(self, "loadAnimations")
        l.prop(self, "MajorasAnims")
        l.prop(self, "ExternalAnimes")
        l.prop(self, "prefixMultiImport")
        l.prop(self, "setView3dParameters")
        l.separator()
        l.prop(self, "logging_level")
        l.prop(self, 'logging_logfile_enable')
        if self.logging_logfile_enable:
            l.prop(self, 'logging_logfile_path')
