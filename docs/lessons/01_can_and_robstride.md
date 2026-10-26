# 01 — CAN and RobStride

## Learning goals

After this lesson, you should be able to read an identifier and a data field,
calculate a nominal CAN bit rate from the bxCAN timing registers, and explain
why a passive monitor must not acknowledge frames.

The examples use classic CAN with eight data bytes. CAN FD is a related format,
but is not the format in the cited RobStride traffic.

## 1. What the bus carries

A CAN bus is a shared, differential pair: CAN_H and CAN_L.
A transceiver drives a differential voltage for a dominant bit and releases the
pair for a recessive bit. The recessive bus state is therefore also the idle
state.

The dominant state wins when two nodes transmit at once. This wired arbitration
lets a transmitter observe the bus while it sends its identifier.
If it sends recessive but observes dominant, it loses arbitration cleanly and
stops transmitting without corrupting the winning frame.

```text
Node A TX:  dominant  recessive  recessive ...
Node B TX:  dominant  dominant   ...
Bus:        dominant  dominant   ...
                                  ^ B wins here
```

Differential signaling improves rejection of common-mode electrical noise.
It does not make wiring arbitrary: use a twisted pair, keep stubs short, share
a suitable reference ground, and respect the transceiver's common-mode limits.

## 2. CAN frame fields

A classic data frame begins with Start of Frame, then arbitration and control
fields, data, CRC, ACK, and End of Frame.
The CRC detects frame corruption; the ACK slot confirms that at least one
receiver accepted the frame's syntax and checksum.

An ACK is not an application-level success message.
It does not prove that the intended motor understood a command or acted on it.
A missing reply at the application layer still needs a timeout or feedback check.

Standard frames carry an 11-bit identifier (`0x000`–`0x7FF`).
Extended frames carry a 29-bit identifier (`0x00000000`–`0x1FFFFFFF`).
The identifier participates in arbitration; it is not inherently a destination
address. A protocol may allocate some bits as a device address.

In classic CAN, the payload has 0–8 bytes. The Data Length Code (DLC) gives its
length. Remote frames request data in older CAN designs but are uncommon in
modern command/feedback protocols.

Bit stuffing inserts a complementary bit after five consecutive equal bits in
the stuffed portion of a frame. This limits long runs and helps receivers
resynchronize. Stuff bits consume bus time and matter when estimating utilization.

```text
SOF | arbitration / ID | control | 0..8 data bytes | CRC | ACK | EOF
```

The ACK slot is recessive from the sender. Any active receiver that correctly
receives the frame may pull it dominant. The sender samples the slot to tell
whether a receiver acknowledged it.

## 3. Bit timing at 42 MHz

A CAN bit is divided into time quanta (tq). For bxCAN:

$$T_{bit} = T_{q} (1 + BS1 + BS2), \qquad
T_q = \frac{BRP+1}{f_{CAN}}$$

Here `1` is the Sync Segment. Register fields encode `BRP-1`, `BS1-1`, and
`BS2-1`; always distinguish the encoded field from the actual count.

The monitor's 42 MHz branch sets BTR fields with `BRP field = 2`,
`TS1 field = 10`, and `TS2 field = 1` (`tools/can_monitor/firmware/can_rx.c:45-48`).
Therefore the actual divider is 3, BS1 is 11 tq, and BS2 is 2 tq.

$$N_{tq}=1+11+2=14, \qquad
f_{bit}=\frac{42\,000\,000}{3\cdot14}=1\,000\,000\;bit/s$$

The literal value written is `0x801A0002`: bit 31 enables SILM, bit 20 encodes
TS2=1, bits 16–19 encode TS1=10, and the BRP field is 2.
This is a calculated decode of the register expression, not a scope measurement.

The sample point is at the end of Sync + BS1:

$$\text{sample fraction}=\frac{1+11}{14}=0.8571\quad (85.7\%)$$

That timing must match the network's nominal bitrate and have a suitable sample
point for propagation delay and oscillator tolerance. A correct bitrate alone
does not guarantee a robust physical link.

## 4. ACK, error counters, and fault states

CAN nodes monitor transmitted bits and check CRC, frame format, and timing.
A detected error causes an error flag and causes transmitters to retry later.
Repeated transmit and receive errors increase the Transmit Error Counter (TEC)
and Receive Error Counter (REC).

In the classical CAN fault-confinement model, a node becomes error passive
when TEC or REC reaches 128. A transmit error counter above 255 moves it to
bus-off. A bus-off node stops influencing the bus until recovery conditions are
met; controller policy may automate recovery.

A lone active transmitter with no active receiver sees no ACK and will retry.
This is why a listen-only monitor should not be treated as the bus's ACK partner.
A monitor is an observer, not a substitute for a functioning receiving node.

`can_monitor` sets the bxCAN SILM bit in BTR (`can_rx.c:45-49`).
In silent mode the controller receives frames but does not drive ACK or error
flags. That prevents the diagnostic board from changing the behavior of the
robot bus while observing it.

## 5. Termination and wiring

A high-speed CAN trunk is normally terminated with 120 Ω at each physical end.
With power removed, a correctly terminated network commonly measures about
60 Ω between CAN_H and CAN_L because the two resistors are in parallel.

```text
120 Ω                                      120 Ω
  |                                          |
CAN_H ========================================
CAN_L ========================================
  |                                          |
  +-- node -- node -- monitor (short stub) --+
```

