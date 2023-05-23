from ctypes import LittleEndianStructure, Union, c_int, c_int8, c_int16,\
        c_uint8, c_uint16, c_uint32, c_uint64


class Vtx_t(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("ob", c_int16 * 3),
        ("flag", c_uint16),
        ("tc", c_int16 * 2),
        ("cn", c_uint8 * 4)
    ]  # 16 bytes


class Vtx_tn(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("ob", c_int * 3),
        ("flag", c_uint16),
        ("tc", c_int16 * 2),
        ("n", c_int8 * 3),
        ("a", c_uint8),
    ]  # 16 bytes


class Vtx(Union):
    _fields_ = [
        ("v", Vtx_t),
        ("n", Vtx_tn),
        ("force_structure_alignment", c_uint64)
    ]  # 16 bytes, qword (8) aligned


# iiiiiiii pp------ xx------
# i: pointer to limb index list
# p: number of parts
# x: number of display lists
class Hierarchy(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("limbs_ptr", c_uint16),
        ("num_parts", c_uint8),
        ("_pad0", c_int, 24),
        ("num_lists", c_uint8),
        ("_pad1", c_int, 24)
    ]  # 12 bytes


# xxxxyyyy zzzzaabb dddddddd
# x: x translation relative to parent
# y: y translation relative to parent
# z: z translation relative to parent
# a: child limb index in list
# b: sibling limb index in list
# d: display list address
class Limb(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("translation", c_uint16 * 3),
        ("child_index", c_uint8),
        ("sibling_index", c_uint8),
        ("sibling_list_ptr", c_uint32),
    ]  # 12 bytes


# ssss---- rrrrrrrr iiiiiiii llll----
# s: # of frames
# r: pointer to rotation value list
#     - rotation animation data, indexed via rotation index list
# i: pointer to rotation index list
#     - start of rotation data in animation, limb indexed
# l: index pivot
#     - rotation value list indices less than this value
#       remain constant.
#     - rotation value list indices greater than this value
#       are treated as sequential rotation frames.
class Animation(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("num_frames", c_uint16),
        ("_pad0", c_uint16),
        ("rotation_values_ptr", c_uint32),
        ("rotation_indices_ptr", c_uint32),
        ("pivot", c_uint16),
        ("_pad1", c_uint16)
    ]  # 16 bytes


# ssss---- aaaaaaaa
# s: # of frames
# a: pointer to animation
class Link_Animation(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("num_frames", c_uint16),
        ("_pad0", c_uint16),
        ("animation_ptr", c_uint32)
    ]  # 16 bytes


# iiiiiiii -------- -------- wwwwhhhh ffsspppp llll
# i: address to JFIF image
# w: image width (typically 320px)
# h: image height (typically 240px)
# f: image format - format of texel - G_IM_FMT_*
# s: image size - size of texel -  G_IM_SIZ_*
# p: image palette - pallet number
# l: image flip - right & left image inversion (Inverted by G_BG_FLAG_FLIPS)
class Background(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("imagePtr", c_uint32),
        ("_unk0", c_uint32),  # maybe frameW/H, scaleW/H, imageX/Y, or frameX/Y
        ("_unk1", c_uint32),  # maybe frameW/H, scaleW/H, imageX/Y, or frameX/Y
        ("imageW", c_uint16),
        ("imageH", c_uint16),
        ("imageFmt", c_uint8),
        ("imageSiz", c_uint8),
        ("imagePal", c_uint16),
        ("imageFlip", c_uint16)
        # maybe more down here...
    ]


class BackgroundRecord(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("_unk_0x0082", c_uint16),
        ("backgroundId", c_int8),
        ("_pad0", c_uint8),
        ("background", Background)
    ]


# Simple mesh format; renders all display lists specified.
# --------------------------
# 00cc---- ssssssss eeeeeeee
# c: number of entries
# s: start of display list entries
# e: end of display list entries
class SimpleMesh(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("header_type", c_uint8),
        ("num_entries", c_uint8),
        ("_pad0", c_uint16),
        ("entryRecord", c_uint32),
        ("entryRecordEnd", c_uint32)
    ]


# This format is used with certain pre-rendered areas, specifically to
# render a static background image rather than the panoramas. Notably,
# the JFIF image is rendered via the S2DEX microcode, rather than the
# primary rendering microcode (F3DZEX2). The JFIF is drawn using
# S2DEX's gsSPBgRectCopy (0x0A) macro.
# -----------------
# 01tt---- pppppppp
# t: background type
# p: pointer to entry record
class BackgroundMeshSingle(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("header_type", c_uint8),
        ("format", c_uint8),
        ("_pad0", c_uint16),
        ("entryRecord", c_uint32),
        ("background", Background)
    ]


class BackgroundMeshMulti(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("header_type", c_uint8),
        ("format", c_uint8),
        ("_pad0", c_uint16),
        ("entryRecord", c_uint32),
        ("imagePtr", c_uint32),
        ("_unk0", c_uint32),
        ("_unk1", c_uint32),
        ("background_width", c_uint16),
        ("background_height", c_uint16),
        ("imageFmt", c_uint8),
        ("imageSiz", c_uint8),
        ("imagePal", c_uint16),
        ("imageFlip", c_uint16)
    ]


class BackgroundMesh(Union):
    _fields_ = [
        ("single", BackgroundMeshSingle),
        ("multi", BackgroundMeshMulti)
    ]


# Mesh that culls if the camera behind a set point by a certain
# distance.
# --------------------------
# 02cc---- ssssssss eeeeeeee
# c: number of entries
# s: start of display list entries
# e: end of display list entries
class CullingMesh(SimpleMesh):
    pass


class Mesh(Union):
    _fields_ = [
        ("type", c_uint8),
        ("simple_mesh", SimpleMesh),
        ("background_mesh", BackgroundMesh),
        ("culling_mesh", CullingMesh)
    ]
