import logging
# from collections.abc import Callable
# from abc import ABC, abstractmethod
from typing import List
# from struct import unpack, calcsize
from ctypes import pointer, memmove, sizeof,\
        LittleEndianStructure, c_int, c_uint8, c_uint32
#        LittleEndianStructure, c_int, c_uint8, c_uint16, c_uint32, c_uint64


from .. import memory
# from . import cpu
from f3dzex2 import types


logger = logging.getLogger(__name__)


# TODO: Impose size limits
# Buffers
vector_buffer: List[types.Vtx] = []


def unpack(inst: bytes, struct: LittleEndianStructure):
    global INSTRUCTION_WIDTH

    if struct is None:
        raise Exception("instruction {inst[0]:01X} has no format")
    if sizeof(struct) != INSTRUCTION_WIDTH:
        raise Exception("instruction {inst[0]:01X} has incorrect width")

    struct_inst = struct()
    memmove(pointer(struct_inst), inst, INSTRUCTION_WIDTH)

    return struct_inst


def NOSYS(inst: bytes):
    logger.warn("instruction {cir[0]:01X} has no implementation")


# https://wiki.cloudmodding.com/oot/F3DZEX/Opcode_Details

# G_NOOP
# gsDPNoOp()
# gsDPNoOpTag(tag)
# -----------------
# 00000000 tttttttt
# t: tag | Pointer to string tag
# NOTE: stalls the RDP
G_NOOP = NOSYS


# G_VTX
# gsSPVertex(vaddr, numv, vbidx)
# -----------------
# 010nn0aa vvvvvvvv
# n: numv                         | Number of vertices to load
# a: ((vbidx + numv) & 0x7F) << 1 | Index of vertex buffer to begin storing
#                                 |  vertices to
# v: vaddr                        | Address of vertices
class _G_VTX(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8),
        ("_pad0", c_int, 4),
        ("numv", c_int, 8),
        ("_pad1", c_int, 4),
        ("vbidx", c_int, 8),  # align 8
        ("vaddr", c_uint32)
    ]


def G_VTX(_inst: bytes):
    inst = unpack(_inst, _G_VTX)

    global vector_buffer

    vertex_size = sizeof(types.Vtx)
    index = inst.vbidx / vertex_size
    for _ in range(inst.numv):
        vertex_data = memory.read(inst.numv, vertex_size)
        vertex = types.Vtx()
        memmove(pointer(vertex), vertex_data, vertex_size)

        vector_buffer[--index] = vertex


# G_MODIFYVTX
# gsSPModifyVertex(vbidx, where, val)
# -----------------
# 02wwnnnn vvvvvvvv
# w: where     | Enumerated set of values specifying what to change
# n: vbidx * 2 | Vertex buffer index of vertex to modify
# v: val       | New value to insert
G_CULLDL = NOSYS


# G_CULLDL
# gsSPCullDisplayList(vfirst, vlast)
# -----------------
# 0300vvvv 0000wwww
# v: vfirst * 2 | Vertex buffer index of first vertex for bounding volume
# w: vlast * 2  | Vertex buffer index of last vertex for bounding volume
G_CULLDL = NOSYS


# G_BRANCH_Z
# gsSPBranchLessZraw(newdl, vbidx, zval)
# -----------------
# E1000000 dddddddd *set RDP high dword to display list address, see 0xE1
# 04aaabbb zzzzzzzz
# d: newdl     | Address of display list to branch to *see 0xE1
# a: vbidx * 5 | Vertex buffer index of vertex to test
# b: vbidx * 2 | Vertex buffer index of vertex to test
# z: zval      | Z value to test against
G_BRANCH_Z = NOSYS


# G_TRI
# gsSP1Triangle(v0, v1, v2, flag)
# -----------------
# 05vvvvvv 00000000
# v: (v0|v1|v2) * 2 | Vertex buffer index of one vertex of the triangle
# NOTE: vvvvvv looks like aabbcc * 2 where
#       aa, bb, and cc correspond to v0, v1, and v2


