from typing import Any, ByteString, Final, Self, Sequence, Type, TypedDict, TypeVar, overload
from collections.abc import Buffer
import ctypes

from functionfs.common import u8

from functionfs import (
    Function,
    EndpointINFile,
    EndpointOUTFile,
)


USB_INTERFACE_SUBCLASS_NONE: Final[int]
USB_INTERFACE_SUBCLASS_RBC: Final[int]
USB_INTERFACE_SUBCLASS_MMC5: Final[int]
USB_INTERFACE_SUBCLASS_QIC157: Final[int]
USB_INTERFACE_SUBCLASS_UFI: Final[int]
USB_INTERFACE_SUBCLASS_SFF8070I: Final[int]
USB_INTERFACE_SUBCLASS_SCSI: Final[int]
USB_INTERFACE_SUBCLASS_LSDFS: Final[int]
USB_INTERFACE_SUBCLASS_IEEE1667: Final[int]

USB_INTERFACE_PROTOCOL_CBI_WITH_COMPLETION: Final[int]
USB_INTERFACE_PROTOCOL_CBI: Final[int]
USB_INTERFACE_PROTOCOL_BBB: Final[int]
USB_INTERFACE_PROTOCOL_UAS: Final[int]

USBMS_REQ_ADSC: Final[int]
USBMS_REQ_LSD_GET_REQUESTS: Final[int]
USBMS_REQ_LSD_PUT_REQUESTS: Final[int]
USBMS_REQ_BBB_GET_MAX_LUN: Final[int]
USBMS_REQ_BBB_RESET: Final[int]

USBMS_CBW_MAGIC: Final[int]
USBMS_CSW_MAGIC: Final[int]

SCSI_CMD_TEST_UNIT_READY: Final[int]
SCSI_CMD_REQUEST_SENSE: Final[int]
SCSI_CMD_INQUIRY: Final[int]
SCSI_CMD_MODE_SENSE6: Final[int]
SCSI_CMD_START_STOP_UNIT: Final[int]
SCSI_CMD_PREVENT_ALLOW_MEDIUM_REMOVAL: Final[int]
SCSI_CMD_READ_FORMAT_CAPACITY: Final[int]
SCSI_CMD_READ_CAPACITY10: Final[int]
SCSI_CMD_READ10: Final[int]
SCSI_CMD_WRITE10: Final[int]
SCSI_CMD_VERIFY10: Final[int]
SCSI_CMD_MODE_SENSE10: Final[int]


_T_SCSIParameterReader = TypeVar(
    '_T_SCSIParameterReader',
    bound=ctypes.Structure,
)


class SCSIParametersVoid6(ctypes.BigEndianStructure):
    control: int


SCSIParametersTestUnitReady = SCSIParametersVoid6


class SCSIParametersRequestSense(ctypes.BigEndianStructure):
    flags: int
    allocation_length: int
    control: int


class SCSIParametersInquiry(ctypes.BigEndianStructure):
    flags: int
    page_code: int
    allocation_length: int
    control: int


class SCSIParametersModeSense6(ctypes.BigEndianStructure):
    flags: int
    page: int
    subpage_code: int
    allocation_length: int
    control: int


class SCSIParametersStartStopUnit(ctypes.BigEndianStructure):
    flags1: int
    flags2: int
    control: int


class SCSIParametersPreventAllowMediumRemoval(ctypes.BigEndianStructure):
    flags: int
    control: int


class SCSIParametersReadCapacity10(ctypes.BigEndianStructure):
    flags1: int
    lba: int
    flags2: int
    control: int


class SCSIParametersIO10(ctypes.BigEndianStructure):
    flags: int
    lba: int
    group_number: int
    transfer_length: int
    control: int


SCSIParametersRead10 = SCSIParametersIO10
SCSIParametersWrite10 = SCSIParametersIO10


class SCSIParametersVerify10(ctypes.BigEndianStructure):
    flags1: int
    lba: int
    flags2: int
    verification_length: int
    control: int


class SCSICommandBuffer(ctypes.LittleEndianStructure):
    command: int
    parameters: ctypes.Array[u8]

    @property
    def cdb_size(self) -> int: ...
    @cdb_size.setter
    def cdb_size(self, new_val: int) -> None: ...
    def parseable(self) -> bool: ...
    @overload
    def cast(self, to: Type[_T_SCSIParameterReader]) -> _T_SCSIParameterReader: ...
    @overload
    def cast(self, to: None) -> ctypes.Structure: ...
    @overload
    def cast(self) -> ctypes.Structure: ...


