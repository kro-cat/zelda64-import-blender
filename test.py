import os
import logging
import sys

import f3dzex
from f3dzex.segments import load_segment
from f3dzex.animations import load_animations, load_link_animations


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

#f3dzex.logger.setLevel(logging.DEBUG)
#f3dzex.segments.logger.setLevel(logging.DEBUG)
#f3dzex.animations.logger.setLevel(logging.DEBUG)

f3dzex.prefix = os.path.join(f3dzex.prefix, "_tests")

load_segment(0x06, "01939000_-_0193D810.zobj")

anims = load_animations(5)
