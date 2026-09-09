"""Correlate captured united IMU with raw motion; summarize whole-window delivery."""
import json,pathlib,bisect,datetime
p=pathlib.Path(__file__).resolve().parent
out={}
for case in 'ABC':
 f=p/(case+'_RATES.json')
 if not f.exists():continue
 d=json.loads(f.read_text()); ts=d['topics']; result={'start':datetime.datetime.fromtimestamp(d['start_epoch'],datetime.timezone.utc).isoformat(),'end':datetime.datetime.fromtimestamp(d['end_epoch'],datetime.timezone.utc).isoformat(),'topics':{}}
 for t,v in ts.items():result['topics'][t]={k:v[k] for k in ['count','arrival_hz','stamp_hz','max_stamp_gap','max_arrival_gap','nonpositive_stamp_steps','mean_xyz_gyro_accel','mean_accel_norm'] if k in v}|{'count_per_window_second':v['count']/d['duration_seconds']}
 log=p/(case+'_LOG.txt'); lines=log.read_text().splitlines() if log.exists() else []
 selected=[]
 for line in lines:
  try: stamp=datetime.datetime.fromisoformat(line.split()[0].replace('Z','+00:00')).timestamp()
  except (ValueError,IndexError):continue
  if d['start_epoch']<=stamp<=d['end_epoch']:selected.append(line)
 result['incomplete_notifications_in_window']=sum('Incomplete video frame detected' in l for l in selected)
 result['calibration_warning_in_run']=any('IMU Calibration is not available' in l for l in lines)
 a=ts['/camera/accel/sample'];g=ts['/camera/gyro/sample'];u=ts['/camera/imu']
 if all('raw_vectors' in x for x in [a,g,u]):
  at=a['raw_stamps']; av=[v[3:] for v in a['raw_vectors']]; gm=dict(zip(g['raw_stamps'],g['raw_vectors'])); avset=set(map(tuple,av)); counts=dict(united=len(u['raw_stamps']),gyro_stamp_and_vector_match=0,accel_exact_any_raw=0,bracketed=0,copy_previous_exact=0,linear_match_1e_6=0,distinguishable=0,distinguishable_copy=0,distinguishable_linear=0)
  for stamp,v in zip(u['raw_stamps'],u['raw_vectors']):
   counts['gyro_stamp_and_vector_match']+=stamp in gm and gm[stamp][:3]==v[:3]
   counts['accel_exact_any_raw']+=tuple(v[3:]) in avset
   i=bisect.bisect_right(at,stamp)-1
   if i<0 or i+1>=len(at):continue
   counts['bracketed']+=1
   ratio=(stamp-at[i])/(at[i+1]-at[i]); interp=[x+(y-x)*ratio for x,y in zip(av[i],av[i+1])]
   cp=av[i]==v[3:]; li=max(abs(x-y) for x,y in zip(interp,v[3:]))<1e-6
   counts['copy_previous_exact']+=cp;counts['linear_match_1e_6']+=li
   if max(abs(x-y) for x,y in zip(interp,av[i]))>1e-5:
    counts['distinguishable']+=1;counts['distinguishable_copy']+=cp;counts['distinguishable_linear']+=li
  result['imu_correlation']=counts
 out[case]=result
(p/'RESUME_SUMMARY.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