class SCSIRequestSenseExt(ctypes.BigEndianStructure):
    command_specific_information: int
    asc_ascq: int
    field_replaceable_unit_code: int
    sense_key_specific_0: int
    sense_key_specific_1: int
    sense_key_specific_2: int


class SCSIRequestSenseHeader(ctypes.BigEndianStructure):
    field_0: int
    _obsolete: int
    field_2: int
    information: int
    additional_sense_length: int


class SCSIResponseRequestSense(ctypes.BigEndianStructure):
    header: SCSIRequestSenseHeader
    ext: SCSIRequestSenseExt

    @property
    def error_code(self) -> int: ...
    @error_code.setter
    def error_code(self, val: int) -> int: ...
    @property
    def sense_key(self) -> int: ...
    @sense_key.setter
    def sense_key(self, val: int) -> None: ...
    @classmethod
    def simple(cls, sense_key: int, asc_ascq: int = ...) -> Self: ...


class SCSIResponseInquiryHeader(ctypes.BigEndianStructure):
    peripheral_type: int
    field_1: int
    version: int
    field_3: int
    additional_length: int


class SCSIResponseInquiryFeatures(ctypes.BigEndianStructure):
    field_0: int
    flags: int
    vendor_id: ctypes.Array[u8]
    product_id: ctypes.Array[u8]
    product_revision: ctypes.Array[u8]


class SCSIResponseInquiry(ctypes.BigEndianStructure):
    header: SCSIResponseInquiryHeader
    features: SCSIResponseInquiryFeatures

    @classmethod
    def simple(cls,
               peripheral_type: int,
               is_removable: bool,
               vendor: ByteString,
               product: ByteString,
               revision: ByteString) -> Self: ...


class SCSIResponseModeSense6Header(ctypes.BigEndianStructure):
    mode_data_length: int
    medium_type: int
    device_specific_params: int
    block_descriptor_length: int


class SCSIResponseModeSense10Header(ctypes.BigEndianStructure):
    mode_data_length: int
    medium_type: int
    device_specific_params: int
    flags: int
    block_descriptor_length: int


class CBW(ctypes.LittleEndianStructure):
    dCBWSignature: int
    dCBWTag: int
    dCBWDataTransferLength: int
    bmCBWFlags: int
    bCBWLUN: int
    bCBWCBLength: int
    CBWCB: SCSICommandBuffer


class CSW(ctypes.LittleEndianStructure):
    dCSWSignature: int
    dCSWTag: int
    dCSWDataResidue: int
    bCSWStatus: int

    @classmethod
    def simple(cls, tag: int, status: int = ..., data_residue: int = ...) -> Self: ...


class MassStorageError(RuntimeError):
    def __init__(self, csw_status: int, sense: SCSIResponseRequestSense | None = ...) -> None: ...


class MassStoragePhaseError(MassStorageError):
    def __init__(self) -> None: ...


class MassStorageIllegalRequestError(MassStorageError):
    def __init__(self, details: int = ...): ...


class MassStorageLogicalUnit:
    sense: SCSIResponseRequestSense | None

    def onReset(self) -> None: ...
    def onCommand(self,
                  cbw: CBW,
                  data: ByteString | None = ...) -> ByteString | Buffer | None: ...
    def onTestUnitReady(self) -> None: ...
    def onInquiry(self, request_size: int) -> Buffer: ...
    def onReadCapacity(self) -> tuple[int, int]: ...
    def onRead(self, lba: int, length: int) -> ByteString: ...
    def onWrite(self, lba: int, data: ByteString) -> None: ...
    def onVerify(self, lba: int, data: ByteString | None) -> None: ...


class MassStorageLogicalUnitStates(TypedDict):
    impl: MassStorageLogicalUnit
    sense: SCSIResponseRequestSense | None


class MassStorageFunction(Function):
    _receiving_length: int
    _received_data: bytearray
    _current_cbw: CBW | None
    _logical_units: Sequence[MassStorageLogicalUnit]

    def __init__(self, path, logical_units,
                 fs_list=(), hs_list=(), ss_list=(), os_list=(), lang_dict=(), all_ctrl_recip=False,
                 config0_setup=False, in_aio_blocks_max=32, out_aio_blocks_per_endpoint=2,
                 out_aio_blocks_max_packet_count=10):
    def reset(self) -> None: ...
    def getMaxLUN(self) -> int: ...
    def _processCBW(self, cbw: CBW, data: bytearray | None = ...): ...
    def _onOutEndpointComplete(self, data: memoryview | None, status: int | None): ...


class MassStorageEndpointINFile(EndpointINFile):
    parent: MassStorageFunction


class MassStorageEndpointOUTFile(EndpointOUTFile):
    parent: MassStorageFunction