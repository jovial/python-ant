# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011, Martín Raúl Villalba
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
##############################################################################

import struct

from ant.core.exceptions import MessageError
from ant.core.constants import *
 
def convertBytes(bytes):
    if len(bytes) == 1:
        return ord(bytes[0])
    elif len(bytes) == 2:
        data_string = ''.join(bytes)
        return struct.unpack('<H', data_string)[0]
    else: 
        raise ValueError('Unsupported number of bytes')


class Message(object):
    def __init__(self, type_=0x00, payload='',sync= MESSAGE_TX_SYNC):
        self.setType(type_)
        self.setPayload(payload)
        self.setSync(sync)

    def getPayload(self):
        return ''.join(self.payload)

    def getPayloadAsList(self):
        return self.payload

    def setPayload(self, payload):
        if len(payload) > 9:
            #raise MessageError(
            #      'Could not set payload (payload too long).')
            pass

        self.payload = []
        for byte in payload:
            self.payload += byte

    def getRawData(self):
        payload = self.getPayload()[1:9]
        return payload

    def setRawData(self,raw):
        payload = self.getPayloadAsList()
        payload[1:9] = raw
        self.setPayload(payload)

    def getType(self):
        return self.type_

    def setType(self, type_):
        if (type_ > 0xFF) or (type_ < 0x00):
            raise MessageError('Could not set type (type out of range).')

        self.type_ = type_

    def getSync(self):
        return self.sync

    def setSync(self, sync):
        if sync != MESSAGE_TX_SYNC and sync != MESSAGE_TX_SYNC_LSB:
            raise MessageError('Could not set sync (Unknown value).')
        self.sync = sync    

    def getChecksum(self):
        data = chr(len(self.getPayload()))
        data += chr(self.getType())
        data += self.getPayload()

        checksum = self.getSync()
        for byte in data:
            checksum = (checksum ^ ord(byte)) % 0xFF

        return checksum


    def getSize(self):
        return len(self.getPayload()) + 4

    def encode(self):
        raw = struct.pack('BBB',
                          self.getSync(),
                          len(self.getPayload()),
                          self.getType())
        raw += self.getPayload()
        raw += chr(self.getChecksum())

        return raw

    def decode(self, raw):
        if len(raw) < 5:
            raise MessageError('Could not decode (message is incomplete).')

        sync, length, type_ = struct.unpack('BBB', raw[:3])

        if sync != MESSAGE_TX_SYNC and sync != MESSAGE_TX_SYNC_LSB:
            raise MessageError('Could not decode (expected TX sync).')
        if length > 9:
            #raise MessageError('Could not decode (payload too long).')
            #print length
            pass
        if len(raw) < (length + 4):
            raise MessageError('Could not decode (message is incomplete).')

        self.setType(type_)
        self.setPayload(raw[3:length + 3])
        self.setSync(sync)

        if self.getChecksum() != ord(raw[length + 3]):
            raise MessageError('Could not decode (bad checksum).',
                               internal='CHECKSUM')

        return self.getSize()

    def _getBurstMsg(self):
        format = self.getFormat()
        if format == MessageFormat.EXTENDED:
            msg = ExtendedChannelBurstDataMessage()
        else:
            msg = ChannelBurstDataMessage() 
        return msg

    def _getBroadcastMessage(self):
        format = self.getFormat()
        if format == MessageFormat.EXTENDED:
            msg = ExtendedChannelBroadcastDataMessage()
        else:
            msg = ChannelBroadcastDataMessage()
        return msg

    def _getAckDataMessage(self):
        format = self.getFormat()
        if format == MessageFormat.EXTENDED:
            msg = ExtendedChannelAcknowledgedDataMessage()
        else:
            msg = ChannelAcknowledgedDataMessage() 
        return msg           

    def getFormat(self):
        length = len(self.getPayloadAsList())
        format = MessageFormat.LEGACY
        if length > MESSAGE_LENGTH_LEGACY:
            format = MessageFormat.EXTENDED
        return format

    def getHandler(self, raw=None):
        if raw:
            self.decode(raw)

        msg = None
        if self.type_ == MESSAGE_CHANNEL_UNASSIGN:
            msg = ChannelUnassignMessage()
        elif self.type_ == MESSAGE_CHANNEL_ASSIGN:
            msg = ChannelAssignMessage()
        elif self.type_ == MESSAGE_CHANNEL_ID:
            msg = ChannelIDMessage()
        elif self.type_ == MESSAGE_CHANNEL_PERIOD:
            msg = ChannelPeriodMessage()
        elif self.type_ == MESSAGE_CHANNEL_SEARCH_TIMEOUT:
            msg = ChannelSearchTimeoutMessage()
        elif self.type_ == MESSAGE_CHANNEL_FREQUENCY:
            msg = ChannelFrequencyMessage()
        elif self.type_ == MESSAGE_CHANNEL_TX_POWER:
            msg = ChannelTXPowerMessage()
        elif self.type_ == MESSAGE_NETWORK_KEY:
            msg = NetworkKeyMessage()
        elif self.type_ == MESSAGE_TX_POWER:
            msg = TXPowerMessage()
        elif self.type_ == MESSAGE_SYSTEM_RESET:
            msg = SystemResetMessage()
        elif self.type_ == MESSAGE_CHANNEL_OPEN:
            msg = ChannelOpenMessage()
        elif self.type_ == MESSAGE_CHANNEL_CLOSE:
            msg = ChannelCloseMessage()
        elif self.type_ == MESSAGE_CHANNEL_REQUEST:
            msg = ChannelRequestMessage()
        elif self.type_ == MESSAGE_CHANNEL_BROADCAST_DATA:
            msg = self._getBroadcastMessage()
        elif self.type_ == MESSAGE_CHANNEL_ACKNOWLEDGED_DATA:
            msg = self._getAckDataMessage()
        elif self.type_ == MESSAGE_CHANNEL_BURST_DATA:
            msg = self._getBurstMsg()
        elif self.type_ == MESSAGE_CHANNEL_EXTENDED_BROADCAST_DATA:
            msg = LegacyChannelBroadcastDataMessage()
        elif self.type_ == MESSAGE_CHANNEL_EXTENDED_ACKNOWLEDGED_DATA:
            msg = LegacyChannelAcknowledgedDataMessage()
        elif self.type_ == MESSAGE_CHANNEL_EXTENDED_BURST_DATA:
            msg = LegacyChannelBurstDataMessage()
        elif self.type_ == MESSAGE_CHANNEL_EVENT:
            msg = ChannelEventMessage()
        elif self.type_ == MESSAGE_CHANNEL_STATUS:
            msg = ChannelStatusMessage()
        elif self.type_ == MESSAGE_VERSION:
            msg = VersionMessage()
        elif self.type_ == MESSAGE_CAPABILITIES:
            msg = CapabilitiesMessage()
        elif self.type_ == MESSAGE_SERIAL_NUMBER:
            msg = SerialNumberMessage()
        elif self.type_ == MESSAGE_STARTUP:
            msg = StartupMessage()
        else:
            raise MessageError('Could not find message handler ' \
                               '(unknown message type).', internal = 'UNKNOWN_MESSAGE_TYPE')

        msg.setPayload(self.getPayload())
        return msg


