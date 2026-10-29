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
