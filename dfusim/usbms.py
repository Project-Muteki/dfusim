import ctypes
import errno
import functools
import os
import traceback

from functionfs import (
    ch9,
    Function,
    EndpointINFile,
    EndpointOUTFile,
    getDescriptor,
    USBInterfaceDescriptor,
    USBEndpointDescriptorNoAudio,
    USBSSEPCompDescriptor,
    _MAX_PACKET_SIZE_DICT,
)

from functionfs.common import le32, le16, u8


USB_INTERFACE_SUBCLASS_NONE = 0x00
"SCSI command set not reported."
USB_INTERFACE_SUBCLASS_RBC = 0x01
"Reduced Block Command (RBC)."
USB_INTERFACE_SUBCLASS_MMC5 = 0x02
"MMC-5 (ATAPI)."
USB_INTERFACE_SUBCLASS_QIC157 = 0x03
"QIC-157 (obsolete)."
USB_INTERFACE_SUBCLASS_UFI = 0x04
"UFI (floppy drive)."
USB_INTERFACE_SUBCLASS_SFF8070I = 0x05
"SFF-8070i (obsolete)."
USB_INTERFACE_SUBCLASS_SCSI = 0x06
"SCSI transparent command set."
USB_INTERFACE_SUBCLASS_LSDFS = 0x07
"Lockable Storage Devices (LSD) feature specification."
USB_INTERFACE_SUBCLASS_IEEE1667 = 0x08
"IEEE-1667."

USB_INTERFACE_PROTOCOL_CBI_WITH_COMPLETION = 0x00
"Control/Block/Interrupt (CBI) (with command completion interrupt)."
USB_INTERFACE_PROTOCOL_CBI = 0x01
"Control/Block/Interrupt (CBI) (without command completion interrupt)."
USB_INTERFACE_PROTOCOL_BBB = 0x50
"Bulk-only (BBB)."
USB_INTERFACE_PROTOCOL_UAS = 0x62
"USB Attached SCSI (UAS)."

USBMS_REQ_ADSC = 0x00
"Accept Device-Specific Command (ADSC)"
USBMS_REQ_LSD_GET_REQUESTS = 0xfc
"LSD Get Requests"
USBMS_REQ_LSD_PUT_REQUESTS = 0xfd
"LSD Put Requests"
USBMS_REQ_BBB_GET_MAX_LUN = 0xfe
"Bulk-only Get Max LUN"
USBMS_REQ_BBB_RESET = 0xff
"Bulk-only Reset"

USBMS_CBW_MAGIC = 0x43425355
USBMS_CSW_MAGIC = 0x53425355

USBMS_CBW_DIR_MASK = 0x80
USBMS_CBW_DIR_IN = 0x80
USBMS_CBW_DIR_OUT = 0x00

USBMS_CSW_STATUS_GOOD = 0x00
USBMS_CSW_STATUS_BAD = 0x01
USBMS_CSW_STATUS_PHASE_ERROR = 0x02

SCSI_CMD_TEST_UNIT_READY = 0x00
SCSI_CMD_REQUEST_SENSE = 0x03
SCSI_CMD_INQUIRY = 0x12
SCSI_CMD_MODE_SENSE6 = 0x1a
SCSI_CMD_START_STOP_UNIT = 0x1b
SCSI_CMD_PREVENT_ALLOW_MEDIUM_REMOVAL = 0x1e
SCSI_CMD_READ_FORMAT_CAPACITY = 0x23
SCSI_CMD_READ_CAPACITY10 = 0x25
SCSI_CMD_READ10 = 0x28
SCSI_CMD_WRITE10 = 0x2a
SCSI_CMD_VERIFY10 = 0x2f
SCSI_CMD_MODE_SENSE10 = 0x5a

SCSI_REQUEST_SENSE_F0_ERROR_CODE_MASK = 0x7f
SCSI_REQUEST_SENSE_F0_VALID_MASK = 0x80
SCSI_ERROR_CODE_CURRENT = 0x70
SCSI_ERROR_CODE_DEFERRED = 0x71

