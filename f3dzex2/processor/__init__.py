import logging
# from collections.abc import Callable
# from abc import ABC, abstractmethod
# from struct import unpack, calcsize
from typing import List
# from ctypes import pointer, memmove, sizeof,\
from ctypes import c_uint32, c_uint64
#        LittleEndianStructure, c_int, c_uint8, c_uint16, c_uint32, c_uint64

from .. import memory
# from ..memory import MemoryException
from . import microcode


logger = logging.getLogger(__name__)


# S2DEX GBI 2
# 0x01: G_OBJ_RECTANGLE
# 0x02: G_OBJ_SPRITE
# ...
# 0x04: G_SELECT_DL
# 0x05: G_OBJ_LOADTXTR
# 0x06: G_OBJ_LDTX_SPRITE
# 0x07: G_OBJ_LDTX_RECT
# 0x08: G_OBJ_LDTX_RECT_R
# 0x09: G_BG_1CYC
# 0x0A: G_BG_COPY
# 0x0B: G_OBJ_RENDERMODE
# ...
# 0xDA: G_OBJ_RECTANGLE_R
# 0xDC: G_OBJ_MOVEMEM
# 0xE4: G_RDPHALF_0


# https://wiki.cloudmodding.com/oot/F3DZEX/Opcode_Details
opcodes = {
    0x00: microcode.G_NOOP,
    0x01: microcode.G_VTX,
    0x02: microcode.G_MODIFYVTX,
    0x03: microcode.G_CULLDL,
    0x04: microcode.G_BRANCH_Z,
    0x05: microcode.G_TRI,
    0x06: microcode.G_TRI2,
    0x07: microcode.G_QUAD,
    # ...
    0xD6: microcode.G_DMA_IO,
    0xD7: microcode.G_TEXTURE,
    0xD8: microcode.G_POPMTX,
    0xD9: microcode.G_GEOMETRYMODE,
    0xDA: microcode.G_MTX,
    0xDB: microcode.G_MOVEWORD,
    0xDC: microcode.G_MOVEMEM,
    0xDD: microcode.G_LOAD_UCODE,
    0xDE: microcode.G_DL,
    0xDF: microcode.G_ENDDL,
    0xE0: microcode.G_SPNOOP,
    0xE1: microcode.G_RDPHALF_1,
    0xE2: microcode.G_SETOTHERMODE_L,
    0xE3: microcode.G_SETOTHERMODE_H,
    0xE4: microcode.G_TEXRECT,
    0xE5: microcode.G_TEXRECTFLIP,
    0xE6: microcode.G_RDPLOADSYNC,
    0xE7: microcode.G_RDPPIPESYNC,
    0xE8: microcode.G_RDPTILESYNC,
    0xE9: microcode.G_RDPFULLSYNC,
    0xEA: microcode.G_SETKEYGB,
    0xEB: microcode.G_SETKEYR,
    0xEC: microcode.G_SETCONVERT,
    0xED: microcode.G_SETSCISSOR,
    0xEE: microcode.G_SETPRIMDEPTH,
    0xEF: microcode.G_RDPSETOTHERMODE,
    0xF0: microcode.G_LOADTLUT,
    0xF1: microcode.G_RDPHALF_2,
    0xF2: microcode.G_SETTILESIZE,
    0xF3: microcode.G_LOADBLOCK,
    0xF4: microcode.G_LOADTILE,
    0xF5: microcode.G_SETTILE,
    0xF6: microcode.G_FILLRECT,
    0xF7: microcode.G_SETFILLCOLOR,
    0xF8: microcode.G_SETFOGCOLOR,
    0xF9: microcode.G_SETBLENDCOLOR,
    0xFA: microcode.G_SETPRIMCOLOR,
    0xFB: microcode.G_SETENVCOLOR,
    0xFC: microcode.G_SETCOMBINE,
    0xFD: microcode.G_SETTIMG,
    0xFE: microcode.G_SETZIMG,
    0xFF: microcode.G_SETCIMG
}


logger = logging.getLogger(__name__)


INSTRUCTION_WIDTH = 8

# Registers
pc: c_uint32 = 0
rsp: c_uint64 = 0

# TODO: Impose size limits
# Stacks
rip: List[c_uint32] = 0


def run(address: int):
    global pc, INSTRUCTION_WIDTH
    pc = address
    try:
        cir = memory.read(pc, INSTRUCTION_WIDTH)
        pc += INSTRUCTION_WIDTH
        id = cir[0]
        if id in opcodes:
            opcodes[id](cir)
        else:
            raise Exception(f"bad instruction {id:01X}")
    except Exception as e:
        logger.error(f"RCP execution failed at {pc:08X}: {str(e)}")