# G_TRI2
# gsSP2Triangles(v00, v01, v02, flag0, v10, v11, v12, flag1)
# -----------------
# 06vvvvvv 00wwwwww
# v: (v00|v01|v02) * 2 | Vertex buffer index of one vertex of the
#                      |  first triangle
# w: (v10|v11|v12) * 2 | Vertex buffer index of one vertex of the
#                      |  second triangle
# NOTE: flag0 and flag1 are only used to produce the opcode.


# G_QUAD
# gsSPQuadrangle(v0, v1, v2, v3, flag)
# -----------------
# 07vvvvvv 00wwwwww
# v: (v0|v1|v2) * 2 | Vertex buffer index of one vertex of the
#                   |  first triangle
# w: (v0|v2|v3) * 2 | Vertex buffer index of one vertex of the
#                   |  second triangle
# NOTE: flag is only used to produce the opcode.


# ...

# G_DMA_IO
# gsSPDma_io(flag, dmem, dram, size)
# -----------------
# D6___sss rrrrrrrr
#   ___ -> (bits) fmmm mmmm mmm0
# f: flag & 1           | (1 bit) Chooses between read (0) or write (1)
# m: (dmem / 8) & 0x4FF | (10 bits) Address in DMEM/IMEM(?)
# s: size - 1           | (Presumably) size of data to transfer
# r: dram               | DRAM address


# G_TEXTURE
# gsSPTexture(scaleS, scaleT, level, tile, on)
# -----------------
# D700____ sssstttt
#     ____ -> (bits) 00LL Lddd nnnn nnn0
# L: level & 7 | (3 bits) Maximum number of mipmap levels
#              |  aside from the first
# d: tile & 7  | (3 bits) Tile descriptor number
# n: on & 0x7F | (7 bits) Decides whether to turn the given texture
#              |  on or off
# s: scaleS    | Scaling factor for the S-axis (horizontal)
# d: scaleT    | Scaling factor for the T-axis (vertical)


# G_POPMTX
# gsSPPopMatrixN(which, num)
# -----------------
# D8380002 aaaaaaaa
# a: num * 64 | The number of matrices to pop
# NOTE: "which" is silently ignored. the only stack used is the
#       modelview matrix stack


# G_GEOMETRYMODE
# gsSPGeometryMode(clearbits, setbits)
# -----------------
# D9cccccc ssssssss
# c: ~clearbits | Geometry mode bits to clear
# s: setbits    | Geometry mode bits to set


# G_MTX
# gsSPMatrix(mtxaddr, params)
# -----------------
# DA3800pp mmmmmmmm
# p: params ^ gs.G_MTX_PUSH | Parameters controlling nature of matrix addition
# m: mtxaddr             | RAM address of new matrix
# NOTE: see
# https://wiki.cloudmodding.com/oot/F3DZEX/Opcode_Details#0xDA_.E2.80.94_gs.G_MTX


# G_MOVEWORD
# gsMoveWd(index, offset, data)
# gsSPSegment(segment, base)
# -----------------
# DBiioooo dddddddd
# i: index  | Index into DMEM pointer table(?)
# o: offset | Offset from the indexed base address(?)
# d: data   | New 32-bit value
# NOTE: see
# https://wiki.cloudmodding.com/oot/F3DZEX/Opcode_Details#0xDB_.E2.80.94_gs.G_MOVEWORD


# G_MOVEMEM
# gsMoveMem(size, index, offset, address) *imaginary opcode
# -----------------
# DCnnooii aaaaaaaa
# n: ((size - 1) / 8 & 0x1F) << 3 | Size in bytes of memory to be moved
# o: offset / 8                   | Offset from indexed base address
# i: index                        | Index into table of DMEM addresses
# a: address                      | RAM address of memory


# G_LOAD_UCODE
# gsSPLoadUcodeEx(tstart, dstart, dsize)
# -----------------
# E1000000 dddddddd *set RDP high dword to data section address, see 0xE1
# DD00ssss tttttttt
# d: dstart | Start of data section *see 0xE1
# s: dsize  | Size of data section
# t: tstart | Start of text section