SCSI_REQUEST_SENSE_F2_SENSE_KEY_MASK = 0x0f
SCSI_SENSE_KEY_NO_SENSE = 0x0
SCSI_SENSE_KEY_RECOVERED_ERROR = 0x1
SCSI_SENSE_KEY_NOT_READY = 0x2
SCSI_SENSE_KEY_MEDIUM_ERROR = 0x3
SCSI_SENSE_KEY_HARDWARE_ERROR = 0x4
SCSI_SENSE_KEY_ILLEGAL_REQUEST = 0x5
SCSI_SENSE_KEY_UNIT_ATTENTION = 0x6
SCSI_SENSE_KEY_DATA_PROTECT = 0x7
SCSI_SENSE_KEY_BLANK_CHECK = 0x8
SCSI_SENSE_KEY_VENDOR_SPECIFIC = 0x9
SCSI_SENSE_KEY_COPY_ABORTED = 0xa
SCSI_SENSE_KEY_ABORTED_COMMAND = 0xb
SCSI_SENSE_KEY_VOLUME_OVERFLOW = 0xd
SCSI_SENSE_KEY_MISCOMPARE = 0xe

SCSI_ASC_NONE = 0x00
SCSI_ASC_LUN_NOT_READY = 0x0400
SCSI_ASC_LUN_STARTING = SCSI_ASC_LUN_NOT_READY | 0x01
SCSI_ASC_INVALID_FIELD_IN_CDB = 0x2400
SCSI_ASC_LUN_NOT_SUPPORTED = 0x2500

SCSI_INQUIRY_HEADER_F1_RMB = 0x80
SCSI_INQUIRY_HEADER_F3_AERC = 0x80
SCSI_INQUIRY_HEADER_F3_NORMACA = 0x20
SCSI_INQUIRY_HEADER_F3_HISUP = 0x10
SCSI_INQUIRY_HEADER_F3_FORMAT_MASK = 0x0f
SCSI_INQUIRY_HEADER_FORMAT_SPC2 = 0x02

SCSI_INQUIRY_HEADER_VERSION_NONE = 0x0
SCSI_INQUIRY_HEADER_VERSION_SCSI2_ANSI = 0x2
SCSI_INQUIRY_HEADER_VERSION_SPC = 0x3
SCSI_INQUIRY_HEADER_VERSION_SPC2 = 0x4
SCSI_INQUIRY_HEADER_VERSION_SCSI2_ISO = 0x80

SCSI_INQUIRY_PERIF_QUALIFIER_LOADED = 0 << 5
SCSI_INQUIRY_PERIF_QUALIFIER_UNLOADED = 1 << 5
SCSI_INQUIRY_PERIF_QUALIFIER_UNKNOWN = 3 << 5
SCSI_INQUIRY_PERIF_TYPE_DIRECT = 0x00

SCSI_INQUIRY_FEATURES_F0_SCCS = 0x80
SCSI_INQUIRY_FEATURES_FLAG_BQUE = 0x8000
SCSI_INQUIRY_FEATURES_FLAG_ENCSERV = 0x4000
SCSI_INQUIRY_FEATURES_FLAG_MULTIP = 0x1000
SCSI_INQUIRY_FEATURES_FLAG_MCHNGR = 0x0800
SCSI_INQUIRY_FEATURES_FLAG_ADDR16 = 0x0100
SCSI_INQUIRY_FEATURES_FLAG_RELADR = 0x0080
SCSI_INQUIRY_FEATURES_FLAG_WBUS16 = 0x0020
SCSI_INQUIRY_FEATURES_FLAG_SYNC = 0x0010
SCSI_INQUIRY_FEATURES_FLAG_LINKED = 0x0008
SCSI_INQUIRY_FEATURES_FLAG_CMDQUE = 0x0002

SCSI_VERIFY_F1_BYTCHK = 0x02


