import os
import logging
import sys

import f3dzex
import f3dzex.memory as memory
import f3dzex.helpers as helpers


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# f3dzex.logger.setLevel(logging.DEBUG)
# f3dzex.segments.logger.setLevel(logging.DEBUG)
# f3dzex.animations.logger.setLevel(logging.DEBUG)

f3dzex.prefix = os.path.join(f3dzex.prefix, "_tests")

memory.load_from_file(0x06000000, "01939000_-_0193D810.zobj")

hiers = helpers.find_all_hierarchies()
for hier in hiers:
    anims = helpers.find_all_animations(len(hier.limbs))
