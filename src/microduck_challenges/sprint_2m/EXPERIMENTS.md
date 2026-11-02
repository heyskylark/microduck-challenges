# Sprint 2 m: experiment log

Every training run of this folder, with its hypothesis and the Arena evaluator's numbers for it
(`arena.workshop` evaluation of every checkpoint, run on this machine: indicative, not official).
**Score** = best mean time over 5 seeds at the best commanded vx; a fall or no finish costs 50 s.

How runs work: one change per run, on top of the best run so far. 2000 iterations, 4096 envs, seed 1,
local RTX 3090, a checkpoint every 100 iterations. The run name says the change. A run is judged by its
best checkpoint. A change that adds falls is not thrown out on that alone: speed and stability are tuned
together.

## Outcome

**4.800 s → 1.233 s, 5/5** locally (run0 → LX-both3000-s1, checkpoint 2900). Published: K2 1999, **1.412 s** on the
Space. The folder now holds LP-both's recipe (`env.py`, `rewards.py`) with a 3000-iteration `[recipe]` in
`challenge.toml`: K2's, plus the running head pulled forward and the trunk pulled to a 12° lean.

What the recipe changes against the folder as cloned, all kept by the runs below:

| Change | Where | Run | Gain when added |
|---|---|---|---|
| `lane_progress` = 10 · clip(v along the spawn heading, 0, 2)/2, whatever the command | `rewards.py`, `env.py` | A2, E3 | −1.9 s, then −0.23 s |
| `action_rate_l2` ramp capped at −0.3 (was −1.0 by 1500) | `env.py` curriculum | B2 | −0.73 s |
| Forward tracking one-sided: going faster than the command costs nothing | `rewards.py` `track_linear_velocity_at_least` | D1 | −0.28 s |
| Head: tolerance 0.5 → 1.0 rad, `head_pose_bias` faded out with speed; then at full speed pulled to neck −1.0 rad, head +0.5 rad from home | `rewards.py` head terms | B4, LP | −0.33 s; then −0.06 s (free) and −0.01 s more (target) |
| Trunk: forward-lean tolerance widened with speed (std² 0.05 → 1.0); then pulled to a 12° lean at speed | `rewards.py` `upright_lean` | B1, LP | −0.03 s; freedom alone unused; the target −0.03 s with the head target |
| Standing envs held at 2% (was ramped to 25%) | `env.py` curriculum | G3 | −0.05 s |
| Mirror-symmetry loss (`ENABLE_SYMMETRY`) | `env.py` | I2 | late checkpoints off the wall |
| `lane_drift` = 2 · exp(−v_across² / 0.15²) | `rewards.py`, `env.py` | I3 | late checkpoints off the wall |

Checkpoints to choose from (all local, indicative):

| Checkpoint | Score | Sweep | End y of the trace seed | Neighbours |
|---|---|---|---|---|
| **LX-both3000-s1 2900** (`2026-11-01_03-41-59_LX-both3000-s1`) | 1.233 s @1.10 | 1.21–1.41 s at all 21 vx | +0.08 m | every checkpoint from 200 is 5/5 |
| LX-both3000-s2 2900 (`2026-11-01_03-42-05_LX-both3000-s2`) | 1.263 s @0.55 | 1.24–1.32 s at all 21 vx | −0.01 m | every checkpoint from 200 is 5/5 |
| LP-both-s1 1999 (`2026-10-31_18-01-53_LP-both-s1`) | 1.334 s @0.75 | 1.31–1.41 s at all 21 vx | −0.27 m | every checkpoint from 200 is 5/5 |
| K2 1999 (`2026-10-30_20-27-50_K2-mirror-drift-s2`), published | 1.412 s @1.20 | 1.40–1.51 s at all 21 vx | −0.08 m | every checkpoint from 200 is 5/5 |

Simulations on another CPU drift apart after a few seconds; both LX 2900 checkpoints end within 0.08 m of
centre (0.32 m of margin to a wall).

What was learned (details per run below):
- The original ceiling was the reward's shape, not the robot: speed tracking is a bell curve around the
  command, which pays nothing for being far below it and charges for going above it.
- The smoothness ramp to −1.0 was the main brake once speed was paid for.
- Loosening a term the policy already pays for (rocking B3, running pose E4) does not change the gait.
- Pushes in training make the Arena runs more robust (F4: removing them made 9 of 20 checkpoints fall).
- Late checkpoints fail because the fast gaits drift sideways into the lane's wall, which training does
  not have (trace analysis, G batch). A tighter heading tolerance does not fix it (I1); the mirror loss
  and `lane_drift` do; a wall termination does too, at a cost of ~0.1 s (J batch).
- Fall penalties, γ 0.995 and progress weight 20 did not help (F1, F2, G1).

## Next: the gait batch (running) and what waits

### Head and trunk lean: what the faster entries do
Measured in the Arena's own race (trace forward kinematics, steady running, the first quarter skipped). Head lean
is the angle of the neck-base → head vector from vertical: 0° is straight up, 90° straight ahead.

| Policy | Board | Neck pitch (home 20°) | Head pitch (home 20°) | Head lean | Head ahead of trunk | Trunk pitch |
|---|---|---|---|---|---|---|
| run0 1500 | 4.80 s | 11° | 26° | −12° | 0.8 cm | 0.5° |
| **K2 1999** | 1.41 s | −3° | 49° | **13°** | 4.5 cm | 0.7° |
| K4 1999 | 1.36 s | 3° | 52° | 10° | 4.2 cm | 2.6° |
| RhodWeo | 1.01 s | −35° | 56° | 58° | 9.4 cm | 11.6° |
| azukiq | 1.02 s | −52° | 50° | **81°** | 10.6 cm | 17.8° |
| almuli | 1.09 s | −46° | 6° | 41° | 8.2 cm | 1.6° |
| TheSauceman | 1.17 s | −39° | 14° | 32° | 6.9 cm | −2.2° |
| ctcheung | 1.21 s | −18° | 44° | 30° | 7.0 cm | 4.1° |
| RemiFabre | 1.24 s | −4° | 35° | 9° | 4.0 cm | 1.2° |
| wwkkkoo | 1.30 s | −61° | −44° | 31° | 6.3 cm | −0.2° |

Every entry faster than 1.2 s carries its head 30–81° forward. K2 tips the neck 23° forward and the head
29° back, which keeps the head nearly upright. What prices the lean in K2:
- `head_pose_tracking` pays K2 1.46 of 2.0 even at its upright head. Azukiq's neck/head pose would cost
  ~0.52/s at the running tolerance (σh 1.0) and ~0.83/s below 0.8 m/s (σh 0.5).
- `upright` charges a 17.8° forward trunk 0.53/s at σf² 0.3.
- The neck's joint range allows 90° forward of zero (110° from home), so the joint limits do not block it.

### L: head and trunk lean, a 2×2 on K2's recipe
K1/K2 are the baseline cell (seeds 1 and 2). g is the speed gate (0 below 0.3 m/s down the lane, 1 above 0.8).

