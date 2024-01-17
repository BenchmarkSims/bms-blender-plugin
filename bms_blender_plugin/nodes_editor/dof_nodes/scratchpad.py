class Scratchpad:
    """Holds the representation of the BMS-internal scratch variables. In general, we just have to make sure to allocate
    unique scratchpad IDs and throw an error when too many variables are used."""
    BMS_SCRATCHPAD_MEMORY_SIZE = 100
    
    memory = [False] * BMS_SCRATCHPAD_MEMORY_SIZE

    @staticmethod
    def clear():
        Scratchpad.memory = [False] * Scratchpad.BMS_SCRATCHPAD_MEMORY_SIZE

    @staticmethod
    def alloc():
        for i in range(0, len(Scratchpad.memory)):
            if not Scratchpad.memory[i]:
                Scratchpad.memory[i] = True
                return i

        raise Exception("Scratchpad memory is full")

    @staticmethod
    def free(var_number):
        Scratchpad.memory[var_number] = False
