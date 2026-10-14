from pathlib import Path
import subprocess,json
root=Path('/home/richard/wbr-evidence/2026-09-13-d435i-post-reboot-20260913T023833Z'); root.mkdir(parents=True,exist_ok=False)
n0=root/'n0'; n0.mkdir()
commands={'utc.txt': ['date', '-u', '--iso-8601=seconds'], 'uptime.txt': ['uptime'], 'boot-id.txt': ['cat', '/proc/sys/kernel/random/boot_id'], 'power.txt': ['vcgencmd', 'get_throttled'], 'temperature.txt': ['vcgencmd', 'measure_temp'], 'thermal-zone0.txt': ['cat', '/sys/class/thermal/thermal_zone0/temp'], 'ip-addresses.txt': ['ip', '-br', 'addr'], 'routes.txt': ['ip', 'route'], 'lsusb.txt': ['lsusb'], 'usb-tree.txt': ['lsusb', '-t'], 'kernel-boot-utc.log': ['journalctl', '-k', '-b', '--no-pager', '-o', 'short-iso-precise', '--utc'], 'kernel-boot-monotonic.log': ['journalctl', '-k', '-b', '--no-pager', '-o', 'short-monotonic'], 'processes.txt': ['ps', '-eo', 'pid,ppid,user,comm,args'], 'memory.txt': ['free', '-h'], 'filesystems.txt': ['df', '-hT'], 'storage-devices.txt': ['lsblk', '-o', 'NAME,MODEL,SERIAL,TRAN,SIZE,FSTYPE,UUID,MOUNTPOINTS']}
receipts={}
for name, argv in commands.items():
 p=subprocess.run(argv,capture_output=True,text=True)
 (n0/name).write_text(p.stdout+p.stderr)
 receipts[name]={'argv':argv,'returncode':p.returncode}
(n0/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n')
print(root)
print((n0/'power.txt').read_text())
print((n0/'usb-tree.txt').read_text())