| Cell | Change | Reward |
|---|---|---|
| L-H (head) | `head_pose_tracking` free at full speed | (1 − g)·mean_j e^{−(e_j/0.5)²} + g·1 (was σh 0.5 → 1.0 with g) |
| L-T (trunk) | `upright` forward-lean tolerance wider at speed | σf² = 0.05 + g·(1.0 − 0.05) (was up to 0.3) |
| L-HT | both | |

| Batch | Runs | Commits |
|---|---|---|
| L1 (done) | LH-headfree-s1 · LT-lean10-s1 · LHT-headfree-lean10-s1 · LHT-headfree-lean10-s2 | 5172e1a · 185ad84 · 19ea1e9 |
| L2 (done) | LH-headfree-s2 · LT-lean10-s2 · LP-headtarget-s1 · LP-trunktarget-s1 | 35edfa0 · e43d9d1 · 2a2f840 · e8b8e71 |
| L3 (done) | LP-both-s1 · LP-both-s2 · LP-headtarget-s2 · LP-trunktarget-s2 | ef41a22 · 6e4fc4a · c594e01 |

L1 results (baseline cell: K1 1.463 s, K2 1.412 s; head lean 13°, trunk 1°):

| Run | Best | 5/5 among 1000–1999 | Head lean from 1000 on | Trunk pitch | Sweep of the best |
|---|---|---|---|---|---|
| LH s1 (head free) | **1.368 s** @1900 | 10 of 10 (every one from 200) | 24–41° | −3 to 0° | 1.36–1.42 s at all 21 vx |
| LT s1 (lean σf² 1.0) | 1.451 s @1900 | 10 of 10 | 7–12° | 0–3° | 1.45–1.52 s |
| LHT s1 (both) | **1.364 s** @1700 | 8 of 10 (1500, 1900 4/5) | 26–36° | −1 to 2° | 1.35–1.41 s |
| LHT s2 (both) | 1.383 s @1500 | 10 of 10 | 24–31° | −1 to 1° | 1.37–1.44 s |

- **Freeing the head works**: the head leans 24–41° (K2 13°) and all three head-free runs beat K2 by 0.03–0.05 s
  and K1 by ~0.1 s, with every late checkpoint but two 5/5. Not the 58–81° of the 1.0 s entries, though.
- **Freeing the trunk does nothing**: the trunk stays at 0–3° with σf² 1.0, alone (1.451 s ≈ K1) or with the head
  free (where the head's forward lean makes the trunk sit slightly back). The lean was not taxed away; the
  policy just does not use it.
- So L2 swaps the planned conditional for **targets** on L-HT: the head pulled to the 1.0 s entries' pose (neck
  −1.0 rad, head +0.5 rad from home, σ 0.5 at speed), and the trunk pulled to 12° forward (std² 0.05 short of
  the target at speed). One seed each; LH and LT get their second seeds.

L2 results:

| Run | Best | 5/5 among 200–1999 | Head lean from 1000 on | Trunk pitch |
|---|---|---|---|---|
| LH s2 (head free) | 1.381 s @1900 | 18 of 18 | 29–36° | −2 to 1° |
| LT s2 (lean σf² 1.0) | 1.469 s @1900 | 18 of 18 | 8–17° | −1 to 2° |
| **LP-head s1** (head pulled to neck −1.0, head +0.5 rad) | **1.350 s** @1999 | **19 of 19** | **36–47°** | −1 to 0° |
| LP-trunk s1 (trunk pulled to 12°) | 1.357 s @1999 | 18 of 19 (700 4/5) | 12–19° | **11–14°** |

The 2×2 on two seeds each (means): baseline (K1, K2) 1.438 s · H 1.375 s · T 1.460 s · H+T 1.374 s. Freeing the head
is worth −0.06 s; freeing the trunk 0; they do not interact.

Targets get the lean that freedom did not: the head target 36–47° (free: 24–41°), the trunk target 12–14° (free:
0–3°). Both are the fastest runs of the log, one seed each, still improving at 1999 (LP-head 1.40 → 1.35 over its
last 500 iterations). With the trunk pulled forward the head leans less (12–19°): the trunk takes over part of
the head's job. Next (L3): both targets together on two seeds, and each target's second seed.

L3 results, and the targets' grid on two seeds (each target on the L-HT base: head free, σf² 1.0):

| Cell | Seed 1 | Seed 2 | Mean | Head lean (late) | Trunk pitch (late) | 5/5 among 200–1999 |
|---|---|---|---|---|---|---|
| L-HT (no target) | 1.364 | 1.383 | 1.374 s | 24–36° | −1 to 2° | 17 + 18 of 18 |
| head target | 1.350 | 1.375 | 1.363 s | 36–48° | −3 to 0° | 19 + 18 of 19 |
| trunk target | 1.357 | 1.380 | 1.369 s | 14–24° | 11–14° | 18 + 19 of 19 |
| **both targets** | **1.334** | **1.348** | **1.341 s** | **39–57°** | **8–12°** | **19 + 19 of 19** |

- Both targets together beat either alone on each seed (s1: 1.334 vs 1.350/1.357; s2: 1.348 vs 1.375/1.380), and
  are the only cell 5/5 at every checkpoint from 200 on both seeds. −0.03 s on L-HT, −0.10 s on K2's recipe.
- Each target alone is within seed noise of L-HT; together they add up to more than either.
- Every L3 run is still improving at 1999 (LP-both-s1: 1.41 → 1.33 over its last 500 iterations): a longer run
  is the obvious next test.
- Still short of the 1.0–1.1 s entries' 58–81° head and 12–18° trunk: head lean is 39–57° with the target at the
  pose of those entries' joints, because the head target's σ (0.5 rad) leaves room.

### LX: LP-both for 3000 iterations (commit 789ffc5)
| Run | Best | At 1999 | At 2900 | Head lean (late) | Trunk pitch (late) | 5/5 among 200–2999 |
|---|---|---|---|---|---|---|
| LX s1 | **1.233 s** @2900 | 1.34 s | 1.23 s | 41–53° | 10–13° | 29 of 29 |
| LX s2 | 1.263 s @2900 | 1.34 s | 1.26 s | 38–56° | 10–15° | 29 of 29 |

−0.10 and −0.09 s over the 2000-iteration runs. Both best checkpoints finish at all 21 vx (1.21–1.41 s and
1.24–1.32 s) and end within 0.08 m of centre. The gain is flattening by 2500–2900, and the lean does not grow
with the extra iterations. The recipe is now 3000 iterations.

### LY: pushing the lean further, on LX, two seeds each (commits 4a67c0d, 06cee95)
| Cell | Seed 1 | Seed 2 | Mean | Head lean (late) | Trunk pitch (late) |
|---|---|---|---|---|---|
| LX (target 12°, head σ 0.5) | **1.233** | **1.263** | **1.248 s** | 38–56° | 10–15° |
| trunk target 18° | 1.281 | 1.285 | 1.283 s | 45–64° | 17–22° |
| head target σ 0.3 rad | 1.267 | 1.280 | 1.274 s | 42–64° | 9–14° |

- Refuted on both seeds: each push gets its lean (the trunk at 17–22°, the head reaching 60–64° at times), and
  costs 0.02–0.05 s. Every checkpoint of all four stays 5/5.
