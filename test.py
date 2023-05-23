import os
import logging
import sys

import f3dzex2
import f3dzex2.helpers as helpers


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# f3dzex2.logger.setLevel(logging.DEBUG)
# f3dzex2.segments.logger.setLevel(logging.DEBUG)
# f3dzex2.animations.logger.setLevel(logging.DEBUG)

f3dzex2.prefix = os.path.join(f3dzex2.prefix, "_tests")

f3dzex2.load_segment_from_file(0x06, "01939000_-_0193D810.zobj")

# hiers = helpers.find_all_hierarchies()
# for hier in hiers:
#     anims = helpers.find_all_animations(len(hier.limbs))


from f3dzex2.processor.microcode import G_VTX, vector_buffer

inst = G_VTX.struct()
inst.numv = 1
inst.vbidx = 1
inst.vaddr = 0x06000000

G_VTX.fn(inst)

print(str(vector_buffer))
