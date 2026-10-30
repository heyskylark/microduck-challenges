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
| B3-rock | dc198f3 | B2 + roll/pitch rate tolerance std² 0.5 → 1.5 | running | | | | |
| A3-nofwdtrack | 2540a2a | A2 + `track_linear_velocity` without vx | 1000 (stopped) | 5.022 s | 5/5 | 0.70 | +2.14 s vs A2: refuted |
| B1-lean | 18905d7 | B2 + forward lean allowed with speed | running | | | | |

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
