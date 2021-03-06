"""
Extending on demo-03, implements an event callback we can use to process the
incoming data.

"""

import sys
import time
import struct

from ant.core import driver
from ant.core import node
from ant.core import event
from ant.core import message
from ant.core.constants import *

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
        #print msg
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print 'Heart Rate:', ord(msg.payload[8])
            #msg = message.ChannelRequestMessage(message_id=MESSAGE_CHANNEL_ID)

            #channel.node.driver.write(msg.encode()) 
            #try:
            #    print len(msg.payload)
            #    print type(msg.payload)
            #    test = struct.unpack('BBBBBBBBB',msg.payload)
           # except Exception, e:
            #    print e
            #print test
            #print 'hi'
            #for i in range(0,8):
            #    print ord(msg.payload[i])

# Initialize
#stick = driver.USB2Driver(SERIAL, log=LOG, debug=DEBUG)
##antnode = node.Node(stick)
#antnode.start()

atexit.register(exit)

daemon = Pyro4.core.Daemon()

hrm = HRMListener()
daemon.register(hrm)

with Pyro4.core.Proxy("PYRONAME:pyant.server") as antnode:
    #print type(antnode.getChannels())
    # Setup channel
    key = node.NetworkKey('N:ANT+', NETKEY)
    #daemon.register(key)
    antnode.setNetworkKey(0, key)
    channel = antnode.getFreeChannel()
    channel.name = 'C:HRM'
    channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
    channel.setID(120, 0, 0)
    channel.setSearchTimeout(TIMEOUT_NEVER)
    channel.setPeriod(8070)
    channel.setFrequency(57)
    msg = message.ChannelEnableExtendedMessage(enable=True)
    driver = antnode.getDriver()
    driver.write(msg.encode())  
    channel.open()
    channel.registerCallback(hrm)
    print 'after call'

daemon.requestLoop()


# Setup callback
# Note: We could also register an event listener for non-channel events by
# calling registerEventListener() on antnode rather than channel.
#channel.registerCallback(HRMListener())

# Wait
#print "Listening for HR monitor events (120 seconds)..."
#time.sleep(240)

# Shutdown
#channel.close()
#channel.unassign()
#antnode.stop()