class IncompleteReadException(Exception):
    pass

class TrackedBuffer(object):
    def __init__(self, payload):
        self.payload = payload
        self.index = 0

    def read(self, length):
        if self.index + length > len(self.payload):
            raise IncompleteReadException("Too few bytes for requested read")
        rtn = self.payload[self.index:self.index+length]
        self.index += length
        return rtn

class ChannelData(object):
    def __init__(self,device_number=None, device_type=None, transmission_type=None):
        self.device_number = device_number
        self.device_type = device_type
        self.transmission_type = transmission_type

    def getDeviceNumber(self):
        return self.device_number

    def setDeviceNumber(self, device_number):
        self.device_number = device_number

    def getDeviceType(self):
        return self.device_type

    def setDeviceType(self, device_type):
        self.device_type = device_type

    def getTransmissionType(self):
        return self.transmission_type

    def setTransmissionType(self, trans_type):
        self.transmission_type = trans_type   

class ExtendedMessage(Message,ChannelData):
    def __init__(self, type_=0x00, payload='\x00'*11,sync= MESSAGE_TX_SYNC):
        Message.__init__(self,type_=type_,payload=payload,sync=sync)
        self.flag = None    
        self.rssi_type = None;
        self.rssi_value = None;
        self.rssi_threshold = None;
        self.timestamp = None;

    def setPayload(self, payload):
        Message.setPayload(self,payload)
        self.update()

    def update(self):
        payload = self.getPayloadAsList()
        
        if len(payload) < 10:
            raise MessageError('Too few bytes for an extended message (too few bytes)')

        flag = convertBytes(payload[9:10])
        self.setFlag(flag)

        # start at first byte of extended data
        extended_data = TrackedBuffer(payload[10:])
        if flag & ExtendedMessageFlags.ENABLE_CHANNEL_ID == ExtendedMessageFlags.ENABLE_CHANNEL_ID:
            # piggy back ChannelIDMessage
            #id_message = ChannelIDMessage()

            #dummy_payload = []
            #payload = self.getPayloadAsList()
            
            #include channel id
            #dummy_payload.extend(payload[:ElementSize.CHANNEL_ID])

            # include actual data 
            #length =  ElementSize.DEVICE_NUMBER + ElementSize.DEVICE_TYPE + ElementSize.TRANSMISSION_TYPE
            #dummy_payload.extend(extended_data.read(length))

            #id_message.setPayload(dummy_payload)
            
            device_number = convertBytes(extended_data.read(ElementSize.DEVICE_NUMBER))
            self.setDeviceNumber(device_number)

            device_type = convertBytes(extended_data.read(ElementSize.DEVICE_TYPE))
            self.setDeviceType(device_type)
            
            transmission_type = convertBytes(extended_data.read(ElementSize.TRANSMISSION_TYPE))
            self.setTransmissionType(transmission_type)

        if flag & ExtendedMessageFlags.ENABLE_RSSI_OUTPUT == ExtendedMessageFlags.ENABLE_RSSI_OUTPUT:
            rssi_type = convertBytes(extended_data.read(ElementSize.RSSI_MEASUREMENT_TYPE))
            self.setRssiType(rssi_type)

            rssi_value = convertBytes(extended_data.read(ElementSize.RSSI_VALUE))
            self.setRssiValue(rssi_value)

            rssi_threshold = convertBytes(extended_data.read(ElementSize.RSSI_THRESHOLD_CONFIG))
            self.setRssiThreshold(rssi_threshold)

        if flag & ExtendedMessageFlags.ENABLE_RX_TIMESTAMP == ExtendedMessageFlags.ENABLE_RX_TIMESTAMP:
            timestamp = convertBytes(extended_data.read(ElementSize.RX_TIMESTAMP))
            self.setTimestamp(timestamp)

    
    def decode(self,raw):
        size = Message.decode(self,raw)
        
        self.update()

        return size

    def encode(self):
        payload = self.getPayload()[0:9]
        msg = Message(type_=self.getType(),payload=payload,sync=self.getSync())
        raw = msg.encode()
        return raw                                                                    

    def getTimestamp(self):
        return self.timestamp

    def setTimestamp(self,timestamp):
        self.timestamp = timestamp

    def getRssiType(self):
        return self.rssi_type

    def setRssiType(self, rssi_type):
        self.rssi_type = rssi_type

    def getRssiValue(self):
        return self.rssi_value

    def setRssiValue(self, rssi_value):
        self.rssi_value = rssi_value               

    def getRssiThreshold(self):
        return self.rssi_threshold

    def setRssiThreshold(self, rssi_threshold):
        self.rssi_threshold = rssi_threshold  
                                   
    def setFlag(self, flag):
        self.flag = flag

    def getFlag(self):
        return self.flag    
    
    