# G_DL
# gsSPDisplayList(dl) *pp = 0x00
# gsSPBranchList(dl) *pp = 0x01
# -----------------
# DEpp0000 dddddddd
# p: mode | push current dl pointer to address stack if zero
# d: dl   | Address of new display list to jump to


# G_ENDDL
# gsSPEndDisplayList()
# -----------------
# DF000000 00000000
# NOTE: ends current display list. pop dl pointer from address stack or,
#       if address stack is empty, end graphics processing.


# G_SPNOOP
# gsSPNoOp()
# -----------------
# E0000000 00000000
# NOTE: stalls the RSP


# G_RDPHALF_1
# no macro
# -----------------
# E1000000 hhhhhhhh
# h: new high dword of RDP


# G_SETOTHERMODE_L
# gsSPSetOtherMode(0xE2, shift, length, data)
# -----------------
# E200ssnn dddddddd
# s: 32 - shift - length | Amount data is shifted by
# n: length - 1          | Size of data affected, in bits
# d: data                | New bit settings to be applied
# NOTE: see
# https://wiki.cloudmodding.com/oot/F3DZEX/Opcode_Details#0xE2_.E2.80.94_gs.G_SETOTHERMODE_L


# G_SETOTHERMODE_H
# gsSPSetOtherMode(0xE3, shift, length, data)
# -----------------
# E300ssnn dddddddd
# s: 32 - shift - length | Amount data is shifted by
# n: length - 1          | Size of data affected, in bits
# d: data                | New bit settings to be applied
# NOTE: see
# https://wiki.cloudmodding.com/oot/F3DZEX/Opcode_Details#0xE2_.E2.80.94_gs.G_SETOTHERMODE_H


# G_TEXRECT
# gsSPTextureRectangle(ulx, uly, lrx, lry, tile, uls, ult, dsdx, dtdy)
# -----------------
# E4xxxyyy 0iXXXYYY
# E1000000 sssstttt *set RDP high dword, see 0xE1
# F1000000 ddddeeee *set RDP low dword, see 0xF1
# x: lrx  | Lower-right corner X coordinate
# y: lry  | Lower-right corner Y coordinate
# i: tile | Tile descriptor to use for rectangle
# X: ulx  | Upper-left corner X coordinate
# Y: uly  | Upper-left corner Y coordinate
# s: uls  | Texture S coordinate at upper-left corner
# t: ult  | Texture T coordinate at upper-left corner
# d: dsdx | Change in S coordinate over change in X coordinate
# e: dtdy | Change in T coordinate over change in Y coordinate
# TODO: handle 128-bit variant


# G_TEXRECTFLIP
# gsSPTextureRectangleFlip(ulx, uly, lrx, lry, tile, uls, ult, dtdx, dsdy)
# -----------------
# E5xxxyyy 0iXXXYYY
# E1000000 sssstttt *set RDP high dword, see 0xE1
# F1000000 ddddeeee *set RDP low dword, see 0xF1
# x: lrx  | Lower-right corner X coordinate
# y: lry  | Lower-right corner Y coordinate
# i: tile | Tile descriptor to use for rectangle
# X: ulx  | Upper-left corner X coordinate
# Y: uly  | Upper-left corner Y coordinate
# s: uls  | Texture S coordinate at upper-left corner
# t: ult  | Texture T coordinate at upper-left corner
# d: dtdx | Change in T coordinate over change in X coordinate
# e: dsdy | Change in S coordinate over change in Y coordinate
# NOTE: same as gs.G_TEXRECT except texture is flipped about its diagonal
# TODO: handle 128-bit variant


# G_RDPLOADSYNC
# gsDPLoadSync()
# -----------------
# E6000000 00000000
# NOTE: blocking; wait for texture loading to finish


# G_RDPPIPESYNC
# gsDPPipeSync()
# -----------------
# E7000000 00000000
# NOTE: blocking; wait for primitive loading to finish


# G_RDPTILESYNC
# gsDPTileSync()
# -----------------
# E8000000 00000000
# NOTE: blocking; wait for tile descriptor update to finish


# G_RDPFULLSYNC
# gsDPFullSync()
# -----------------
# E9000000 00000000
# NOTE: interrupts the CPU to signify RDP is finished.
#       typically seen before 0xDF


