# Compute strategy: OEG Cho Mo, borrowed computers, lab GPU and cloud

Date: 2026-10-20, Asia/Ho_Chi_Minh. Status: **analysis complete; proposed choices, pending owner/Claude review**.
Analysis base: `819659c` (merged PR #51). Branch: `chatgpt/20261020-cafe-compute-review`.
This document does not approve a simulator migration, new experiment, purchase, bank-account opening or prepaid deposit.

## 1. Decision in brief

**Recommendation:** keep MuJoCo as the project reference. A cafe is a plausible combination of a morning workspace and an occasional workstation, conditional on a successful native-Windows pilot. Do not treat an hourly gaming seat as a persistent cloud server.

- For private study and existing CPU experiments: investigate **Cho Mo Private**, RTX 4060 8 GB / 16 GB RAM, at 22,000 VND/h before any promotion. It is a workspace candidate, not the full-Isaac workstation.
- For inexpensive nonprivate experimentation: investigate **Cho Mo VIP** (confirm RAM) or **Training Station**, both advertising RTX 3060 12 GB. VRAM capacity can matter more than the GPU generation number.
- For **full Isaac Sim GUI/RTX work or a justified large GPU batch**: investigate **Cho Mo Stadium, RTX 4090 24 GB / 64 GB RAM**. It is the clear hardware match among the supplied options, subject to actual OS, driver, disk and permissions.
- Infinity Capsule doubles Stadium's advertised hourly rate without increasing the advertised 24 GB VRAM; justify it by confirmed room/privacy benefits, not an assumed doubling of training speed.
- Prefer the lab machine for unattended campaigns if access, persistence and hardware are suitable; use cloud for a deadline, Linux-only backend or uninterrupted job that the available local resources cannot satisfy.
- Do not prepay 500,000–1,000,000 VND before testing the installation/restore process and confirming bonus-credit terms.

This is a proposed resource allocation, not a claim that any cafe GPU was benchmarked. Cafe quietness, room isolation and early-morning availability are unmeasured.

## 2. Owner constraints and the actual project workload

Owner wants balance/push recovery versus LQR, about half the work time for simulation/RL and half for ORB-SLAM3. The Cho Mo trip is inconvenient, accepted if worthwhile; visits would occupy a full morning. The owner explicitly narrowed this comparison to Cho Mo only. Six paid hours is the **calculation scenario**, not a confirmed booking duration. A private room is preferred.

Owner reports OEG allows software installation, but shutting down resets the computer. Permission for admin operations/VM installation is uncertain. Assume no persistent local packages, caches or results until staff identifies a persistent location. Remote/unattended operation is unconfirmed.

Available alternatives: daily Mac; borrowed i7-11800H/32 GB/RTX 3060 Laptop 6 GB requiring a Mac swap; potentially stronger lab GPU with exact model/OS/access unknown; first cloud budget below USD 50. CAD is in progress, probably SolidWorks; link inertias/export quality remain unknown.

**Important measured update:** [the completed comparison](../../../sim/rl/RESULTS_2026-10-20.md) already trained five seeds × 150,000 steps on the Intel Mac CPU. Each concurrent process took approximately 448–454 s; these are not five serial durations to add. LQR succeeded 160/160, PPO 0/800. This negative result is conditional on the frozen recipe and budget, not an execution failure or proof that RL cannot work. Evaluation/audits take additional time.

The runtime uses CPU MuJoCo plus a Python delay/lag/noise layer, Gymnasium and SB3; `sim/rl/training.py` explicitly selects `device='cpu'`. The pinned stack is MuJoCo 3.3.7, Torch 2.2.2, SB3 2.3.2, Python 3.12. Renting a 4090 does not automatically move the physics, Python substeps or trace writing onto that GPU.

The immediate research bottleneck is understanding/experiment design, not demonstrated lack of GPU. Further training/protocol changes remain pending the existing Claude review. No new training was launched for this report.

## 3. Hardware and tariff evidence

Only owner-supplied images 1–6 are in scope. The [official Cho Mo page](https://cyber.oeg.vn/tttm-cho-mo) was fetched with certificate verification on 20 October. The table uses its decoded server-rendered advertised data; this is not hardware inspection. Images7–8 are excluded from this revised comparison.

| Location / zone | Advertised CPU | GPU / VRAM | RAM | Listed VND/h |
| --- | --- | --- | ---: | ---: |
| Cho Mo VIP | i5-12400F | RTX 3060 /12 GB | 32 GB* | 16,500 |
| Cho Mo Private | i5-12400F | RTX 4060 /8 GB | 16 GB | 22,000 |
| Cho Mo Training Station | i7-13700F | RTX 3060 /12 GB | 32 GB | 24,200 |
| Cho Mo Premium | i7-13700F | RTX 3060 /12 GB | 32 GB | 27,500 |
| Cho Mo Stadium | i9-13900F | RTX 4090 /24 GB | 64 GB | 49,500 |
| Cho Mo Infinity | i9-13900F | RTX 4090 /24 GB | 64 GB | 99,000 |

Other Cho Mo overview prices: Duo/MOBA 16,500; FPS 18,700; Couple 27,500; Stream 38,500 VND/h. Current page data list Couple and Stream with GTX 1660 Super6 GB/ 16 GB RAM, so they are poor candidates for full Isaac and offer no established compute advantage over the shortlist. Their room/comfort value needs direct confirmation.

### Conflicts that must remain visible

- Image 3 Stadium popup says 45,000, whereas image1 and current page data say 49,500. Budget at 49,500 until the actual account debit is confirmed.
- Image 5 Premium popup says 25,000; overview/current data say 27,500.
- Image 2 Stream popup says 35,000, i7-13700F, RTX 4060 Ti8 GB; its RAM artwork says 32 GB and table 64 GB. Current page data instead list 38,500, i5-12400F, GTX 1660 Super6 GB,16 GB. **Do not book Stream for CUDA/Isaac on the popup's promise.**
- Image 6 VIP RAM is16 GB; current page data say 32 GB (* above). Check the assigned seat.
- Some price differences equal 10%, but tax or an update is only a hypothesis; no VAT explanation was confirmed.
- A room's price may be per seat, per room or subject to a minimum: this is unconfirmed. All calculations assume one billed seat at the stated rate. Physical isolation of Private/Couple/Stream/Infinity is not established by a zone name.

Monitor refresh rate, mouse, keyboard and gaming branding do not establish RL throughput. Private room denotes physical separation, not a trusted personal computer. A newer 8 GB card is not a VRAM upgrade over a 12 GB 3060.

## 4. Promotion economics

The x3/newbie terms are **owner-relayed staff statements**, not independently verified. The public Cho Mo page did not expose a matching offer in its text. Keep the staff conversation for the exact account/branch.

Reported: under 100k receives x1.5;100k–200k x2; above 200k x3, within an account's first 30 days, with a seven-day check-in description. A separate first transaction from 100k grants 50% promotional credit. A bank-account offer mentions 50k. Eligibility, repeatability/check-in steps, eligible zones, credit expiry, balance priority, caps, refundability and stacking are unknown. The 30-day eligibility window does not establish when credited money expires.

Assume **x3 means total playable balance = 3 × cash deposited**, fully usable for the selected seat. It does not mean cash plus three extra copies. Do not stack the 50% or50k offers into the base calculation.

$$
p_{\rm effective}=p/3,\qquad C_{6 h}=6p/3,\qquad H=3D/p.
$$

Thus 49,500/3 = **16,500**, not 18,500 VND/h. If the lower 45,000 popup were honored it would be 15,000/h.

| Zone | No bonus VND/h | x2 VND/h | x3 VND/h | Six hours at x3 | Hours from 500k cash at x3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cho Mo VIP | 16,500 | 8,250 | 5,500 | 33,000 | 90.91 |
| Cho Mo Private | 22,000 | 11,000 | 7,333.33 | 44,000 | 68.18 |
| Cho Mo Training | 24,200 | 12,100 | 8,066.67 | 48,400 | 61.98 |
| Cho Mo Premium | 27,500 | 13,750 | 9,166.67 | 55,000 | 54.55 |
| Cho Mo Stadium | 49,500 | 24,750 | 16,500 | 99,000 | 30.30 |
| Cho Mo Infinity | 99,000 | 49,500 | 33,000 | 198,000 | 15.15 |

One million cash doubles the last column. 500k would fund about five 6 h Stadium visits or about eleven 6 h Cho Mo Private visits. Do not buy more locked credit merely because the theoretical hourly price is low.

If only fraction f of credited balance is ultimately consumed, realized cash cost is p/(3f): 50% utilization gives p/1.5; one-third gives p. Food, travel, parking, unconsumed credit and room minimums are additional. At most, a confirmed additional 0.5D bonus would make 3.5D total under additive stacking; multiplying promotions to 4.5D is unjustified without explicit terms.

## 5. Windows: VM is not a universal prerequisite

| Software path | Native Windows possibility | Consequence here |
| --- | --- | --- |
| CPU MuJoCo + Python/SB3 | Yes at library level | Lowest-friction candidate; project portability still needs a real smoke run |
| PyTorch CUDA | Yes | Accelerates supported tensor computation; does not move CPU physics automatically |
| MJX-JAX NVIDIA | No native Windows CUDA in current JAX support table; WSL2 experimental | Poor assumption for a locked/resetting cafe PC |
| MuJoCo Warp / GPU framework | Candidate requiring exact version/platform validation | New environment/backend integration, not a switch in the existing CLI |
| Full Isaac Sim + Isaac Lab | Windows 11 supported for compatible releases | No Ubuntu VM required, but OS/driver/storage/system settings still matter |
| Isaac Lab 3 Newton-only | Windows 11 supported; full Isaac Sim optional | Potential lean GPU experiment, still a new framework for this project |

Sources: [MuJoCo platforms](https://mujoco.readthedocs.io/en/stable/programming/index.html), [PyTorch Windows](https://pytorch.org/get-started/locally/), [JAX support table](https://docs.jax.dev/en/latest/installation.html), [MuJoCo Warp](https://mujoco.readthedocs.io/en/latest/mjwarp/index.html).

Current [Isaac Sim requirements](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/installation/requirements.html) list Windows 11,32 GB RAM,16 GB VRAM,50 GB SSD, with an RTX 4080-class minimum GPU. Training/sensors can require more. Stadium/Infinity meet the advertised memory/GPU class; the 8/12 GB seats are below that workstation baseline. This is not proof that every tiny headless task fails below16 GB. The requirement is also not a universal minimum for MuJoCo or Newton-only training.

[Isaac Lab 3 installation](https://isaac-sim.github.io/IsaacLab/release/3.0.0/source/isaaclab/installation.html) documents Windows 11/Python 3.12 and Newton without Isaac Sim. Its default CUDA 13 stack requires a suitable driver (Windows 580.88+); Windows setup includes elevated long-path configuration if not already enabled. Full Sim has its own release-specific tested drivers. Do not mix commands from different release families. Exact compatibility must be pinned before the visit; no blanket downgrade or driver change is proposed.

[Isaac Sim Python installation](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_python.html) supports a Python environment on Windows, with long-path considerations. Download permission is not equivalent to permission for driver/system changes. WSL enabling, Docker/virtualization or reboots can require staff administration. Do not bypass cafe restrictions.

The current C parity build explicitly supports macOS/Linux only; it is separate from RL and need not be forced onto Windows for a cafe training session. Existing CLI examples contain Mac paths, authorization/source hashes and strict guards: they are not ready-to-paste Windows launch commands. No Windows project execution was claimed here.

## 6. Reset-on-shutdown changes the economics

An ordinary Python virtual environment from macOS cannot be copied to Windows. Prepare a **Windows-specific** package cache/wheelhouse, source revision, model assets, configs, setup script and checksums on owner-controlled storage. Create/restore the Windows environment at the seat. A whole venv is not assumed relocatable. A VM image does not solve missing admin permission, GPU access or persistence.

For a 6 h visit, reserve 30 minutes for saving/verifying results. Illustrative remaining compute time is:

| Setup/cache restoration | Useful compute time | Stadium seat cost/useful hour | Cho Mo Private seat cost/useful hour |
| ---: | ---: | ---: | ---: |
| 0.5 h | 5 h | 19,800 VND | 8,800 VND |
| 1.5 h | 4 h | 24,750 VND | 11,000 VND |
| 3 h | 2.5 h | 39,600 VND | 17,600 VND |

These are scenarios, not measured installation durations. Add round-trip travel/parking to the total before dividing by useful time. One-off Isaac package downloads, asset/shader/kernel compilation and cache restoration may dominate a short visit; a staff-maintained persistent installation would materially improve this option.

Copy checkpoints, configs, logs and result manifests to owner storage **before** logout/shutdown; verify destination checksums while the seat is still active. Do not rely on local disk surviving. A source commit, policy checkpoint and normalization state alone may be insufficient for an exact mid-training resume: optimizer state, RNG, environment/progress and algorithm-specific state must also be accounted for. Save full evidence for any formal comparison.

Unattended runs while away need explicit seat/session arrangements; lock, sleep, reboot and account expiry behavior are unknown. Use minimal-access authentication, avoid persistent personal/cloud keys on the shared OS, and clear session authentication afterward. A private room does not make the shared software trusted. An external SSD protects persistence, not host access to mounted files.

## 7. Cafe versus cloud, using the same useful-work denominator

[Runpod's current displayed Pod prices](https://www.runpod.io/pricing), checked 20 October: RTX 4090 24 GB USD 0.89/h, RTX A5000 24 GB USD 0.27/h, RTX 3090 24 GB USD 0.50/h. These are advertised offers, subject to capacity/type; storage/tax and idle billed time are extra. GPU names alone do not establish equal CPU allocation or training throughput. For full Isaac rendering, choose a compatible RTX GPU, not an arbitrary datacenter accelerator.

For arithmetic only use **26,000 VND/USD, an explicit planning assumption, not a fetched exchange rate**. Cloud 4090 becomes 23,140 VND/h; A5000 becomes 7,020/h. A5000 is not assumed equal in performance to 4090. USD 50 buys about 56.18 advertised 4090 hours before extras; a budget ceiling is not a mandatory spend.

For 6 h Stadium, x3 cash-equivalent seat cost 99,000 VND. With 0.5 h restoration and 0.5 h export,5 h useful work costs 19,800/useful hour before travel. Five useful cloud 4090 hours cost 115,700 **if cloud setup/idle overhead is negligible**. The difference is only 16,700 VND: greater trip overhead removes the cash saving under these equal-throughput assumptions. At1.5 h cafe restoration,4 useful hours cost 99,000 versus92,560 cloud before cloud overhead.

General comparison:

$$
C_{\rm cafe/useful\ hour}=\frac{pT/3+C_{\rm travel}+C_{\rm other}}{T-S-E},
\qquad
C_{\rm cloud}=q_{\rm USD/h}X(T_{\rm useful}+S_{\rm cloud})+C_{\rm storage}.
$$

T is paid cafe duration, S setup, E export, X the chosen exchange-rate assumption. For equal experiment size, also divide each site's productive rate by measured end-to-end transitions/s: cheap hours are not necessarily cheap completed runs. Both cafe and cloud have setup costs.

If the owner studies productively during training, workspace comfort/privacy has real value and the cafe need not beat cloud on pure compute cost. Conversely, attending a seat solely to babysit an overnight job imposes human time costs absent from an unattended remote server. Do not count the same six hours as six hours of uninterrupted study AND six hours of setup-intensive experimentation.

## 8. Ranking by the owner's actual task

| Objective | First candidate | Reason / condition |
| --- | --- | --- |
| Learn mechanics, LQR, RL and inspect existing results | Mac; private cafe if workspace itself is valuable | Current model already runs locally |
| Private cafe morning with CPU research | Cho Mo Private | 44,000 per 6 h at x3;16 GB RAM/8 GB VRAM, suitable scope must fit |
| Need privacy and more than8 GB GPU memory | Investigate Infinity or a staff-assigned private high-memory machine | No cheaper confirmed private12 GB option in the provided evidence; do not assume Couple has one |
| Low-cost nonprivate MuJoCo pilot | Cho Mo VIP/Training | Select by actual CPU throughput, RAM and comfort, not gaming FPS |
| Full Isaac learning / visual sensor work | Cho Mo Stadium | 24 GB/64 GB; verify Windows 11 and compatible driver |
| Privacy plus24 GB | Investigate Infinity room isolation or ask staff for a suitable private workstation | No evidence Stadium itself is private; Infinity costs 198k per 6 h at x3 |
| Long scheduled training without giving up Mac | Lab machine | Exact GPU and access/persistence still unknown |
| Guaranteed long Linux campaign or urgent deadline | Rented cloud instance | Capacity/price not guaranteed until provisioned; use a spend limit |

Training Station and Premium list the same CPU/GPU/RAM but different prices; examine room/seat conditions before paying more. No measured speed ranking across these machines exists.

**Recommendation on scope:** keep the current MuJoCo reference and the 50/50 perception/control split. Learning Isaac for a bounded morning is legitimate, but a production backend migration changes physics/environment implementation and needs separate architecture approval and cross-checks. CAD-derived mass/inertia/joint data remain useful to either simulator; CAD completeness does not replace actuator/contact/state-interface validation. Do not use GPU access as the reason to restart the project in another engine.

## 9. One morning pilot, before a large deposit

This is a proposed procedure, not a claim it was executed. No OS install, hardware change or new policy training occurred in this analysis.

Before travel, confirm: x3 total balance and eligible zones/expiry; actual debit and per-seat/room basis; private-room assignment; Windows version, driver, free local SSD; permitted Python/AI install and long-path/admin support; whether external SSD/package caches and result export work. Ask whether staff can retain an Isaac environment. No need for Ubuntu unless the chosen backend requires it.

Choose **one** pilot: (A) private native-Windows MuJoCo study, or (B) Stadium Isaac/GPU compatibility. Do not spend the first morning setting up both frameworks plus WSL. Bring the matching Windows installers/wheels/assets, a public or sanitized source bundle, pinned revision/config, and independent result storage; preparing this kit is separate implementation work.

1. Start the actual application early; debug actual errors. Record hardware/versions and setup time. Read-only checks include `nvidia-smi` and `python -c "import mujoco; print(mujoco.__version__)"`; PyTorch GPU tests only for a matching installed stack.
2. For MuJoCo, load/render the intended model, reproduce an approved LQR trace, and use a separately authorized short optimizer smoke. For Isaac, launch its compatible example/viewer and a small stock training task before any WBR port.
3. After it runs, measure a fixed workload. CPU candidate counts 1/4/8; a new GPU backend could try 64/256/1024 environments only as a memory/throughput sweep, not a promise they fit. Distinguish parallel environments from independent training seeds. Keep the scientific recipe fixed for comparison; batch changes can change learning behavior.
4. Record total/steady-state transitions/s, setup/compile/update times, CPU/RAM/GPU/VRAM, logging/I/O, warnings/dropped trace records if applicable, and completed work. Retain logs/config/commit/version/hashes. GPU utilization alone is not a benchmark.
5. Export with at least 30 minutes remaining; reload a saved policy/result and verify hashes on the destination. Test reboot persistence only with staff consent after outputs are safe.

Proposed economic acceptance: restoration/export consume at most 1.5 h of a 6 h repeated visit, the actual selected workload completes, and its total cost is acceptable relative to lab/cloud. This threshold is a planning choice for owner/Claude review, not an existing experiment gate. If restoration repeatedly consumes much of the morning, use the cafe for workspace only or move campaigns to the lab/cloud.

Failure symptoms: permission prompt requiring unavailable staff access; CUDA architecture/driver mismatch; out-of-memory; missing assets; repeated cache rebuilds; reset erasing local state; CPU-bound job with idle GPU. Preserve the actual error; do not assume a faster GPU fixes it or bypass source/authorization checks.

## 10. Review record, reproducibility and next decision

Evidence labels: **MEASURED** applies only to existing repository experiments; **OWNER-REPORTED** to promotions, preferences and reset policy; **ADVERTISED** to cafe configurations; **CALCULATED** to economics; **PROPOSED/UNKNOWN** to workflow and untested compatibility. No benchmark extrapolation, cafe access guarantee or RL improvement is claimed.

Small source receipts and extracted advertised configurations: `~/wbr-evidence-archive/cafe-compute-review-20261020-01/`. `source-receipts.json` records retrieval provenance and original attachment hashes; `scope.json` limits this revision to Cho Mo and images 1–6. Historical out-of-scope fetches are retained, not used in the revised comparison. Original screenshots remain user attachments and were not added to git; raw Cho Mo HTML in `/private/tmp/wbr-oeg-chomo-20261020.html` is not durable. Extracted Cho Mo JSON is durable. Formulas/tables above allow arithmetic reproduction without external artifacts.

In-scope screenshot map:1=Cho Mo price overview;2=Stream popup;3=Stadium popup;4=Private popup;5=Premium popup;6=VIP popup. Conflicts are retained in Section3 rather than silently resolved.

Affected files: this review, one scoped session log and a documentation-log entry. Current runtime, protocol, model, dependencies, protected exercise and the other chat's CURRENT ownership are unchanged. Rollback: revert the documentation commit; no environment migration needs undoing. No new architectural decision is entered before approval.

Validation: inspect 6 in-scope attachments and decode the official Cho Mo page; inspect official compatibility/pricing references and existing experiment/code; independently recalculate revised tariffs, 6 h overhead and cloud examples; check relative Markdown links, excluded-branch removal and whitespace. Runtime tests are unnecessary for this documentation-only analysis; Windows/Isaac execution remains an explicitly proposed pilot. Publication receipts belong in the scoped session log.

### Claude review questions

1. Does the measured CPU workload justify keeping MuJoCo/Mac as the current baseline while treating cafe GPU use as a conditional pilot?
2. Are the proposed private/12 GB/Stadium choices and the promotion, tariff-conflict and reset caveats adequately separated?
3. Is the six-hour pilot and deposit restraint appropriate, and when would a GPU-backend/Isaac migration become justified?

### Recommendation awaiting review

Approve the analysis and a small Windows pilot **in principle**, conditional on staff confirmation and actual pricing. Do not approve a 500k–1m deposit, an Isaac migration or another training campaign from this document alone. Owner can choose the private-workspace pilot or the Stadium Isaac pilot after reviewing it. Keep the free lab resource ahead of paid long-running compute when access permits. Claude's response is pending.