- Both learn more slowly (at 1400: 1.53–1.66 s against LX's 1.44–1.49) and never catch up.
- So LX's posture (head ~45°, trunk ~11°) is about where this recipe is fastest; the 1.0–1.1 s entries' extra
  lean is not what makes them faster here. The recipe stays LX.

Judged on the score, on the share of checkpoints from 1000 on that are 5/5, and on the head lean and trunk pitch
per checkpoint (`report.py` now prints both from the Arena trace).

Evaluation note: with four trainings on the GPU (23.8 GB of 24.5), the evaluator's ONNX export ran out of GPU
memory; it now runs with `CUDA_VISIBLE_DEVICES=` (export and race on the CPU). Arena 0.7.0 (from the upstream
merge) re-scored every stored checkpoint; the scores match the 0.5.1 ones (K2 1999: 1.412 s).

### The gait batch: head, switching, rocking, speed cap (commits 97a47d8, bacd8a0, a519324, 0b7f5c1, c0287c8)
What the sub-1 s entries do that LX does not, measured in the Arena's race on unseen seeds 6–10 (lookup
entries fall back to their network there) at each entry's scored vx, the policy's actions recorded next to the
trace (`logs/analysis/gait.py`; steady part from 0.3 s):

| Policy | Time | Steady speed | Neck / head from home | Head lean | Trunk roll σ (p5–p95) | Σ(Δa)² per step | Leg error past the current limit | Leg joint speed |
|---|---|---|---|---|---|---|---|---|
| sudhirmts | 0.906 s | 2.32 m/s | −84° / −8° | 78° | 16.0° (50°) | 24.3 | 80% | 7.4 rad/s |
| dadudu (fallback) | 0.936 s | 2.23 m/s | −81° / −12° | 71° | 15.4° (47°) | 24.0 | 80% | 7.1 rad/s |
| namenu | 0.948 s | 2.17 m/s | −63° / +19° | 64° | 21.7° (66°) | 24.6 | 82% | 7.2 rad/s |
| Arcod | 1.000 s | 2.11 m/s | −89° / −5° | 69° | 33.2° (104°) | 16.9 | 78% | 6.8 rad/s |
| bat-cha | 1.087 s | 1.99 m/s | −57° / +33° | 55° | 9.6° (28°) | 10.3 | 83% | 7.7 rad/s |
| almuli | 1.099 s | 1.89 m/s | −71° / −19° | 42° | 10.0° (31°) | 20.1 | 78% | 7.2 rad/s |
| **LX s1** | 1.238 s | 1.77 m/s | −52° / +34° | 56° | 4.1° (12°) | 5.3 | 76% | 7.8 rad/s |
| LX s2 | 1.262 s | 1.67 m/s | −47° / +31° | 49° | 4.5° (15°) | 4.7 | 76% | 7.8 rad/s |

- **Head**: LX sits on its target (neck −1.0, head +0.5 rad = −57°/+29°); the fastest run the neck 81–89° down with
  the head in line. LY tightened the tolerance around the old target; the target itself never moved.
- **Legs**: the servo is current-limited once the target is ≥ 1.16 rad from the joint (`arena/actuator.py`), and
  every policy sits there 66–87% of the time at the same joint speed. What differs is how hard the targets
  switch: Σ(Δa)² 17–25 against LX's 5 (−7.3/step against −1.6 at the −0.3 cap).
