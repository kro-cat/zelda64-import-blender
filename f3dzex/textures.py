import logging

from .memory import Memory, MemoryException


logger = logging.getLogger(__name__)


class InvalidTextureException(Exception):
    pass


class TexturesLoader:
    def __init__(self):
        pass


class TexturesLoader:
    memory: Memory

    def __init__(self, memory: Memory):
        self.memory = memory

    def load_texture(self, address: int) -> Texture:
        pass

    def load_textures(self):


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

