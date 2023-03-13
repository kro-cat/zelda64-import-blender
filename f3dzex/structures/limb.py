class Limb:
    def __init__(self):
        self.parent, self.child, self.sibling = -1, -1, -1
        self.pos = Vector([0, 0, 0])
        self.near, self.far = 0x00000000, 0x00000000
        self.poseBone = None
        self.poseLocPath, self.poseRotPath = None, None
        self.poseLoc, self.poseRot = Vector([0, 0, 0]), None

    def read(self, segment, offset, actuallimb, BoneCount):
        seg, offset = splitOffset(offset)

        rot_offset = offset & 0xFFFFFF
        rot_offset += (0 * (BoneCount * 6 + 8));

        self.pos.x = unpack_from(">h", segment[seg], offset)[0]
        self.pos.z = unpack_from(">h", segment[seg], offset + 2)[0]
        self.pos.y = -unpack_from(">h", segment[seg], offset + 4)[0]
        global scaleFactor
        self.pos *= scaleFactor
        self.child = unpack_from("b", segment[seg], offset + 6)[0]
        self.sibling = unpack_from("b", segment[seg], offset + 7)[0]
        self.near = unpack_from(">L", segment[seg], offset + 8)[0]
        self.far = unpack_from(">L", segment[seg], offset + 12)[0]

        self.poseLoc.x = unpack_from(">h", segment[seg], rot_offset)[0]
        self.poseLoc.z = unpack_from(">h", segment[seg], rot_offset + 2)[0]
        self.poseLoc.y = unpack_from(">h", segment[seg], rot_offset + 4)[0]
        getLogger('Limb.read').trace("      Limb %r: %f,%f,%f", actuallimb, self.poseLoc.x, self.poseLoc.z, self.poseLoc.y)
