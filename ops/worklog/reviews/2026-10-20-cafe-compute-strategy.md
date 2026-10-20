# Which compute resource should I use?

20 October 2026. **Chợ Mơ only with confirmed ×3 credit. No ×3 → no top-up.** This replaces the earlier ×2 planning assumption.

## Choose by the job

| Resource | Cost / constraint | Use when |
| --- | --- | --- |
| **Your Mac** — i9, 16 GB RAM | No rental fee | Daily coding, learning, ORB-SLAM3 analysis and current CPU-based MuJoCo/PPO. Long runs occupy your daily machine. |
| **Brother’s laptop** — i7, 32 GB, RTX 3060 Laptop 6 GB | Free, but you must lend away the Mac | A prepared CUDA experiment fits 6 GB and lab access is unavailable. Borrow for a specific benefit, not simply for the NVIDIA label. |
| **Lab PC** — exact hardware unknown | Free if access is granted | Preferred free resource for long CPU/GPU runs, provided access and persistent storage work. Verify its configuration first. |
| **Chợ Mơ at ×3** | Seat, travel and setup costs | A planned morning combining study and experiments: **Private for privacy, Training Station for CPU work, Stadium for useful 4090 work**. Shutdown resets files. |
| **NVIDIA GPU cloud** | Hourly rental plus extras | Long/unattended GPU or Linux jobs, unavailable lab access, or more VRAM. Keep your Mac and avoid travel. |

## Price comparison

Six hours means rental time, **not predicted training duration**. Café ×3 credit must be fully usable and consumed.

| Option | VND/hour | Six hours |
| --- | ---: | ---: |
| Chợ Mơ Private — RTX 4060 8 GB / 16 GB RAM | 7,333 | 44,000 |
| Chợ Mơ Training — RTX 3060 12 GB / 32 GB RAM | 8,067 | 48,400 |
| Chợ Mơ Stadium — RTX 4090 24 GB / 64 GB RAM | 16,500 | 99,000 |
| Cloud RTX A5000 24 GB — $0.27/h | 7,020 | 42,120 |
| Cloud RTX 4090 24 GB — $0.89/h | 23,140 | 138,840 |
| Cloud L40S 48 GB — $1.09/h | 28,340 | 170,040 |

Cloud prices are advertised Runpod rates, converted at an **assumed 26,000 VND/USD**; storage/tax are extra and availability varies. Café travel/food are extra. Different CPUs/GPUs mean equal rental hours are not equal completed work. Infinity’s 24 GB 4090 costs 33,000 VND/h at ×3; room benefits must justify that premium.

**At ×2:** Stadium becomes 24,750 VND/h, above the cloud 4090 example before extras. That does not make every cloud option better, but your rule remains **×3 only**. Confirm eligibility and expiry; no bonus stacking is assumed.

## Recommendation

**Default: Mac for development/current CPU work; lab for larger runs.** Borrow the laptop only for a specific GPU need. Choose the café when its workspace plus prepared experiments justifies the trip; choose cloud for continuous GPU access. Current CPU physics will not automatically accelerate on a GPU; CPU VMs remain another option.

For the approved café pilot, time one v2 seed and require **setup plus export under one hour**. Preserve results before shutdown. No payment, duplicate training or Isaac migration is authorized by this comparison.

Sources: [OEG Chợ Mơ](https://cyber.oeg.vn/tttm-cho-mo), [Runpod rates](https://www.runpod.io/pricing), checked 20 October; personal/lab hardware and promotions are owner-reported, with Mac CPU/RAM checked locally. [Detailed history](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/blob/dc1e0fb2967b546a0aa2b01758575bde27a011fa/ops/worklog/reviews/2026-10-20-cafe-compute-strategy.md).