class LegacyExtendedMessage(Message, ChannelData):
    def __init__(self, type_=0x00, payload='\x00'*13,sync= MESSAGE_TX_SYNC):
        Message.__init__(self,type_=type_,payload=payload,sync=sync)
        self.device_number = 0x00
        self.device_type = 0x00
        self.transmission_type = 0x00


    def setPayload(self, payload, update=True):
        Message.setPayload(self,payload)
        if update:
            self.update()

    def update(self):
        payload = self.getPayloadAsList()
               
        extended_data = TrackedBuffer(payload[1:5])
    
        device_number = convertBytes(extended_data.read(ElementSize.DEVICE_NUMBER))
        self.setDeviceNumber(device_number)

        device_type = convertBytes(extended_data.read(ElementSize.DEVICE_TYPE))
        self.setDeviceType(device_type)
        
        transmission_type = convertBytes(extended_data.read(ElementSize.TRANSMISSION_TYPE))
        self.setTransmissionType(transmission_type)


    def decode(self,raw):
        size = Message.decode(self,raw)
        self.update()

        return size

    def encode(self):
        payload = self.getPayload()
        if len(payload) != 13:
            raise MessageError('Length of payload doesn\'t match expected value')

        #payload[1:3] = struct.pack('<H', self.getDeviceNumber())
        #payload[4] = chr(self.getDeviceType())
        #payload[5] = chr(self.getTransmissionType())
        
        raw = struct.pack('BBB',
                          self.getSync(),
                          len(payload),
                          self.getType())
        raw += payload
        raw += chr(self.getChecksum())

        return raw

    def setDeviceNumber(self, device_number):
        payload = self.getPayloadAsList()
        payload[1:3] = struct.pack('<H', device_number)
        self.setPayload(payload,update=False)
        
    def setDeviceType(self, device_type):
        payload = self.getPayloadAsList()
        payload[3] = chr(device_type)
        self.setPayload(payload,update=False)

    def setTransmissionType(self, trans_type):
        payload = self.getPayloadAsList()
        payload[4] = chr(trans_type)
        self.setPayload(payload,update=False)

    def getDeviceNumber(self):
        payload = self.getPayloadAsList()
        return convertBytes(payload[1:3])
        
    def getDeviceType(self):
        payload = self.getPayloadAsList()
        return convertBytes(payload[3])

    def getTransmissionType(self):
        payload = self.getPayloadAsList()
        return convertBytes(payload[4])

    def getRawData(self):
        payload = self.getPayload()[5:]
        return payload

    def setRawData(self,raw):
        payload = self.getPayloadAsList()
        payload[5:] = raw
        self.setPayload(payload)
                    