- **Rocking**: the trunk rolls once per stride (roll frequency = stride frequency), 15–33° σ against LX's 4°.
  `upright` (std² 0.05) keeps 0.49 of itself at sudhirmts's roll, 0.91 at LX's; `body_ang_vel` costs ≈ −2.7/step
  against −0.3. (`track_angular_velocity`'s roll/pitch part already pays ~0 at speed: B3 loosened it for nothing.)
- **Speed cap**: the fastest run 2.1–2.3 m/s steady; `lane_progress` pays nothing above v_ref 2.0.

One change each on LX (f516666), 3000 iterations; seed 1 first (four fit the GPU at 5.7 GB each, V waits for a
slot), then seed 2 of all five.

| ID | Change | Commit |
|---|---|---|
| H | running head target neck −1.0 → −1.45 rad, head +0.5 → 0 | 97a47d8 |
| A | `action_rate_l2` held at −0.1 (no ramp to −0.3) | bacd8a0 |
| W1 | `upright` roll std² 0.05 → 0.5 with speed (new `roll_std` in `upright_lean`) | a519324 |
| W2 | `body_ang_vel` −0.05 → −0.01 | 0b7f5c1 |
| V | `lane_progress` v_ref 2.0 → 3.0 m/s, weight 10 → 15 (same pay per m/s) | c0287c8 |

Doubts, before running: B2 showed the action-rate ramp was the main brake, so A has history behind it; B3 showed
freeing a rocking tax can leave the gait unchanged, which W1/W2 may repeat; V does not bind until a run passes
2.0 m/s steady (LX: 1.77).

### Waiting: M1/M2, on hold
| ID | Change | Hypothesis |
|---|---|---|
| M1 | pacer: r = clip(v_lane − pace, 0, 0.3)/0.3, w 2; pace = never-decreasing EMA (α 0.01/step) of the 75th percentile of v_lane over walking envs past their first second | Pay concentrated at the current frontier |
| M2 | rank: r = percentile of v_lane among walking envs past their first second, w 3 | The same, scale-free |

Doubts, written down before running:
- `lane_progress` is already linear (no dead zone), and F2 showed that more speed pressure alone trades away
  balance. M1 and M2 differ in paying the frontier rather than speed in general; a small gain at best.
- **Adaptive command curriculum: not planned.** K2's sweep is flat (1.40–1.51 s at every vx): the policy ignores
  the command. One-sided tracking pays fully for any speed at or above the command, and the policy already
  runs faster than 1.2 m/s. A curriculum would raise the command range past 1.2, which the Arena never sends.
- **PBT: deferred.** It would be 4 members (what the 3090 runs at once), exploiting by Arena score every ~400
  iterations by copying the best member into the worst with perturbed weights (progress, σh, action-rate
  cap). Its target is the seed spread (K1 1.463 vs K2 1.412). It needs resume plumbing (curricula restart
  on warm start), a few times the engineering of an ablation.

## Summary

| Run | Commit | Change | Best checkpoint | Score | Finishes | vx | vs. best before |
|---|---|---|---|---|---|---|---|
| run0 | 9aaec6d | default knobs (3000 iterations) | 1500 | 4.800 s | 5/5 | 0.50 | (baseline) |
| A1-fwd4 | 7a33a51 | `forward_reward` 2 → 4 | 700 | 2.802 s | 5/5 | 0.80 | −2.00 s vs run0 |
| A2-progress | 368ffa2 | + `lane_progress` (w 5, v_ref 2.0), forward back at 2 | 700 | 2.882 s | 5/5 | 0.90 | −1.92 s vs run0; more robust than A1 |
| **B2-rate03** | 37d71dd | A2 + `action_rate_l2` ramp capped at −0.3 | 1999 | **2.156 s** | 5/5 | 1.20 | −0.73 s vs A2; finishes at every vx |
| B3-rock | dc198f3 | B2 + roll/pitch rate tolerance std² 0.5 → 1.5 | 1999 | 2.203 s | 5/5 | 1.20 | +0.05 s vs B2: no gain, dropped |
| A3-nofwdtrack | 2540a2a | A2 + `track_linear_velocity` without vx | 1000 (stopped) | 5.022 s | 5/5 | 0.70 | +2.14 s vs A2: refuted |
| B1-lean | 18905d7 | B2 + forward lean allowed with speed | 1900 | 2.124 s | 5/5 | 1.20 | −0.03 s vs B2: small, kept |
| **B4-head** | 5f6d00f | B2 + head freed at speed | 1900 | **1.824 s** | 5/5 | 1.20 | −0.33 s vs B2 |
| D1-atleast | 9870cb4 | B2 + forward tracking one-sided (no cap above the command) | 1999 | 1.874 s | 5/5 | 1.20 | −0.28 s vs B2 |
| E1-combo | 14a07a0 | B2 + D1 + B1, 3000 iterations | 2600 | 1.871 s | 5/5 | 1.20 | = D1: B1 adds nothing on D1, flat from 1500 |
| E2-stack-s1 | c8deff2 | B2 + D1 + B1 + B4 (seed 1) | 1600 | 1.744 s | 5/5 | 1.20 | −0.08 s vs B4 |
| E2-stack-s2 | c8deff2 | same, seed 2 | 1500 | 1.708 s | 5/5 | 1.20 | replicates E2 (1.71–1.74) |
| **E3-prog10** | 263f189 | E2 + `lane_progress` weight 5 → 10 | 1800 | **1.494 s** | 5/5 | 0.85 | −0.23 s vs E2; ~1.5 s at every vx |
| E4-runpose | 5bc6ec8 | E2 + `pose` running tolerance from 0.6 m/s | 1999 | 1.771 s | 5/5 | 1.20 | = E2 (within seed noise): dropped |
| F1-fallpen | 847a889 | E3 + `is_terminated` −250 (fall penalty) | 1100 | 1.531 s | 5/5 | 1.20 | = E3; 5/5 to 1100, then unstable |
| F2-prog20 | 1fa4af8 | E3 + `lane_progress` weight 10 → 20 | 800 | 1.504 s | 5/5 | 0.60 | = E3; collapses after 800 |
| F3-e3-s2 | 77d3ff3 | E3, seed 2 | 1000 | 1.483 s | 5/5 | 1.15 | replicates E3 (1.48–1.49) |
| **F4-nopush** | cd446bf | E3 + pushes off | 1400 | **1.464 s** | 5/5 | 1.05 | −0.03 s vs E3, but 9 of 20 checkpoints fall |
| G1-prog20-fallpen | 9901f67 | F2 + F1 (progress 20 + fall penalty) | 800 | 1.509 s | 5/5 | 0.85 | = F2: the penalty does not tame progress 20 |
| G2-com5 | 350496a | E3 + CoM randomization capped at ±5 mm | 1200 | 1.521 s | 5/5 | 0.80 | = E3: dropped |
| **G3-stand2** | 4087290 | E3 + standing envs held at 2% | 1300 | **1.438 s** | 5/5 | 1.05 | −0.05 s vs E3; 1.41–1.47 s at every vx |
| G4-com5-stand2 | 274fc1b | E3 + G2 + G3 (both, on purpose) | 1200 | 1.440 s | 5/5 | 0.45 | = G3 |
| H1, H2, H4 | c0142ed, d840bfa, b7fe5da | G3 + fall penalty −1000 / γ 0.995 / fall penalty −250 | stopped < 100 | | | | premise refuted (see below) |
| H3-g3-s2 | 6045e42 | G3, seed 2 | 1700 | 1.428 s | 5/5 | 1.10 | replicates G3's speed; 9 of 11 checkpoints from 1000 fall |
| I1-heading015 | 37cc525 | G3 + `heading_hold` std 0.4 → 0.15 rad | 1100 | 1.497 s | 5/5 | 0.95 | no gain; still drifts to the wall |
| **I2-mirror** | 0fff47a | G3 + mirror-symmetry loss | 1999 | **1.416 s** | 5/5 | 0.75 | −0.02 s vs G3; 7 of 11 late checkpoints 5/5 |
| **I3-lanedrift** | 4b29b33 | G3 + `lane_drift` (sideways speed across the lane) | 1800 | **1.424 s** | 5/5 | 1.05 | −0.01 s vs G3; 9 of 11 late checkpoints 5/5 |
| J1-wall | aa1ea89 | G3 + `lane_wall` termination (0.3 m, first 2.5 m) | 1500 | 1.527 s | 5/5 | 1.20 | +0.09 s vs G3, but 10 of 11 late checkpoints 5/5 |
| J2-drift-wall | 32984ef | I3 + `lane_wall` | 1000 (stopped) | 3.77 s | 5/5 | 0.30 | refuted: 0/5 at every checkpoint to 600, 3.77 s at 1000 |
| J3-mirror-wall | 13d0ccd | I2 + `lane_wall` | 1900 | 1.578 s | 5/5 | 1.15 | slowest of the batch, but 5/5 at every checkpoint from 100 |
| J4-wall-s2 | 05ecd5b | J1, seed 2 | 1999 | 1.492 s | 5/5 | 1.20 | 11 of 11 late checkpoints 5/5 |
| K1-mirror-drift | aded45a | I2 + I3 (mirror loss + lane_drift, on purpose) | 1999 | 1.463 s | 5/5 | 1.05 | 5/5 at every checkpoint from 200 |
| **K2-mirror-drift-s2** | dfd67e0 | K1, seed 2 | 1999 | **1.412 s** | 5/5 | 1.20 | 5/5 at every checkpoint from 200; **recommended** |
| K3-lanedrift-s2 | 8fcf5e9 | I3, seed 2 | 1900 | 1.489 s | 5/5 | 0.60 | 2 of 19 checkpoints from 200 fall |
| **K4-mirror-s2** | d604aec | I2, seed 2 | 1999 | **1.359 s** | 5/5 | 0.65 | fastest, but ends 0.25 m off centre; 1800 is 3/5 |
| LH-headfree-s1 | 5172e1a | K2 + head free at full speed | 1900 | 1.368 s | 5/5 | 0.90 | −0.04 s vs K2; head 24–41° |
| LT-lean10-s1 | 185ad84 | K2 + forward-lean σf² 0.3 → 1.0 | 1900 | 1.451 s | 5/5 | 1.20 | ≈ K1: trunk stays at 0–3° |
| **LHT-headfree-lean10-s1** | 19ea1e9 | K2 + both | 1700 | **1.364 s** | 5/5 | 1.10 | −0.05 s vs K2; 1500, 1900 4/5 |
| LHT-headfree-lean10-s2 | 19ea1e9 | same, seed 2 | 1500 | 1.383 s | 5/5 | 1.20 | every checkpoint from 300 5/5 |
| LH-headfree-s2 | 35edfa0 | LH, seed 2 | 1900 | 1.381 s | 5/5 | 0.30 | replicates LH (1.37–1.38) |
| LT-lean10-s2 | e43d9d1 | LT, seed 2 | 1900 | 1.469 s | 5/5 | 0.95 | replicates LT: no gain |
| **LP-headtarget-s1** | 2a2f840 | LHT + running head pulled to neck −1.0, head +0.5 rad | 1999 | **1.350 s** | 5/5 | 1.20 | −0.06 s vs K2; head 36–47°; 19/19 5/5 |
| LP-trunktarget-s1 | e8b8e71 | LHT + trunk pulled to 12° forward at speed | 1999 | 1.357 s | 5/5 | 1.20 | trunk 12–14°, head 12–19° |
| **LP-both-s1** | ef41a22 | head target + trunk target | 1999 | **1.334 s** | 5/5 | 0.75 | −0.08 s vs K2; best of the log; 19/19 5/5 |
| LP-both-s2 | ef41a22 | same, seed 2 | 1999 | 1.348 s | 5/5 | 1.10 | 19/19 5/5; head 39–57°, trunk 8–11° |
| LP-headtarget-s2 | 6e4fc4a | LP-head, seed 2 | 1999 | 1.375 s | 5/5 | 0.80 | head 38–48° |
| LP-trunktarget-s2 | c594e01 | LP-trunk, seed 2 | 1999 | 1.380 s | 5/5 | 1.10 | trunk 11–13° |
| **LX-both3000-s1** | 789ffc5 | LP-both, 3000 iterations | 2900 | **1.233 s** | 5/5 | 1.10 | −0.10 s vs LP-both-s1; 29/29 from 200 5/5 |
| LX-both3000-s2 | 789ffc5 | same, seed 2 | 2900 | 1.263 s | 5/5 | 0.55 | −0.09 s vs LP-both-s2; 29/29 from 200 5/5 |
| LY-trunk18-s1 | 4a67c0d | LX + trunk lean target 12° → 18° | 2800 | 1.281 s | 5/5 | 1.05 | +0.05 s vs LX-s1; trunk 17–22°, head 45–63° |
| LY-trunk18-s2 | 4a67c0d | same, seed 2 | 2800 | 1.285 s | 5/5 | 1.20 | +0.02 s vs LX-s2: refuted |
| LY-headtight-s1 | 06cee95 | LX + running head target σ 0.5 → 0.3 rad | 2900 | 1.267 s | 5/5 | 0.60 | +0.03 s vs LX-s1; head 42–60° |
| LY-headtight-s2 | 06cee95 | same, seed 2 | 2900 | 1.280 s | 5/5 | 1.20 | +0.02 s vs LX-s2: refuted |

Pollen reference: 4.883 s at 0.55 m/s.

## Runs

### run0: baseline (commit 9aaec6d)
- **Setup**: default `challenge.toml` (forward 2, upright 2, step 3), 3000 iterations, a checkpoint every 250.
- **Score per checkpoint**: 500 9.73 · 750 5.54 · 1000 4.91 · 1250 4.96 · **1500 4.80** · 1750 15.13 (4/5) ·
  2000 5.22 · 2250 5.24 · 2500 5.24 · 2750 4.84 · 2999 5.01.
- **Sweep of checkpoint 1500**: 0.45–0.60 m/s finish in 4.8–5.1 s; 0.70 m/s takes 39 s; every vx ≥ 0.75
  times out after 0.5–1.9 m.
- **Curves at the end**: episode length 968/1000, fell_over 0.27, air time 0.127 s, peak foot height 15 mm.
  `action_rate_l2` is the biggest term (−0.94/s, against +0.83/s for `track_linear_velocity`).
- **Reading**: speed tracking is a bell curve with std² 0.1. Commands far above what the robot can do pay
  about 0, so nothing pushes it faster. The ceiling is the reward shape, not the robot.

### A1-fwd4: forward_reward 2 → 4 (commit 7a33a51)
- **Hypothesis**: doubling the speed-tracking weight against the other terms lifts the best vx above 0.6 m/s.
- **Score per checkpoint**: 400 3.39 · 500 31.2 (2/5) · 600 31.2 (2/5) · **700 2.80** · 800 40.6 (1/5) ·
  900 2.88 · 1000 2.85 · 1100 12.5 (4/5) · 1200 3.00 · 1300 3.15 · 1400 3.66 · 1500 3.25 · 1600–1999 3.29–3.38.
- **Sweep of checkpoint 700**: finishes only at 0.25–0.35 m/s (5.5–7.8 s) and **0.70–0.90 m/s (2.77–2.94 s)**.
  It falls at 0.40–0.65 and at 0.95–1.15 m/s. Fast but brittle: it holds one fast gait in a narrow band.
- **Curves at the end**: fell_over 0.29, air time 0.115 s, peak foot height 14 mm, `action_rate_l2` −1.53/s.
- **Reading**: confirmed. The knob alone took 2 s off. The best checkpoint is early (700), and the score
  worsens from 1000 on while the `action_rate_l2` ramp tightens (−0.4 at 750 to −1.0 at 1500).

### A2-progress: + lane_progress (commit 368ffa2)
- **Hypothesis**: paying for speed down the lane whatever the command (`5 · clip(v_lane, 0, 2)/2`) removes the
  dead zone of the tracking bell curve and lifts the best vx.
- **Score per checkpoint**: 300 4.05 · 400 12.7 (4/5) · 500 2.94 · 600 3.22 · **700 2.88** · 800 2.95 · 900 3.00 ·
  1000 2.94 · 1100 3.12 · 1200 3.20 · 1300 3.26 · 1400 3.47 · 1500 3.30 · 1600–1900 3.41–3.55 · 1999 5.15.
- **Sweep of checkpoint 700**: **every vx from 0.60 to 1.20 m/s finishes in 2.89–3.27 s**. It also finishes at
  0.20–0.45 except 0.35, and falls at 0.35, 0.50 and 0.55. From 0.85 m/s up the time hardly changes with the command: the
  policy runs at its own pace.
- **Curves at the end**: fell_over 0.19 (the lowest so far), peak foot height 18–20 mm, `lane_progress` peaks
  at 1.09/s around iteration 1000 then drops to 0.87 by 1999.
- **Reading**: confirmed. The score matches A1's, but there are 4/5 checkpoints from 500 on and a gait that holds at
  every high command, so A2 is the base to stack on. Like A1, it slows from 1000 on: average lane speed falls
  while `action_rate_l2` tightens. Next: B2 (cap that ramp) and A3 (drop vx tracking), in parallel.

### A3-nofwdtrack: track_linear_velocity without vx (commit 2540a2a), stopped at 1000
- **Hypothesis**: on A2, dropping the forward part of speed tracking removes the command's cap on speed, so
  every env runs at full pace.
- **Score per checkpoint**: 0–300 50 (0/5) · 400 23.3 · 500 50 (0/5) · 600 25.2 · 700 8.87 · 800 9.45 · 900 5.62 ·
  **1000 5.02**. A2 at the same checkpoints: 2.94–3.22.
- **Curves at 1000**: `lane_progress` 0.65/s (A2: 1.09/s), so it is slower in training too. `track_linear_velocity`
  without vx pays 1.56 of 2.0 for nearly nothing.
- **Reading**: refuted, and stopped at 1000 to free the GPU. The bell curve around the command was the
  strongest "go" signal: near a command it pays about 2·2·err/0.1 per m/s, against lane_progress's flat
  2.5 per m/s. Ignoring the command needs a stronger progress term. To retest only if progress weight ≥ 10
  turns out to be worth it.

### B2-rate03: action_rate_l2 ramp capped at −0.3 (commit 37d71dd)
- **Hypothesis**: on A2, stopping the smoothness ramp at −0.3 (instead of −1.0 by 1500) keeps the speed A1 and
  A2 lost from 1000 on.
- **Score per checkpoint**: 400 3.17 · 500 2.94 · 600 2.83 · 700 2.79 · 800 2.81 · 900 2.77 · 1000 2.66 · 1100 2.67 ·
  1200 2.52 · 1300 2.65 · 1400 2.40 · 1500 2.35 · 1600 2.44 · 1700 2.33 · 1800 2.27 · 1900 2.26 · **1999 2.16**.
  Every checkpoint from 200 on is 5/5.
- **Sweep of checkpoint 1999**: **every vx from 0.20 to 1.20 finishes, and the time falls steadily with vx**:
  0.20 6.42 · 0.50 3.10 · 0.80 2.43 · 1.00 2.23 · 1.15 2.15 · 1.20 2.15. It tracks the command, all the way up
  to the top of the range.
- **Curves at the end**: fell_over 0.30, air time 0.118 s, peak foot height 23 mm (A2: 18), `air_time` 1.41/s
  (A2: 1.16), `lane_progress` 1.13/s and still rising.
- **Reading**: confirmed, the biggest gain so far. Smoothness at −1.0 was the brake: the gait now keeps getting
  faster until the last checkpoint, so it has not converged at 2000. It is fastest at the highest command,
  1.2 m/s, which means **the command's ceiling is now the limit**: the tracking bell curve also charges for
  going faster than 1.2. Two ideas follow. (1) One-sided tracking, charging only for falling short of the
  command, which keeps its strong pull and loses its cap (D1). (2) Training longer.

### B1-lean: forward lean allowed at speed (commit 18905d7)
- **Hypothesis**: on B2, widening `upright`'s tolerance for a forward lean (std² 0.05 → 0.3 as lane speed goes
  0.3 → 0.8 m/s; roll and backward lean unchanged) lets the robot lean into the run and stride faster.
