# R2: Robot integration and the Pi–STM32 boundary (read slides_roadmap/COMMON.md first)
Write `slides_roadmap/research/R2_integration.md` (aim 3–6 pages, dense, cited).
1. What exactly crosses from the Pi to the STM32H7 and back: a perception-health message
   (fields, rate, staleness timeout, validity flags), optional pose/velocity reference for
   navigation, and what the STM32 does when it is absent/stale/invalid. Physical link options the
   repo already assumes (check docs; UART, CAN, Ethernet, USB-CDC, micro-ROS) and a recommendation
   with framing, CRC, sequence numbers, timestamps.
2. Mechanical/electrical integration of the D435i and Pi 5 on a wheel-biped: mounting position and
   rigidity, vibration isolation vs rigid mount for VIO (cite guidance), cable strain, power from
   the robot battery (DC-DC to 5.1 V/5 A for Pi 5 with USB peripherals; isolation from motor noise),
   thermal, emergency behaviour.
3. How comparable wheel-legged/balancing robots handle perception (e.g. Ascento, Diablo/Direct Drive
   Tech, Unitree wheeled robots, academic wheel-biped papers): what sensors, where computed, how
   coupled to balance control. Extract only lessons that apply.
4. Integration test ladder on the robot: bench (robot on a stand, wheels off ground), tethered
   balancing, slow driving in a mapped room, closed-loop navigation; what to measure at each and
   what makes it safe; ground-truth options in a lab without motion capture (tape-measured loop,
   AprilTag markers, return-to-start drift, external camera).
5. Failure modes on a moving robot (motion blur, vibration, wheel slip, featureless floors, lighting,
   IMU saturation during falls/jumps) and mitigations.
End with: integration checklist table (step | hardware | software | risk | exit evidence | source).
