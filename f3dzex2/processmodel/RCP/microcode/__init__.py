import logging
# from typing import NamedTuple

# from .. import memory
# from ..memory import MemoryException
from . import gs


logger = logging.getLogger(__name__)


# https://wiki.cloudmodding.com/oot/F3DZEX/Opcode_Details
opcodes = {
    0x00: gs.NOOP(),
    0x01: gs.G_VTX(),
    0x02: gs.G_MODIFYVTX(),
    0x03: gs.G_CULLDL(),
    0x04: gs.G_BRANCH_Z(),
    0x05: gs.G_TRI(),
    0x06: gs.G_TRI2(),
    0x07: gs.G_QUAD(),
    # ...
    0x0A: gs.G_COPYRECT(),  # This is actually a S2DEX opcode
    # ...
    0xD6: gs.G_DMA_IO(),
    0xD7: gs.G_TEXTURE(),
    0xD8: gs.G_POPMTX(),
    0xD9: gs.G_GEOMETRYMODE(),
    0xDA: gs.G_MTX(),
    0xDB: gs.G_MOVEWORD(),
    0xDC: gs.G_MOVEMEM(),
    0xDD: gs.G_LOAD_UCODE(),
    0xDE: gs.G_DL(),
    0xDF: gs.G_ENDDL(),
    0xE0: gs.G_SPNOOP(),
    0xE1: gs.G_RDPHALF_1(),
    0xE2: gs.G_SETOTHERMODE_L(),
    0xE3: gs.G_SETOTHERMODE_H(),
    0xE4: gs.G_TEXRECT(),
    0xE5: gs.G_TEXRECTFLIP(),
    0xE6: gs.G_RDPLOADSYNC(),
    0xE7: gs.G_RDPPIPESYNC(),
    0xE8: gs.G_RDPTILESYNC(),
    0xE9: gs.G_RDPFULLSYNC(),
    0xEA: gs.G_SETKEYGB(),
    0xEB: gs.G_SETKEYR(),
    0xEC: gs.G_SETCONVERT(),
    0xED: gs.G_SETSCISSOR(),
    0xEE: gs.G_SETPRIMDEPTH(),
    0xEF: gs.G_RDPSETOTHERMODE(),
    0xF0: gs.G_LOADTLUT(),
    0xF1: gs.G_RDPHALF_2(),
    0xF2: gs.G_SETTILESIZE(),
    0xF3: gs.G_LOADBLOCK(),
    0xF4: gs.G_LOADTILE(),
    0xF5: gs.G_SETTILE(),
    0xF6: gs.G_FILLRECT(),
    0xF7: gs.G_SETFILLCOLOR(),
    0xF8: gs.G_SETFOGCOLOR(),
    0xF9: gs.G_SETBLENDCOLOR(),
    0xFA: gs.G_SETPRIMCOLOR(),
    0xFB: gs.G_SETENVCOLOR(),
    0xFC: gs.G_SETCOMBINE(),
    0xFD: gs.G_SETTIMG(),
    0xFE: gs.G_SETZIMG(),
    0xFF: gs.G_SETCIMG()
}