class SCSIParametersVoid6(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('_reserved', u8 * 4),
        ('control', u8),
    ]


SCSIParametersTestUnitReady = SCSIParametersVoid6


class SCSIParametersRequestSense(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('flags', u8),
        ('_reserved', u8 * 2),
        ('allocation_length', u8),
        ('control', u8),
    ]


class SCSIParametersInquiry(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('flags', u8),
        ('page_code', u8),
        ('allocation_length', le16),
        ('control', u8),
    ]


class SCSIParametersModeSense6(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('flags', u8),
        ('page', u8),
        ('subpage_code', u8),
        ('allocation_length', u8),
        ('control', u8),
    ]


class SCSIParametersStartStopUnit(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('flags1', u8),
        ('_reserved', u8 * 2),
        ('flags2', u8),
        ('control', u8),
    ]


class SCSIParametersPreventAllowMediumRemoval(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('_reserved', u8 * 3),
        ('flags', u8),
        ('control', u8),
    ]


class SCSIParametersReadCapacity10(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('flags1', u8),
        ('lba', le32),
        ('_reserved', u8 * 2),
        ('flags2', u8),
        ('control', u8),
    ]


class SCSIParametersIO10(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('flags', u8),
        ('lba', le32),
        ('group_number', u8),
        ('transfer_length', le16),
        ('control', u8),
    ]


SCSIParametersRead10 = SCSIParametersIO10
SCSIParametersWrite10 = SCSIParametersIO10


class SCSIParametersVerify10(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('flags1', u8),
        ('lba', le32),
        ('flags2', u8),
        ('verification_length', le16),
        ('control', u8),
    ]


class SCSIParametersModeSense10(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('flags', u8),
        ('page', u8),
        ('_reserved', u8 * 4),
        ('allocation_length', le16),
        ('control', u8),
    ]


class SCSICommandBuffer(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('command', u8),
        ('parameters', u8 * 15),
    ]

    _PARSERS = {
        SCSI_CMD_TEST_UNIT_READY: SCSIParametersTestUnitReady,
        SCSI_CMD_REQUEST_SENSE: SCSIParametersRequestSense,
        SCSI_CMD_INQUIRY: SCSIParametersInquiry,
        SCSI_CMD_MODE_SENSE6: SCSIParametersModeSense6,
        SCSI_CMD_START_STOP_UNIT: SCSIParametersStartStopUnit,
        SCSI_CMD_PREVENT_ALLOW_MEDIUM_REMOVAL: SCSIParametersPreventAllowMediumRemoval,
        SCSI_CMD_READ_CAPACITY10: SCSIParametersReadCapacity10,
        SCSI_CMD_READ10: SCSIParametersIO10,
        SCSI_CMD_WRITE10: SCSIParametersIO10,
        SCSI_CMD_VERIFY10: SCSIParametersVerify10,
        SCSI_CMD_MODE_SENSE10: SCSIParametersModeSense10,
    }

    @property
    def cdb_size(self):
        if hasattr(self, '_cdb_size_override'):
            return getattr(self, '_cdb_size_override')

        # TODO extract from custom parser
        if 0x00 <= self.command <= 0x1f:
            return 6
        elif 0x20 <= self.command <= 0x5f:
            return 10
        elif 0x80 <= self.command <= 0x9f:
            return 16
        elif 0xa0 <= self.command <= 0xbf:
            return 12
        return 0

    @cdb_size.setter
    def cdb_size(self, size):
        setattr(self, '_cdb_size_override', size)

    def parseable(self):
        """
        Check whether the current command parameter can be cast.
        """
        return self.command in self._PARSERS

    def cast(self, to=None):
        """
        Cast the parameters to their appropriate format.
        """
        if to is not None:
            return to.from_buffer(self.parameters)
        parser = self._PARSERS.get(self.command)
        if parser is None:
            raise TypeError(f'Unknown command {self.command}')
        return parser.from_buffer(self.parameters)