class ChannelMessage(Message):
    def __init__(self, type_, payload='', number=0x00):
        Message.__init__(self, type_, '\x00' + payload)
        self.setChannelNumber(number)

    def getChannelNumber(self):
        payload = self.getPayloadAsList()
        return ord(payload[0])

    def setChannelNumber(self, number):
        if (number > 0xFF) or (number < 0x00):
            raise MessageError('Could not set channel number ' \
                                   '(out of range).')
        payload = self.getPayloadAsList()
        payload[0] = chr(number)
        self.setPayload(payload)

class LegacyChannelMessage(ChannelMessage, LegacyExtendedMessage):
    pass

class ExtendedChannelMessage(ChannelMessage, ExtendedMessage):
    pass


# Config messages

class ChannelLibConfigMessage(Message):
    def __init__(self, type_=MESSAGE_LIB_CONFIG, mask=ExtendedMessageFlags.ENABLE_RX_TIMESTAMP | ExtendedMessageFlags.ENABLE_CHANNEL_ID):
        #usb2 stick doesn't support rssi | ExtendedMessageFlags.ENABLE_RSSI_OUTPUT 
        # filler byte required
        payload = struct.pack('BB',0,mask)

        Message.__init__(self, type_, payload)
        

class ChannelEnableExtendedMessage(Message):
    def __init__(self, type_=MESSAGE_ENABLE_EXTENDED_MESSAGES, enable=True):

        enable_flag = 1
        if not enable:
            enable_flag = 0
        
        payload = struct.pack('BB',0,enable_flag)

        Message.__init__(self, type_, payload)


class ChannelUnassignMessage(ChannelMessage):
    def __init__(self, number=0x00):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_UNASSIGN,
                         number=number)


class ChannelAssignMessage(ChannelMessage):
    def __init__(self, number=0x00, type_=0x00, network=0x00):
        payload = struct.pack('BB', type_, network)
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_ASSIGN,
                                payload=payload, number=number)

    def getChannelType(self):
        return ord(self.payload[1])

    def setChannelType(self, type_):
        self.payload[1] = chr(type_)

    def getNetworkNumber(self):
        return ord(self.payload[2])

    def setNetworkNumber(self, number):
        self.payload[2] = chr(number)


class ChannelIDMessage(ChannelMessage):
    def __init__(self, number=0x00, device_number=0x0000, device_type=0x00,
                 trans_type=0x00):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_ID,
                                payload='\x00' * 4, number=number)
        self.setDeviceNumber(device_number)
        self.setDeviceType(device_type)
        self.setTransmissionType(trans_type)

    def getDeviceNumber(self):
        return struct.unpack('<H', self.getPayload()[1:3])[0]

    def setDeviceNumber(self, device_number):
        self.payload[1:3] = struct.pack('<H', device_number)

    def getDeviceType(self):
        return ord(self.payload[3])

    def setDeviceType(self, device_type):
        self.payload[3] = chr(device_type)

    def getTransmissionType(self):
        return ord(self.payload[4])

    def setTransmissionType(self, trans_type):
        self.payload[4] = chr(trans_type)


