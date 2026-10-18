# N4A throttle fixture provenance

`n4a_real_throttle_samples.csv` is a **derived fixture**, not a captured sampler
row. The measured source is the shared checkout's read-only
`experiments/2026-10-13-n4a-euroc-mh01/REPORT.md`, §2 “Results”: 87/178 five-second
observations reported `0x50005`; maximum temperature was 63 °C. The source also
states that timing was invalid and MH01's camera rate was 20 Hz.

The fixture copies those reported values into the profile CSV schema. The
clock epoch (`monotonic_ns=1`), PID, CPU count, memory values, process identity
and sample duration are **SYNTHETIC** scaffolding. The source does not establish
that its maximum temperature and this throttle bitmask occurred in the same
poll. Decoded bits 0, 2, 16 and 18 are **CALCULATED** from the mask using the
existing repository bit definitions. The fixture tests rejection of known bad
evidence and cannot reproduce a complete measured timing window.
