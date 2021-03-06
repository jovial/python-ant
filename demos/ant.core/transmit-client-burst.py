"""
Extending on demo-03, implements an event callback we can use to process the
incoming data.

"""

import sys
import time
import struct
import array

from ant.core import driver
from ant.core import node
from ant.core import event
from ant.core import message
from ant.core.constants import *
import traceback

from config import *

import Pyro4
import atexit

NETKEY = '\xB9\xA5\x21\xFB\xBD\x72\xC3\x45'

#channel = None


def exit():
    channel.close()
    channel.unassign()


# A run-the-mill event listener
class HRMListener(event.EventCallback):
    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print 'Heart Rate:', ord(msg.payload[-1])

# Initialize
#stick = driver.USB2Driver(SERIAL, log=LOG)
#antnode = node.Node(stick)
#antnode.start()

#with Pyro4.core.Proxy("PYRONAME:pyant.server") as antnode:
antnode = Pyro4.core.Proxy("PYRONAME:pyant.server")
# Setup channel
key = node.NetworkKey('N:ANT+', NETKEY)
antnode.setNetworkKey(0, key)
print 1
channel = antnode.getFreeChannel()
print 2
channel.name = 'C:HRM'
channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_TRANSMIT)
channel.setID(0x78,0x1234, 1)
channel.setSearchTimeout(50)
channel.setPeriod(8070)
channel.setFrequency(57)
print 3
channel.open()
print 4
atexit.register(exit)

# Setup callback
# Note: We could also register an event listener for non-channel events by
# calling registerEventListener() on antnode rather than channel.
#channel.registerCallback(HRMListener())

# Wait
#print "Listening for HR monitor events (120 seconds)..."
#time.sleep(120)

hr = 50
hr_change = 2
hr_seq = 0

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

    
try:
    while True:
        msg = message.ChannelBurstDataMessage()
        payload = msg.getPayload()
        channel_no = 0
        #seq = 0b110
        #first = channel_no | (seq << 5)
        b = BurstSequence()
        for i in range(0,10):

            hr_seq = hr_seq + 1;
            if (hr_seq >= 256):
                hr_seq = 0    
            hr = hr + hr_change
            if hr > 200 or hr < 40:
                hr_change = -hr_change

            pack = struct.pack('B' * 9,b.combine(channel_no),1,0,3,4,5,6,hr_seq,hr)
            payload = pack
            msg.setPayload(payload)
            #print 'Heart Rate:', ord(msg.payload[-1])
            driver = antnode.getDriver()
            driver.write(msg.encode())
        b.finish()
        pack = struct.pack('B' * 9,b.combine(channel_no),1,0,3,4,5,6,hr_seq,hr)
        payload = pack
        msg.setPayload(payload)
        #print 'Heart Rate:', ord(msg.payload[-1])
        driver = antnode.getDriver()
        driver.write(msg.encode())  
        
        #print first
        #print type(payload)
        #print ord(payload[0])
        #bytes = bytearray(payload)
        #bytes[-1] = chr(hr)
        #bytes[-2] = chr(hr_seq)
        #bytes[0] = chr(channel.number)
        #print chr(channel.number)
        #test = struct.unpack('BBBBBBBB',payload)
        #test[-1] = chr(hr)
        #test[-2] = chr(hr_seq)
        #test[0] = chr(channel.number)

        time.sleep(0.1)
except Exception, e:
    print e
    tb = traceback.format_exc()
    print tb
    #pass

# Shutdown
#channel.close()
#channel.unassign()
#antnode.stop()