# G_SETKEYGB
# gsDPSetKeyGB(centerG, scaleG, widthG, centerB, scaleB, widthB)
# -----------------
# EAwwwxxx ccssddtt
# w: widthG  | Scaled width of half the key window for green
# x: widthB  | Scaled width of half the key window for blue
# c: centerG | Intensity of active key for green
# s: scaleG  | Reciprocal of size of soft edge,
#            |  normalized to 0..0xFF, for green
# d: centerB | Intensity of active key for blue
# t: scaleB  | Reciprocal of size of soft edge,
#            |  normalized to 0..0xFF, for blue


# G_SETKEYR
# gsDPSetKeyR(centerR, widthR, scaleR)
# -----------------
# EB000000 0wwwccss
# w: widthG  | Scaled width of half the key window for red
# c: centerG | Intensity of active key for red
# s: scaleG  | Reciprocal of size of soft edge,
#            |  normalized to 0..0xFF, for red


# G_SETCONVERT
# gsDPSetConvert(k0, k1, k2, k3, k4, k5)
# -----------------
# EC______ ________
#   ______ ________ -> (bits) 00aa aaaa  aaab bbbb  bbbb cccc  cccc cddd
#                             dddd ddee  eeee eeef  ffff ffff
# a: (9 bits) k0 term of conversion matrix
# b: (9 bits) k1 term of conversion matrix
# c: (9 bits) k2 term of conversion matrix
# d: (9 bits) k3 term of conversion matrix
# e: (9 bits) k4 term of conversion matrix
# f: (9 bits) k5 term of conversion matrix


# G_SETSCISSOR
# gsDPSetScissor(mode, ulx, uly, lrx, lry)
# -----------------
# EDxxxyyy m0vvvwww
# x: ulx  | Upper-left X coordinate of rectangle
# y: uly  | Upper-left Y coordinate of rectangle
# m: mode | Interpolation mode setting
# v: lrx  | Lower-right X coordinate of rectangle
# w: lry  | Lower-right Y coordinate of rectangle


# G_SETPRIMDEPTH
# gsDPSetPrimDepth(z, dz)
# -----------------
# EE000000 zzzzdddd
# z: z  | Z value for primitive
# d: dz | delta Z value for primitive


# G_RDPSETOTHERMODE
# gsDPSetOtherMode(omodeH, omodeL)
# -----------------
# EFhhhhhh LLLLLLLL
# h: omodeH | Settings for other mode higher word bits
# L: omodeL | Settings for other mode lower word bits


# G_LOADTLUT
# gsDPLoadTLUTCmd(tile, count)
# -----------------
# F0000000 0tccc000
# t: tile                 | Tile descriptor to load from
# c: (count & 0x3FF) << 2 | Number of colors to load minus one


# G_RDPHALF_2
# gsDPWord(wordhi, wordlo)
# -----------------
# E1000000 hhhhhhhh *set RDP high dword, see 0xE1
# F1000000 llllllll
# h: wordhi | new RDP high dword *see 0xE1
# l: wordlo | new RDP low dword


# G_SETTILESIZE
# gsDPSetTileSize(tile, uls, ult, lrs, lrt)
# -----------------
# F2sssttt 0iuuuvvv
# s: uls  | Upper-left texture coordinate, S-axis
# t: ult  | Upper-left texture coordinate, T-axis
# i: tile | Tile descriptor to modify
# u: lrs  | Lower-right texture coordinate, S-axis
# v: lrt  | Lower-right texture coordinate, T-axis


# G_LOADBLOCK
# gsDPLoadBlock(tile, uls, ult, texels, dxt)
# -----------------
# F3sssttt 0ixxxddd
# s: uls    | Upper-left corner of texture to load, S-axis
# t: ult    | Upper-left corner of texture to load, T-axis
# i: tile   | Tile descriptor to modify
# x: texels | Number of texels to load to TMEM, minus one
# d: dxt    | Change in T-axis per scanline


