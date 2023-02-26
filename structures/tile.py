# Tile functions

def splitOffset(offset):
    return offset >> 24, offset & 0x00FFFFFF

def translateRotation(rot):
    """ axis, angle """
    return Matrix.Rotation(rot[3], 4, Vector(rot[:3]))

def validOffset(segment, offset):
    seg, offset = splitOffset(offset)
    if seg > 15:
        return False
    if offset >= len(segment[seg]):
        return False
    return True

def pow2(val):
    i = 1
    while i < val:
        i <<= 1
    return int(i)

def powof(val):
    num, i = 1, 0
    while num < val:
        num <<= 1
        i += 1
    return int(i)

def checkUseVertexAlpha():
    global useVertexAlpha
    return useVertexAlpha

class Tile:
    def __init__(self):
        self.current_texture_file_path = None
        self.texFmt, self.texBytes = 0x00, 0
        self.width, self.height = 0, 0
        self.rWidth, self.rHeight = 0, 0
        self.texSiz = 0
        self.lineSize = 0
        self.rect = Vector([0, 0, 0, 0])
        self.scale = Vector([1, 1])
        self.ratio = Vector([1, 1])
        self.clip = Vector([0, 0])
        self.mask = Vector([0, 0])
        self.shift = Vector([0, 0])
        self.tshift = Vector([0, 0])
        self.offset = Vector([0, 0])
        self.data = 0x00000000
        self.palette = 0x00000000

    def getFormatName(self):
        fmt = ['RGBA','YUV','CI','IA','I']
        siz = ['4','8','16','32']
        return '%s%s' % (
            fmt[self.texFmt] if self.texFmt < len(fmt) else 'UnkFmt',
            siz[self.texSiz] if self.texSiz < len(siz) else '_UnkSiz'
        )

    def create(self, segment, use_transparency, prefix=""):
        # todo texture files are written several times, at each usage
        log = getLogger('Tile.create')
        fmtName = self.getFormatName()
        #Noka here
        extrastring = ""
        w = self.rWidth
        if int(self.clip.x) & 1 != 0:
            if replicateTexMirrorBlender:
                w <<= 1
            if enableTexMirrorSharpOcarinaTags:
                extrastring += "#MirrorX"
        h = self.rHeight
        if int(self.clip.y) & 1 != 0:
            if replicateTexMirrorBlender:
                h <<= 1
            if enableTexMirrorSharpOcarinaTags:
                extrastring += "#MirrorY"
        if int(self.clip.x) & 2 != 0 and enableTexClampSharpOcarinaTags:
            extrastring += "#ClampX"
        if int(self.clip.y) & 2 != 0 and enableTexClampSharpOcarinaTags:
            extrastring += "#ClampY"
        self.current_texture_file_path = (
            '%s/textures/%s%s_%08X%s%s.tga'
            % (fpath, prefix, fmtName, self.data,
                ('_pal%08X' % self.palette) if self.texFmt == 2 else '',
                extrastring))
        if exportTextures: # fixme exportTextures == False breaks the script
            try:
                os.mkdir(fpath + "/textures")
            except FileExistsError:
                pass
            except:
                log.exception('Could not create textures directory %s' % (fpath + "/textures"))
                pass
            if not os.path.isfile(self.current_texture_file_path):
                log.debug('Writing texture %s (format 0x%02X)' % (self.current_texture_file_path, self.texFmt))
                file = open(self.current_texture_file_path, 'wb')
                self.write_error_encountered = False
                if self.texFmt == 2:
                    if self.texSiz not in (0, 1):
                        log.error('Unknown texture format %d with pixel size %d', self.texFmt, self.texSiz)
                    p = 16 if self.texSiz == 0 else 256
                    file.write(pack("<BBBHHBHHHHBB",
                        0,  # image comment length
                        1,  # 1 = paletted
                        1,  # 1 = indexed uncompressed colors
                        0,  # index of first palette entry (?)
                        p,  # amount of entries in palette
                        32, # bits per pixel
                        0,  # bottom left X (?)
                        0,  # bottom left Y (?)
                        w,  # width
                        h,  # height
                        8,  # pixel depth
                        8   # 8 bits alpha hopefully?
                    ))
                    self.writePalette(file, segment, p)
                else:
                    file.write(pack("<BBBHHBHHHHBB",
                        0, # image comment length
                        0, # no palette
                        2, # uncompressed Truecolor (24-32 bits)
                        0, # irrelevant, no palette
                        0, # irrelevant, no palette
                        0, # irrelevant, no palette
                        0, # bottom left X (?)
                        0, # bottom left Y (?)
                        w, # width
                        h, # height
                        32,# pixel depth
                        8  # 8 bits alpha (?)
                    ))
                if int(self.clip.y) & 1 != 0 and replicateTexMirrorBlender:
                    self.writeImageData(file, segment, True)
                else:
                    self.writeImageData(file, segment)
                file.close()
                if self.write_error_encountered:
                    oldName = self.current_texture_file_path
                    oldNameDir, oldNameBase = os.path.split(oldName)
                    newName = oldNameDir + '/' + prefix + 'fallback_' + oldNameBase
                    log.warning('Moving failed texture file import from %s to %s', oldName, newName)
                    if os.path.isfile(newName):
                        os.remove(newName)
                    os.rename(oldName, newName)
                    self.current_texture_file_path = newName
        try:
            tex_name = prefix + ('tex_%s_%08X' % (fmtName,self.data))
            tex = bpy.data.textures.new(name=tex_name, type='IMAGE')
            img = load_image(self.current_texture_file_path)
            if img:
                tex.image = img
                if int(self.clip.x) & 2 != 0 and enableTexClampBlender:
                    img.use_clamp_x = True
                if int(self.clip.y) & 2 != 0 and enableTexClampBlender:
                    img.use_clamp_y = True
            mtl_name = prefix + ('mtl_%08X' % self.data)
            mtl = bpy.data.materials.new(name=mtl_name)
            if enableShadelessMaterials:
                mtl.use_shadeless = True
            mt = mtl.texture_slots.add()
            mt.texture = tex
            mt.texture_coords = 'UV'
            mt.use_map_color_diffuse = True
            if use_transparency:
                mt.use_map_alpha = True
                tex.use_mipmap = True
                tex.use_interpolation = True
                tex.use_alpha = True
                mtl.use_transparency = True
                mtl.alpha = 0.0
                mtl.game_settings.alpha_blend = 'ALPHA'
            return mtl
        except:
            log.exception('Failed to create material mtl_%08X %r', self.data)
            return None

    def calculateSize(self):
        log = getLogger('Tile.calculateSize')
        maxTxl, lineShift = 0, 0
        # fixme what is maxTxl? this whole function is rather mysterious, not sure how/why it works
        #texFmt 0 2 texSiz 0
        # RGBA CI 4b
        if (self.texFmt == 0 or self.texFmt == 2) and self.texSiz == 0:
            maxTxl = 4096
            lineShift = 4
        # texFmt 3 4 texSiz 0
        # IA I 4b
        elif (self.texFmt == 3 or self.texFmt == 4) and self.texSiz == 0:
            maxTxl = 8192
            lineShift = 4
        # texFmt 0 2 texSiz 1
        # RGBA CI 8b
        elif (self.texFmt == 0 or self.texFmt == 2) and self.texSiz == 1:
            maxTxl = 2048
            lineShift = 3
        # texFmt 3 4 texSiz 1
        # IA I 8b
        elif (self.texFmt == 3 or self.texFmt == 4) and self.texSiz == 1:
            maxTxl = 4096
            lineShift = 3
        # texFmt 0 3 texSiz 2
        # RGBA IA 16b
        elif (self.texFmt == 0 or self.texFmt == 3) and self.texSiz == 2:
            maxTxl = 2048
            lineShift = 2
        # texFmt 2 4 texSiz 2
        # CI I 16b
        elif (self.texFmt == 2 or self.texFmt == 4) and self.texSiz == 2:
            maxTxl = 2048
            lineShift = 0
        # texFmt 0 texSiz 3
        # RGBA 32b
        elif self.texFmt == 0 and self.texSiz == 3:
            maxTxl = 1024
            lineShift = 2
        else:
            log.warning('Unknown format for texture %s texFmt %d texSiz %d', self.current_texture_file_path, self.texFmt, self.texSiz)
        lineWidth = self.lineSize << lineShift
        self.lineSize = lineWidth
        tileWidth = self.rect.z - self.rect.x + 1
        tileHeight = self.rect.w - self.rect.y + 1
        maskWidth = 1 << int(self.mask.x)
        maskHeight = 1 << int(self.mask.y)
        lineHeight = 0
        if lineWidth > 0:
            lineHeight = min(int(maxTxl / lineWidth), tileHeight)
        if self.mask.x > 0 and (maskWidth * maskHeight) <= maxTxl:
            self.width = maskWidth
        elif (tileWidth * tileHeight) <= maxTxl:
            self.width = tileWidth
        else:
            self.width = lineWidth
        if self.mask.y > 0 and (maskWidth * maskHeight) <= maxTxl:
            self.height = maskHeight
        elif (tileWidth * tileHeight) <= maxTxl:
            self.height = tileHeight
        else:
            self.height = lineHeight
        clampWidth, clampHeight = 0, 0
        if self.clip.x == 1:
            clampWidth = tileWidth
        else:
            clampWidth = self.width
        if self.clip.y == 1:
            clampHeight = tileHeight
        else:
            clampHeight = self.height
        if maskWidth > self.width:
            self.mask.x = powof(self.width)
            maskWidth = 1 << int(self.mask.x)
        if maskHeight > self.height:
            self.mask.y = powof(self.height)
            maskHeight = 1 << int(self.mask.y)
        if int(self.clip.x) & 2 != 0:
            self.rWidth = pow2(clampWidth)
        elif int(self.clip.x) & 1 != 0:
            self.rWidth = pow2(maskWidth)
        else:
            self.rWidth = pow2(self.width)
        if int(self.clip.y) & 2 != 0:
            self.rHeight = pow2(clampHeight)
        elif int(self.clip.y) & 1 != 0:
            self.rHeight = pow2(maskHeight)
        else:
            self.rHeight = pow2(self.height)
        self.shift.x, self.shift.y = 1.0, 1.0
        if self.tshift.x > 10:
            self.shift.x = 1 << int(16 - self.tshift.x)
        elif self.tshift.x > 0:
            self.shift.x /= 1 << int(self.tshift.x)
        if self.tshift.y > 10:
            self.shift.y = 1 << int(16 - self.tshift.y)
        elif self.tshift.y > 0:
            self.shift.y /= 1 << int(self.tshift.y)
        self.ratio.x = (self.scale.x * self.shift.x) / self.rWidth
        if not enableToon:
            self.ratio.x /= 32;
        if int(self.clip.x) & 1 != 0 and replicateTexMirrorBlender:
            self.ratio.x /= 2
        self.offset.x = self.rect.x
        self.ratio.y = (self.scale.y * self.shift.y) / self.rHeight
        if not enableToon:
            self.ratio.y /= 32;
        if int(self.clip.y) & 1 != 0 and replicateTexMirrorBlender:
            self.ratio.y /= 2
        self.offset.y = 1.0 + self.rect.y

    def writePalette(self, file, segment, palSize):
        log = getLogger('Tile.writePalette')
        if not validOffset(segment, self.palette + palSize * 2 - 1):
            log.error('Segment offsets 0x%X-0x%X are invalid, writing black palette to %s (has the segment data been loaded?)' % (self.palette, self.palette + palSize * 2 - 1, self.current_texture_file_path))
            for i in range(palSize):
                file.write(pack("L", 0))
            self.write_error_encountered = True
            return
        seg, offset = splitOffset(self.palette)
        for i in range(palSize):
            color = unpack_from(">H", segment[seg], offset + i * 2)[0]
            r = int(255/31 * ((color >> 11) & 0b11111))
            g = int(255/31 * ((color >> 6) & 0b11111))
            b = int(255/31 * ((color >> 1) & 0b11111))
            a = 255 * (color & 1)
            file.write(pack("BBBB", b, g, r, a))

    def writeImageData(self, file, segment, fy=False, df=False):
        log = getLogger('Tile.writeImageData')
        if fy == True:
            dir = (0, self.rHeight, 1)
        else:
            dir = (self.rHeight - 1, -1, -1)
        if self.texSiz <= 3:
            bpp = (0.5,1,2,4)[self.texSiz] # bytes (not bits) per pixel
        else:
            log.warning('Unknown texSiz %d for texture %s, defaulting to 4 bytes per pixel' % (self.texSiz, self.current_texture_file_path))
            bpp = 4
        lineSize = self.rWidth * bpp
        writeFallbackData = False
        if not validOffset(segment, self.data + int(self.rHeight * lineSize) - 1):
            log.error('Segment offsets 0x%X-0x%X are invalid, writing default fallback colors to %s (has the segment data been loaded?)' % (self.data, self.data + int(self.rHeight * lineSize) - 1, self.current_texture_file_path))
            writeFallbackData = True
        if (self.texFmt,self.texSiz) not in (
            (0,2), (0,3), # RGBA16, RGBA32
            #(1,-1), # YUV ? "not used in z64 games"
            (2,0), (2,1), # CI4, CI8
            (3,0), (3,1), (3,2), # IA4, IA8, IA16
            (4,0), (4,1), # I4, I8
        ):
            log.error('Unknown fmt/siz combination %d/%d (%s?)', self.texFmt, self.texSiz, self.getFormatName())
            writeFallbackData = True
        if writeFallbackData:
            size = self.rWidth * self.rHeight
            if int(self.clip.x) & 1 != 0 and replicateTexMirrorBlender:
                size *= 2
            if int(self.clip.y) & 1 != 0 and replicateTexMirrorBlender:
                size *= 2
            for i in range(size):
                if self.texFmt == 2: # CI (paletted)
                    file.write(pack("B", 0))
                else:
                    file.write(pack(">L", 0x000000FF))
            self.write_error_encountered = True
            return
        seg, offset = splitOffset(self.data)
        for i in range(dir[0], dir[1], dir[2]):
            off = offset + int(i * lineSize)
            line = []
            j = 0
            while j < int(self.rWidth * bpp):
                if bpp < 2: # 0.5, 1
                    color = unpack_from("B", segment[seg], off + int(floor(j)))[0]
                    if bpp == 0.5:
                        color = ((color >> 4) if j % 1 == 0 else color) & 0xF
                elif bpp == 2:
                    color = unpack_from(">H", segment[seg], off + j)[0]
                else: # 4
                    color = unpack_from(">L", segment[seg], off + j)[0]
                if self.texFmt == 0: # RGBA
                    if self.texSiz == 2: # RGBA16
                        r = ((color >> 11) & 0b11111) * 255 // 31
                        g = ((color >> 6) & 0b11111) * 255 // 31
                        b = ((color >> 1) & 0b11111) * 255 // 31
                        a = (color & 1) * 255
                    elif self.texSiz == 3: # RGBA32
                        r = (color >> 24) & 0xFF
                        g = (color >> 16) & 0xFF
                        b = (color >> 8) & 0xFF
                        a = color & 0xFF
                elif self.texFmt == 2: # CI
                    if self.texSiz == 0: # CI4
                        p = color
                    elif self.texSiz == 1: # CI8
                        p = color
                elif self.texFmt == 3: # IA
                    if self.texSiz == 0: # IA4
                        r = g = b = (color >> 1) * 255 // 7
                        a = (color & 1) * 255
                    elif self.texSiz == 1: # IA8
                        r = g = b = (color >> 4) * 255 // 15
                        a = (color & 0xF) * 255 // 15
                    elif self.texSiz == 2: # IA16
                        r = g = b = color >> 8
                        a = color & 0xFF
                elif self.texFmt == 4: # I
                    if self.texSiz == 0: # I4
                        r = g = b = a = color * 255 // 15
                    elif self.texSiz == 1: # I8
                        r = g = b = a = color
                try:
                    if self.texFmt == 2: # CI
                        line.append(p)
                    else:
                        line.append((b << 24) | (g << 16) | (r << 8) | a)
                except UnboundLocalError:
                    log.error('Unknown format texFmt %d texSiz %d', self.texFmt, self.texSiz)
                    raise
                """
                if self.texFmt == 0x40 or self.texFmt == 0x48 or self.texFmt == 0x50:
                    line.append(a)
                else:
                    line.append((b << 24) | (g << 16) | (r << 8) | a)
                """
                j += bpp
            if self.texFmt == 2: # CI # in (0x40, 0x48, 0x50):
                file.write(pack("B" * len(line), *line))
            else:
                file.write(pack(">" + "L" * len(line), *line))
            if int(self.clip.x) & 1 != 0 and replicateTexMirrorBlender:
                line.reverse()
                if self.texFmt == 2: # CI # in (0x40, 0x48, 0x50):
                    file.write(pack("B" * len(line), *line))
                else:
                    file.write(pack(">" + "L" * len(line), *line))
        if int(self.clip.y) & 1 != 0 and df == False and replicateTexMirrorBlender:
            if fy == True:
                self.writeImageData(file, segment, False, True)
            else:
                self.writeImageData(file, segment, True, True)
