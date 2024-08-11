import hashlib
import platform

from functionfs.gadget import (
    GadgetSubprocessManager,
    ConfigFunctionFFSSubprocess,
)

from .usbms import MassStorageFunction, MassStorageLogicalUnit


SERIAL = hashlib.sha256(platform.node().encode('utf-8')).hexdigest()[:32].upper()


class MassStorageLogicalUnitDummy(MassStorageLogicalUnit):
    BLOCK_SIZE = 512
    LBA_COUNT = 16 * 1024 * 1024 // BLOCK_SIZE

    def __init__(self):
        self._io = bytearray(self.BLOCK_SIZE * self.LBA_COUNT)

    def onRead(self, lba, length):
        offset = lba * self.BLOCK_SIZE
        size = length * self.BLOCK_SIZE
        return memoryview(self._io)[offset:offset+size]

    def onWrite(self, lba, data):
        offset = lba * self.BLOCK_SIZE
        self._io[offset:offset+len(data)] = data

    def onReadCapacity(self):
        return self.LBA_COUNT - 1, self.BLOCK_SIZE


def get_function_instance(*args, **kwargs):
    return MassStorageFunction(*args, logical_units=(MassStorageLogicalUnitDummy,), **kwargs)


def main():
    """
    Entry point.
    """
    args = GadgetSubprocessManager.getArgumentParser(
        description='Besta RTOS DFU simulator.',
    ).parse_args()

    def getConfigFunctionSubprocess(**kw):
        return ConfigFunctionFFSSubprocess(
            getFunction=get_function_instance,
            **kw
        )

    with GadgetSubprocessManager(
        args=args,
        config_list=[
            # A single configuration
            {
                'function_list': [
                    getConfigFunctionSubprocess,
                ],
                'MaxPower': 500,
                'lang_dict': {
                    0x409: {
                        'configuration': 'Besta RTOS DFU Config',
                    },
                },
            }
        ],
        idVendor=0x1d6b,  # Linux Foundation
        idProduct=0x0104,  # Multifunction Composite Gadget
        lang_dict={
            0x409: {
                'product': 'Besta RTOS DFU',
                'manufacturer': 'python-functionfs',
                'serialnumber': SERIAL,
            },
        },
    ) as gadget:
        print('Gadget ready, waiting for function to exit.')
        try:
            gadget.waitForever()
        finally:
            print('Gadget exiting.')