class ChannelPeriodMessage(ChannelMessage):
    def __init__(self, number=0x00, period=8192):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_PERIOD,
                                payload='\x00' * 2, number=number)
        self.setChannelPeriod(period)

    def getChannelPeriod(self):
        return struct.unpack('<H', self.getPayload()[1:3])[0]

    def setChannelPeriod(self, period):
        self.payload[1:3] = struct.pack('<H', period)


class ChannelSearchTimeoutMessage(ChannelMessage):
    def __init__(self, number=0x00, timeout=0xFF):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_SEARCH_TIMEOUT,
                                payload='\x00', number=number)
        self.setTimeout(timeout)

    def getTimeout(self):
        return ord(self.payload[1])

    def setTimeout(self, timeout):
        self.payload[1] = chr(timeout)


class ChannelFrequencyMessage(ChannelMessage):
    def __init__(self, number=0x00, frequency=66):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_FREQUENCY,
                                payload='\x00', number=number)
        self.setFrequency(frequency)

    def getFrequency(self):
        return ord(self.payload[1])

    def setFrequency(self, frequency):
        self.payload[1] = chr(frequency)


class ChannelTXPowerMessage(ChannelMessage):
    def __init__(self, number=0x00, power=0x00):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_TX_POWER,
                                payload='\x00', number=number)

    def getPower(self):
        return ord(self.payload[1])

    def setPower(self, power):
        self.payload[1] = chr(power)


class NetworkKeyMessage(Message):
    def __init__(self, number=0x00, key='\x00' * 8):
        Message.__init__(self, type_=MESSAGE_NETWORK_KEY, payload='\x00' * 9)
        self.setNumber(number)
        self.setKey(key)

    def getNumber(self):
        return ord(self.payload[0])

    def setNumber(self, number):
        self.payload[0] = chr(number)

    def getKey(self):
        return self.getPayload()[1:]

    def setKey(self, key):
        self.payload[1:] = key


class TXPowerMessage(Message):
    def __init__(self, power=0x00):
        Message.__init__(self, type_=MESSAGE_TX_POWER, payload='\x00\x00')
        self.setPower(power)

    def getPower(self):
        return ord(self.payload[1])

    def setPower(self, power):
        self.payload[1] = chr(power)


# Control messages
class SystemResetMessage(Message):
    def __init__(self):
        Message.__init__(self, type_=MESSAGE_SYSTEM_RESET, payload='\x00')


class ChannelOpenMessage(ChannelMessage):
    def __init__(self, number=0x00):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_OPEN,
                                number=number)

class ChannelOpenRxScanMessage(ChannelMessage):
    def __init__(self, number=0x00):
        ChannelMessage.__init__(self, type_=MESSAGE_OPEN_RX_SCAN,
                                number=number)

class ChannelCloseMessage(ChannelMessage):
    def __init__(self, number=0x00):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_CLOSE,
                                number=number)


class ChannelRequestMessage(ChannelMessage):
    def __init__(self, number=0x00, message_id=MESSAGE_CHANNEL_STATUS):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_REQUEST,
                                number=number, payload='\x00')
        self.setMessageID(message_id)

    def getMessageID(self):
        return ord(self.payload[1])

    def setMessageID(self, message_id):
        if (message_id > 0xFF) or (message_id < 0x00):
            raise MessageError('Could not set message ID ' \
                                   '(out of range).')

        self.payload[1] = chr(message_id)


class RequestMessage(ChannelRequestMessage):
    pass


class BurstChannelMixin(object):
    
    CHANNEL_MASK = 0b11111
    SEQUENCE_MASK = 0b111 << 5

    def getChannelNumber(self):
        payload = self.getPayloadAsList()
        return ord(payload[0]) & BurstChannelMixin.CHANNEL_MASK

    def setChannelNumber(self, number):
        if (number > BurstChannelMixin.CHANNEL_MASK) or (number < 0x00):
            raise MessageError('Could not set channel number ' \
                                   '(out of range).')
        payload = self.getPayloadAsList()
        burstSequence = ord(payload[0]) & BurstChannelMixin.SEQUENCE_MASK
        payload[0] = chr(number | burstSequence << 5)
        self.setPayload(payload)
    
    def getSequenceCode(self):
        payload = self.getPayloadAsList()
        return ord(payload[0]) & BurstChannelMixin.SEQUENCE_MASK
    
    def setSequenceCode(self, code):
        if (code > 0b111) or (code < 0x00):
            raise MessageError('Could not set sequence code ' \
                                   '(out of range).')
        payload = self.getPayloadAsList()        
        number = ord(payload[0]) & BurstChannelMixin.CHANNEL_MASK
        payload[0] = chr(number | code << 5)
        self.setPayload(payload)
        

