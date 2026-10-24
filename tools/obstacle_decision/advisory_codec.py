"""PROPOSED TerrainAdvisory codec using link_proto framing; informational only."""
import struct
from tools.link_proto.py import link_proto as lp

TYPE=4
PAYLOAD_SIZE=struct.calcsize('<QQBBffffff')

def encode(session, sequence, *, pi_monotonic_ns, frame_stamp_ns, advisory,
           confidence, distance_m, height_m, width_m, plane_valid,
           plane_pitch_rad, plane_height_m):
    vals=(confidence,distance_m,height_m,width_m,plane_pitch_rad,plane_height_m)
    if not all(__import__('math').isfinite(v) for v in vals): raise ValueError('fields must be finite')
    payload=struct.pack('<QQBBffffff',pi_monotonic_ns,frame_stamp_ns,int(advisory),int(bool(plane_valid)),*vals)
    return lp._wire(TYPE,session,sequence,payload)

def decode(packet):
    if not packet.endswith(b'\0'): raise ValueError('missing delimiter')
    raw=_cobs_decode(packet[:-1])
    if len(raw)<20: raise ValueError('short record')
    version,kind,n,session,seq=struct.unpack_from('<BBHQI',raw)
    if version!=lp.VERSION or kind!=TYPE or n!=PAYLOAD_SIZE or len(raw)!=20+n: raise ValueError('header/length')
    if struct.unpack_from('<I',raw,16+n)[0]!=lp.crc32c(raw[:16+n]): raise ValueError('CRC')
    stamp,frame,adv,valid,conf,d,h,w,pitch,ph=struct.unpack_from('<QQBBffffff',raw,16)
    return dict(session=session,sequence=seq,pi_monotonic_ns=stamp,frame_stamp_ns=frame,advisory=adv,plane_valid=bool(valid),confidence=conf,distance_m=d,height_m=h,width_m=w,plane_pitch_rad=pitch,plane_height_m=ph)

def _cobs_decode(data):
    out=bytearray(); i=0
    while i<len(data):
        code=data[i]; i+=1
        if code==0 or i+code-1>len(data): raise ValueError('invalid COBS')
        out.extend(data[i:i+code-1]); i+=code-1
        if code<255 and i<len(data): out.append(0)
    return bytes(out)