- **Score per checkpoint**: 500 2.91 · 700 2.80 · 900 2.72 · 1100 2.73 · 1200 2.61 · 1300 2.48 · 1400 2.41 · 1500 2.31 ·
  1600 2.20 · 1700 2.24 · 1800 2.18 · **1900 2.12** · 1999 2.14. B2 from 1600 on: 2.44 · 2.33 · 2.27 · 2.26 · 2.16.
- **Sweep of checkpoint 1900**: finishes at every vx and gets faster with vx, as B2 does, about 0.05–0.1 s quicker at
  each vx below 1.0 (0.50: 2.91 against 3.10).
- **Curves at the end**: fell_over 0.34 (B2 0.30), `upright` 1.74 (unchanged: the lean it buys is now free),
  `pose` 0.36 (B2 0.40: bigger strides), peak foot height 23 mm.
- **Reading**: a small gain, ahead of B2 at each of the last five checkpoints, so kept; with one seed it
  is within noise. It does not add falls in the Arena.

### B3-rock: roll/pitch rates loosened (commit dc198f3)
- **Hypothesis**: on B2, a separate, looser tolerance for roll/pitch rotation speed (std² 0.5 → 1.5, yaw kept at
  0.5) stops taxing each stride's rocking and frees a faster gait.
- **Score per checkpoint**: tracks B2 checkpoint for checkpoint, 0.05–0.1 s behind until 1300, then level:
  1500 2.33 · 1700 2.26 · 1800 2.23 · 1900 2.22 · **1999 2.20** (B2 1999: 2.16).
