# Course projects (OS + CN): overnight 2026-10-29/30, Claude 2

- BLOCKED: the Pi reboot was denied twice by my permission check, even with the owner's approval relayed. So the camera check, OS-T1 and CN-T1/T2 did not run. Camera software is already built (`. /opt/rpi-cam/env.sh`).
- DONE, CN (local branch `work/RTP0`, 98 tests pass): ns-3 sweeps CN-T3/T5. Frame loss matches 1-(1-p)^n, e.g. 5 % loss with 11 packets per frame: calculated 43.1 %, simulated 43.6 %.
- DONE, CN simulator fix (SIM3): playout is now anchored on the first packet's arrival and jitter is netem-like. CN-T4 rerun: with normal jitter of 20 ms, late frames fall from 99.9 % at D=20 ms to 0.02 % at D=100 ms. The simulation matches the calculated values.
- DONE, CN-T8 (SIM2 + ABR1 adaptive bitrate): at 15 % loss, on-time frames rise from 18 % to 72 %. The 5 s recovery criterion FAILS: quality climbs only +5 per 3 RTCP receiver reports. Conductor fix: ABR never stepped up, because random jitter rises reset its clean-report count.
- DONE, OS PRs (not merged): #11 FW3 MPU6050 task (conductor fixed the I2C clock: it gave 48 kHz, now 400 kHz), #12 FW4 CAN state output (500 kbit/s, bit timing checked), #13 camera report chapter in English and Vietnamese. #7 also has the OS-T5 baud fix: 921600, not 115200.
- PARTIAL: the CN report draft `rtp/report/DRAFT_EN.md` has CN-T3/T5. A worker is adding CN-T4/T8; hardware sections are PENDING. AGY literature notes are in `rtp/report/LITERATURE_NOTES.md`; check citations before using them.
- OPEN: camera timestamps use CLOCK_BOOTTIME but the bridge's age check uses CLOCK_MONOTONIC_RAW. Resolve this before using bridge or STM32 age as camera AoI. A worker found it.
- Physical step: reboot the Pi (or allow this session to), then I check imx219 and run OS-T1 and CN-T1/T2.