# Data messages
class ChannelBroadcastDataMessage(ChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 8):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_BROADCAST_DATA,
                                payload=data, number=number)


class ChannelAcknowledgedDataMessage(ChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 8):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_ACKNOWLEDGED_DATA,
                                payload=data, number=number)


class ChannelBurstDataMessage(BurstChannelMixin,ChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 8):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_BURST_DATA,
                                payload=data, number=number)

#legacy extended data

class LegacyChannelBroadcastDataMessage(LegacyChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 12):
        LegacyChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_EXTENDED_BROADCAST_DATA,
                                payload=data, number=number)

class LegacyChannelAcknowledgedDataMessage(LegacyChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 12):
        LegacyChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_EXTENDED_ACKNOWLEDGED_DATA,
                                payload=data, number=number)

class LegacyChannelBurstDataMessage(BurstChannelMixin,LegacyChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 12):
        LegacyChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_EXTENDED_BURST_DATA,
                                payload=data, number=number)

#extended data

class ExtendedChannelBroadcastDataMessage(ChannelBroadcastDataMessage,ExtendedChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 10):
        ExtendedChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_BROADCAST_DATA,
                                payload=data, number=number)


class ExtendedChannelAcknowledgedDataMessage(ChannelAcknowledgedDataMessage,ExtendedChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 10):
        ExtendedChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_ACKNOWLEDGED_DATA,
                                payload=data, number=number)


class ExtendedChannelBurstDataMessage(ChannelBurstDataMessage,ExtendedChannelMessage):
    def __init__(self, number=0x00, data='\x00' * 10):
        ExtendedChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_BURST_DATA,
                                payload=data, number=number)


# Channel event messages
class ChannelEventMessage(ChannelMessage):
    def __init__(self, number=0x00, message_id=0x00, message_code=0x00):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_EVENT,
                                number=number, payload='\x00\x00')
        self.setMessageID(message_id)
        self.setMessageCode(message_code)

    def getMessageID(self):
        return ord(self.payload[1])

    def setMessageID(self, message_id):
        if (message_id > 0xFF) or (message_id < 0x00):
            raise MessageError('Could not set message ID ' \
                                   '(out of range).')

        self.payload[1] = chr(message_id)

    def getMessageCode(self):
        return ord(self.payload[2])

    def setMessageCode(self, message_code):
        if (message_code > 0xFF) or (message_code < 0x00):
            raise MessageError('Could not set message code ' \
                                   '(out of range).')

        self.payload[2] = chr(message_code)


# Requested response messages
class ChannelStatusMessage(ChannelMessage):
    def __init__(self, number=0x00, status=0x00):
        ChannelMessage.__init__(self, type_=MESSAGE_CHANNEL_STATUS,
                                payload='\x00', number=number)
        self.setStatus(status)

    def getStatus(self):
        return ord(self.payload[1])

    def setStatus(self, status):
        if (status > 0xFF) or (status < 0x00):
            raise MessageError('Could not set channel status ' \
                                   '(out of range).')

        self.payload[1] = chr(status)

#class ChannelIDMessage(ChannelMessage):


class VersionMessage(Message):
    def __init__(self, version='\x00' * 9):
        Message.__init__(self, type_=MESSAGE_VERSION, payload='\x00' * 9)
        self.setVersion(version)

    def getVersion(self):
        return self.getPayload()

    def setVersion(self, version):
        if (len(version) != 9):
            raise MessageError('Could not set ANT version ' \
                               '(expected 9 bytes).')

        self.setPayload(version)