# G_LOADTILE
# gsDPLoadTile(tile, uls, ult, lrs, lrt)
# -----------------
# F4sssttt 0iuuuvvv
# s: uls  | Upper-left corner of tile, S-axis
# t: ult  | Upper-left corner of tile, T-axis
# i: tile | Tile descriptor being loaded into
# u: lrs  | Lower-right corner of tile, S-axis
# v: lrt  | Lower-right corner of tile, T-axis
class G_LOADTILE_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_LOADTILE(Opcode):
    struct = G_LOADTILE_Struct

    def fn(data: G_LOADTILE_Struct):
        raise Exception("implement me!")


# G_SETTILE
# gsDPSetTile(fmt, siz, line, tmem, tile, palette,
#             cmT, maskT, shiftT, cmS, maskS, shiftS)
# -----------------
# F5______ ________
#   ______ ________ -> (bits) fffi i0nn  nnnn nnnm  mmmm mmmm  0000 0ttt
#                             pppp ccaa  aass ssdd  bbbb uuuu
# f: fmt     | (3 bits) Sets color format
# i: siz     | (2 bits) Sets bit size of pixel
# n: line    | (9 bits) Number of 64-bit values per row
# m: tmem    | (9 bits) Offset of texture in TMEM
# t: tile    | (3 bits) Tile descriptor being modified
# p: palette | (4 bits) Which palette to use for colors (if relevant)
# c: cmT     | (2 bits) Clamp and Mirror flags for the T axis
# a: maskT   | (4 bits) Sets how much of T axis is shown before wrapping
# s: shiftT  | (4 bits) Sets the amount to shift T axis values after
#            |  perspective division
# d: cmS     | (2 bits) Clamp and Mirror flags for the S axis
# b: maskS   | (4 bits) Sets how much of S axis is shown before wrapping
# u: shiftS  | (4 bits) Sets the amount to shift S axis values after
#            |  perspective division
class G_SETTILE_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETTILE(Opcode):
    struct = G_SETTILE_Struct

    def fn(data: G_SETTILE_Struct):
        raise Exception("implement me!")


# G_FILLRECT
# gsDPFillRectangle(ulx, uly, lrx, lry)
# -----------------
# F6xxxyyy 00vvvwww
# x: (lrx & 0x3FF) << 2 | Lower-right corner of rectangle, X-axis
# y: (lry & 0x3FF) << 2 | Lower-right corner of rectangle, Y-axis
# v: (ulx & 0x3FF) << 2 | Upper-left corner of rectangle, X-axis
# w: (uly & 0x3FF) << 2 | Upper-left corner of rectangle, Y-axis
class G_FILLRECT_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_FILLRECT(NOSYS):
    struct = G_FILLRECT_Struct


# G_SETFILLCOLOR
# gsDPSetFillColor(color)
# -----------------
# F7000000 cccccccc
# c: color | Fill value for use in fill mode
class G_SETFILLCOLOR_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETFILLCOLOR(NOSYS):
    struct = G_SETFILLCOLOR_Struct


# G_SETFOGCOLOR
# gsDPSetFogColor(R, G, B, A)
# -----------------
# F8000000 rrggbbaa
# r: R | Red component of fog color
# g: G | Green component of fog color
# b: B | Blue component of fog color
# a: A | Alpha component of fog color
class G_SETFOGCOLOR_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETFOGCOLOR(NOSYS):
    struct = G_SETFOGCOLOR_Struct


# G_SETBLENDCOLOR
# gsDPBlendColor(R, G, B, A)
# -----------------
# F9000000 rrggbbaa
# r: R | Red component of blend color
# g: G | Green component of blend color
# b: B | Blue component of blend color
# a: A | Alpha component of blend color
class G_SETBLENDCOLOR_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETBLENDCOLOR(NOSYS):
    struct = G_SETBLENDCOLOR_Struct


# G_SETPRIMCOLOR
# gsDPSetPrimColor(minlevel, lodfrac, R, G, B, A)
# -----------------
# FA00mmff rrggbbaa
# m: minlevel | Minimum possible LOD value (clamped to this at minimum)
# f: lodfrac  | Primitive LOD fraction for mipmap filtering
# r: R        | Red component of primitive color
# g: G        | Green component of primitive color
# b: B        | Blue component of primitive color
# a: A        | Alpha component of primitive color
class G_SETPRIMCOLOR_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETPRIMCOLOR(Opcode):
    struct = G_SETPRIMCOLOR_Struct

    def fn(data: G_SETPRIMCOLOR_Struct):
        raise Exception("implement me!")