class SCSIRequestSenseExt(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('command_specific_information', le32),
        ('asc_ascq', le16),
        ('field_replaceable_unit_code', u8),
        ('sense_key_specific_0', u8),
        ('sense_key_specific_1', u8),
        ('sense_key_specific_2', u8),
    ]


class SCSIRequestSenseHeader(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('field_0', u8),
        ('_obsolete', u8),
        ('field_2', u8),
        ('information', le32),
        ('additional_sense_length', u8),
    ]


class SCSIResponseRequestSense(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('header', SCSIRequestSenseHeader),
        ('ext', SCSIRequestSenseExt),
    ]

    @property
    def error_code(self):
        return self.header.field_0 & SCSI_REQUEST_SENSE_F0_ERROR_CODE_MASK

    @error_code.setter
    def error_code(self, val):
        self.header.field_0 &= (~SCSI_REQUEST_SENSE_F0_ERROR_CODE_MASK) & 0xff
        self.header.field_0 |= val & SCSI_REQUEST_SENSE_F0_ERROR_CODE_MASK

    @property
    def sense_key(self):
        return self.header.field_2 & SCSI_REQUEST_SENSE_F2_SENSE_KEY_MASK

    @sense_key.setter
    def sense_key(self, val):
        self.header.field_2 &= (~SCSI_REQUEST_SENSE_F2_SENSE_KEY_MASK) & 0xff
        self.header.field_2 |= val & SCSI_REQUEST_SENSE_F2_SENSE_KEY_MASK

    @classmethod
    def simple(cls, sense_key, asc_ascq):
        result = cls()
        result.header.additional_sense_length = ctypes.sizeof(SCSIRequestSenseExt)
        result.error_code = SCSI_ERROR_CODE_CURRENT
        result.sense_key = sense_key
        result.ext.asc_ascq = asc_ascq
        return result


class SCSIResponseInquiryHeader(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('peripheral_type', u8),
        ('field_1', u8),
        ('version', u8),
        ('field_3', u8),
        ('additional_length', u8),
    ]


class SCSIResponseInquiryFeatures(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('field_0', u8),
        ('flags', le16),
        ('vendor_id', u8 * 8),
        ('product_id', u8 * 16),
        ('product_revision', u8 * 4),
    ]


class SCSIResponseInquiry(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('header', SCSIResponseInquiryHeader),
        ('features', SCSIResponseInquiryFeatures),
    ]

    @classmethod
    def simple(cls, peripheral_type, is_removable, vendor, product, revision):
        if len(vendor) > SCSIResponseInquiryFeatures.vendor_id.size:
            raise ValueError('Vendor string too large.')
        if len(product) > SCSIResponseInquiryFeatures.product_id.size:
            raise ValueError('Product string too large.')
        if len(revision) > SCSIResponseInquiryFeatures.product_revision.size:
            raise ValueError('Revision string too large.')

        result = cls(
            header=SCSIResponseInquiryHeader(
                peripheral_type=peripheral_type,
                field_1=SCSI_INQUIRY_HEADER_F1_RMB if is_removable else 0,
                version=SCSI_INQUIRY_HEADER_VERSION_SPC2,
                field_3=SCSI_INQUIRY_HEADER_FORMAT_SPC2,
                additional_length=ctypes.sizeof(SCSIResponseInquiryFeatures)
            )
        )
        ctypes.memmove(result.features.vendor_id, vendor, len(vendor))
        ctypes.memmove(result.features.product_id, product, len(product))
        ctypes.memmove(result.features.product_revision, revision, len(revision))
        return result


class SCSIResponseModeSense6Header(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('mode_data_length', u8),
        ('medium_type', u8),
        ('device_specific_params', u8),
        ('block_descriptor_length', u8),
    ]


class SCSIResponseModeSense10Header(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('mode_data_length', le16),
        ('medium_type', u8),
        ('device_specific_params', u8),
        ('flags', u8),
        ('_reserved', u8),
        ('block_descriptor_length', le16),
    ]


