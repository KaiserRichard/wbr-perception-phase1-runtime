"""Synthetic policy checks; no physical storage qualification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bounded_microsd import validate_probe, check_binding


class BoundedMicroSDTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bag = Path(self.temp.name).resolve()/'bag'
        self.mount = {'target':'/','source':'/dev/mmcblk0p2','fstype':'ext4','options':'rw'}
        self.probe = {'stage':'BOUNDED_MICROSD_PROBE','verdict':'PASS','failures':[],
            'bytes':128*1024**2,'probe_removed':True,'write_sha256':'a'*64,'readback_sha256':'a'*64,
            'overall_MB_s':20,'worst_batch_MB_s':16,'power_before':'throttled=0x0','power_after':'throttled=0x0',
            'mount':json.dumps({'filesystems':[self.mount]}),'device_st_dev':self.bag.parent.stat().st_dev,
            'utc_end':'2026-09-13T00:00:00+00:00'}

    def valid(self, data=None, seconds=20):
        with patch('bounded_microsd.check_binding'):
            return validate_probe(data or self.probe,self.bag,seconds)

    def test_explicit_limited_scope(self):
        self.assertEqual(self.valid()['scope'],'BOUNDED_MICROSD_DIAGNOSTIC_ONLY')
        with self.assertRaises(RuntimeError): self.valid(seconds=61)

    def test_checksum_speed_power_and_scope_rejections(self):
        for key,value in [('readback_sha256','b'*64),('worst_batch_MB_s',9),('power_after','throttled=0x50000'),('stage','STORAGE_QUALIFY')]:
            with self.subTest(key=key):
                data=copy.deepcopy(self.probe); data[key]=value
                with self.assertRaises(RuntimeError): self.valid(data)

    def test_mount_change_rejected(self):
        binding=self.valid()
        changed=dict(self.mount,source='/dev/sda1')
        with patch('bounded_microsd.checked',return_value=json.dumps({'filesystems':[changed]})):
            with self.assertRaises(RuntimeError): check_binding(binding)

    def test_symlink_path_rejected(self):
        self.bag.symlink_to(self.bag.parent/'elsewhere')
        with self.assertRaises(RuntimeError): self.valid()


if __name__ == '__main__': unittest.main()