- **Curves at the end**: `track_angular_velocity` 0.74 (B2 0.44): the term pays more, but the gait is the same
  (air time, foot height, lane_progress all match B2).
- **Reading**: no gain, dropped. The rocking tax was not what held speed back; the policy just collects the
  freed reward.

### D1-atleast: one-sided forward tracking (commit 9870cb4)
- **Hypothesis**: on B2, charging only for falling short of the forward command (`max(cmd_x − v_x, 0)` in the bell
  curve) keeps tracking's strong pull without its cap at 1.2 m/s.
- **Score per checkpoint**: 800 2.39 · 900 2.30 · 1000 2.16 · 1100 11.8 (4/5) · 1200 2.05 · 1300 2.04 · 1400 1.94 ·
  1500 1.89 · 1600 1.93 · 1700 2.00 · 1800 1.91 · 1900 1.92 · **1999 1.87**.
- **Sweep of checkpoint 1999**: 1.87–2.35 s at every vx from 0.25 to 1.20, so it runs near full speed whatever the
  command; it falls only at 0.20. 0.80 m/s takes 2.55 s, an outlier.
- **Curves at the end**: `lane_progress` 1.35/s (B2 1.13), peak foot height 28 mm (B2 23), `pose` 0.24 (B2 0.40),
  fell_over 0.40 (B2 0.30).
- **Reading**: confirmed. With no cap above the command, the policy settles on one fast gait. It strides
  further from the home pose (`pose` keeps dropping), which suggests `pose` is now one of the brakes (E4). It falls
  a bit more in training, but finishes 5/5 at 20 of the 21 commands in the Arena.

### B4-head: head freed at speed (commit 5f6d00f)
- **Hypothesis**: on B2, widening the head's tolerance (0.5 → 1.0 rad) and fading out `head_pose_bias` as lane
  speed goes 0.3 → 0.8 m/s lets the 280 g head (38% of the mass) act as a counterweight.
- **Score per checkpoint**: ahead of B2 at every checkpoint from 600 on: 700 2.40 · 900 2.20 · 1000 2.11 · 1200 2.03 ·
  1300 1.96 · 1400 1.94 · 1600 1.91 · 1800 1.83 · **1900 1.82** · 1999 1.86.
- **Sweep of checkpoint 1900**: finishes at every vx and gets faster with vx, as B2 does, from 4.11 s at 0.20 to
  **1.79 s at 1.20** (seed 1).
- **Curves at the end**: `lane_progress` 1.23/s (B2 1.13), `head_pose_bias` −0.12 (B2 −0.17), fell_over 0.35.
- **Reading**: confirmed, the best single change. Still tracks the command, so it stacks naturally with D1.

### E1-combo: D1 + B1, 3000 iterations (commit 14a07a0)
- **Hypothesis**: the D1 and B1 gains add up, and training 3000 iterations gains more, since B2/B1 were still
  improving at 2000.
- **Score per checkpoint**: 1000 2.31 · 1300 2.14 · 1500 1.95 · 1800 1.90 · 2100 1.88 · 2300 1.89 · **2600 1.87** ·
  2900 1.90 · 2999 1.96. Flat at 1.87–1.99 from 1500 on.
