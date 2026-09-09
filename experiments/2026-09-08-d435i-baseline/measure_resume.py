"""Read-only simultaneous ROS sensor measurement; no sensor settings changed."""
import rclpy,time,json,sys,math,statistics
from rclpy.qos import qos_profile_sensor_data,QoSProfile,DurabilityPolicy,ReliabilityPolicy
from sensor_msgs.msg import Image,Imu,CameraInfo
from tf2_msgs.msg import TFMessage
from rosidl_runtime_py.convert import message_to_ordereddict
rclpy.init(); node=rclpy.create_node('d435i_audit_probe'); data={}; subs=[]
topics={'/camera/image_raw':Image,'/camera/infra2/image_rect_raw':Image,'/camera/gyro/sample':Imu,'/camera/accel/sample':Imu,'/camera/imu':Imu,'/camera/camera_info':CameraInfo}
def cb(topic,msg):
 d=data.setdefault(topic,{'arrival':[],'stamp':[],'vectors':[]}); d['arrival'].append(time.monotonic()); d['stamp'].append(msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9)
 if 'sample' not in d:
  d['sample']=({k:getattr(msg,k) for k in ['width','height','encoding','step','is_bigendian']}|{'frame_id':msg.header.frame_id}) if isinstance(msg,Image) else message_to_ordereddict(msg)
 if isinstance(msg,Imu): d['vectors'].append([msg.angular_velocity.x,msg.angular_velocity.y,msg.angular_velocity.z,msg.linear_acceleration.x,msg.linear_acceleration.y,msg.linear_acceleration.z])
for topic,typ in topics.items(): subs.append(node.create_subscription(typ,topic,lambda msg,t=topic:cb(t,msg),qos_profile_sensor_data))
static=[]
subs.append(node.create_subscription(TFMessage,'/tf_static',lambda m:static.append(message_to_ordereddict(m)),QoSProfile(depth=10,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)))
start=time.monotonic(); wall=time.time(); duration=float(sys.argv[1]) if len(sys.argv)>1 else 30
while time.monotonic()-start<duration:rclpy.spin_once(node,timeout_sec=.1)
out={'start_epoch':wall,'end_epoch':time.time(),'duration_seconds':time.monotonic()-start,'topics':{},'tf_static':static}
for t in topics:
 d=data.get(t)
 if not d:out['topics'][t]={'count':0};continue
 a=d.pop('arrival');s=d.pop('stamp');v=d.pop('vectors');n=len(a)
 d.update(count=n,arrival_hz=(n-1)/(a[-1]-a[0]) if n>1 else None,stamp_hz=(n-1)/(s[-1]-s[0]) if n>1 and s[-1]!=s[0] else None,first_stamp=s[0],last_stamp=s[-1],nonpositive_stamp_steps=sum(y<=x for x,y in zip(s,s[1:])),max_stamp_gap=max([y-x for x,y in zip(s,s[1:])] or [0]),max_arrival_gap=max([y-x for x,y in zip(a,a[1:])] or [0]))
 if v:
  d['raw_stamps']=s; d['raw_vectors']=v
  d['mean_xyz_gyro_accel']=[statistics.mean(x) for x in zip(*v)];d['stdev_xyz_gyro_accel']=[statistics.pstdev(x) for x in zip(*v)];d['mean_accel_norm']=statistics.mean(math.sqrt(sum(z*z for z in x[3:])) for x in v)
 out['topics'][t]=d
print(json.dumps(out,indent=2));node.destroy_node();rclpy.shutdown()