class CBW(ctypes.LittleEndianStructure):
    """
    Command Block Wrapper (CBW). Must be sent as a separate packet
    **before** any data transfer.
    """
    _pack_ = 1
    _fields_ = [
        ('dCBWSignature', le32),
        ('dCBWTag', le32),
        ('dCBWDataTransferLength', le32),
        ('bmCBWFlags', u8),
        ('bCBWLUN', u8),
        ('bCBWCBLength', u8),
        ('CBWCB', SCSICommandBuffer),
    ]


class CSW(ctypes.LittleEndianStructure):
    """
    Command Status Wrapper (CSW). Must be sent as a separate packet
    **after** any data transfer.
    """
    _pack_ = 1
    _fields_ = [
        ('dCSWSignature', le32),
        ('dCSWTag', le32),
        ('dCSWDataResidue', le32),
        ('bCSWStatus', u8),
    ]

    @classmethod
    def simple(cls, tag, status=USBMS_CSW_STATUS_GOOD, data_residue=0):
        return cls(
            dCSWSignature=USBMS_CSW_MAGIC,
            dCSWTag=tag,
            dCSWDataResidue=data_residue,
            bCSWStatus=status,
        )


class MassStorageError(RuntimeError):
    """
    Mass storage error class. Raise this in a request handler to gracefully
    return the appropriate error code and set the correct sense data.
    """
    _NAMES = {
        USBMS_CSW_STATUS_GOOD: 'Good status',
        USBMS_CSW_STATUS_BAD: 'Bad status',
        USBMS_CSW_STATUS_PHASE_ERROR: 'Phase error',
    }

    def __init__(self, csw_status, sense=None):
        self.csw_status = csw_status
        self.sense = sense

    def __str__(self):
        name = self._NAMES.get(self.csw_status, f'Status {self.csw_status:#02x}')
        return name


class MassStoragePhaseError(MassStorageError):
    def __init__(self):
        super().__init__(USBMS_CSW_STATUS_PHASE_ERROR, None)


class MassStorageIllegalRequestError(MassStorageError):
    """
    Raise an illegal request error to the USB host.
    """
    def __init__(self, details=SCSI_ASC_NONE):
        raise MassStorageError(
            USBMS_CSW_STATUS_BAD,
            SCSIResponseRequestSense.simple(
                SCSI_SENSE_KEY_ILLEGAL_REQUEST,
                asc_ascq=details
            )
        )


class MassStorageNotReadyError(MassStorageError):
    """
    Raise an illegal request error to the USB host.
    """
    def __init__(self, details=SCSI_ASC_NONE):
        raise MassStorageError(
            USBMS_CSW_STATUS_BAD,
            SCSIResponseRequestSense.simple(
                SCSI_SENSE_KEY_NOT_READY,
                asc_ascq=details
            )
        )


# Currently unused
class MassStorageEndpointINFile(EndpointINFile):
    def __init__(self, path, submit, eventfd):
        super().__init__(path, submit, eventfd)

    def onComplete(self, buffer_list, user_data, status):
        if status == -errno.ESHUTDOWN:
            return False
        return super().onComplete(buffer_list, user_data, status)

    # TODO handle onSubmitEAGAIN


class MassStorageEndpointOUTFile(EndpointOUTFile):
    def __init__(self, complete_callback, path, submit, release, aio_block_list):
        self.onOutEndpointComplete = complete_callback
        super().__init__(path, submit, release, aio_block_list)

    def onComplete(self, data, status):
        if status == -errno.ESHUTDOWN:
            print('Endpoint halt!')
            return
        self.onOutEndpointComplete(data, status)


