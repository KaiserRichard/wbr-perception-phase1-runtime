"""CANDIDATE / PROPOSED Pi encoder; firmware owner review required.

No transport, clock mapping, enable action, or live estimate generation.
Inputs must come from a reviewed snapshot/mapping service; see ../SPEC.md.
"""
import math
import struct

VERSION = 1
HEALTH, BODY_REF, MCU_STATUS = 1, 2, 3
MAX_RAW = 192


def crc32c(data):
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82F63B78 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


def cobs_encode(data):
    out = bytearray([0])
    code_index, code = 0, 1
    for byte in data:
        if byte == 0:
            out[code_index] = code
            code_index = len(out)
            out.append(0)
            code = 1
        else:
            out.append(byte)
            code += 1
            if code == 255:
                out[code_index] = code
                code_index = len(out)
                out.append(0)
                code = 1
    out[code_index] = code
    return bytes(out)


def _wire(kind, session, seq, payload):
    raw = struct.pack('<BBHQI', VERSION, kind, len(payload), session, seq) + payload
    raw += struct.pack('<I', crc32c(raw))
    if len(raw) > MAX_RAW:
        raise ValueError('record exceeds PROPOSED cap')
    return cobs_encode(raw) + b'\x00'


def perception_health(session, seq, *, estimate_seq, map_epoch,
                      transform_revision, mapping_revision, reset_counter,
                      tracking, estimator_id, source_domain, flags, frame_id,
                      child_frame_id, quality, reasons, source_ns,
                      mapped_mcu_ns, pi_send_ns, age_at_send_ns, uncertainty_ns):
    if not -1 <= quality <= 100:
        raise ValueError('quality must be -1, 0, or 1..100')
    payload = struct.pack('<IIIIBBBBHHHb x IQQQQI12x',
                          estimate_seq, map_epoch, transform_revision,
                          mapping_revision, reset_counter, tracking,
                          estimator_id, source_domain, flags, frame_id,
                          child_frame_id, quality, reasons, source_ns,
                          mapped_mcu_ns, pi_send_ns, age_at_send_ns, uncertainty_ns)
    return _wire(HEALTH, session, seq, payload)


def body_velocity_ref(session, seq, *, estimate_seq, map_epoch,
                      mapping_revision, frame_id, reset_counter,
                      pi_creation_ns, mapped_mcu_creation_ns, lease_us,
                      forward_m_s, yaw_rad_s):
    if not all(math.isfinite(v) for v in (forward_m_s, yaw_rad_s)):
        raise ValueError('nonfinite reference')
    payload = struct.pack('<IIIHBxQQIff', estimate_seq, map_epoch,
                          mapping_revision, frame_id, reset_counter,
                          pi_creation_ns, mapped_mcu_creation_ns, lease_us,
                          forward_m_s, yaw_rad_s)
    return _wire(BODY_REF, session, seq, payload)


def mcu_status(session, seq, *, sample_mcu_ns, last_health_seq,
               last_estimate_seq, last_ref_seq, faults, action_mcu_ns,
               battery_mv, fsm, armed, operator_enable, state, reason,
               battery_valid):
    payload = struct.pack('<QIIIIQHBBBBBB4x', sample_mcu_ns,
                          last_health_seq, last_estimate_seq, last_ref_seq,
                          faults, action_mcu_ns, battery_mv, fsm, armed,
                          operator_enable, state, reason, battery_valid)
    return _wire(MCU_STATUS, session, seq, payload)
