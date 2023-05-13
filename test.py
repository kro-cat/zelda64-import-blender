import os
import logging
import sys

import f3dzex
from f3dzex.memory import Memory
from f3dzex.animations import AnimationLoader
from f3dzex.hierarchies import HierarchyLoader


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# f3dzex.logger.setLevel(logging.DEBUG)
# f3dzex.segments.logger.setLevel(logging.DEBUG)
# f3dzex.animations.logger.setLevel(logging.DEBUG)

f3dzex.prefix = os.path.join(f3dzex.prefix, "_tests")

model = Memory()

model.load_memory_from_file(0x06000000, "01939000_-_0193D810.zobj")

anim_loader = AnimationLoader(model)
hier_loader = HierarchyLoader(model)

anims = anim_loader.load_animations(5)
hiers = hier_loader.load_hierarchies()