class MassStorageFunction(Function):
    """
    Implement USB Mass Storage (Bulk-Only) protocol.
    """

    def __init__(self, path, logical_units,
                 fs_list=(), hs_list=(), ss_list=(), os_list=(),
                 lang_dict=(),
                 all_ctrl_recip=False,
                 config0_setup=False,
                 in_aio_blocks_max=32,
                 out_aio_blocks_per_endpoint=2,
                 out_aio_blocks_max_packet_count=10):

        def buildDescriptor(max_packet, need_companion=False):
            ifd = getDescriptor(
                USBInterfaceDescriptor,
                bNumEndpoints=2,
                bInterfaceClass=ch9.USB_CLASS_MASS_STORAGE,
                bInterfaceSubClass=USB_INTERFACE_SUBCLASS_SCSI,
                bInterfaceProtocol=USB_INTERFACE_PROTOCOL_BBB,
            )
            inep = getDescriptor(
                USBEndpointDescriptorNoAudio,
                bEndpointAddress=1 | ch9.USB_DIR_IN,
                bmAttributes=ch9.USB_ENDPOINT_XFER_BULK,
                wMaxPacketSize=max_packet,
                bInterval=0,
            )
            outep = getDescriptor(
                USBEndpointDescriptorNoAudio,
                bEndpointAddress=2 | ch9.USB_DIR_OUT,
                bmAttributes=ch9.USB_ENDPOINT_XFER_BULK,
                wMaxPacketSize=max_packet,
                bInterval=0,
            )

            if need_companion:
                inep_comp = getDescriptor(
                    USBSSEPCompDescriptor,
                    bMaxBurst=3,
                    bmAttributes=ch9.USB_ENDPOINT_XFER_BULK,
                    wBytesPerInterval=0,
                )
                outep_comp = getDescriptor(
                    USBSSEPCompDescriptor,
                    bMaxBurst=3,
                    bmAttributes=ch9.USB_ENDPOINT_XFER_BULK,
                    wBytesPerInterval=0,
                )
                return [ifd, inep, inep_comp, outep, outep_comp]
            return [ifd, inep, outep]

        if len(logical_units) == 0:
            raise ValueError('Cannot have 0 logical unit.')

        self._receiving_length = 0
        self._received_data = bytearray()
        self._current_cbw = None
        self._logical_units = tuple(luc() for luc in logical_units)

        super().__init__(
            path,
            fs_list=fs_list or buildDescriptor(
                _MAX_PACKET_SIZE_DICT[ch9.USB_ENDPOINT_XFER_BULK][0]
            ),
            hs_list=hs_list or buildDescriptor(
                _MAX_PACKET_SIZE_DICT[ch9.USB_ENDPOINT_XFER_BULK][1]
            ),
            ss_list=ss_list or buildDescriptor(
                _MAX_PACKET_SIZE_DICT[ch9.USB_ENDPOINT_XFER_BULK][2]
            ),
            os_list=os_list,
            lang_dict=lang_dict,
            all_ctrl_recip=all_ctrl_recip,
            config0_setup=config0_setup,
            in_aio_blocks_max=in_aio_blocks_max,
            out_aio_blocks_per_endpoint=out_aio_blocks_per_endpoint,
            out_aio_blocks_max_packet_count=out_aio_blocks_max_packet_count
        )

    def onSetup(self, request_type, request, value, index, length):
        """
        Called when a setup USB transaction was received.

        For mass storage, 2 extra class-specific requests were handled in
        addition to its parent class:
        - USBMS_REQ_BBB_RESET (calls the reset method)
        - USBMS_REQ_BBB_GET_MAX_LUN (calls the getMaxLUN method)

        If this method raises anything, endpoint 0 is halted by its caller and
        exception is let through.

        May be overridden in subclass.
        """
        if (
            (request_type & ch9.USB_ENDPOINT_DIR_MASK) == ch9.USB_DIR_OUT and
            (request_type & ch9.USB_TYPE_MASK) == ch9.USB_TYPE_CLASS and
            (request_type & ch9.USB_RECIP_MASK) == ch9.USB_RECIP_INTERFACE and
            request == USBMS_REQ_BBB_RESET
        ):
            self.reset()
            return
        elif (
            (request_type & ch9.USB_ENDPOINT_DIR_MASK == ch9.USB_DIR_IN) and
            (request_type & ch9.USB_TYPE_MASK == ch9.USB_TYPE_CLASS) and
            (request_type & ch9.USB_RECIP_MASK == ch9.USB_RECIP_INTERFACE) and
            request == USBMS_REQ_BBB_GET_MAX_LUN
        ):
            max_lun = self.getMaxLUN()
            self.ep0.write(max_lun.to_bytes(1, 'big'))
            return
        super().onSetup(request_type, request, value, index, length)

    def getEndpointClass(self, is_in, descriptor):
        if is_in:
            return MassStorageEndpointINFile
        else:
            return functools.partial(
                MassStorageEndpointOUTFile,
                self._onOutEndpointComplete
            )

    def onBind(self):
        self.reset()

    def reset(self):
        """
        Called when the host issues a USBMS_REQ_BBB_RESET class-specific
        request. Should perform any reset tasks and return nothing.

        May be overridden in subclass.
        """
        for lu in self._logical_units:
            lu.onReset()

        self._receiving_length = 0
        self._received_data.clear()
        self._current_cbw = None

    def getMaxLUN(self):
        """
        Called when the host issues a USBMS_REQ_BBB_GET_MAX_LUN class-specific
        request. Should return an integer in range(16) that indicates the
        maximum Logic Unit Number (LUN) available on this function.

        May be overridden in subclass.
        """
        return len(self._logical_units) - 1

    def _processCBW(self, cbw, data=None):
        inep = self.getEndpoint(1)
        try:
            response_data = self._logical_units[cbw.bCBWLUN].onCommand(
                cbw, data
            )
            if response_data is not None:
                inep.write(response_data)
            inep.write(CSW.simple(cbw.dCBWTag))
        except MassStorageError as err:
            # Bus state is still sane enough for us to return an error code.
            # So we return it.
            traceback.print_exc()
            self._logical_units[cbw.bCBWLUN].sense = err.sense
            inep.write(
                CSW.simple(cbw.dCBWTag, status=err.csw_status)
            )
        except Exception:
            # Unknown errors are treated as phase errors.
            traceback.print_exc()
            self._logical_units[cbw.bCBWLUN].sense = None
            inep.write(
                CSW.simple(cbw.dCBWTag, status=USBMS_CSW_STATUS_PHASE_ERROR)
            )

    def _onOutEndpointComplete(self, data, status):
        print(len(data) if data is not None else None, os.strerror(-status))
        if status != 0:
            # Low-level fault detected. Just STALL the endpoints.
            self.getEndpoint(1).halt()
            self.getEndpoint(2).halt()
            raise IOError(-status)
        try:
            if self._receiving_length == 0:
                cbw = CBW.from_buffer(data)
                if cbw.dCBWSignature != USBMS_CBW_MAGIC:
                    self.getEndpoint(1).halt()
                    self.getEndpoint(2).halt()
                    print('Invalid CBW magic')
                    return
                if (cbw.dCBWDataTransferLength == 0 or
                        cbw.bmCBWFlags & USBMS_CBW_DIR_MASK == USBMS_CBW_DIR_IN):
                    self._processCBW(cbw)
                    return
                print(f'Receiving {cbw.dCBWDataTransferLength} bytes...')
                self._receiving_length = cbw.dCBWDataTransferLength
                self._received_data.clear()
                self._current_cbw = CBW.from_buffer_copy(data)
            else:
                self._received_data.extend(data)
                print(hex(self._current_cbw.CBWCB.command), len(self._received_data))
                if len(self._received_data) == self._receiving_length:
                    assert self._current_cbw is not None
                    print('Received.')
                    self._receiving_length = 0
                    self._processCBW(self._current_cbw, self._received_data)
        except Exception:
            # STALL the endpoints so host know something nasty has happened
            traceback.print_exc()
            self.getEndpoint(1).halt()
            self.getEndpoint(2).halt()


