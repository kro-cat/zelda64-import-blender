class Vertex:
    def __init__(self):
        self.pos = Vector([0, 0, 0])
        self.uv = Vector([0, 0])
        self.normal = Vector([0, 0, 0])
        self.color = [0, 0, 0, 0]
        self.limb = None

    def read(self, segment, offset):
        log = getLogger('Vertex.read')
        if not validOffset(segment, offset + 16):
            log.warning('Invalid segmented offset 0x%X for vertex' % (offset + 16))
            return
        seg, offset = splitOffset(offset)
        self.pos.x = unpack_from(">h", segment[seg], offset)[0]
        self.pos.z = unpack_from(">h", segment[seg], offset + 2)[0]
        self.pos.y = -unpack_from(">h", segment[seg], offset + 4)[0]
        global scaleFactor
        self.pos *= scaleFactor
        self.uv.x = float(unpack_from(">h", segment[seg], offset + 8)[0])
        self.uv.y = float(unpack_from(">h", segment[seg], offset + 10)[0])
        self.normal.x = unpack_from("b", segment[seg], offset + 12)[0] / 128
        self.normal.z = unpack_from("b", segment[seg], offset + 13)[0] / 128
        self.normal.y = -unpack_from("b", segment[seg], offset + 14)[0] / 128
        self.color[0] = min(segment[seg][offset + 12] / 255, 1.0)
        self.color[1] = min(segment[seg][offset + 13] / 255, 1.0)
        self.color[2] = min(segment[seg][offset + 14] / 255, 1.0)
        if checkUseVertexAlpha():
            self.color[3] = min(segment[seg][offset + 15] / 255, 1.0)
