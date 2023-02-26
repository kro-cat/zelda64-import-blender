class Hierarchy:
    def __init__(self):
        self.name, self.offset = "", 0x00000000
        self.limbCount, self.dlistCount = 0x00, 0x00
        self.limb = []
        self.armature = None

    def read(self, segment, offset, prefix=""):
        log = getLogger('Hierarchy.read')
        self.dlistCount = None
        if not validOffset(segment, offset + 5):
            log.error('Invalid segmented offset 0x%X for hierarchy' % (offset + 5))
            return False
        if not validOffset(segment, offset + 9):
            log.warning('Invalid segmented offset 0x%X for hierarchy (incomplete header), still trying to import ignoring dlistCount' % (offset + 9))
            self.dlistCount = 1
        self.name = prefix + ("sk_%08X" % offset)
        self.offset = offset
        seg, offset = splitOffset(offset)
        limbIndex_offset = unpack_from(">L", segment[seg], offset)[0]
        if not validOffset(segment, limbIndex_offset):
            log.error("        ERROR:  Limb index table 0x%08X out of range" % limbIndex_offset)
            return False
        limbIndex_seg, limbIndex_offset = splitOffset(limbIndex_offset)
        self.limbCount = segment[seg][offset + 4]
        if not self.dlistCount:
            self.dlistCount = segment[seg][offset + 8]
        for i in range(self.limbCount):
            limb_offset = unpack_from(">L", segment[limbIndex_seg], limbIndex_offset + 4 * i)[0]
            limb = Limb()
            limb.index = i
            self.limb.append(limb)
            if validOffset(segment, limb_offset + 12):
                limb.read(segment, limb_offset, i, self.limbCount)
            else:
                log.error("        ERROR:  Limb 0x%02X offset 0x%08X out of range" % (i, limb_offset))[0]
        self.limb[0].pos = Vector([0, 0, 0])
        self.initLimbs(0x00)
        return True

    def create(self):
        rx, ry, rz = 90,0,0
        if (bpy.context.active_object):
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        for i in bpy.context.selected_objects:
            i.select = False
        self.armature = bpy.data.objects.new(self.name, bpy.data.armatures.new("%s_armature" % self.name))
        self.armature.show_x_ray = True
        self.armature.data.draw_type = 'STICK'
        bpy.context.scene.objects.link(self.armature)
        bpy.context.scene.objects.active = self.armature
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        for i in range(self.limbCount):
            bone = self.armature.data.edit_bones.new("limb_%02i" % i)
            bone.use_deform = True
            bone.head = self.limb[i].pos

        for i in range(self.limbCount):
            bone = self.armature.data.edit_bones["limb_%02i" % i]
            if (self.limb[i].parent != -1):
                bone.parent = self.armature.data.edit_bones["limb_%02i" % self.limb[i].parent]
                bone.use_connect = False
            bone.tail = bone.head + Vector([0, 0, 0.0001])
        bpy.ops.object.mode_set(mode='OBJECT')

    def initLimbs(self, i):
        if (self.limb[i].child > -1 and self.limb[i].child != i):
            self.limb[self.limb[i].child].parent = i
            self.limb[self.limb[i].child].pos += self.limb[i].pos
            self.initLimbs(self.limb[i].child)
        if (self.limb[i].sibling > -1 and self.limb[i].sibling != i):
            self.limb[self.limb[i].sibling].parent = self.limb[i].parent
            self.limb[self.limb[i].sibling].pos += self.limb[self.limb[i].parent].pos
            self.initLimbs(self.limb[i].sibling)

    def getMatrixLimb(self, offset):
        j = 0
        index = (offset & 0x00FFFFFF) / 0x40
        for i in range(self.limbCount):
            if self.limb[i].near != 0:
                if (j == index):
                    return self.limb[i]
                j += 1
        return self.limb[0]