class MassStorageLogicalUnit:
    """
    Handler class for logical unit operations.
    """

    def __init__(self):
        self.sense = None

    def onReset(self):
        pass

    def onCommand(self, cbw, data=None):
        if not cbw.CBWCB.parseable():
            raise MassStorageIllegalRequestError()

        params = cbw.CBWCB.cast()

        if ctypes.sizeof(params) != cbw.bCBWCBLength - 1:
            raise MassStorageIllegalRequestError()

        if isinstance(params, SCSIParametersVoid6):
            if cbw.CBWCB.command == SCSI_CMD_TEST_UNIT_READY:
                self.onTestUnitReady()
            return
        elif isinstance(params, SCSIParametersRequestSense):
            if self.sense is not None:
                return self.sense
            return SCSIResponseRequestSense.simple(
                SCSI_SENSE_KEY_NO_SENSE,
                SCSI_ASC_NONE
            )
        elif isinstance(params, SCSIParametersModeSense6):
            # Stubbed to return no mode since we don't implement any modes,
            # nor is it necessary for now.
            return SCSIResponseModeSense6Header(
                mode_data_length=(
                    ctypes.sizeof(SCSIResponseModeSense6Header) -
                    SCSIResponseModeSense6Header.mode_data_length.size
                )
            )
        elif isinstance(params, SCSIParametersInquiry):
            # TODO ensure no flag is set, otherwise call onInquiryEx
            return self.onInquiry(params.allocation_length)
        elif isinstance(params, SCSIParametersStartStopUnit):
            # Stubbed to always succeed for now.
            return
        elif isinstance(params, SCSIParametersPreventAllowMediumRemoval):
            # Stubbed to always succeed for now.
            return
        elif isinstance(params, SCSIParametersReadCapacity10):
            if params.flags2 == 0:
                num_lba, sector_size = self.onReadCapacity()
                return (
                    num_lba.to_bytes(4, 'big') +
                    sector_size.to_bytes(4, 'big')
                )
            raise MassStorageIllegalRequestError(SCSI_ASC_INVALID_FIELD_IN_CDB)
        elif isinstance(params, SCSIParametersIO10):
            if cbw.CBWCB.command == SCSI_CMD_READ10:
                data = self.onRead(params.lba, params.transfer_length)
                return data
            elif cbw.CBWCB.command == SCSI_CMD_WRITE10:
                # This shouldn't happen, but in case it happens, raise a phase
                # error.
                if data is None:
                    raise MassStoragePhaseError()
                print(len(data))
                self.onWrite(params.lba, data)
                return
        elif isinstance(params, SCSIParametersVerify10):
            do_byte_check = bool(params.flags1 & SCSI_VERIFY_F1_BYTCHK)
            if data is None and do_byte_check:
                raise MassStorageIllegalRequestError(
                    SCSI_ASC_INVALID_FIELD_IN_CDB
                )
            self.onVerify(params.lba, data if do_byte_check else None)
            return

        raise MassStorageIllegalRequestError()

    def onTestUnitReady(self):
        """
        Test whether the current logical unit is ready or not.

        Should return nothing. When the unit is not ready, an MassStorageError
        exception should be raised to report the status.
        """
        return

    def onInquiry(self, request_size):
        if request_size >= ctypes.sizeof(SCSIResponseInquiry):
            return SCSIResponseInquiry.simple(
                (SCSI_INQUIRY_PERIF_QUALIFIER_LOADED |
                 SCSI_INQUIRY_PERIF_TYPE_DIRECT),
                True,
                b'PyFFS',
                b'USBMS',
                b'0000',
            )
        raise MassStorageIllegalRequestError(SCSI_ASC_INVALID_FIELD_IN_CDB)

    def onReadCapacity(self):
        """
        Return the capacity of current logical unit.

        This function shall return a tuple of exactly 2 integers, the first one
        being the total number of LBAs available and the second one being the
        size of each LBA.
        """
        return 0, 512

    def onRead(self, lba, length):
        return b'\x00' * length * 512

    def onWrite(self, lba, data):
        pass

    def onVerify(self, lba, data):
        pass
