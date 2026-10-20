# Chợ Mơ: short compute plan

20 October 2026 — one MuJoCo pilot approved; no large deposit or Isaac migration.

## Decision

**Keep MuJoCo. Use the Mac or lab PC for training.** If trying Chợ Mơ, use **Training Station for one morning**. Current PPO spends most of its work on CPU physics; an expensive GPU does not automatically help.

| Seat | Main use | Listed price/hour | Effective price at ×2 |
| --- | --- | ---: | ---: |
| Private — i5, 16 GB RAM | Privacy and study | 22,000 VND | 11,000 VND |
| Training Station — i7, 32 GB RAM | The approved training pilot | 24,200 VND | 12,100 VND |
| Stadium — i9, 64 GB RAM | More compute, higher cost | 49,500 VND | 24,750 VND |

**First visit: deposit at most 100–200k.** The reported tier gives ×2; ×3 requires more than 200k. Confirm the actual offer and credit expiry. Six Training Station hours consume **72,600 VND cash-equivalent credit**, excluding travel and food; the upfront deposit is separate.

## Pilot

1. Bring the Windows MuJoCo/Python packages and project on an SSD. No Ubuntu VM is needed for this path.
2. Run one declared PPO v2 seed; record setup time and training throughput.
3. Copy results off before shutdown: the café resets its computers. Continue only if **setup plus export takes less than one hour**.

## Not now

- No 500k–1m deposit; reconsider only after two successful pilots and confirmed expiry terms.
- No move to Isaac. A later learning session is separate from this pilot.
- No paid cloud unless local/lab compute proves insufficient; compare CPU VMs first.

**Unknown:** actual café training speed and installation time. Measure them; the earlier time estimates were not benchmarks.

Sources: [OEG Chợ Mơ](https://cyber.oeg.vn/tttm-cho-mo) and owner-relayed Claude review. [Detailed analysis and review, retained in Git](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/blob/dc1e0fb2967b546a0aa2b01758575bde27a011fa/ops/worklog/reviews/2026-10-20-cafe-compute-strategy.md).
