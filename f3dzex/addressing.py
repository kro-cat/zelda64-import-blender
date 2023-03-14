

def segment_offset(address: int):
        return ((address >> 24), (address & 0x00ffffff))
