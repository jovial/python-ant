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

#
# Beware s/he who enters: uncommented, non unit-tested,
# don't-fix-it-if-it-ain't-broken kind of threaded code ahead.
#

MAX_ACK_QUEUE = 25
MAX_MSG_QUEUE = 25

import thread
import time

from ant.core.constants import *
from ant.core.message import Message, ChannelEventMessage
from ant.core.exceptions import MessageError
import struct


def ProcessBuffer(buffer_):
    messages = []
    
    #print 'buffer'

    #print buffer_

    while True:
        if len(buffer_) == 0:
            break
        hf = Message()
        try:
            msg = hf.getHandler(buffer_)
            buffer_ = buffer_[len(msg.getPayload()) + 4:]
            #print msg
            messages.append(msg)
        except MessageError, e:
            print e
            #if e.internal == "CHECKSUM":
            #try:
            #    msg_length = ord(buffer_[1])
                #extended msgs are upto 23 bytes ?
            #    if msg_length > 0 and msg_length <= MAX_MESSAGE_LENGTH:
            #        buffer_ = buffer_[msg_length + 4:]
            #except:
            # try and find next message by locating sync byte -msg length corrupted?
            next_message_start = len(buffer_)
            count = 0
            for index,byte in enumerate(buffer_):
                byte_value = ord(byte)
                if byte_value == MESSAGE_TX_SYNC or byte_value == MESSAGE_TX_SYNC_LSB:
                    count += 1
                    # look for next sync byte
                    if count > 1:
                        next_message_start = index
                        break                    
                
            buffer_ = buffer_[next_message_start:]

            #data = struct.unpack('B' * len(buffer_), buffer_)
            #print data
            #else:
            #print len(buffer_)
            #    break

    return (buffer_, messages,)


def EventPump(evm):
    evm.pump_lock.acquire()
    evm.pump = True
    evm.pump_lock.release()
    go = True
    buffer_ = ''
    while go:
        evm.running_lock.acquire()
        if not evm.running:
            go = False
        evm.running_lock.release()

        buffer_ += evm.driver.read(20)
        if len(buffer_) == 0:
            continue
        buffer_, messages = ProcessBuffer(buffer_)

        evm.callbacks_lock.acquire()
        for message in messages:
            #print message
            for callback in evm.callbacks:
                try:
                    callback.process(message)
                except Exception, e:
                    print e
                    pass

        evm.callbacks_lock.release()

        time.sleep(0.002)

    evm.pump_lock.acquire()
    evm.pump = False
    evm.pump_lock.release()


class EventCallback(object):
    def process(self, msg):
        pass


class AckCallback(EventCallback):
    def __init__(self, evm):
        self.evm = evm

    def process(self, msg):
        if isinstance(msg, ChannelEventMessage):
            self.evm.ack_lock.acquire()
            self.evm.ack.append(msg)
            if len(self.evm.ack) > MAX_ACK_QUEUE:
                self.evm.ack = self.evm.ack[-MAX_ACK_QUEUE:]
            self.evm.ack_lock.release()


class MsgCallback(EventCallback):
    def __init__(self, evm):
        self.evm = evm

    def process(self, msg):
        self.evm.msg_lock.acquire()
        self.evm.msg.append(msg)
        if len(self.evm.msg) > MAX_MSG_QUEUE:
            self.evm.msg = self.evm.msg[-MAX_MSG_QUEUE:]
        self.evm.msg_lock.release()


class EventMachine(object):
    callbacks_lock = thread.allocate_lock()
    running_lock = thread.allocate_lock()
    pump_lock = thread.allocate_lock()
    ack_lock = thread.allocate_lock()
    msg_lock = thread.allocate_lock()

    def __init__(self, driver):
        self.driver = driver
        self.callbacks = []
        self.running = False
        self.pump = False
        self.ack = []
        self.msg = []
        self.registerCallback(AckCallback(self))
        self.registerCallback(MsgCallback(self))

    def registerCallback(self, callback):
        self.callbacks_lock.acquire()
        if callback not in self.callbacks:
            self.callbacks.append(callback)
        self.callbacks_lock.release()

    def removeCallback(self, callback):
        self.callbacks_lock.acquire()
        if callback in self.callbacks:
            self.callbacks.remove(callback)
        self.callbacks_lock.release()

    def waitForAck(self, msg):
        while True:
            self.ack_lock.acquire()
            for emsg in self.ack:
                if msg.getType() != emsg.getMessageID():
                    continue
                self.ack.remove(emsg)
                self.ack_lock.release()
                return emsg.getMessageCode()
            self.ack_lock.release()
            time.sleep(0.002)

    def waitForMessage(self, class_):
        while True:
            self.msg_lock.acquire()
            for emsg in self.msg:
                if not isinstance(emsg, class_):
                    continue
                self.msg.remove(emsg)
                self.msg_lock.release()
                return emsg
            self.msg_lock.release()
            time.sleep(0.002)

    def start(self, driver=None):
        self.running_lock.acquire()

        if self.running:
            self.running_lock.release()
            return
        self.running = True
        if driver is not None:
            self.driver = driver

        thread.start_new_thread(EventPump, (self,))
        while True:
            self.pump_lock.acquire()
            if self.pump:
                self.pump_lock.release()
                break
            self.pump_lock.release()
            time.sleep(0.001)

        self.running_lock.release()

    def stop(self):
        self.running_lock.acquire()

        if not self.running:
            self.running_lock.release()
            return
        self.running = False
        self.running_lock.release()

        while True:
            self.pump_lock.acquire()
            if not self.pump:
                self.pump_lock.release()
                break
            self.pump_lock.release()
            time.sleep(0.001)
