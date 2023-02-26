class F3DZEX:
    def __init__(self, prefix=""):
        self.prefix = prefix

        self.use_transparency = detectedDisplayLists_use_transparency
        self.alreadyRead = []
        self.segment, self.vbuf, self.tile  = [], [], []
        self.geometryModeFlags = set()

        self.animTotal = 0
        self.TimeLine = 0
        self.TimeLinePosition = 0
        self.displaylists = []

        for i in range(16):
            self.alreadyRead.append([])
            self.segment.append([])
            self.vbuf.append(Vertex())
        for i in range(2):
            self.tile.append(Tile())
            pass#self.vbuf.append(Vertex())
        for i in range(14 + 32):
            pass#self.vbuf.append(Vertex())
        while len(self.vbuf) < 32:
            self.vbuf.append(Vertex())
        self.curTile = 0
        self.material = []
        self.hierarchy = []
        self.resetCombiner()

    def loaddisplaylists(self, path):
        log = getLogger('F3DZEX.loaddisplaylists')
        if not os.path.isfile(path):
            log.info('Did not find %s (use to manually set offsets of display lists to import)', path)
            self.displaylists = []
            return
        try:
            file = open(path)
            self.displaylists = file.readlines()
            file.close()
            log.info("Loaded the display list list successfully!")
        except:
            log.exception('Could not read displaylists.txt')

    def loadSegment(self, seg, path):
        try:
            file = open(path, 'rb')
            self.segment[seg] = file.read()
            file.close()
        except:
            getLogger('F3DZEX.loadSegment').error('Could not load segment 0x%02X data from %s' % (seg, path))
            pass

    def locateHierarchies(self):
        log = getLogger('F3DZEX.locateHierarchies')
        data = self.segment[0x06]
        for i in range(0, len(data)-11, 4):
            # test for header "bboooooo pp000000 xx000000": if segment bb=0x06 and offset oooooo 4-aligned and not zero parts (pp!=0)
            if data[i] == 0x06 and (data[i+3] & 3) == 0 and data[i+4] != 0:
                offset = unpack_from(">L", data, i)[0] & 0x00FFFFFF
                if offset < len(data):
                    # each Limb index entry is 4 bytes starting at offset
                    offset_end = offset + (data[i+4] << 2)
                    if offset_end <= len(data):
                        j = offset
                        while j < offset_end:
                            # test for limb entry "bboooooo": valid limb entry table as long as segment bb=0x06 and offset oooooo 4-aligned and offset is valid
                            if data[j] != 0x06 or (data[j+3] & 3) != 0 or (unpack_from(">L", data, j)[0] & 0x00FFFFFF) > len(data):
                                break
                            j += 4
                        if (j == i):
                            j |= 0x06000000
                            log.info("    hierarchy found at 0x%08X", j)
                            h = Hierarchy()
                            if h.read(self.segment, j, prefix=self.prefix):
                                self.hierarchy.append(h)
                            else:
                                log.warning('Skipping hierarchy at 0x%08X', j)

    def locateAnimations(self):
        log = getLogger('F3DZEX.locateAnimations')
        data = self.segment[0x06]
        self.animation = []
        self.offsetAnims = []
        self.durationAnims = []
        for i in range(0, len(data)-15, 4):
            # detect animation header
            # ffff0000 rrrrrrrr iiiiiiii llll0000
            # fixme data[i] == 0 but should be first byte of ffff
            # fixme data[i+1] > 1 but why not 1 (or 0)
            if ((data[i] == 0) and (data[i+1] > 1) and
                 (data[i+2] == 0) and (data[i+3] == 0) and
                 (data[i+4] == 0x06) and
                 (((data[i+5] << 16)|(data[i+6] << 8)|data[i+7]) < len(data)) and
                 (data[i+8] == 0x06) and
                 (((data[i+9] << 16)|(data[i+10] << 8)|data[i+11]) < len(data)) and
                 (data[i+14] == 0) and (data[i+15] == 0)):
                log.info("          Anims found at %08X Frames: %d", i, data[i+1] & 0x00FFFFFF)
                self.animation.append(i)
                self.offsetAnims.append(i)
                self.offsetAnims[self.animTotal] = (0x06 << 24) | i
                # fixme it's two bytes, not one
                self.durationAnims.append(data[i+1] & 0x00FFFFFF)
                self.animTotal += 1
        if(self.animTotal > 0):
                log.info("          Total Anims                         : %d", self.animTotal)

    def locateExternAnimations(self):
        log = getLogger('F3DZEX.locateExternAnimations')
        data = self.segment[0x0F]
        self.animation = []
        self.offsetAnims = []
        for i in range(0, len(data)-15, 4):
            if ((data[i] == 0) and (data[i+1] > 1) and
                 (data[i+2] == 0) and (data[i+3] == 0) and
                 (data[i+4] == 0x06) and
                 (((data[i+5] << 16)|(data[i+6] << 8)|data[i+7]) < len(data)) and
                 (data[i+8] == 0x06) and
                 (((data[i+9] << 16)|(data[i+10] << 8)|data[i+11]) < len(data)) and
                 (data[i+14] == 0) and (data[i+15] == 0)):
                log.info("          Ext Anims found at %08X" % i, "Frames:", data[i+1] & 0x00FFFFFF)
                self.animation.append(i)
                self.offsetAnims.append(i)
                self.offsetAnims[self.animTotal] = (0x0F << 24) | i
                self.animTotal += 1
        if(self.animTotal > 0):
            log.info("        Total Anims                   :", self.animTotal)

    def locateLinkAnimations(self):
        log = getLogger('F3DZEX.locateLinkAnimations')
        data = self.segment[0x04]
        self.animation = []
        self.offsetAnims = []
        self.animFrames = []
        self.animTotal = -1
        if (len( self.segment[0x04] ) > 0):
            if (MajorasAnims):
                for i in range(0xD000, 0xE4F8, 8):
                    self.animTotal += 1
                    self.animation.append(self.animTotal)
                    self.animFrames.append(self.animTotal)
                    self.offsetAnims.append(self.animTotal)
                    self.offsetAnims[self.animTotal]     = unpack_from(">L", data, i + 4)[0]
                    self.animFrames[self.animTotal] = unpack_from(">h", data, i)[0]
                    log.debug('- Animation #%d offset: %07X frames: %d', self.animTotal+1, self.offsetAnims[self.animTotal], self.animFrames[self.animTotal])
            else:
                for i in range(0x2310, 0x34F8, 8):
                    self.animTotal += 1
                    self.animation.append(self.animTotal)
                    self.animFrames.append(self.animTotal)
                    self.offsetAnims.append(self.animTotal)
                    self.offsetAnims[self.animTotal]     = unpack_from(">L", data, i + 4)[0]
                    self.animFrames[self.animTotal] = unpack_from(">h", data, i)[0]
                    log.debug('- Animation #%d offset: %07X frames: %d', self.animTotal+1, self.offsetAnims[self.animTotal], self.animFrames[self.animTotal])
        log.info("         Link has come to town!!!!")
        if ( (len( self.segment[0x07] ) > 0) and (self.animTotal > 0)):
            self.buildLinkAnimations(self.hierarchy[0], 0)

    def importJFIF(self, data, initPropsOffset, name_format='bg_%08X'):
        log = getLogger('F3DZEX.importJFIF')
        (   imagePtr,
            unknown, unknown2,
            background_width, background_height,
            imageFmt, imageSiz, imagePal, imageFlip
        ) = struct.unpack_from('>IIiHHBBHH', data, initPropsOffset)
        t = Tile()
        t.texFmt = imageFmt
        t.texSiz = imageSiz
        log.debug(
            'JFIF background image init properties\n'
            'imagePtr=0x%X size=%dx%d fmt=%d, siz=%d (%s) imagePal=%d imageFlip=%d',
            imagePtr, background_width, background_height,
            imageFmt, imageSiz, t.getFormatName(), imagePal, imageFlip
        )
        if imagePtr >> 24 != 0x03:
            log.error('Skipping JFIF background image, pointer 0x%08X is not in segment 0x03', imagePtr)
            return False
        jfifDataStart = imagePtr & 0xFFFFFF
        # read header just for sanity checks
        # source: CloudModding wiki https://wiki.cloudmodding.com/oot/JFIF_Backgrounds
        (   marker_begin,
            marker_begin_header, header_length,
            jfif, null, version,
            dens, densx, densy,
            thumbnail_width, thumbnail_height,
            marker_end_header
        ) = struct.unpack_from('>HHHIBHBHHBBH', data, jfifDataStart)
        badJfif = []
        if marker_begin != 0xFFD8:
            badJfif.append('Expected marker_begin=0xFFD8 instead of 0x%04X' % marker_begin)
        if marker_begin_header != 0xFFE0:
            badJfif.append('Expected marker_begin_header=0xFFE0 instead of 0x%04X' % marker_begin_header)
        if header_length != 16:
            badJfif.append('Expected header_length=16 instead of %d=0x%04X' % (header_length, header_length))
        if jfif != 0x4A464946: # JFIF
            badJfif.append('Expected jfif=0x4A464946="JFIF" instead of 0x%08X' % jfif)
        if null != 0:
            badJfif.append('Expected null=0 instead of 0x%02X' % null)
        if version != 0x0101:
            badJfif.append('Expected version=0x0101 instead of 0x%04X' % version)
        if dens != 0:
            badJfif.append('Expected dens=0 instead of %d=0x%02X' % (dens, dens))
        if densx != 1:
            badJfif.append('Expected densx=1 instead of %d=0x%04X' % (densx, densx))
        if densy != 1:
            badJfif.append('Expected densy=1 instead of %d=0x%04X' % (densy, densy))
        if thumbnail_width != 0:
            badJfif.append('Expected thumbnail_width=0 instead of %d=0x%02X' % (thumbnail_width, thumbnail_width))
        if thumbnail_height != 0:
            badJfif.append('Expected thumbnail_height=0 instead of %d=0x%02X' % (thumbnail_height, thumbnail_height))
        if marker_end_header != 0xFFDB:
            badJfif.append('Expected marker_end_header=0xFFDB instead of 0x%04X' % marker_end_header)
        if badJfif:
            log.error('Bad JFIF format for background image at 0x%X:', jfifDataStart)
            for badJfifMessage in badJfif:
                log.error(badJfifMessage)
            return False
        jfifData = None
        i = jfifDataStart
        for i in range(jfifDataStart, len(data)-1):
            if data[i] == 0xFF and data[i+1] == 0xD9:
                jfifData = data[jfifDataStart:i+2]
                break
        if jfifData is None:
            log.error('Did not find end marker 0xFFD9 in background image at 0x%X', jfifDataStart)
            return False
        try:
            os.mkdir(fpath + '/textures')
        except FileExistsError:
            pass
        except:
            log.exception('Could not create textures directory %s' % (fpath + '/textures'))
            pass
        jfifPath = '%s/textures/jfif_%s.jfif' % (fpath, (name_format % jfifDataStart))
        with open(jfifPath, 'wb') as f:
            f.write(jfifData)
        log.info('Copied jfif image to %s', jfifPath)
        jfifImage = load_image(jfifPath)
        me = bpy.data.meshes.new(self.prefix + (name_format % jfifDataStart))
        me.vertices.add(4)
        cos = (
            (background_width, 0),
            (0,                0),
            (0,                background_height),
            (background_width, background_height),
        )
        import bmesh
        bm = bmesh.new()
        transform = Matrix.Scale(scaleFactor, 4)
        bm.faces.new(bm.verts.new(transform * Vector((cos[i][0], 0, cos[i][1]))) for i in range(4))
        bm.to_mesh(me)
        bm.free()
        del bmesh
        me.uv_textures.new().data[0].image = jfifImage
        ob = bpy.data.objects.new(self.prefix + (name_format % jfifDataStart), me)
        ob.location.z = max(max(v.co.z for v in obj.data.vertices) for obj in bpy.context.scene.objects if obj.type == 'MESH')
        bpy.context.scene.objects.link(ob)
        return ob

    def importMap(self):
        if importStrategy == 'NO_DETECTION':
            self.importMapWithHeaders()
        elif importStrategy == 'BRUTEFORCE':
            self.searchAndImport(3, False)
        elif importStrategy == 'SMART':
            self.importMapWithHeaders()
            self.searchAndImport(3, True)
        elif importStrategy == 'TRY_EVERYTHING':
            self.importMapWithHeaders()
            self.searchAndImport(3, False)

    def importMapWithHeaders(self):
        log = getLogger('F3DZEX.importMapWithHeaders')
        data = self.segment[0x03]
        for i in range(0, len(data), 8):
            if data[i] == 0x0A:
                mapHeaderSegment = data[i+4]
                if mapHeaderSegment != 0x03:
                    log.warning('Skipping map header located in segment 0x%02X, referenced by command at 0x%X', mapHeaderSegment, i)
                    continue
                # mesh header offset 
                mho = (data[i+5] << 16) | (data[i+6] << 8) | data[i+7]
                if not mho < len(data):
                    log.error('Mesh header offset 0x%X is past the room file size, skipping', mho)
                    continue
                type = data[mho]
                log.info("            Mesh Type: %d" % type)
                if type == 0:
                    if mho + 12 > len(data):
                        log.error('Mesh header at 0x%X of type %d extends past the room file size, skipping', mho, type)
                        continue
                    count = data[mho+1]
                    startSeg = data[mho+4]
                    start = (data[mho+5] << 16) | (data[mho+6] << 8) | data[mho+7]
                    endSeg = data[mho+8]
                    end = (data[mho+9] << 16) | (data[mho+10] << 8) | data[mho+11]
                    if startSeg != endSeg:
                        log.error('Mesh header at 0x%X of type %d has start and end in different segments 0x%02X and 0x%02X, skipping', mho, type, startSeg, endSeg)
                        continue
                    if startSeg != 0x03:
                        log.error('Skipping mesh header at 0x%X of type %d: entries are in segment 0x%02X', mho, type, startSeg)
                        continue
                    log.info('Reading %d display lists from 0x%X to 0x%X', count, start, end)
                    for j in range(start, end, 8):
                        opa = unpack_from(">L", data, j)[0]
                        if opa:
                            self.use_transparency = False
                            self.buildDisplayList(None, [None], opa, mesh_name_format='%s_opa')
                        xlu = unpack_from(">L", data, j+4)[0]
                        if xlu:
                            self.use_transparency = True
                            self.buildDisplayList(None, [None], xlu, mesh_name_format='%s_xlu')
                elif type == 1:
                    format = data[mho+1]
                    entrySeg = data[mho+4]
                    entry = (data[mho+5] << 16) | (data[mho+6] << 8) | data[mho+7]
                    if entrySeg == 0x03:
                        opa = unpack_from(">L", data, entry)[0]
                        if opa:
                            self.use_transparency = False
                            self.buildDisplayList(None, [None], opa, mesh_name_format='%s_opa')
                        xlu = unpack_from(">L", data, entry+4)[0]
                        if xlu:
                            self.use_transparency = True
                            self.buildDisplayList(None, [None], xlu, mesh_name_format='%s_xlu')
                    else:
                        log.error('Skipping mesh header at 0x%X of type %d: entry is in segment 0x%02X', mho, type, entrySeg)
                    if format == 1:
                        if not self.importJFIF(data, mho + 8):
                            log.error('Failed to import jfif background image, mesh header at 0x%X of type 1 format 1', mho)
                    elif format == 2:
                        background_count = data[mho + 8]
                        backgrounds_array = unpack_from(">L", data, mho + 0xC)[0]
                        if backgrounds_array >> 24 == 0x03:
                            backgrounds_array &= 0xFFFFFF
                            for i in range(background_count):
                                bg_record_offset = backgrounds_array + i * 0x1C
                                unk82, bgid = struct.unpack_from('>HB', data, bg_record_offset)
                                if unk82 != 0x0082:
                                    log.error('Skipping JFIF: mesh header at 0x%X type 1 format 2 background record entry #%d at 0x%X expected unk82=0x0082, not 0x%04X', mho, i, bg_record_offset, unk82)
                                    continue
                                ob = self.importJFIF(
                                    data, bg_record_offset + 4,
                                    name_format='bg_%d_%s' % (i, '%08X')
                                )
                                ob.location.y -= scaleFactor * 100 * i
                                if not ob:
                                    log.error('Failed to import jfif background image from record entry #%d at 0x%X, mesh header at 0x%X of type 1 format 2', i, bg_record_offset, mho)
                        else:
                            log.error('Skipping mesh header at 0x%X of type 1 format 2: backgrounds_array=0x%08X is not in segment 0x03', mho, backgrounds_array)
                    else:
                        log.error('Unknown format %d for mesh type 1 in mesh header at 0x%X', format, mho)
                elif type == 2:
                    if mho + 12 > len(data):
                        log.error('Mesh header at 0x%X of type %d extends past the room file size, skipping', mho, type)
                        continue
                    count = data[mho+1]
                    startSeg = data[mho+4]
                    start = (data[mho+5] << 16) | (data[mho+6] << 8) | data[mho+7]
                    endSeg = data[mho+8]
                    end = (data[mho+9] << 16) | (data[mho+10] << 8) | data[mho+11]
                    if startSeg != endSeg:
                        log.error('Mesh header at 0x%X of type %d has start and end in different segments 0x%02X and 0x%02X, skipping', mho, type, startSeg, endSeg)
                        continue
                    if startSeg != 0x03:
                        log.error('Skipping mesh header at 0x%X of type %d: entries are in segment 0x%02X', mho, type, startSeg)
                        continue
                    log.info('Reading %d display lists from 0x%X to 0x%X', count, start, end)
                    for j in range(start, end, 16):
                        opa = unpack_from(">L", data, j+8)[0]
                        if opa:
                            self.use_transparency = False
                            self.buildDisplayList(None, [None], opa, mesh_name_format='%s_opa')
                        xlu = unpack_from(">L", data, j+12)[0]
                        if xlu:
                            self.use_transparency = True
                            self.buildDisplayList(None, [None], xlu, mesh_name_format='%s_xlu')
                else:
                    log.error('Unknown mesh type %d in mesh header at 0x%X', type, mho)
            elif (data[i] == 0x14):
                return
        log.warning('Map headers ended unexpectedly')

    def importObj(self):
        log = getLogger('F3DZEX.importObj')
        log.info("Locating hierarchies...")
        self.locateHierarchies()

        if len(self.displaylists) != 0:
            log.info('Importing display lists defined in displaylists.txt')
            for offsetStr in self.displaylists:
                while offsetStr and offsetStr[-1] in ('\r','\n'):
                    offsetStr = offsetStr[:-1]
                if re.match(r'^[0-9]+$', offsetStr):
                    log.warning('Reading offset %s as hexadecimal, NOT decimal', offsetStr)
                if len(offsetStr) > 2 and offsetStr[:2] == '0x':
                    offsetStr = offsetStr[2:]
                try:
                    offset = int(offsetStr, 16)
                except ValueError:
                    log.error('Could not parse %s from displaylists.txt as hexadecimal, skipping entry', offsetStr)
                    continue
                if (offset & 0xFF000000) == 0:
                    log.info('Defaulting segment for offset 0x%X to 6', offset)
                    offset |= 0x06000000
                log.info('Importing display list 0x%08X (from displaylists.txt)', offset)
                self.buildDisplayList(None, 0, offset)

        for hierarchy in self.hierarchy:
            log.info("Building hierarchy '%s'..." % hierarchy.name)
            hierarchy.create()
            for i in range(hierarchy.limbCount):
                limb = hierarchy.limb[i]
                if limb.near != 0:
                    if validOffset(self.segment, limb.near):
                        log.info("    0x%02X : building display lists..." % i)
                        self.resetCombiner()
                        self.buildDisplayList(hierarchy, limb, limb.near)
                    else:
                        log.info("    0x%02X : out of range" % i)
                else:
                    log.info("    0x%02X : n/a" % i)
        if len(self.hierarchy) > 0:
            bpy.context.scene.objects.active = self.hierarchy[0].armature
            self.hierarchy[0].armature.select = True
            bpy.ops.object.mode_set(mode='POSE', toggle=False)
            global AnimtoPlay
            if (AnimtoPlay > 0):
                bpy.context.scene.frame_end = 1
                if(ExternalAnimes and len(self.segment[0x0F]) > 0):
                    self.locateExternAnimations()
                else:
                    self.locateAnimations()
                if len(self.animation) > 0:
                    for h in self.hierarchy:
                        if h.armature.animation_data is None:
                            h.armature.animation_data_create()
                    # use the hierarchy with most bones
                    # this works for building any animation regardless of its target skeleton (bone positions) because all limbs are named limb_XX, so the hierarchy with most bones has bones with same names as every other armature
                    # and the rotation and root location animated values don't rely on the actual armature used
                    # and in blender each action can be used for any armature, vertex groups/bone names just have to match
                    # this is useful for iron knuckles and anything with several hierarchies, although an unedited iron kunckles zobj won't work
                    hierarchy = max(self.hierarchy, key=lambda h:h.limbCount)
                    armature = hierarchy.armature
                    log.info('Building animations using armature %s in %s', armature.data.name, armature.name)
                    for i in range(len(self.animation)):
                        AnimtoPlay = i + 1
                        log.info("   Loading animation %d/%d 0x%08X", AnimtoPlay, len(self.animation), self.offsetAnims[AnimtoPlay-1])
                        action = bpy.data.actions.new(self.prefix + ('anim%d_%d' % (AnimtoPlay, self.durationAnims[i])))
                        # not sure what users an action is supposed to have, or what it should be linked to
                        action.use_fake_user = True
                        armature.animation_data.action = action
                        self.buildAnimations(hierarchy, 0)
                    for h in self.hierarchy:
                        h.armature.animation_data.action = action
                    bpy.context.scene.frame_end = max(self.durationAnims)
                else:
                    self.locateLinkAnimations()
            else:
                log.info("    Load anims OFF.")

        if importStrategy == 'NO_DETECTION':
            pass
        elif importStrategy == 'BRUTEFORCE':
            self.searchAndImport(6, False)
        elif importStrategy == 'SMART':
            self.searchAndImport(6, True)
        elif importStrategy == 'TRY_EVERYTHING':
            self.searchAndImport(6, False)

    def searchAndImport(self, segment, skipAlreadyRead):
        log = getLogger('F3DZEX.searchAndImport')
        data = self.segment[segment]
        self.use_transparency = detectedDisplayLists_use_transparency
        log.info(
            'Searching for %s display lists in segment 0x%02X (materials with transparency: %s)',
            'non-read' if skipAlreadyRead else 'any', segment, 'yes' if self.use_transparency else 'no')
        log.warning('If the imported geometry is weird/wrong, consider using displaylists.txt to manually define the display lists to import!')
        validOpcodesStartIndex = 0
        validOpcodesSkipped = set()
        for i in range(0, len(data), 8):
            opcode = data[i]
            # valid commands are 0x00-0x07 and 0xD3-0xFF
            # however, could be not considered valid:
            # 0x07 G_QUAD
            # 0xEC G_SETCONVERT (YUV-related)
            # 0xE4 G_TEXRECT, 0xF6 G_FILLRECT (2d overlay)
            # 0xEB, 0xEE, 0xEF, 0xF1 ("unimplemented -> rarely used" being the reasoning)
            # but filtering out those hurts the resulting import
            isValid = (opcode <= 0x07 or opcode >= 0xD3) #and opcode not in (0x07,0xEC,0xE4,0xF6,0xEB,0xEE,0xEF,0xF1)
            if isValid and detectedDisplayLists_consider_unimplemented_invalid:
                
                isValid = opcode not in (0x07,0xE5,0xEC,0xD3,0xDB,0xDC,0xDD,0xE0,0xE5,0xE9,0xF6,0xF8)
                if not isValid:
                    validOpcodesSkipped.add(opcode)
            if not isValid:
                validOpcodesStartIndex = None
            elif validOpcodesStartIndex is None:
                validOpcodesStartIndex = i
            # if this command means "end of dlist"
            if (opcode == 0xDE and data[i+1] != 0) or opcode == 0xDF:
                # build starting at earliest valid opcode
                log.debug('Found opcode 0x%X at 0x%X, building display list from 0x%X', opcode, i, validOpcodesStartIndex)
                self.buildDisplayList(
                    None, [None], (segment << 24) | validOpcodesStartIndex,
                    mesh_name_format = '%s_detect',
                    skipAlreadyRead = skipAlreadyRead,
                    extraLenient = True
                )
                validOpcodesStartIndex = None
        if validOpcodesSkipped:
            log.info('Valid opcodes %s considered invalid because unimplemented (meaning rare)', ','.join('0x%02X' % opcode for opcode in sorted(validOpcodesSkipped)))

    def resetCombiner(self):
        self.primColor = Vector([1.0, 1.0, 1.0, 1.0])
        self.envColor = Vector([1.0, 1.0, 1.0, 1.0])
        if checkUseVertexAlpha():
            self.vertexColor = Vector([1.0, 1.0, 1.0, 1.0])
        else:
            self.vertexColor = Vector([1.0, 1.0, 1.0])
        self.shadeColor = Vector([1.0, 1.0, 1.0])

    def checkUseNormals(self):
        return vertexMode == 'NORMALS' or (vertexMode == 'AUTO' and 'G_LIGHTING' in self.geometryModeFlags)

    def getCombinerColor(self):
        def mult4d(v1, v2):
            return Vector([v1[i] * v2[i] for i in range(4)])
        cc = Vector([1.0, 1.0, 1.0, 1.0])
        # todo these have an effect even if vertexMode == 'NONE' ?
        if enablePrimColor:
            cc = mult4d(cc, self.primColor)
        if enableEnvColor:
            cc = mult4d(cc, self.envColor)
        # todo assume G_LIGHTING means normals if set, and colors if clear, but G_SHADE may play a role too?
        if vertexMode == 'COLORS' or (vertexMode == 'AUTO' and 'G_LIGHTING' not in self.geometryModeFlags):
            cc = mult4d(cc, self.vertexColor.to_4d())
        elif self.checkUseNormals():
            cc = mult4d(cc, self.shadeColor.to_4d())
        if checkUseVertexAlpha():
            return cc
        else:
            return cc.xyz

    def buildDisplayList(self, hierarchy, limb, offset, mesh_name_format='%s', skipAlreadyRead=False, extraLenient=False):
        log = getLogger('F3DZEX.buildDisplayList')
        segment = offset >> 24
        segmentMask = segment << 24
        data = self.segment[segment]

        startOffset = offset & 0x00FFFFFF
        endOffset = len(data)
        if skipAlreadyRead:
            log.trace('is 0x%X in %r ?', startOffset, self.alreadyRead[segment])
            for fromOffset,toOffset in self.alreadyRead[segment]:
                if fromOffset <= startOffset and startOffset <= toOffset:
                    log.debug('Skipping already read dlist at 0x%X', startOffset)
                    return
                if startOffset <= fromOffset:
                    if endOffset > fromOffset:
                        endOffset = fromOffset
                        log.debug('Shortening dlist to end at most at 0x%X, at which point it was read already', endOffset)
            log.trace('no it is not')

        def buildRec(offset):
            self.buildDisplayList(hierarchy, limb, offset, mesh_name_format=mesh_name_format, skipAlreadyRead=skipAlreadyRead)

        mesh = Mesh()
        has_tex = False
        material = None
        if hierarchy:
            matrix = [limb]
        else:
            matrix = [None]

        log.debug('Reading dlists from 0x%08X', segmentMask | startOffset)
        for i in range(startOffset, endOffset, 8):
            w0 = unpack_from(">L", data, i)[0]
            w1 = unpack_from(">L", data, i + 4)[0]
            # G_NOOP
            if data[i] == 0x00:
                pass
            elif data[i] == 0x01:
                count = (w0 >> 12) & 0xFF
                index = ((w0 & 0xFF) >> 1) - count
                vaddr = w1
                if validOffset(self.segment, vaddr + int(16 * count) - 1):
                    for j in range(count):
                        self.vbuf[index + j].read(self.segment, vaddr + 16 * j)
                        if hierarchy:
                            self.vbuf[index + j].limb = matrix[len(matrix) - 1]
                            if self.vbuf[index + j].limb:
                                self.vbuf[index + j].pos += self.vbuf[index + j].limb.pos
            elif data[i] == 0x02:
                try:
                    index = ((data[i + 2] & 0x0F) << 3) | (data[i + 3] >> 1)
                    if data[i + 1] == 0x10:
                        self.vbuf[index].normal.x = unpack_from("b", data, i + 4)[0] / 128
                        self.vbuf[index].normal.z = unpack_from("b", data, i + 5)[0] / 128
                        self.vbuf[index].normal.y = -unpack_from("b", data, i + 6)[0] / 128
                        # wtf? BBBB pattern and [0]
                        self.vbuf[index].color = unpack_from("BBBB", data, i + 4)[0] / 255
                    elif data[i + 1] == 0x14:
                        self.vbuf[index].uv.x = float(unpack_from(">h", data, i + 4)[0])
                        self.vbuf[index].uv.y = float(unpack_from(">h", data, i + 6)[0])
                except IndexError:
                    if not extraLenient:
                        log.exception('Bad vertex indices in 0x02 at 0x%X %08X %08X', i, w0, w1)
            elif data[i] == 0x05 or data[i] == 0x06:
                if has_tex:
                    material = None
                    for j in range(len(self.material)):
                        if self.material[j].name == "mtl_%08X" % self.tile[0].data:
                            material = self.material[j]
                            break
                    if material == None:
                        material = self.tile[0].create(self.segment, self.use_transparency, prefix=self.prefix)
                        if material:
                            self.material.append(material)
                    has_tex = False
                v1, v2 = None, None
                vi1, vi2 = -1, -1
                if not importTextures:
                    material = None
                nbefore_props = ['verts','uvs','colors','vgroups','faces','faces_use_smooth','normals']
                nbefore_lengths = [(nbefore_prop, len(getattr(mesh, nbefore_prop))) for nbefore_prop in nbefore_props]
                # a1 a2 a3 are microcode values
                def addTri(a1, a2, a3):
                    try:
                        verts = [self.vbuf[a >> 1] for a in (a1,a2,a3)]
                    except IndexError:
                        if extraLenient:
                            return False
                        raise
                    verts_pos = [(v.pos.x, v.pos.y, v.pos.z) for v in verts]
                    verts_index = [mesh.verts.index(pos) if pos in mesh.verts else None for pos in verts_pos]
                    for j in range(3):
                        if verts_index[j] is None:
                            mesh.verts.append(verts_pos[j])
                            verts_index[j] = len(mesh.verts) - 1
                    mesh.uvs.append(material)
                    face_normals = []
                    for j in range(3):
                        v = verts[j]
                        vi = verts_index[j]
                        # todo is this computation of shadeColor correct?
                        sc = (((v.normal.x + v.normal.y + v.normal.z) / 3) + 1.0) / 2
                        if checkUseVertexAlpha():
                            self.vertexColor = Vector([v.color[0], v.color[1], v.color[2], v.color[3]])
                        else:
                            self.vertexColor = Vector([v.color[0], v.color[1], v.color[2]])
                        self.shadeColor = Vector([sc, sc, sc])
                        mesh.colors.append(self.getCombinerColor())
                        mesh.uvs.append((self.tile[0].offset.x + v.uv.x * self.tile[0].ratio.x, self.tile[0].offset.y - v.uv.y * self.tile[0].ratio.y))
                        if hierarchy:
                            if v.limb:
                                limb_name = 'limb_%02i' % v.limb.index
                                if not (limb_name in mesh.vgroups):
                                    mesh.vgroups[limb_name] = []
                                mesh.vgroups[limb_name].append(vi)
                        face_normals.append((vi, (v.normal.x, v.normal.y, v.normal.z)))
                    mesh.faces.append(tuple(verts_index))
                    mesh.faces_use_smooth.append('G_SHADE' in self.geometryModeFlags and 'G_SHADING_SMOOTH' in self.geometryModeFlags)
                    mesh.normals.append(tuple(face_normals))
                    if len(set(verts_index)) < 3 and not extraLenient:
                        log.warning('Found empty tri! %d %d %d' % tuple(verts_index))
                    return True

                try:
                    revert = not addTri(data[i+1], data[i+2], data[i+3])
                    if data[i] == 0x06:
                        revert = revert or not addTri(data[i+4+1], data[i+4+2], data[i+4+3])
                except:
                    log.exception('Failed to import vertices and/or their data from 0x%X', i)
                    revert = True
                if revert:
                    # revert any change
                    for nbefore_prop, nbefore in nbefore_lengths:
                        val_prop = getattr(mesh, nbefore_prop)
                        while len(val_prop) > nbefore:
                            val_prop.pop()
            # G_TEXTURE
            elif data[i] == 0xD7:
                log.debug('0xD7 G_TEXTURE used, but unimplemented')
                # fixme ?
