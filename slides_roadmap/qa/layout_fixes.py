from pathlib import Path
import re
p=Path('slides_roadmap/main.tex');s=p.read_text()
s=re.sub(r'(\\begin\{frame\}\{[^\n]*\}\n)(\{\\small)',r'\1\\relax\n\2',s)
s=s.replace(r'Measured target, stand,\\light, workstation',r'A0 grid, stand,\\light, workstation')
s=s.replace(r'STM32 board, reviewed\\link, debugger',r'STM32, link,\\debugger')
s=s.replace(r'WBR, mount, power rail,\\stand, stop, tether',r'WBR, mount, rail,\\stand, stop, tether')
s=s.replace(r'Final cooling/data path,\\marked room route',r'Pi, cooling, storage,\\marked room')
s=s.replace(r'Patch-4 rebuild pending',r'Crash-fix build pending')
s=s.replace('measured rigid A0 AprilGrid target','measured A0 AprilGrid (tag-pattern target)')
s=s.replace('Headless ORB;','ORB without a display;')
s=s.replace('CPU/RAM, temperature','processor/memory, temperature')
s=s.replace('fresh heartbeat','fresh status message').replace('A fresh heartbeat','A fresh status message')
p.write_text(s)
