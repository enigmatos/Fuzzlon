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

import os
import cfg
import random
import construct as ct
import crcmod.predefined
from ct_dot154 import fcf_t, frame_type_t, addressing_mode_t, mpdu_t,\
        is_address_present, frame_t

crc_kermit = crcmod.predefined.mkPredefinedCrcFun("kermit")


def fix_fcf(fcf):

    """
1. The Frame Type subfield shall not contain a reserved frame type.
    """
    fcf.type = int(fcf.type) % (1 + max(frame_type_t.ksymapping.keys()))

    """
2. The Frame Version subfield shall not contain a reserved value.
    """
    fcf.version %= 2
    # for some reason version 1 is not valid
    fcf.version = 0

    """
5. If the frame type indicates that the frame is a beacon frame, the source PAN
identifier shall match macPANId unless macPANId is equal to 0xFFFF, in which
case the beacon frame shall be accepted regardless of the source PAN
identifier.
6. If only source addressing fields are included in a data or MAC command
frame, the frame shall be accepted only if the device is the PAN coordinator
and the source PAN identifier matches macPANId.
    """
    # beacon must have a source if the device isn't pan coordinator
    if int(fcf.type) == int(frame_type_t.BEACON) and \
            not cfg.IS_PAN_COORDINATOR:
        if not is_address_present(fcf.src_addressing_mode):
            fcf.src_addressing_mode = int(addressing_mode_t.SHORT)
        # this is understood by trial and error :/
        # the atmel doesn't like it when I have destination address in a beacon
        fcf.dst_addressing_mode = int(addressing_mode_t.NOT_PRESENT)
    elif not is_address_present(fcf.dst_addressing_mode):
        fcf.dst_addressing_mode = int(addressing_mode_t.SHORT)

    """
7. The frame type shall indicate that the frame is not an acknowledgment (ACK)
frame.
    """
    if int(fcf.type) == int(frame_type_t.ACK):
        fcf.type = frame_type_t.DATA

    """
8. At least one address field must be present.
    """
    if not is_address_present(fcf.dst_addressing_mode) and\
            not is_address_present(fcf.src_addressing_mode):
        fcf.dst_addressing_mode = int(addressing_mode_t.SHORT)

    # YL: let's not have reserved addresses
    if int(fcf.dst_addressing_mode) == int(addressing_mode_t.RESERVED):
        fcf.dst_addressing_mode = int(addressing_mode_t.NOT_PRESENT)
    if int(fcf.src_addressing_mode) == int(addressing_mode_t.RESERVED):
        fcf.src_addressing_mode = int(addressing_mode_t.NOT_PRESENT)

    # YL: I force destination addr to be broadcast:
    if int(fcf.dst_addressing_mode) == int(addressing_mode_t.LONG):
        fcf.dst_addressing_mode = int(addressing_mode_t.SHORT)

    return fcf


def fix_mpdu(mpdu):
    fcf = fix_fcf(fcf_t.parse(mpdu[:fcf_t.sizeof()]))
    mpdu = mpdu_t.parse(fcf_t.build(fcf) + mpdu[fcf_t.sizeof():])

    try:
        """
3. If a destination PAN identifier is included in the frame, it shall match
macPANId or shall be the broadcast PAN identifier (0xFFFF).
        """
        mpdu.mac.dst_addr.pan_id = cfg.PAN_ID
        """
4. If a short destination address is included in the frame, it shall match
either macShortAddress or the broadcast address (0xFFFF). Otherwise, if an
extended destination address is included in the frame, it shall match
aExtendedAddress.
        """
        mpdu.mac.dst_addr.addr = 0xffff
    except:
        pass

    try:
        """
5. If the frame type indicates that the frame is a beacon frame, the source PAN
identifier shall match macPANId unless macPANId is equal to 0xFFFF, in which
case the beacon frame shall be accepted regardless of the source PAN
identifier.
6. If only source addressing fields are included in a data or MAC command
frame, the frame shall be accepted only if the device is the PAN coordinator
and the source PAN identifier matches macPANId.
        """
        mpdu.mac.src_addr.pan_id = cfg.PAN_ID
    except:
        pass

    """compute checksum"""
    buf = mpdu_t.build(mpdu)
    mpdu.fcs = crc_kermit(buf[:-2])

    return mpdu_t.build(mpdu)


def gen_packet():
    while True:
        try:
            raw = os.urandom(random.randint(6, 127))
            mpdu = fix_mpdu(raw)
            frame = ct.Container(
                    phr=ct.Container(
                        reserved=random.randint(0, 1),
                        size=len(mpdu),
                    ),
                    mpdu=mpdu_t.parse(mpdu),
                )
            built_frame = frame_t.build(frame)
            return built_frame

        except ct.StreamError:
            continue
        except ct.ExplicitError:
            continue