#                for i in range(2):
#                    if ((w1 >> 16) & 0xFFFF) < 0xFFFF:
#                        self.tile[i].scale.x = ((w1 >> 16) & 0xFFFF) * 0.0000152587891
#                    else:
#                        self.tile[i].scale.x = 1.0
#                    if (w1 & 0xFFFF) < 0xFFFF:
#                        self.tile[i].scale.y = (w1 & 0xFFFF) * 0.0000152587891
#                    else:
#                        self.tile[i].scale.y = 1.0
                pass
            # G_POPMTX
            elif data[i] == 0xD8 and enableMatrices:
                if hierarchy and len(matrix) > 1:
                    matrix.pop()
            # G_MTX
            elif data[i] == 0xDA and enableMatrices:
                log.debug('0xDA G_MTX used, but implementation may be faulty')
                # fixme this looks super weird, not sure what it's doing either
                if hierarchy and data[i + 4] == 0x0D:
                    if (data[i + 3] & 0x04) == 0:
                        matrixLimb = hierarchy.getMatrixLimb(unpack_from(">L", data, i + 4)[0])
                        if (data[i + 3] & 0x02) == 0:
                            newMatrixLimb = Limb()
                            newMatrixLimb.index = matrixLimb.index
                            newMatrixLimb.pos = (Vector([matrixLimb.pos.x, matrixLimb.pos.y, matrixLimb.pos.z]) + matrix[len(matrix) - 1].pos) / 2
                            matrixLimb = newMatrixLimb
                        if (data[i + 3] & 0x01) == 0:
                            matrix.append(matrixLimb)
                        else:
                            matrix[len(matrix) - 1] = matrixLimb
                    else:
                        matrix.append(matrix[len(matrix) - 1])
                elif hierarchy:
                    log.error("unknown limb %08X %08X" % (w0, w1))
            # G_DL
            elif data[i] == 0xDE:
                log.trace('G_DE at 0x%X %08X%08X', segmentMask | i, w0, w1)
                #mesh.create(mesh_name_format, hierarchy, offset, self.checkUseNormals())
                #mesh.__init__()
                #offset = segmentMask | i
                if validOffset(self.segment, w1):
                    buildRec(w1)
                if data[i + 1] != 0x00:
                    mesh.create(mesh_name_format, hierarchy, offset, self.checkUseNormals(), prefix=self.prefix)
                    self.alreadyRead[segment].append((startOffset,i))
                    return
            # G_ENDDL
            elif data[i] == 0xDF:
                log.trace('G_ENDDL at 0x%X %08X%08X', segmentMask | i, w0, w1)
                mesh.create(mesh_name_format, hierarchy, offset, self.checkUseNormals(), prefix=self.prefix)
                self.alreadyRead[segment].append((startOffset,i))
                return
            # handle "LOD dlists"
            elif data[i] == 0xE1:
                # 4 bytes starting at data[i+8+4] is a distance to check for displaying this dlist
                #mesh.create(mesh_name_format, hierarchy, offset, self.checkUseNormals())
                #mesh.__init__()
                #offset = segmentMask | i
                if validOffset(self.segment, w1):
                    buildRec(w1)
                else:
                    log.warning('Invalid 0xE1 offset 0x%04X, skipping', w1)
            # G_RDPPIPESYNC
            elif data[i] == 0xE7:
                #mesh.create(mesh_name_format, hierarchy, offset, self.checkUseNormals())
                #mesh.__init__()
                #offset = segmentMask | i
                pass
            elif data[i] == 0xF0:
                self.palSize = ((w1 & 0x00FFF000) >> 13) + 1
            elif data[i] == 0xF2:
                self.tile[self.curTile].rect.x = (w0 & 0x00FFF000) >> 14
                self.tile[self.curTile].rect.y = (w0 & 0x00000FFF) >> 2
                self.tile[self.curTile].rect.z = (w1 & 0x00FFF000) >> 14
                self.tile[self.curTile].rect.w = (w1 & 0x00000FFF) >> 2
                self.tile[self.curTile].width = (self.tile[self.curTile].rect.z - self.tile[self.curTile].rect.x) + 1
                self.tile[self.curTile].height = (self.tile[self.curTile].rect.w - self.tile[self.curTile].rect.y) + 1
                self.tile[self.curTile].texBytes = int(self.tile[self.curTile].width * self.tile[self.curTile].height) << 1
                if (self.tile[self.curTile].texBytes >> 16) == 0xFFFF:
                    self.tile[self.curTile].texBytes = self.tile[self.curTile].size << 16 >> 15
                self.tile[self.curTile].calculateSize()
            # G_LOADTILE, G_TEXRECT, G_SETZIMG, G_SETCIMG (2d "direct" drawing?)
            elif data[i] == 0xF4 or data[i] == 0xE4 or data[i] == 0xFE or data[i] == 0xFF:
                log.debug('0x%X %08X : %08X', data[i], w0, w1)
            # G_SETTILE
            elif data[i] == 0xF5:
                self.tile[self.curTile].texFmt = (w0 >> 21) & 0b111
                self.tile[self.curTile].texSiz = (w0 >> 19) & 0b11
                self.tile[self.curTile].lineSize = (w0 >> 9) & 0x1FF
                self.tile[self.curTile].clip.x = (w1 >> 8) & 0x03
                self.tile[self.curTile].clip.y = (w1 >> 18) & 0x03
                self.tile[self.curTile].mask.x = (w1 >> 4) & 0x0F
                self.tile[self.curTile].mask.y = (w1 >> 14) & 0x0F
                self.tile[self.curTile].tshift.x = w1 & 0x0F
                self.tile[self.curTile].tshift.y = (w1 >> 10) & 0x0F
            elif data[i] == 0xFA:
                self.primColor = Vector([((w1 >> (8*(3-i))) & 0xFF) / 255 for i in range(4)])
                log.debug('new primColor -> %r', self.primColor)
                if enablePrimColor and self.primColor.w != 1 and not checkUseVertexAlpha():
                    log.warning('primColor %r has non-opaque alpha, merging it into vertex colors may produce unexpected results' % self.primColor)
                #self.primColor = Vector([min(((w1 >> 24) & 0xFF) / 255, 1.0), min(0.003922 * ((w1 >> 16) & 0xFF), 1.0), min(0.003922 * ((w1 >> 8) & 0xFF), 1.0), min(0.003922 * ((w1) & 0xFF), 1.0)])
            elif data[i] == 0xFB:
                self.envColor = Vector([((w1 >> (8*(3-i))) & 0xFF) / 255 for i in range(4)])
                log.debug('new envColor -> %r', self.envColor)
                if enableEnvColor and self.envColor.w != 1 and not checkUseVertexAlpha():
                    log.warning('envColor %r has non-opaque alpha, merging it into vertex colors may produce unexpected results' % self.envColor)
                #self.envColor = Vector([min(0.003922 * ((w1 >> 24) & 0xFF), 1.0), min(0.003922 * ((w1 >> 16) & 0xFF), 1.0), min(0.003922 * ((w1 >> 8) & 0xFF), 1.0)])
                if invertEnvColor:
                    self.envColor = Vector([1 - c for c in self.envColor])
            elif data[i] == 0xFD:
                try:
                    if data[i - 8] == 0xF2:
                        self.curTile = 1
                    else:
                        self.curTile = 0
                except:
                    log.exception('Failed to switch texel? at 0x%X', i)
                    pass
                try:
                    if data[i + 8] == 0xE8:
                        self.tile[0].palette = w1
                    else:
                        self.tile[self.curTile].data = w1
                except:
                    log.exception('Failed to switch texel data? at 0x%X', i)
                    pass
                has_tex = True
            # G_CULLDL, G_BRANCH_Z, G_SETOTHERMODE_L, G_SETOTHERMODE_H, G_RDPLOADSYNC, G_RDPTILESYNC, G_LOADBLOCK,
            elif data[i] in (0x03,0x04,0xE2,0xE3,0xE6,0xE8,0xF3,):
                # not relevant for importing
                pass
            # G_GEOMETRYMODE
            elif data[i] == 0xD9:
                # todo do not push mesh if geometry mode doesnt actually change?
                #mesh.create(mesh_name_format, hierarchy, offset, self.checkUseNormals())
                #mesh.__init__()
                #offset = segmentMask | i
                # https://wiki.cloudmodding.com/oot/F3DZEX#RSP_Geometry_Mode
                # todo SharpOcarina tags
                geometryModeMasks = {
                    'G_ZBUFFER':            0b00000000000000000000000000000001,
                    'G_SHADE':              0b00000000000000000000000000000100, # used by 0x05/0x06 for mesh.faces_use_smooth
                    'G_CULL_FRONT':         0b00000000000000000000001000000000, # todo set culling (not possible per-face or per-material or even per-object apparently) / SharpOcarina tags
                    'G_CULL_BACK':          0b00000000000000000000010000000000, # todo same
                    'G_FOG':                0b00000000000000010000000000000000,
                    'G_LIGHTING':           0b00000000000000100000000000000000,
                    'G_TEXTURE_GEN':        0b00000000000001000000000000000000, # todo billboarding?
                    'G_TEXTURE_GEN_LINEAR': 0b00000000000010000000000000000000, # todo billboarding?
                    'G_SHADING_SMOOTH':     0b00000000001000000000000000000000, # used by 0x05/0x06 for mesh.faces_use_smooth
                    'G_CLIPPING':           0b00000000100000000000000000000000,
                }
                clearbits = ~w0 & 0x00FFFFFF
                setbits = w1
                for flagName, flagMask in geometryModeMasks.items():
                    if clearbits & flagMask:
                        self.geometryModeFlags.discard(flagName)
                        clearbits = clearbits & ~flagMask
                    if setbits & flagMask:
                        self.geometryModeFlags.add(flagName)
                        setbits = setbits & ~flagMask
                log.debug('Geometry mode flags as of 0x%X: %r', i, self.geometryModeFlags)
                """
                # many unknown flags. keeping this commented out for any further research
                if clearbits:
                    log.warning('Unknown geometry mode flag at 0x%X in clearbits %s', i, bin(clearbits))
                if setbits:
                    log.warning('Unknown geometry mode flag at 0x%X in setbits %s', i, bin(setbits))
                """
            # G_SETCOMBINE
            elif data[i] == 0xFC:
                # https://wiki.cloudmodding.com/oot/F3DZEX/Opcode_Details#0xFC_.E2.80.94_G_SETCOMBINE
                pass # todo
            else:
                log.warning('Skipped (unimplemented) opcode 0x%02X' % data[i])
        log.warning('Reached end of dlist started at 0x%X', startOffset)
        mesh.create(mesh_name_format, hierarchy, offset, self.checkUseNormals(), prefix=self.prefix)
        self.alreadyRead[segment].append((startOffset,endOffset))

    def LinkTpose(self, hierarchy):
        log = getLogger('F3DZEX.LinkTpose')
        segment = []
        data = self.segment[0x06]
        segment = self.segment
        RX, RY, RZ = 0,0,0
        BoneCount  = hierarchy.limbCount
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = True
        bonesIndx = [0,-90,0,0,0,0,0,0,0,90,0,0,0,180,0,0,-180,0,0,0,0]
        bonesIndy = [0,90,0,0,0,90,0,0,90,-90,-90,-90,0,0,0,90,0,0,90,0,0]
        bonesIndz = [0,0,0,0,0,0,0,0,0,0,0,0,0,-90,0,0,90,0,0,0,0]

        log.info("Link T Pose...")
        for i in range(BoneCount):
            bIndx = ((BoneCount-1) - i)
            if (i > -1):
                bone = hierarchy.armature.bones["limb_%02i" % (bIndx)]
                bone.select = True
                bpy.ops.transform.rotate(value = radians(bonesIndx[bIndx]), axis=(0, 0, 0), constraint_axis=(True, False, False))
                bpy.ops.transform.rotate(value = radians(bonesIndz[bIndx]), axis=(0, 0, 0), constraint_axis=(False, False, True))
                bpy.ops.transform.rotate(value = radians(bonesIndy[bIndx]), axis=(0, 0, 0), constraint_axis=(False, True, False))
                bpy.ops.pose.select_all(action="DESELECT")

        hierarchy.armature.bones["limb_00"].select = True ## Translations
        bpy.ops.transform.translate(value =(0, 0, 0), constraint_axis=(True, False, False))
        bpy.ops.transform.translate(value = (0, 0, 50), constraint_axis=(False, False, True))
        bpy.ops.transform.translate(value = (0, 0, 0), constraint_axis=(False, True, False))
        bpy.ops.pose.select_all(action="DESELECT")
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

        for i in range(BoneCount):
            bIndx = i
            if (i > -1):
                bone = hierarchy.armature.bones["limb_%02i" % (bIndx)]
                bone.select = True
                bpy.ops.transform.rotate(value = radians(-bonesIndy[bIndx]), axis=(0, 0, 0), constraint_axis=(False, True, False))
                bpy.ops.transform.rotate(value = radians(-bonesIndz[bIndx]), axis=(0, 0, 0), constraint_axis=(False, False, True))
                bpy.ops.transform.rotate(value = radians(-bonesIndx[bIndx]), axis=(0, 0, 0), constraint_axis=(True, False, False))
                bpy.ops.pose.select_all(action="DESELECT")

        hierarchy.armature.bones["limb_00"].select = True ## Translations
        bpy.ops.transform.translate(value =(0, 0, 0), constraint_axis=(True, False, False))
        bpy.ops.transform.translate(value = (0, 0, -50), constraint_axis=(False, False, True))
        bpy.ops.transform.translate(value = (0, 0, 0), constraint_axis=(False, True, False))
        bpy.ops.pose.select_all(action="DESELECT")

    def buildLinkAnimations(self, hierarchy, newframe):
        global AnimtoPlay
        global Animscount
        log = getLogger('F3DZEX.buildLinkAnimations')
        # todo buildLinkAnimations hasn't been rewritten/improved like buildAnimations has
        log.warning('The code to build link animations has not been improved/tested for a while, not sure what features it lacks compared to regular animations, pretty sure it will not import all animations')
        segment = []
        rot_indx = 0
        rot_indy = 0
        rot_indz = 0
        data = self.segment[0x06]
        segment = self.segment
        n_anims = self.animTotal
        seg, offset = splitOffset(hierarchy.offset)
        BoneCount  = hierarchy.limbCount
        RX, RY, RZ = 0,0,0
        frameCurrent = newframe

        if (AnimtoPlay > 0 and AnimtoPlay <= n_anims):
          currentanim = AnimtoPlay - 1
        else:
          currentanim = 0

        log.info("currentanim: %d frameCurrent: %d", currentanim+1, frameCurrent+1)
        AnimationOffset = self.offsetAnims[currentanim]
        TAnimationOffset = self.offsetAnims[currentanim]
        AniSeg = AnimationOffset >> 24
        AnimationOffset &= 0xFFFFFF
        rot_offset = AnimationOffset
        rot_offset += (frameCurrent * (BoneCount * 6 + 8))
        frameTotal = self.animFrames[currentanim]
        rot_offset += BoneCount * 6

        Trot_offset = TAnimationOffset & 0xFFFFFF
        Trot_offset += (frameCurrent * (BoneCount * 6 + 8))
        TRX = unpack_from(">h", segment[AniSeg], Trot_offset)[0]
        Trot_offset += 2
        TRZ = unpack_from(">h", segment[AniSeg], Trot_offset)[0]
        Trot_offset += 2
        TRY = -unpack_from(">h", segment[AniSeg], Trot_offset)[0]
        Trot_offset += 2
        BoneListListOffset = unpack_from(">L", segment[seg], offset)[0]
        BoneListListOffset &= 0xFFFFFF

        BoneOffset = unpack_from(">L", segment[seg], BoneListListOffset + (0 << 2))[0]
        S_Seg = (BoneOffset >> 24) & 0xFF
        BoneOffset &= 0xFFFFFF
        TRX += unpack_from(">h", segment[S_Seg], BoneOffset)[0]
        TRZ += unpack_from(">h", segment[S_Seg], BoneOffset + 2)[0]
        TRY += -unpack_from(">h", segment[S_Seg], BoneOffset + 4)[0]
        newLocx = TRX / 79
        newLocz = -25.5
        newLocz += TRZ / 79
        newLocy = TRY / 79

        bpy.context.scene.tool_settings.use_keyframe_insert_auto = True

        for i in range(BoneCount):
            bIndx = ((BoneCount-1) - i) # Had to reverse here, cuz didn't find a way to rotate bones on LOCAL space, start rotating from last to first bone on hierarchy GLOBAL.
            RX = unpack_from(">h", segment[AniSeg], rot_offset)[0]
            rot_offset -= 2
            RY = unpack_from(">h", segment[AniSeg], rot_offset + 4)[0]
            rot_offset -= 2
            RZ = unpack_from(">h", segment[AniSeg], rot_offset + 8)[0]
            rot_offset -= 2

            RX /= (182.04444444444444444444)
            RY /= (182.04444444444444444444)
            RZ /= (182.04444444444444444444)

            RXX = (RX)
            RYY = (-RZ)
            RZZ = (RY)

            log.trace('limb: %d RX %d RZ %d RY %d anim: %d frame: %d', bIndx, int(RXX), int(RZZ), int(RYY), currentanim+1, frameCurrent+1)
            if (i > -1):
                bone = hierarchy.armature.bones["limb_%02i" % (bIndx)]
                bone.select = True
                bpy.ops.transform.rotate(value = radians(RXX), axis=(0, 0, 0), constraint_axis=(True, False, False))
                bpy.ops.transform.rotate(value = radians(RZZ), axis=(0, 0, 0), constraint_axis=(False, False, True))
                bpy.ops.transform.rotate(value = radians(RYY), axis=(0, 0, 0), constraint_axis=(False, True, False))
                bpy.ops.pose.select_all(action="DESELECT")

        hierarchy.armature.bones["limb_00"].select = True ## Translations
        bpy.ops.transform.translate(value =(newLocx, 0, 0), constraint_axis=(True, False, False))
        bpy.ops.transform.translate(value = (0, 0, newLocz), constraint_axis=(False, False, True))
        bpy.ops.transform.translate(value = (0, newLocy, 0), constraint_axis=(False, True, False))
        bpy.ops.pose.select_all(action="DESELECT")

        if (frameCurrent < (frameTotal - 1)):## Next Frame ### Could have done some math here but... just reverse previus frame, so it just repose.
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

            hierarchy.armature.bones["limb_00"].select = True ## Translations
            bpy.ops.transform.translate(value = (-newLocx, 0, 0), constraint_axis=(True, False, False))
            bpy.ops.transform.translate(value = (0, 0, -newLocz), constraint_axis=(False, False, True))
            bpy.ops.transform.translate(value = (0, -newLocy, 0), constraint_axis=(False, True, False))
            bpy.ops.pose.select_all(action="DESELECT")

            rot_offset = AnimationOffset
            rot_offset += (frameCurrent * (BoneCount * 6 + 8))
            rot_offset += 6
            for i in range(BoneCount):
                RX = unpack_from(">h", segment[AniSeg], rot_offset)[0]
                rot_offset += 2
                RY = unpack_from(">h", segment[AniSeg], rot_offset)[0]
                rot_offset += 2
                RZ = unpack_from(">h", segment[AniSeg], rot_offset)[0]
                rot_offset += 2

                RX /= (182.04444444444444444444)
                RY /= (182.04444444444444444444)
                RZ /= (182.04444444444444444444)

                RXX = (-RX)
                RYY = (RZ)
                RZZ = (-RY)

                log.trace("limb: %d RX %d RZ %d RY %d anim: %d frame: %d", i, int(RXX), int(RZZ), int(RYY), currentanim+1, frameCurrent+1)
                if (i > -1):
                    bone = hierarchy.armature.bones["limb_%02i" % (i)]
                    bone.select = True
                    bpy.ops.transform.rotate(value = radians(RYY), axis=(0, 0, 0), constraint_axis=(False, True, False))
                    bpy.ops.transform.rotate(value = radians(RZZ), axis=(0, 0, 0), constraint_axis=(False, False, True))
                    bpy.ops.transform.rotate(value = radians(RXX), axis=(0, 0, 0), constraint_axis=(True, False, False))
                    bpy.ops.pose.select_all(action="DESELECT")

            bpy.context.scene.frame_end += 1
            bpy.context.scene.frame_current += 1
            frameCurrent += 1
            self.buildLinkAnimations(hierarchy, frameCurrent)
        else:
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
            bpy.context.scene.frame_current = 1

    def buildAnimations(self, hierarchyMostBones, newframe):
        log = getLogger('F3DZEX.buildAnimations')
        rot_indx = 0
        rot_indy = 0
        rot_indz = 0
        Trot_indx = 0
        Trot_indy = 0
        Trot_indz = 0
        segment = self.segment
        RX, RY, RZ = 0,0,0
        n_anims = self.animTotal
        if (AnimtoPlay > 0 and AnimtoPlay <= n_anims):
            currentanim = AnimtoPlay - 1
        else:
            currentanim = 0

        AnimationOffset = self.offsetAnims[currentanim]
        #seg, offset = splitOffset(hierarchy.offset) # not used, MUST be not relevant because we use hierarchyMostBones (its armature) as placeholder
        BoneCountMax = hierarchyMostBones.limbCount
        armature = hierarchyMostBones.armature
        frameCurrent = newframe

        if not validOffset(segment, AnimationOffset):
            log.warning('Skipping invalid animation offset 0x%X', AnimationOffset)
            return

        AniSeg = AnimationOffset >> 24
        AnimationOffset &= 0xFFFFFF

        frameTotal = unpack_from(">h", segment[AniSeg], (AnimationOffset))[0]
        rot_vals_addr = unpack_from(">L", segment[AniSeg], (AnimationOffset + 4))[0]
        RotIndexoffset = unpack_from(">L", segment[AniSeg], (AnimationOffset + 8))[0]
        Limit = unpack_from(">H", segment[AniSeg], (AnimationOffset + 12))[0] # todo no idea what this is

        rot_vals_addr  &= 0xFFFFFF
        RotIndexoffset &= 0xFFFFFF

        rot_vals_max_length = int ((RotIndexoffset - rot_vals_addr) / 2)
        if rot_vals_max_length < 0:
            log.info('rotation indices (animation data) is located before indexed rotation values, this is weird but fine')
            rot_vals_max_length = (len(segment[AniSeg]) - rot_vals_addr) // 2
        rot_vals_cache = []
        def rot_vals(index, errorDefault=0):
            if index < 0 or (rot_vals_max_length and index >= rot_vals_max_length):
                log.trace('index in rotations table %d is out of bounds (rotations table is <= %d long)', index, rot_vals_max_length)
                return errorDefault
            if index >= len(rot_vals_cache):
                rot_vals_cache.extend(unpack_from(">h", segment[AniSeg], (rot_vals_addr) + (j * 2))[0] for j in range(len(rot_vals_cache),index+1))
                log.trace('Computed rot_vals_cache up to %d %r', index, rot_vals_cache)
            return rot_vals_cache[index]

        bpy.context.scene.tool_settings.use_keyframe_insert_auto = True
        bpy.context.scene.frame_end = frameTotal
        bpy.context.scene.frame_current = frameCurrent + 1

        log.log(
            logging.INFO if (frameCurrent + 1) % min(20, max(min(10, frameTotal), frameTotal // 3)) == 0 else logging.DEBUG,
            "anim: %d/%d frame: %d/%d", currentanim+1, self.animTotal, frameCurrent+1, frameTotal)

        ## Translations
        Trot_indx = unpack_from(">h", segment[AniSeg], RotIndexoffset)[0]
        Trot_indy = unpack_from(">h", segment[AniSeg], RotIndexoffset + 2)[0]
        Trot_indz = unpack_from(">h", segment[AniSeg], RotIndexoffset + 4)[0]

        if (Trot_indx >= Limit):
            Trot_indx += frameCurrent
        if (Trot_indz >= Limit):
            Trot_indz += frameCurrent
        if (Trot_indy >= Limit):
            Trot_indy += frameCurrent

        TRX = rot_vals(Trot_indx)
        TRZ = rot_vals(Trot_indy)
        TRY = rot_vals(Trot_indz)

        global scaleFactor
        newLocx =  TRX * scaleFactor
        newLocz =  TRZ * scaleFactor
        newLocy = -TRY * scaleFactor
        log.trace("X %d Y %d Z %d", int(TRX), int(TRY), int(TRZ))

        log.trace("       %d Frames %d still values %f tracks",frameTotal, Limit, ((rot_vals_max_length - Limit) / frameTotal)) # what is this debug message?
        for i in range(BoneCountMax):
            bIndx = ((BoneCountMax-1) - i) # Had to reverse here, cuz didn't find a way to rotate bones on LOCAL space, start rotating from last to first bone on hierarchy GLOBAL.

            if RotIndexoffset + (bIndx * 6) + 10 + 2 > len(segment[AniSeg]):
                log.trace('Ignoring bone %d in animation %d, rotation table does not have that many entries', bIndx, AnimtoPlay)
                continue

            rot_indexx = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 6)[0]
            rot_indexy = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 8)[0]
            rot_indexz = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 10)[0]

            rot_indx = rot_indexx
            rot_indy = rot_indexy
            rot_indz = rot_indexz

            if (rot_indx >= Limit):
                rot_indx += frameCurrent
            if (rot_indy >= Limit):
                rot_indy += frameCurrent
            if (rot_indz >= Limit):
                rot_indz += frameCurrent

            RX = rot_vals(rot_indx, False)
            RY = rot_vals(rot_indz, False)
            RZ = rot_vals(rot_indy, False)

            if RX is False or RY is False or RZ is False:
                log.trace('Ignoring bone %d in animation %d, rotation table did not have the entry', bIndx, AnimtoPlay)
                continue

            RX /= 182.04444444444444444444 # = 0x10000 / 360
            RY /= -182.04444444444444444444
            RZ /= 182.04444444444444444444

            RXX = radians(RX)
            RYY = radians(RY)
            RZZ = radians(RZ)

            log.trace("limb: %d XIdx: %d %d YIdx: %d %d ZIdx: %d %d frameTotal: %d", bIndx, rot_indexx, rot_indx, rot_indexy, rot_indy, rot_indexz, rot_indz, frameTotal)
            log.trace("limb: %d RX %d RZ %d RY %d anim: %d frame: %d frameTotal: %d", bIndx, int(RX), int(RZ), int(RY), currentanim+1, frameCurrent+1, frameTotal)
            if (bIndx > -1):
                bone = armature.data.bones["limb_%02i" % (bIndx)]
                bone.select = True
                bpy.ops.transform.rotate(value = RXX, axis=(0, 0, 0), constraint_axis=(True, False, False))
                bpy.ops.transform.rotate(value = RZZ, axis=(0, 0, 0), constraint_axis=(False, False, True))
                bpy.ops.transform.rotate(value = RYY, axis=(0, 0, 0), constraint_axis=(False, True, False))
                bpy.ops.pose.select_all(action="DESELECT")

        bone = armature.pose.bones["limb_00"]
        bone.location += mathutils.Vector((newLocx,newLocz,-newLocy))
        bone.keyframe_insert(data_path='location')

        ### Could have done some math here but... just reverse previus frame, so it just repose.
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

        bone = armature.pose.bones["limb_00"]
        bone.location -= mathutils.Vector((newLocx,newLocz,-newLocy))

        for i in range(BoneCountMax):
            bIndx = i

            if RotIndexoffset + (bIndx * 6) + 10 + 2 > len(segment[AniSeg]):
                log.trace('Ignoring bone %d in animation %d, rotation table does not have that many entries', bIndx, AnimtoPlay)
                continue

            rot_indexx = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 6)[0]
            rot_indexy = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 8)[0]
            rot_indexz = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 10)[0]

            rot_indx = rot_indexx
            rot_indy = rot_indexy
            rot_indz = rot_indexz

            if (rot_indx > Limit):
                rot_indx += frameCurrent
            if (rot_indy > Limit):
                rot_indy += frameCurrent
            if (rot_indz > Limit):
                rot_indz += frameCurrent

            RX = rot_vals(rot_indx, False)
            RY = rot_vals(rot_indz, False)
            RZ = rot_vals(rot_indy, False)

            if RX is False or RY is False or RZ is False:
                log.trace('Ignoring bone %d in animation %d, rotation table did not have the entry', bIndx, AnimtoPlay)
                continue

            RX /= -182.04444444444444444444
            RY /= 182.04444444444444444444
            RZ /= -182.04444444444444444444

            RXX = radians(RX)
            RYY = radians(RY)
            RZZ = radians(RZ)

            log.trace("limb: %d XIdx: %d %d YIdx: %d %d ZIdx: %d %d frameTotal: %d", i, rot_indexx, rot_indx, rot_indexy, rot_indy, rot_indexz, rot_indz, frameTotal)
            log.trace("limb: %d RX %d RZ %d RY %d anim: %d frame: %d frameTotal: %d", bIndx, int(RX), int(RZ), int(RY), currentanim+1, frameCurrent+1, frameTotal)
            if (bIndx > -1):
                bone = armature.data.bones["limb_%02i" % (bIndx)]
                bone.select = True
                bpy.ops.transform.rotate(value = RYY, axis=(0, 0, 0), constraint_axis=(False, True, False))
                bpy.ops.transform.rotate(value = RZZ, axis=(0, 0, 0), constraint_axis=(False, False, True))
                bpy.ops.transform.rotate(value = RXX, axis=(0, 0, 0), constraint_axis=(True, False, False))
                bpy.ops.pose.select_all(action="DESELECT")

        if (frameCurrent < (frameTotal - 1)):## Next Frame
            frameCurrent += 1
            self.buildAnimations(hierarchyMostBones, frameCurrent)
        else:
            bpy.context.scene.frame_current = 1

global Animscount
Animscount = 1