class CapabilitiesMessage(Message):
    def __init__(self, max_channels=0x00, max_nets=0x00, std_opts=0x00,
                 adv_opts=0x00, adv_opts2=0x00):
        Message.__init__(self, type_=MESSAGE_CAPABILITIES, payload='\x00' * 4)
        self.setMaxChannels(max_channels)
        self.setMaxNetworks(max_nets)
        self.setStdOptions(std_opts)
        self.setAdvOptions(adv_opts)
        if adv_opts2 is not None:
            self.setAdvOptions2(adv_opts2)

    def getMaxChannels(self):
        return ord(self.payload[0])

    def getMaxNetworks(self):
        return ord(self.payload[1])

    def getStdOptions(self):
        return ord(self.payload[2])

    def getAdvOptions(self):
        return ord(self.payload[3])

    def getAdvOptions2(self):
        return ord(self.payload[4]) if len(self.payload) == 5 else 0x00

    def setMaxChannels(self, num):
        if (num > 0xFF) or (num < 0x00):
            raise MessageError('Could not set max channels ' \
                                   '(out of range).')

        self.payload[0] = chr(num)

    def setMaxNetworks(self, num):
        if (num > 0xFF) or (num < 0x00):
            raise MessageError('Could not set max networks ' \
                                   '(out of range).')

        self.payload[1] = chr(num)

    def setStdOptions(self, num):
        if (num > 0xFF) or (num < 0x00):
            raise MessageError('Could not set std options ' \
                                   '(out of range).')

        self.payload[2] = chr(num)

    def setAdvOptions(self, num):
        if (num > 0xFF) or (num < 0x00):
            raise MessageError('Could not set adv options ' \
                                   '(out of range).')

        self.payload[3] = chr(num)

    def setAdvOptions2(self, num):
        if (num > 0xFF) or (num < 0x00):
            raise MessageError('Could not set adv options 2 ' \
                                   '(out of range).')

        if len(self.payload) == 4:
            self.payload.append('\x00')
        self.payload[4] = chr(num)


class SerialNumberMessage(Message):
    def __init__(self, serial='\x00' * 4):
        Message.__init__(self, type_=MESSAGE_SERIAL_NUMBER)
        self.setSerialNumber(serial)

    def getSerialNumber(self):
        return self.getPayload()

    def setSerialNumber(self, serial):
        if (len(serial) != 4):
            raise MessageError('Could not set serial number ' \
                               '(expected 4 bytes).')

        self.setPayload(serial)


# notification messages 

class StartupMessage(Message):
    def __init__(self):
        Message.__init__(self, type_=MESSAGE_STARTUP, payload = '\x00'  )

    def isPowerOnReset(self):
        if ord(self.getPayload()[0]) == 0x00:
            return True
        return False

    def isHardwareLineReset(self):
        if ord(self.getPayload()[0]) & (1 << 0) != 0:
            return True
        return False    

    def isWatchDogReset(self):
        if ord(self.getPayload()[0]) & (1 << 1) != 0:
            return True
        return False

    def isCommandReset(self):
        if ord(self.getPayload()[0]) & (1 << 5) != 0:
            return True
        return False

    def isSynchronousReset(self):
        if ord(self.getPayload()[0]) & (1 << 6) != 0:
            return True
        return False

    def isSuspendReset(self):
        if ord(self.getPayload()[0]) & (1 << 7) != 0:
            return True
        return False        

# utilities for burst messages

class BurstSequence(object):

    INIT_VAL = 0b00
    MAX_VAL = 0b011
    WRAP_VAL = 0b001
    FINISH_VAL = 0b110
    MAX_CHANNEL = 0b11111

    
    def __init__(self):
        self.current_val = BurstSequence.INIT_VAL    
    
    def next(self):
        rtn = self.current_val
        if self.current_val == BurstSequence.MAX_VAL:
            self.current_val = BurstSequence.INIT_VAL
        elif self.current_val > BurstSequence.FINISH_VAL:
            raise ValueError('Value out of bounds. Who has been messing with my internals?')
        elif self.current_val == BurstSequence.FINISH_VAL:
            pass
        else:
            self.current_val += 1
        return rtn
    
    def finish(self):
        self.current_val = BurstSequence.FINISH_VAL
    
    def reset(self):
        self.current_val = INIT_VAL

    def combine(self,channel_no):
        if channel_no > BurstSequence.MAX_CHANNEL:
            raise ValueError('Channel number limited to 5 bits (value too large)')
        elif channel_no < 0:
            raise ValueError('Channel number cannot be subzero (value too small)')    
        return channel_no | (self.next() << 5)


    
