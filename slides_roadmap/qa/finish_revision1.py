from pathlib import Path
p=Path('slides_roadmap/main.tex');s=p.read_text()
s=s.replace('→',r'$\to$')
s=s.replace('Independent algorithm scores are judgment-based, not measured Pi/WBR results, so they are omitted.','Algorithm scores on the preceding page are judgment-based, not measured Pi/WBR results.')
s=s.replace('three EuRoC','three EuRoC')
s=s.replace('Three EuRoC MH01 runs measured','Three runs of EuRoC MH01, a dataset with a reference trajectory, measured')
s=s.replace('ORB-SLAM3 stereo + IMU','ORB-SLAM3 stereo/IMU').replace('RTAB-Map own odometry','RTAB-Map own motion estimate').replace('Wheel/body + depth; no SLAM','Wheels/body + depth')
s=s.replace('Default: reuse current route','Default; existing tools').replace('If occupancy mapping becomes first goal','For an obstacle map').replace('First challenger on identical saved data','First matched-data challenger').replace('Only if robot exports already work','Requires working robot exports').replace('Needs another qualified input path','New input path needed').replace('Prove Linux ARM build/adapter advantage','Prove build/adapter benefit').replace('Port effort needs a demonstrated benefit','Prove port benefit').replace('More dependencies; defer for this demo','More dependencies; defer')
s=s.replace('L{51mm}L{13mm}L{12mm}L{17mm}L{13mm}L{70mm}','L{58mm}L{13mm}L{12mm}L{17mm}L{13mm}L{61mm}')
s=s.replace('Scores are engineering judgments from R1b, informed by R1; not measured Pi speed.','Scores from the independent review, checked against the algorithm review; judgments, not Pi benchmarks.')
s=s.replace('Scale 1--5: higher = better expected fit. Total weights:', '1--5: higher = better fit. RGB-D = color + depth. Total weights:')
s=s.replace('These are requests to plan, not confirmed inventory or bookings.','')
s=s.replace(r'\vfill\takeaway{}','')
s=s.replace(r'\vfill\takeaway{Defer extra estimator ports, Pi graphics, Docker and navigation until needed.}',r'\par\smallskip\small Defer extra ports, Pi graphics and navigation until needed.')
s=s.replace('L{28mm}L{50mm}L{63mm}L{49mm}','L{27mm}L{48mm}L{61mm}L{48mm}')
# Keep dense tables at the established small font; reduce only line spacing locally.
for title in ['Algorithm comparison: keep one default, test one challenger','Hardware and lab bookings: bench and calibration','Hardware and lab bookings: live Pi and robot','Software stack by phase']:
    start=s.index(r'\begin{frame}{'+title+'}');end=s.index(r'\end{frame}',start)
    f=s[start:end].replace(r'\arraystretch}{1.18}',r'\arraystretch}{1.05}').replace(r'\small\renewcommand',r'\small\linespread{1.03}\selectfont\renewcommand')
    s=s[:start]+f+s[end:]
p.write_text(s)
