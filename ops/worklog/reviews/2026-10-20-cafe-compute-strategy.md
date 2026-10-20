# Which computer should I use?

20 October 2026. **Café condition: confirmed ×3 credit only. No ×3 → do not top up.** This replaces the earlier ×2 pilot assumption; it does not authorize a payment or simulator migration.

## Choose by the job

| Resource | When to use it | Main trade-off |
| --- | --- | --- |
| **Your Mac** — i9-9880H, 16 GB RAM | Daily learning, coding, ORB-SLAM3 analysis and current CPU-based MuJoCo/PPO | No rental fee; long training occupies your daily machine |
| **Brother’s laptop** — i7-11800H, 32 GB, RTX 3060 Laptop 6 GB | Prepared CUDA experiments or training that fits 6 GB, when lab access is unavailable | No rental fee, but you must lend away the Mac; borrowing is worthwhile only if that trade-off helps |
| **Lab PC** — stronger GPU reported, exact configuration unknown | First choice for substantial CPU/GPU campaigns if access and persistent storage are available | Free access does not mean weaker than cloud; confirm hardware and borrowing/remote-access terms |
| **Chợ Mơ at ×3** | A planned morning of study plus experiments: **Private for privacy; Training Station for CPU work; Stadium for a workload that actually benefits from its 4090** | Travel, repeated setup and shutdown resets; bring an SSD and export results |
| **Rented NVIDIA GPU cloud** | Long/unattended GPU jobs, Linux GPU backends, unavailable lab access, or more GPU memory | Pay for setup/idle time too; preserves your Mac and avoids travel |

## Cash comparison

Six hours means **rental time**, not a predicted training duration. Café prices assume all ×3 credit is usable and consumed.

| Option | Cash-equivalent/hour | Six hours |
| --- | ---: | ---: |
| Chợ Mơ Private — RTX 4060 8 GB, 16 GB RAM | 7,333 VND | 44,000 VND |
| Chợ Mơ Training — RTX 3060 12 GB, 32 GB RAM | 8,067 VND | 48,400 VND |
| Chợ Mơ Stadium — RTX 4090 24 GB, 64 GB RAM | 16,500 VND | 99,000 VND |
| Cloud RTX A5000 24 GB — advertised $0.27/h | 7,020 VND | 42,120 VND |
| Cloud RTX 4090 24 GB — advertised $0.89/h | 23,140 VND | 138,840 VND |
| Cloud L40S 48 GB — advertised $1.09/h | 28,340 VND | 170,040 VND |

Cloud conversions use **26,000 VND/USD as a planning assumption**, not a live exchange quote. Storage/tax are extra; availability varies. Café travel/food are extra. Infinity’s advertised 24 GB 4090 costs 33,000 VND/h at ×3: pay that premium only for confirmed room benefits.

**Is ×2 worse than cloud?** Not universally. Stadium at ×2 is 24,750 VND/h, above the advertised cloud 4090 example; Training at ×2 is 12,100/h, below it. Different CPUs/GPUs mean this is not equal-throughput pricing. Nevertheless, **your buying rule is ×3 only**. Confirm qualifying deposit, expiry and eligible seats; no additional bonus stacking is assumed.

## Recommendation

**Keep MuJoCo and develop on the Mac. Use the lab for long runs when available. Borrow the laptop for a specific GPU need, not merely because it has NVIDIA graphics.** Choose the café when the morning workspace plus prepared experiments is worth the trip; choose cloud for uninterrupted GPU access. Current PPO physics is CPU-based: a GPU rental does not automatically accelerate it, and a CPU VM is another valid option.

The approved café test remains one MuJoCo run; setup plus result export must take **under one hour**. Neither training speed nor setup time has been measured across these machines. Keep the active Mac campaign with its conductor; no duplicate run or move to Isaac is implied.

Sources checked 20 October: [OEG Chợ Mơ](https://cyber.oeg.vn/tttm-cho-mo), [Runpod advertised GPU rates](https://www.runpod.io/pricing). Personal/lab hardware and promotion terms are owner-reported; Mac CPU/RAM were read locally. [Earlier analysis and review](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/blob/dc1e0fb2967b546a0aa2b01758575bde27a011fa/ops/worklog/reviews/2026-10-20-cafe-compute-strategy.md).
