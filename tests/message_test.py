from ant.core.event import *
from ant.core.constants import *
from ant.core.message import *

import unittest
import struct
from anttestutils import *


class ExtendedMessageTest(unittest.TestCase):

                         
    def setUp(self):
        self.buffer1_data = [2,3,0,0,0,0,0,0,0,4,5]     
        
        self.combind_buffer1 = struct.pack(*get_pack_args(self.buffer1_data))

    # tests whether sync byte of next message is sucessfully found
    def test_timestamp(self):
        timestamp = 1234
        packed = struct.pack('<H', timestamp)
        unpacked = struct.unpack('BB',packed)
        buffer_data = [2,3,4,5,6,7,8,9,0x20,unpacked[0],unpacked[1]] 
        buffer_ = struct.pack(*get_pack_args(buffer_data))
        msg = ExtendedMessage()
        msg.update()
        msg2 = Message()
        msg2.decode(buffer_)
        msg.decode(buffer_)
        self.assertEqual(msg.payload,msg2.payload)
        sync = msg.getSync()
        self.assertEqual(sync, MESSAGE_TX_SYNC )
        self.assertEqual(timestamp,msg.getTimestamp())

    def test_all_extensions(self):
        timestamp = 1234
        packed = struct.pack('<H', timestamp)
        timestamp_bytes = struct.unpack('BB',packed)

        device_number = 4567
        packed = struct.pack('<H', device_number)
        number = struct.unpack('BB',packed)

        device_type = 18
        transmission_type = 28

        rssi_type = 71
        rssi_value = 167
        rssi_threshold = 179
        

        buffer_data = [2,3,4,5,6,7,8,9,0xE0,number[0],number[1],device_type,transmission_type,rssi_type,rssi_value,rssi_threshold,timestamp_bytes[0],timestamp_bytes[1]]
        buffer_ = struct.pack(*get_pack_args(buffer_data))

        buffer_ = struct.pack(*get_pack_args(buffer_data))
        msg = ExtendedMessage()
        msg.decode(buffer_)
        
        self.assertEqual(timestamp,msg.getTimestamp())
        self.assertEqual(device_number,msg.getDeviceNumber())
        self.assertEqual(device_type,msg.getDeviceType())
        self.assertEqual(transmission_type,msg.getTransmissionType())
        self.assertEqual(rssi_type,msg.getRssiType())
        self.assertEqual(rssi_value,msg.getRssiValue())
        self.assertEqual(rssi_threshold,msg.getRssiThreshold())

        #reenocde test
        
        msg2 = ExtendedMessage()
        encode = msg.encode()
        
        self.assertRaises(MessageError,msg2.decode,encode)

        msg2 = Message()
        msg2.decode(encode)
    

        #print msg2.payload

        
class LegacyMessageTest(unittest.TestCase): 

    def test_raw_data(self):
        msg = LegacyChannelBroadcastDataMessage()
        pack = struct.pack('B'* 8, 1,2,3,4,5,6,7,8)
        msg.setRawData(pack)
        print "====================="
        print struct.unpack('B'*8,msg.getRawData())
         


if __name__ == '__main__':
    unittest.main()     
        
