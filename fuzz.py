#!/usr/bin/env python2

# MIT License
#
# Copyright (c) 2019 enigmatos
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import elementals
from killerbee import GoodFETCCSPI
import itertools

import cfg
import ct_dot154
import gen_dot154

pmp = elementals.Prompter()
# KillerBee auto detection doesn't work well at all
# better to work with the GoodFET directly
client = GoodFETCCSPI.GoodFETCCSPI()

pmp.info("Connecting to ApiMote...")
client.serInit(cfg.SERIAL_PATH)
pmp.info("Setting up the device")
client.setup()
client.RF_setchan(cfg.CHANNEL)
client.RF_autocrc(1)

fuzzing_status = elementals.StatusBar("Fuzzing", 0)
fuzzing_status.start()
for i in itertools.count():
    pkt = gen_dot154.gen_packet()
    client.RF_txpacket(pkt)
    fuzzing_status.update(
            status="{:d} {}".format(i, str(ct_dot154.frame_t.parse(pkt))))
