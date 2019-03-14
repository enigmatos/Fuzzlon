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

import construct as ct


def LEBitsInteger(n):
    return ct.ByteSwapped(ct.BitsInteger(n))


frame_type_t = ct.Enum(
    LEBitsInteger(3),
    BEACON=0, DATA=1, ACK=2, MAC=3)

addressing_mode_t = ct.Enum(
    LEBitsInteger(2),
    NOT_PRESENT=0, RESERVED=1, SHORT=2, LONG=3)

long_addr_t = ct.Struct("pan_id"/ct.Hex(ct.Int16ul), "addr"/ct.Hex(ct.Int64ul))
short_addr_t = ct.Struct("pan_id"/ct.Hex(ct.Int16ul),
                         "addr"/ct.Hex(ct.Int16ul))


def is_address_present(addr):
    return (int(addr) == int(addressing_mode_t.SHORT) or
            int(addr) == int(addressing_mode_t.LONG))


fcf_t = ct.BitsSwapped(ct.BitStruct(
    "type"/frame_type_t,
    "sec"/ct.Flag,
    "frame_pending"/ct.Flag,
    "ack_requested"/ct.Flag,
    "pan_id_comp"/ct.Flag,
    "reserved"/LEBitsInteger(3),
    "dst_addressing_mode"/addressing_mode_t,
    "version"/LEBitsInteger(2),
    "src_addressing_mode"/addressing_mode_t,
))

mac_header_t = ct.Struct(
    "fcf"/fcf_t,
    "seqnum"/ct.Hex(ct.Int8ul),
    "dst_addr"/ct.Switch(lambda ctx: int(ctx.fcf.dst_addressing_mode), {
        int(addressing_mode_t.SHORT): short_addr_t,
        int(addressing_mode_t.LONG): long_addr_t,
    }),
    "src_addr"/ct.If(
        lambda ctx: is_address_present(ctx.fcf.src_addressing_mode),
        ct.Struct(
            "pan_id"/ct.IfThenElse(
                lambda ctx: ctx._.fcf.pan_id_comp and
                is_address_present(ctx._.fcf.dst_addressing_mode),
                ct.Computed(ct.this._.dst_addr.pan_id),
                ct.Hex(ct.Int16ul)
            ),
            "addr"/ct.Switch(lambda ctx: int(ctx._.fcf.src_addressing_mode), {
                int(addressing_mode_t.SHORT): ct.Hex(ct.Int16ul),
                int(addressing_mode_t.LONG): ct.Hex(ct.Int64ul)
            })
        )
    ),
)

mpdu_t = ct.Struct(
    "mac"/mac_header_t,
    "pdu_offset"/ct.Tell,
    "pdu"/ct.ExprAdapter(ct.HexDump(ct.GreedyBytes),
                         ct.obj_[:-2], ct.obj_+"AA"),
    ct.Seek(-2, ct.io.SEEK_CUR),
    "fcs_offset"/ct.Tell,
    ct.If(ct.this.pdu_offset > ct.this.fcs_offset, ct.Error),
    "fcs"/ct.Hex(ct.Int16ul)
)

phr_t = ct.BitStruct(
    "reserved"/ct.Bit,
    "size"/ct.BitsInteger(7)
)

frame_t = ct.Struct(
    "phr"/phr_t,
    "mpdu"/mpdu_t
    # warn if phr.size != len(mpdu)
)
