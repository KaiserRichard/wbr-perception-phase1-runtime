#!/usr/bin/python3
"""Grant video access only to SDK controls under this D435i's IIO/custom HID nodes.

Default mode is a read-only preview. udev invokes --apply as root on attachment.
No sensor values are written, no directories are recursively chmod'ed, and no
other camera serial is eligible. Source: librealsense v2.58.4 backend-hid.cpp.
"""
import argparse
import grp
import os
from pathlib import Path


def controls(sensor):
    sensor = sensor.resolve(strict=True)
    if not sensor.is_relative_to('/sys/devices'):
        raise ValueError('Expected a device below /sys/devices')
    for parent in sensor.parents:
        if (parent / 'idVendor').is_file():
            identity = [(parent / f).read_text().strip()
                        for f in ('idVendor', 'idProduct', 'serial')]
            if identity != ['8086', '0b3a', '251843061466']:
                raise ValueError('USB identity does not match this experiment camera')
            break
    else:
        raise ValueError('No USB parent found')
    if sensor.name.startswith('iio:device'):
        if (sensor / 'name').read_text().strip() not in ('gyro_3d', 'accel_3d'):
            raise ValueError('Unexpected IIO sensor')
        patterns = ('scan_elements/*_en', 'buffer/enable', 'buffer/length',
                    'trigger/current_trigger', 'in_*_sampling_frequency', 'in_*_hysteresis')
    elif (sensor.name.startswith('HID-SENSOR-2000e1.') and
          (sensor / 'driver').resolve(strict=True).name == 'hid_sensor_custom'):
        # Required by native SDK shutdown; observed permission denial in smoke-01.
        patterns = ('enable_sensor',)
    else:
        raise ValueError('Unexpected sensor')
    paths = sorted({p.resolve(strict=True) for pattern in patterns for p in sensor.glob(pattern)})
    for path in paths:
        if not path.is_relative_to(sensor) or not path.is_file():
            raise ValueError('Control escaped the selected IIO device')
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sensor', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    paths = controls(args.sensor)
    if args.apply and os.geteuid() != 0:
        parser.error('--apply requires root')
    gid = grp.getgrnam('video').gr_gid
    for path in paths:
        if args.apply:
            os.chown(path, 0, gid)
            os.chmod(path, 0o660)
        print(f'{"applied" if args.apply else "preview"}: root:video 0660 {path}')


if __name__ == '__main__':
    main()
