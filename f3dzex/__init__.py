import os
from structures import (vertex, tile)

prefix = os.getcwd() 

# all of this might be unnecessary
use_transparency = detectedDisplayLists_use_transparency
already_read = [[]] * 16
segment = [[]] * 16
vertex_buffer = [(0, 0, 0)] * 32
tiles  = [Tile()] * 32
geometry_mode_flags = set()

animTotal = 0
TimeLine = 0
TimeLinePosition = 0
displaylists = []

curTile = 0
material = []
hierarchy = []
resetCombiner()

#for i in range(16):
#    alreadyRead.append([])
#    segment.append([])
#    vbuf.append(Vertex())
#for i in range(2):
#    tile.append(Tile())
#    # self.vbuf.append(Vertex())
#    pass
#for i in range(14 + 32):
#    # self.vbuf.append(Vertex())
#    pass
#while len(vbuf) < 32
#    vbuf.append(Vertex())

animations_count = 1


