class ImportZ64(bpy.types.Operator, ImportHelper):
    """Load a Zelda64 File"""
    bl_idname    = "file.zobj2020"
    bl_label     = "Import Zelda64"
    bl_options   = {'PRESET', 'UNDO'}
    filename_ext = ".zobj"
    filter_glob  = StringProperty(default="*.zobj;*.zroom;*.zmap", options={'HIDDEN'})

    files = CollectionProperty(
            name="Files",
            type=bpy.types.OperatorFileListElement,)

    directory = StringProperty(subtype='DIR_PATH')

    loadOtherSegments = BoolProperty(
            name="Load Data From Other Segments",
            description="Load data from other segments",
            default=True,)

    importType = EnumProperty(
            name='Import type',
            items=(('AUTO', 'Auto', 'Assume Room File if .zroom or .zmap, otherwise assume Object File'),
                   ('OBJECT', 'Object File', 'Assume the file being imported is an object file'),
                   ('ROOM', 'Room File', 'Assume the file being imported is a room file'),),
            description='What to assume the file being imported is',
            default='AUTO',)
    
    importStrategy = EnumProperty(
            name='Detect DLists',
            items=(('NO_DETECTION', 'Minimum', 'Maps: only use headers\nObjects: only use hierarchies\nOnly this option will not create unexpected geometry'),
                   ('BRUTEFORCE', 'Bruteforce', 'Try to import everything that looks like a display list\n(ignores header for maps)'),
                   ('SMART', 'Smart-ish', 'Minimum + Bruteforce but avoids reading the same display lists several times'),
                   ('TRY_EVERYTHING', 'Try everything', 'Minimum + Bruteforce'),),
            description='How to find display lists to import (try this if there is missing geometry)',
            default='NO_DETECTION',)
    
    vertexMode = EnumProperty(
            name="Vtx Mode",
            items=(('COLORS', "COLORS", "Use vertex colors"),
                   ('NORMALS', "NORMALS", "Use vertex normals as shading"),
                   ('NONE', "NONE", "Don't use vertex colors or normals"),
                   ('AUTO', "AUTO", "Switch between normals and vertex colors automatically according to 0xD9 G_GEOMETRYMODE flags"),),
            description="Legacy option, shouldn't be useful",
            default='AUTO',)
    
    useVertexAlpha = BoolProperty(
            name="Use vertex alpha",
            description="Only enable if your version of blender has native support",
            default=(bpy.app.version == (2,79,7) and bpy.app.build_hash in {b'10f724cec5e3', b'e045fe53f1b0'}),)
    
    enableMatrices = BoolProperty(
            name="Matrices",
            description="Use 0xDA G_MTX and 0xD8 G_POPMTX commands",
            default=True,)
    
    detectedDisplayLists_use_transparency = BoolProperty(
            name="Default to transparency",
            description='Set material to use transparency or not for display lists that were detected',
            default=False,)
    
    detectedDisplayLists_consider_unimplemented_invalid = BoolProperty(
            name='Unimplemented => Invalid',
            description='Consider that unimplemented opcodes are invalid when detecting display lists.\n'
            'The reasoning is that unimplemented opcodes are very rare or never actually used.',
            default=True,)
    
    enablePrimColor = BoolProperty(
            name="Prim Color",
            description="Enable blending with primitive color",
            default=False,) # this may be nice for strictly importing but exporting again will then not be exact
    
    enableEnvColor = BoolProperty(
            name="Env Color",
            description="Enable blending with environment color",
            default=False,) # same as primColor above
    
    invertEnvColor = BoolProperty(
            name="Invert Env Color",
            description="Invert environment color (temporary fix)",
            default=False,) # todo what is this?
    
    exportTextures = BoolProperty(
            name="Export Textures",
            description="Export textures for the model",
            default=True,)
    
    importTextures = BoolProperty(
            name="Import Textures",
            description="Import textures for the model",
            default=True,)
    
    enableTexClampBlender = BoolProperty(
            name="Texture Clamp",
            description="Enable texture clamping in Blender, used by Blender in the 3d viewport and by zzconvert",
            default=False,)
    
    replicateTexMirrorBlender = BoolProperty(
            name="Texture Mirror",
            description="Replicate texture mirroring by writing the textures with the mirrored parts (with double width/height) instead of the initial texture",
            default=False,)
    
    enableTexClampSharpOcarinaTags = BoolProperty(
            name="Texture Clamp SO Tags",
            description="Add #ClampX and #ClampY tags where necessary in the texture filename, used by SharpOcarina",
            default=False,)
    
    enableTexMirrorSharpOcarinaTags = BoolProperty(
            name="Texture Mirror SO Tags",
            description="Add #MirrorX and #MirrorY tags where necessary in the texture filename, used by SharpOcarina",
            default=False,)

    enableShadelessMaterials = BoolProperty(
            name="Shadeless Materials",
            description="Set materials to be shadeless, prevents using environment colors in-game",
            default=False,)
    
    enableToon = BoolProperty(
            name="Toony UVs",
            description="Obtain a toony effect by not scaling down the uv coords",
            default=False,)
    
    originalObjectScale = IntProperty(
            name="File Scale",
            description="Scale of imported object, blender model will be scaled 1/(file scale) (use 1 for maps, actors are usually 100, 10 or 1) (0 defaults to 1 for maps and 100 for actors)",
            default=0, min=0, soft_max=1000)
    
    loadAnimations = BoolProperty(
            name="Load animations",
            description="For animated actors, load all animations or none",
            default=True,)
    
    MajorasAnims = BoolProperty(
            name="MajorasAnims",
            description="Majora's Mask Link's Anims.",
            default=False,)
    
    ExternalAnimes = BoolProperty(
            name="ExternalAnimes",
            description="Load External Animes.",
            default=False,)
    
    prefixMultiImport = BoolProperty(
            name='Prefix multi-import',
            description='Add a prefix to imported data (objects, materials, images...) when importing several files at once',
            default=True,)
    
    setView3dParameters = BoolProperty(
            name="Set 3D View parameters",
            description="For maps, use a more appropriate grid size and clip distance",
            default=True,)
    
    logging_level = IntProperty(
            name="Log level",
            description="(logs in the system console) The lower, the more logs. trace=%d debug=%d info=%d" % (logging_trace_level,logging.DEBUG,logging.INFO),
            default=logging.INFO, min=1, max=51)
    
    report_logging_level = IntProperty(
            name='Report level',
            description='What logs to report to Blender. When the import is done, warnings and errors are shown, if any. trace=%d debug=%d info=%d' % (logging_trace_level,logging.DEBUG,logging.INFO),
            default=logging.INFO, min=1, max=51)
    
    logging_logfile_enable = BoolProperty(
            name='Log to file',
            description='Log everything (all levels) to a file',
            default=False,)
    
    logging_logfile_path = StringProperty(
            name='Log file path',
            #subtype='FILE_PATH', # cannot use two FILE_PATH at the same time
            description='File to write logs to\nPath can be relative (to imported file) or absolute',
            default='log_io_import_z64.txt',)

    def execute(self, context):
        global importStrategy
        global vertexMode, enableMatrices
        global detectedDisplayLists_use_transparency
        global detectedDisplayLists_consider_unimplemented_invalid
        global useVertexAlpha
        global enablePrimColor, enableEnvColor, invertEnvColor
        global importTextures, exportTextures
        global enableTexClampBlender, replicateTexMirrorBlender
        global enableTexClampSharpOcarinaTags, enableTexMirrorSharpOcarinaTags
        global enableMatrices, enableToon
        global AnimtoPlay, MajorasAnims, ExternalAnimes
        global enableShadelessMaterials

        importStrategy = self.importStrategy
        vertexMode = self.vertexMode
        useVertexAlpha = self.useVertexAlpha
        enableMatrices = self.enableMatrices
        detectedDisplayLists_use_transparency = self.detectedDisplayLists_use_transparency
        detectedDisplayLists_consider_unimplemented_invalid = self.detectedDisplayLists_consider_unimplemented_invalid
        enablePrimColor = self.enablePrimColor
        enableEnvColor = self.enableEnvColor
        invertEnvColor = self.invertEnvColor
        importTextures = self.importTextures
        exportTextures = self.exportTextures
        enableTexClampBlender = self.enableTexClampBlender
        replicateTexMirrorBlender = self.replicateTexMirrorBlender
        enableTexClampSharpOcarinaTags = self.enableTexClampSharpOcarinaTags
        enableTexMirrorSharpOcarinaTags = self.enableTexMirrorSharpOcarinaTags
        enableToon = self.enableToon
        AnimtoPlay = 1 if self.loadAnimations else 0
        MajorasAnims = self.MajorasAnims
        ExternalAnimes = self.ExternalAnimes
        enableShadelessMaterials = self.enableShadelessMaterials

        setLoggingLevel(self.logging_level)
        log = getLogger('ImportZ64.execute')
        if self.logging_logfile_enable:
            logfile_path = self.logging_logfile_path
            if not os.path.isabs(logfile_path):
                logfile_path = os.path.join(self.directory, logfile_path)
            log.info('Writing logs to %s' % logfile_path)
            setLogFile(logfile_path)
        setLogOperator(self, self.report_logging_level)

        try:
            for file in self.files:
                filepath = os.path.join(self.directory, file.name)
                if len(self.files) == 1 or not self.prefixMultiImport:
                    prefix = ""
                else:
                    prefix = file.name + "_"
                self.executeSingle(filepath, prefix=prefix)
            bpy.context.scene.update()
        finally:
            setLogFile(None)
            setLogOperator(None)
        return {'FINISHED'}

    def executeSingle(self, filepath, prefix=""):
        global fpath
        global scaleFactor

        fpath, fext = os.path.splitext(filepath)
        fpath, fname = os.path.split(fpath)

        if self.importType == "AUTO":
            if fext.lower() in {'.zmap', '.zroom'}:
                importType = "ROOM"
            else:
                importType = "OBJECT"
        else:
            importType = self.importType

        if self.originalObjectScale == 0:
            if importType == "ROOM":
                scaleFactor = 1 # maps are actually stored 1:1
            else:
                scaleFactor = 1 / 100 # most objects are stored 100:1
        else:
            scaleFactor = 1 / self.originalObjectScale

        log = getLogger('ImportZ64.executeSingle')

        log.info("Importing '%s'..." % fname)
        time_start = time.time()
        self.run_import(filepath, importType, prefix=prefix)
        log.info("SUCCESS:  Elapsed time %.4f sec" % (time.time() - time_start))

    def run_import(self, filepath, importType, prefix=""):
        fpath, fext = os.path.splitext(filepath)
        fpath, fname = os.path.split(fpath)

        log = getLogger('ImportZ64.run_import')
        f3dzex = F3DZEX(prefix=prefix)
        f3dzex.loaddisplaylists(os.path.join(fpath, "displaylists.txt"))
        if self.loadOtherSegments:
            log.debug('Loading other segments')
            # for segment 2, use [room file prefix]_scene then [same].zscene then segment_02.zdata then fallback to any .zscene
            scene_file = None
            if "_room" in fname:
                scene_file = fpath + "/" + fname[:fname.index("_room")] + "_scene"
                if not os.path.isfile(scene_file):
                    scene_file += ".zscene"
            if not scene_file or not os.path.isfile(scene_file):
                scene_file = fpath + "/segment_02.zdata"
            if not scene_file or not os.path.isfile(scene_file):
                scene_file = None
                for f in os.listdir(fpath):
                    if f.endswith('.zscene'):
                        if scene_file:
                            log.warning('Found another .zscene file %s, keeping %s' % (f, scene_file))
                        else:
                            scene_file = fpath + '/' + f
            if scene_file and os.path.isfile(scene_file):
                log.info('Loading scene segment 0x02 from %s' % scene_file)
                f3dzex.loadSegment(2, scene_file)
            else:
                log.debug('No file found to load scene segment 0x02 from')
            for i in range(16):
                if i == 2:
                    continue
                # I was told this is "ZRE" naming?
                segment_data_file = fpath + "/segment_%02X.zdata" % i
                if os.path.isfile(segment_data_file):
                    log.info('Loading segment 0x%02X from %s' % (i, segment_data_file))
                    f3dzex.loadSegment(i, segment_data_file)
                else:
                    log.debug('No file found to load segment 0x%02X from', i)

        if importType == "ROOM":
            log.debug('Importing room')
            f3dzex.loadSegment(0x03, filepath)
            f3dzex.importMap()
        else:
            log.debug('Importing object')
            f3dzex.loadSegment(0x06, filepath)
            f3dzex.importObj()

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

    def draw(self, context):
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
