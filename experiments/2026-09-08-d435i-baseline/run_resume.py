"""Sequential isolated D435i follow-up; preserves initial audit evidence."""
import subprocess as sp, json, time, pathlib, datetime, sys
out=pathlib.Path(__file__).resolve().parent
case=sys.argv[1]
assert case in ['A','B','C']
name='d435i-resume-'+case.lower()
def run(args,timeout=20):
 return sp.run(args,text=True,stdout=sp.PIPE,stderr=sp.STDOUT,timeout=timeout)
def save(suffix,result):
 (out/(case+'_'+suffix)).write_text(result.stdout)
 return result
running=run(['docker','ps','--format','{{.Names}}'])
if running.stdout.strip(): raise SystemExit('Refusing test with running containers: '+running.stdout)
usb=save('USB_BEFORE.txt',run(['lsusb','-t']))
if run(['lsusb','-d','8086:0b3a']).returncode: raise SystemExit('Camera absent')
save('HOST_OWNERS.txt',run(['bash','-lc',"date -Is; ps -eo pid,args | rg '(realsense2_camera_node|rs-enumerate|realsense-viewer)' ; fuser /dev/video* /dev/hidraw* 2>&1" ]))
old=json.loads(run(['docker','inspect','d435i-audit-video']).stdout)[0]
args=['docker','run','-d','--name',name,'--network','host','--ipc','host','--privileged','-v','/dev:/dev','--user','richard' if case=='C' else '0:0']
if case=='C':args+=['--group-add','44']
for m in old['Mounts']:
 if m['Destination']!='/dev': args+=['-v',m['Source']+':'+m['Destination']+('' if m['RW'] else ':ro')]
args+=['-e','ROS_DOMAIN_ID=42','-e','FASTDDS_BUILTIN_TRANSPORTS=UDPv4','-e','RMW_IMPLEMENTATION=rmw_fastrtps_cpp',old['Image']]
cmd=old['Config']['Cmd'][:]
cmd[cmd.index('enable_infra2:=false')]='enable_infra2:='+('true' if case=='A' else 'false')
args+=cmd
(out/(case+'_COMMAND.json')).write_text(json.dumps(args,indent=2))
started=save('START.txt',run(args))
if started.returncode:raise SystemExit(started.stdout)
try:
 time.sleep(12)
 save('INSPECT.json',run(['docker','inspect',name]))
 env='source /opt/ros/jazzy/setup.bash; export ROS_DOMAIN_ID=42 FASTDDS_BUILTIN_TRANSPORTS=UDPv4 RMW_IMPLEMENTATION=rmw_fastrtps_cpp; '
 measured=save('RATES.json',run(['bash','-lc',env+'python3 '+str(out/'measure_resume.py')+' 30'],45))
 print(case+' measurement complete; exit='+str(measured.returncode),flush=True)
 save('PARAMETERS.txt',run(['bash','-lc',env+'timeout 8 ros2 param get /camera unite_imu_method; timeout 8 ros2 param get /camera enable_infra2; timeout 8 ros2 node list --no-daemon --spin-time 2'],30))
finally:
 save('STOP.txt',run(['docker','stop','-t','5',name]))
 save('LOG.txt',run(['docker','logs','--timestamps',name]))
 save('USB_AFTER.txt',run(['lsusb','-t']))
 save('STATE_AFTER.json',run(['docker','inspect',name]))
print(case+' stopped',flush=True)