- **Sweep of checkpoint 2600**: 1.88–2.50 s at every vx, all finishing (D1's fall at 0.20 is gone).
- **Reading**: no gain on D1, and 1000 more iterations add nothing: this gait levels off around 1.87 s. B1 is
  kept as harmless (it fixes D1's 0.20 fall in this run), but the next gain has to come from elsewhere:
  the head (B4), stride freedom (`pose`), or the progress weight.

### E2-stack: D1 + B1 + B4 on B2, seeds 1 and 2 (commit c8deff2)
- **Hypothesis**: one-sided tracking (D1) and the freed head (B4) add up.
- **Score per checkpoint, seed 1**: 900 1.93 · 1000 1.86 · 1200 1.79 · 1400 1.77 · **1600 1.74** · 1800 1.80 · 1999 1.78.
- **Score per checkpoint, seed 2**: 900 1.98 · 1000 1.92 · 1100 1.84 · 1400 1.83 · **1500 1.71** · 1600 11.9 (4/5) ·
  1700 11.5 (4/5) · 1800 1.78 · 1999 1.79.
- **Sweep of seed 1's checkpoint 1600**: finishes at every vx, from 2.35 s at 0.20 to 1.74 s at 1.15–1.20.
- **Curves at the end**: `lane_progress` 1.47/s, peak foot height 30–32 mm, `pose` 0.24–0.27, fell_over 0.32–0.36.
- **Reading**: confirmed, and replicated on two seeds (1.74 and 1.71). The two gains partly add up: −0.08 s on
  B4, −0.13 s on D1. Seed 2 has two 4/5 checkpoints in a row, so pick checkpoints by score, not by order.

### E3-prog10: lane_progress weight 5 → 10 (commit 263f189)
- **Hypothesis**: on E2, paying twice as much for lane speed now that the command no longer caps it buys a
  faster gait.
- **Score per checkpoint**: 300 2.13 · 400 1.97 · 500 11.5 (4/5) · 600 1.68 · 700 11.3 (4/5) · 800 1.62 · 900 1.54 ·
  1000 1.51 · 1100–1700 1.51–1.53 · **1800 1.49** · 1900 1.55 · 1999 1.57. Flat at about 1.51 from 900 on.
- **Sweep of checkpoint 1800**: **1.49–1.66 s at every vx from 0.25 to 1.20** (2.00 at 0.20). The command no longer
  matters: the policy runs one gait, about 1.4 m/s down the lane once up to speed.
- **Curves at the end**: fell_over **1.0** (E2 0.32), episode length 887/1000, peak foot height 42–48 mm,
  `action_rate_l2` −2.85/s (E2 −1.67), `pose` 0.04, `upright` 1.41 (E2 1.72).
- **Reading**: confirmed, the biggest gain since B2 (−0.23 s). It is a much more violent gait: high steps,
  big action changes, three times the training falls. It falls with pushes in training, yet finishes
  21/21 commands 5/5 in the Arena, which has none. Next: price the falls (F1), push harder (F2), replicate (F3),
  and turn off the pushes the Arena does not have (F4).

### E4-runpose: running pose tolerance (commit 5bc6ec8)
- **Hypothesis**: on E2, a running tolerance on `pose` from 0.6 m/s (hip pitch/knee std 0.4 → 0.7, ankle 0.25 → 0.4)
  lets the stride lengthen.
- **Score per checkpoint**: 1000 1.83 · 1100 1.81 · 1200 1.79 · 1500 1.78 · 1800 1.77 · 1900 1.77 · **1999 1.77**.
- **Curves at the end**: `pose` 0.36 (E2 0.27): the term pays more, but the gait, foot height and lane_progress
  match E2's.
- **Reading**: no gain (1.77 against E2's 1.71–1.74), dropped. Like B3: loosening a term the policy was already
  paying for does not change the gait.

### The F batch: on E3 (commits 847a889, 1fa4af8, 77d3ff3, cd446bf)
Four single changes on E3, run together.

| Run | Change | Best | Checkpoints after the best |
|---|---|---|---|
| F1-fallpen | `is_terminated` weight −250 (−5 per fall) | 1100: 1.531 s | 1200–1999: 4/5, 1/5, 4/5, 4/5, 2/5, 2/5, 3/5, 2/5, 3/5 |
| F2-prog20 | `lane_progress` 10 → 20 | 800: 1.504 s | 900–1999: no 5/5; 0/5 at 1300 |
| F3-e3-s2 | E3 again, seed 2 | 1000: 1.483 s | 1100–1999: 5/5 except 1500 (1/5), 1600 (4/5), 1999 (4/5) |
| F4-nopush | velocity pushes off (and the base config's) | 1400: 1.464 s | 1500–1999: 4/5 at 5 of 6 |

- **Sweeps of the best checkpoints**: all four run one gait at every vx. F4 scores 1.44–1.64 s, F3 1.49–1.66,
  F2 1.49–1.55, F1 1.50–1.74.
- **Common pattern**: every run with progress ≥ 10 (E3 included) peaks around checkpoint 1000–1400, then falls more
  and slows. Measured over 50-iteration windows, `fell_over` jumps by 0.2–0.4 and lane speed drops by 0.03–0.05 m/s
  **right at iteration 1000 and again at 1500**, in E3, F1, F3 and F4 alike. Those are the steps of two curricula:
  CoM randomization (±5 → ±10 → ±15 mm trunk, ±10 mm head) and the standing-env share (10 → 15 → 20%).
- **F1**: the fall penalty does what it says until 1100 (`fell_over` 0.42 at 1000 against E3's 0.73, and 5/5 at
  every checkpoint from 200 to 1100), but does not stop the late decline.
- **F2**: too much. Training falls go from 3.3 to 7.4 per reset batch and episode length from 760 to 448 by 1999:
  the policy gives up balance for speed. Its best (1.50 at 800) is no faster than E3's.
- **F3**: E3 replicated, 1.483 against 1.494.
- **F4**: the fastest checkpoint so far (1.464 s at 1400), but it also has the most failing checkpoints (9 of 20 fall).
  Training without pushes is not what makes it fall less in training (`fell_over` matches E3's): the pushes made
  E3 more robust in the Arena, not slower. Pushes stay on.
- **Reading**: progress 10 is the right weight; the problem is now holding the gait late in training. Next (G):
  F1 + F2 together (does the penalty tame progress 20?), and the two curricula behind the late decline, one at a
  time and together.

### The G batch: holding the gait late (commits 9901f67, 350496a, 4087290, 274fc1b)
- **G1 (progress 20 + fall penalty −250)**: best 1.509 s at 800, then 3/5–4/5 at every checkpoint after it; training
  falls climb back to 3.7 by 1999. The penalty does not tame progress 20.
- **G2 (CoM randomization capped at ±5 mm)**: best 1.521 s at 1200; still fails at 1000, 1600–1800 and 1999. No gain on E3.
- **G3 (standing envs held at 2%, was ramped to 25%)**: 5/5 at every checkpoint from 300 to 1300, best **1.438 s
  at 1300** with **1.41–1.47 s at all 21 commands**. Then 4/5, 4/5, 1/5, 3/5, 4/5, 4/5, 2/5 from 1400 to 1999.
- **G4 (both)**: same as G3 to 1200 (1.440 s), fails from 1300 on.
- **Reading**: holding standing envs at 2% is a small gain (the Arena never commands 0, so that share of training
  was wasted), kept. Neither curriculum is behind the late failures, though.

### Why late checkpoints fail: the lane wall (trace analysis)
The Arena's evaluation stores the trunk trajectory of one seed (`trace_b64` in `workshop/model_<N>.json`: trunk
position, quaternion, joints per frame). Decoded, it shows **every fast gait drifting sideways, mostly to the
right**: by the line the trunk is at y ≈ −0.33 m, with a mean yaw of −5° to −15°. The lane is 0.8 m wide (walls at
±0.4 m), so with the legs ~6 cm to either side of the trunk, these runs **touch the right wall at the line**.
The failing checkpoints hit it before the line and fall: G4's 1300 ends at yaw −81° and tilt 25°. G3's checkpoint
1300 (best) ends at y −0.33 with a 1.44 s finish; from 1400 on its trace runs sit at −0.33 with yaw −7° to −15°, and
its seeds fall. In E2 the drift is sometimes to the left (+0.27 at 1800): it is not a fixed asymmetry of the
robot but a yaw bias each policy picks up.

Training has no walls, so a drift costs almost nothing there: `heading_hold` (std 0.4 rad) keeps 98.5% of its
reward at a 5° error and `lane_progress` loses cos 5° = 0.4%. The faster the gait, the further a given yaw
carries it in 2 m, so the late, fastest checkpoints are the ones that reach the wall.

This refutes the premise of H1, H2 and H4 (fall penalty −1000, γ 0.995, fall penalty −250 on G3: "the policy
trades balance for speed"). They were stopped before checkpoint 100. H3 (G3 on seed 2) was kept as a
replication. `logs/analysis/report.py` now prints each checkpoint's end y and mean yaw.

### The I batch: straightness (commits 37cc525, 0fff47a, 4b29b33), on G3
- **I1**: `heading_hold` std 0.4 → 0.15 rad: a 5° heading error costs 29% of the term instead of 1.5%.
- **I2**: `ENABLE_SYMMETRY` (the package's mirror loss, coefficient 0.5): a left/right-mirrored policy has no
  built-in turn.
- **I3**: new `lane_drift` = 2 · exp(−v_lat² / 0.15²), v_lat the trunk's world velocity across the spawn heading:
  prices drifting off the centre line whether by yawing or by crabbing. 0.2 m/s across (what reaches the wall
  by the line) keeps 17% of it.

(Commit 1575f8c, named "I1", only restored G3's env: its edit failed. Its run was deleted at iteration 19 and
I1 relaunched from 37cc525.)

Results, judged on how many checkpoints from 1000 on stay 5/5 (the late failures are what this batch is
about), with the trace seed's end y (walls at ±0.4 m):

| Run | Best | 5/5 among 1000–1999 | End y from 1000 on |
|---|---|---|---|
| G3 (seed 1) | 1.438 s @1300 | 4 of 11 | −0.24 to −0.33 |
| H3 (G3, seed 2) | 1.428 s @1700 | 2 of 11 | +0.19 to +0.34 |
| I1 heading std 0.15 | 1.497 s @1100 | 2 of 11 | +0.22 to +0.34 |
| **I2 mirror loss** | **1.416 s @1999** | **7 of 11** | +0.11 to +0.33 |
| **I3 lane_drift** | 1.424 s @1800 | **9 of 11** | +0.03 to +0.34, mostly ≤ 0.26 |

- **I1 refuted**: a tighter heading tolerance does not stop the drift. `heading_hold` pays 0.22 of 1 throughout,
  so the policy simply takes the loss.
- **I2 confirmed**: the mirror loss gives the fastest checkpoint so far (1.416 s at 1999, 5/5 at 0.75 m/s) and
  more 5/5 late checkpoints, but its trunk still ends at +0.27 to +0.33 m at most of them.
- **I3 confirmed**: lane_drift keeps the end y lowest, and the most checkpoints 5/5. It learns speed more slowly
  (2.59 s at 500 against G3's 1.79) and catches up by 1600 (1.48, 1.45, 1.42, 1.43). `lane_drift` pays 0.39 of 2
  at the end: the gait still sways across the lane, so there is room for more.
- Next (J): the wall itself as a termination, alone and on top of I2 and I3, and on a second seed.

### The J batch: the wall as a termination (commits aa1ea89, 32984ef, 13d0ccd, 05ecd5b)
New termination `lane_wall` (in `rewards.py`): the episode ends when the trunk is more than 0.3 m off the spawn
line within the first 2.5 m of it, where the Arena's wall would stop it. Checked with a throwaway test on a
rotated spawn heading before the run.

| Run | Best | 5/5 among 1000–1999 | End y from 1000 on |
|---|---|---|---|
| J1 (G3 + wall) | 1.527 s @1500 | 10 of 11 | −0.02 to −0.32 |
| J2 (I3 + wall) | 3.77 s @1000, stopped | — | 0/5 at every checkpoint to 600 |
| J3 (I2 + wall) | 1.578 s @1900 | **11 of 11** (5/5 at every checkpoint from 100) | −0.28 to +0.13 |
| J4 (G3 + wall, seed 2) | 1.492 s @1999 | 11 of 11 | −0.05 to +0.35 |

- `lane_wall` ends about three times as many episodes as `fell_over` does: in training, the robots drift
  that far within 2.5 m all the time (velocity pushes included).
- **Reading**: the most reliable runs of the whole log, but 0.07–0.16 s slower than I2 and I3: a gait that must not
  stray 0.3 m from its spawn line in training walks more carefully. Note that the end y in the Arena is
  not smaller than I3's; the Arena runs just stop failing. J2 (lane_drift and the wall together) is too much:
  it could not learn to walk for 600 iterations. The score counts only the best checkpoint, so the wall
  is not kept as the recipe; it is the choice if robustness on the Space (another CPU) matters more than
  the last 0.1 s.
- Next (K): I2 + I3 together, and second seeds of I2, I3 and of their combination, to choose between them.

### The K batch: choosing between I2 and I3 (commits aded45a, dfd67e0, 8fcf5e9, d604aec)

| Run | Best | 5/5 among 200–1999 | End y from 1000 on | Sweep of the best |
|---|---|---|---|---|
| K1 (I2 + I3, seed 1) | 1.463 s @1999 | **19 of 19** | −0.08 to +0.24 | 1.42–1.47 s at all 21 vx |
| **K2 (I2 + I3, seed 2)** | **1.412 s @1999** | **19 of 19** | −0.23 to +0.06 | 1.40–1.51 s at all 21 vx |
| K3 (I3, seed 2) | 1.489 s @1900 | 17 of 19 | +0.13 to +0.34 | — |
| K4 (I2, seed 2) | **1.359 s @1999** | 17 of 19 | −0.35 to +0.03 | — |

- **Mirror loss + lane_drift together (K1, K2)**: the only recipe that finishes 5/5 at every checkpoint from 200
  on, on both seeds, with the trace seed ending within 0.24 m of centre. Kept as the folder's recipe.
- **I2 alone (K4)** reached the fastest checkpoint of the log (1.359 s), but ends 0.25 m off centre and fails at
  1100 and 1800: fast, less safe.
- **I3 alone (K3)** is slower on seed 2 (1.489 s) and still ends at +0.13 to +0.34.
- Their combination is slower to learn early (1.68 s at 1000 against K4's 1.52) and catches up by 1999.