# G_SETENVCOLOR
# gsDPSetEnvColor(R, G, B, A)
# -----------------
# FB000000 rrggbbaa
# r: R | Red component of environment color
# g: G | Green component of environment color
# b: B | Blue component of environment color
# a: A | Alpha component of environment color
class G_SETENVCOLOR_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETENVCOLOR(Opcode):
    struct = G_SETENVCOLOR_Struct

    def fn(data: G_SETENVCOLOR_Struct):
        raise Exception("implement me!")


# G_SETCOMBINE
# gsDPSetCombineLERP(a0, b0, c0, d0, Aa0, Ab0, Ac0, Ad0,
#                    a1, b1, c1, d1, Aa1, Ab1, Ac1, Ad1)
# -----------------
# FC______ ________
#   ______ ________ -> (bits) aaaa cccc  czzz xxxe  eeeg gggg  bbbb ffff
#                             vvvt ttdd  dyyy wwwh  hhuu usss
# a: a0  | (4 bits) Color 'a' value, first cycle
# c: c0  | (5 bits) Color 'c' value, first cycle
# z: Aa0 | (3 bits) Alpha 'a' value, first cycle
# x: Ac0 | (3 bits) Alpha 'c' value, first cycle
# e: a1  | (4 bits) Color 'a' value, second cycle
# g: c1  | (5 bits) Color 'c' value, second cycle
# b: b0  | (4 bits) Color 'b' value, first cycle
# f: b1  | (4 bits) Color 'b' value, second cycle
# v: Aa1 | (3 bits) Alpha 'a' value, second cycle
# t: Ac1 | (3 bits) Alpha 'c' value, second cycle
# d: d0  | (3 bits) Color 'd' value, first cycle
# y: Ab0 | (3 bits) Alpha 'b' value, first cycle
# w: Ad0 | (3 bits) Alpha 'd' value, first cycle
# h: d1  | (3 bits) Color 'd' value, second cycle
# u: Ab1 | (3 bits) Alpha 'b' value, second cycle
# s: Ad1 | (3 bits) Alpha 'd' value, second cycle
class G_SETCOMBINE_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETCOMBINE(Opcode):
    struct = G_SETCOMBINE_Struct

    def fn(data: G_SETCOMBINE_Struct):
        raise Exception("implement me!")


# G_SETTIMG
# gsDPSetTextureImage(fmt, siz, width, imgaddr)
# -----------------
# FD__0www iiiiiiii
#   __ -> (bits) fffs s000
# f: fmt       | (3 bits) Format of texture to be pointed to
# s: siz       | (2 bits) Bit size of pixels in texture to be pointed to
# w: width - 1 | Width of the texture
# i: imgaddr   | RAM address of start of texture
class G_SETTIMG_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETTIMG(Opcode):
    struct = G_SETTIMG_Struct

    def fn(data: G_SETTIMG_Struct):
        raise Exception("implement me!")


# G_SETZIMG
# gsDPSetDepthImage(imgaddr)
# -----------------
# FE000000 iiiiiiii
# i: imgaddr | Address of the depth buffer
class G_SETZIMG_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETZIMG(NOSYS):
    struct = G_SETZIMG_Struct


# G_SETCIMG
# gsDPSetColorImage(fmt, siz, width, imgaddr)
# -----------------
# FD__0www iiiiiiii
#   __ -> (bits) fffs s000
# f: fmt       | (3 bits) Format of color buffer to be pointed to
# s: siz       | (2 bits) Bit size of pixels in color buffer to be pointed to
# w: width - 1 | Width of the color buffer
# i: imgaddr   | RAM address of start of color buffer
class G_SETCIMG_Struct(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # ("id", c_uint8)
        # TODO
    ]


class G_SETCIMG(NOSYS):
    struct = G_SETCIMG_Struct
