import logging

from .memory import segment_offset, load_segment, SegmentNotFoundError


logger = logging.getLogger(__name__)

class InvalidHierarchyException(Exception):
    pass

class Hierarchy:
    def __init__(self):
        pass

    @classmethod
    def load(cls, hdr_segment: mmap, offset: int, num_limbs: int):
        # Hierarchy Header

        hdr_format = ">IBxxxBxxx"
        # iiiiiiii pp000000 xx000000
        # i: segment offset of limb index list
        # p: number of parts
        # x: number of display lists

        seg_offs_end = offset + 12
        if (seg_offs_end > hdr_segment.size()):
            raise InvalidHierarchyException("[Hierarchy::load]" \
                    f" header offset 0x{seg_offs_end:06X} is out of bounds" \
                    f" for segment 0x{segment:02X}")
        hdr = unpack(hdr_format, hdr_segment[offset:seg_offs_end])

        hierarchy = cls()

        lidx_seg_num, lidx_seg_offs = segment_offset(hdr[0])
        part_count = hdr[1]
        hierarchy.displaylist_count = hdr[2]

        if ((lidx_seg_num == 0) or (lidx_seg_num > 16)):
            raise InvalidHierarchyException("[Hierarchy::load]" \
                    f" bad segment 0x{lidx_seg_num:02X} in value list address")

        try:
            lidx_segment = load_segment(lidx_seg_num)
        except SegmentNotFoundError as e:
            raise InvalidHierarchyException from e

        def get_values(offs):
            offs_end = offs + (4 * part_count)
            if (offs_end > lidx_segment.size()):
                raise InvalidAnimationException("[Hierarchy::load.get_limbs]" \
                        f" limb offset 0x{offs_end:06X} is out of" \
                        f" bounds for segment 0x{rval_seg_num:02X}")
            return list(unpack(f">{part_count}L", lidx_segment[offs:offs_end]))

        def get_limbs(offs):
            offs_end = offs + (4 * part_count)
            if (offs_end > lidx_segment.size()):
                raise InvalidAnimationException("[Hierarchy::load.get_limbs]" \
                        f" limb offset 0x{offs_end:06X} is out of" \
                        f" bounds for segment 0x{rval_seg_num:02X}")
            for limb_offset in unpack(f">{part_count}L", lidx_segment[offs:offs_end])

        hierarchy.limbs = get_limbs(lidx_seg_offs)

        return hierarchy

def load_hierarchies():
    hierarchies = []

    # sift through segment data one dword (4 bytes) at a time and try to match
    # the animation header format
    # TODO figure out a better way to load this... "unknown" animation data
    offset = 0
    data = load_segment(0x06)
    seg_offs_end = data.size() - 1
    while ((offset + 12) < seg_offs_end):
        try:
            hierarchy = Hierarchies.load(data, offset)
            logger.info(f"[load_hierarchies] Hierarchy found at" \
                    f" 0x{segment:02X}{offset:06X}")
            hierarchies.append(hierarchy)
            offset += 12
        except InvalidHierarchyException as e:
            logger.debug(e.value)
            offset += 4
            pass

    num_hierarchies = len(hierarchies)
    logger.info(f"[load_hierarchies] Found {num_hierarchies:d} total" \
             f" Hierarchies in segment 0x{segment:02X}")

    return hierarchies


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

