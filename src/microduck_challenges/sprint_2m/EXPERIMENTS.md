# Sprint 2 m: experiment log

Every training run of this folder, with its hypothesis and the Arena evaluator's numbers for it
(`arena.workshop` evaluation of every checkpoint, run on this machine: indicative, not official).
**Score** = best mean time over 5 seeds at the best commanded vx; a fall or no finish costs 50 s.

How runs work: one change per run, on top of the best run so far. 2000 iterations, 4096 envs, seed 1,
local RTX 3090, a checkpoint every 100 iterations. The run name says the change. A run is judged by its
best checkpoint. A change that adds falls is not thrown out on that alone: speed and stability are tuned
together.

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
| H3-g3-s2 | 6045e42 | G3, seed 2 | running | | | | |
| I1-heading015 | 37cc525 | G3 + `heading_hold` std 0.4 → 0.15 rad | running | | | | |
| I2-mirror | 0fff47a | G3 + mirror-symmetry loss | running | | | | |
| I3-lanedrift | 4b29b33 | G3 + `lane_drift` (sideways speed across the lane) | running | | | | |

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
