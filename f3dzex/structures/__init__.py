# helper functions

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