Do not add another terminator just because a new board is attached.
Three 120 Ω terminations produce 40 Ω and overload the drivers.
A missing terminator or long stub can cause reflections, ringing, and intermittent
bit errors, especially at the edges of a long cable.

The monitor code enables F446 CAN pins and configures CAN1/CAN2 filters to
accept all IDs (`can_rx.c:20-38, 53-64`). That is broad capture policy; it does
not identify which frames are safe to interpret as RobStride.

## 6. RobStride extended identifier

The H723 motor driver uses 29-bit extended identifiers. It builds the ID as
five communication-type bits, 16 data/source bits, and eight target-ID bits
(`robstride_drv.c:34-39`). The protocol summary also documents the layout and
examples (`docs/reference/robstride_protocol.md:7-23`).

```text
28        24 23                       8 7              0
+------------+--------------------------+----------------+
| comm type  | data2 / source info      | target motor   |
|   5 bits   |         16 bits          |    8 bits      |
+------------+--------------------------+----------------+
```

Selected communication types in the driver are:

| Type | Meaning | Evidence |
|---|---|---|
| `0x01` | MIT operation-control command | `robstride_drv.c:84-108` |
| `0x02` | motor feedback / active report | `robstride_drv.c:185-214` |
| `0x03` | enable | `robstride_drv.c:46-55` |
| `0x04` | stop/disable | `robstride_drv.c:57-67` |
| `0x11` | read parameter | `robstride_drv.c:150-163` |
| `0x12` | write parameter | `robstride_drv.c:111-148` |

On feedback frames, the driver extracts mode, fault, motor ID, and master ID
from identifier subfields, then decodes position, velocity, torque, and
temperature from the eight data bytes (`robstride_drv.c:185-214`).

The H723 project connects two motors with the same CAN ID on separate buses:
left is FDCAN1 and right is FDCAN3 (`User/APP/motor_task.c:33, 50-53`).
The bus itself separates those identical numeric IDs; they are not two addresses
on one shared physical bus.

## 7. Scaling packed values

For an unsigned $n$-bit value, linear scaling maps integer codes to a range:

$$x = x_{min} + \frac{c}{2^n-1}(x_{max}-x_{min})$$

The driver uses this form in `uint_to_float` and the inverse form in
`float_to_uint` (`robstride_drv.c:12-26`).
For extended MIT control, the ranges are position ±12.57 rad, command velocity
±20 rad/s, torque ±60 Nm, $K_p$ 0–5000, and $K_d$ 0–100, each packed to 16 bits
(`robstride_protocol.md:51-59`; driver packing at `robstride_drv.c:84-108`).

Worked example: encode zero position over $[-12.57,+12.57]$.
The ideal code is

$$c=\frac{0-(-12.57)}{25.14}(65535)=32767.5$$

The C conversion truncates the positive floating result to integer 32767
(`robstride_drv.c:12-19`). Decoding that code gives approximately
$-0.000191$ rad, a half-LSB offset from zero because the integer grid has an
even number of intervals and no exact center code.

For a zero-to-5000 gain, $K_p=1000$ maps to approximately
$1000/5000\cdot65535=13107$ (code `0x3333`). The receiver reconstructs a
quantized value near 1000; it does not receive a floating-point number.

The command's CAN ID stores packed feed-forward torque in its 16-bit data2
field; the payload holds position, velocity, $K_p$, and $K_d$
(`robstride_drv.c:84-108`; `robstride_protocol.md:26-35`).
Feedback uses big-endian 16-bit chunks for position, velocity, torque, and
raw temperature; temperature divides by ten (`robstride_drv.c:189-214`).

## 8. Why monitor mode matters

The monitor initializes both CAN controllers with SILM, then drains FIFO0 and
preserves whether each received frame was standard or extended
(`can_rx.c:45-50, 66-86`).
It can decode frames after capture without sending anything on the bus.

Silent mode lets the monitor attach to a live bus without supplying ACKs,
error flags, or commands. It is appropriate for observation and protocol
learning; it cannot validate that a transmitter receives an ACK from the
intended robot node.

The decoder rejects non-extended frames, out-of-range identifiers, null data,
and unexpected payload lengths (`tools/can_monitor/firmware/robstride_decode.c:24-31`).
This separates physical capture from protocol interpretation.

## How this applies in our project

Use the monitor to learn which IDs, message types, and timing actually occur.
Keep its SILM setting enabled on a live robot bus. Check termination and bus
fault counters before attributing bad decoding to field scaling. A valid ACK
only says some node received a correct frame; verify motor response through
feedback and local safety state.

<details>
<summary>Self-check questions and answers</summary>

1. **A frame has ID `0x123`. Is it standard or extended?**
   Either. The identifier value alone does not specify IDE; inspect the frame's
   format flag.
2. **What bitrate do the monitor's 42 MHz BTR values produce?**
   $42\text{ MHz}/(3\cdot14)=1\text{ Mbit/s}$.
3. **Does an ACK prove a motor executed a command?**
   No. It means at least one active receiver accepted the frame at link level.
4. **Why is the monitor silent?**
   To observe without driving ACK or error bits and changing live-bus behavior.
5. **What does code 32767 represent for a symmetric 16-bit position range?**
   A value near zero, slightly negative by about half one quantization step.

</details>
