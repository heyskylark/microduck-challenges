# Sock Heist 6 m: experiment log

Every training run of this folder, with its hypothesis and the Arena evaluator's numbers for it
(`arena score` on every exported checkpoint, run on this machine: indicative, not official).
**Score** = best mean time over 5 seeds at the best commanded vx; a fall, a catch or no finish within
40 s costs 40 s. **CHECK** = `python -m microduck_challenges.sock_heist_6m.check` over 25 seeds at the
scored speed.

How runs work: one change per run, on top of the best run so far (a change is kept if its best
checkpoint beats the best so far). 4096 envs, seed 1, local RTX 3090, a checkpoint every 100
iterations. The run name says the change.

Bars on this machine: the walker 24.159 s at 1.00 m/s 5/5; heist5-300 (the shipped reference)
16.98 s at 1.20 m/s 5/5.

## Runs

| Run | Commit | Change | Iterations | Best | Score | CHECK 25 seeds at the best |
|---|---|---|---|---|---|---|
| base | 0633566 | The recipe as shipped (heist5's) | 1000 | 999 | 10.532 s 5/5 @1.20 | 25/25, mean 10.68 s, worst drift 1.4 cm, 1.02–1.07 m/s on green |

### base

The recipe as cloned, to measure the folder before changing it.

| Checkpoint | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 999 |
|---|---|---|---|---|---|---|---|---|---|---|
| Score (s) | 23.94 | 19.50 | 17.02 | 15.66 | 15.18 | 13.59 | 13.03 | 11.94 | 11.28 | **10.53** |
| Scored at (m/s) | 1.20 | 1.10 | 1.15 | 1.20 | 1.20 | 1.20 | 1.20 | 1.20 | 1.20 | 1.20 |

Every checkpoint from 100 finishes 5/5. Curves: `caught` peaked near 4.4 per step at 300–500 and fell to
~0.5 by 800; episodes back near 900 steps from 600.

- **Speed is the limit, not stopping**: catches 0/25, worst drift 1.4 cm of 3 cm. From 400 on every
  checkpoint scores best at the sweep's top, 1.20 m/s, and walks ~1.05 m/s on green: `progress` pays
  nothing past the command.
- **Still improving at 999** (−0.75 s per 100 iterations): 1000 iterations is too short.
- The smoothness ramp reaches −0.4 at 750 and −1.0 by 1500 as shipped: the sprint's B2 found it the main
  brake once speed was paid for.

## Next

Four runs in order, 2000 iterations each, each on top of the best so far:

| Run | Change | Sprint source |
|---|---|---|
| long | 2000 iterations, `action_rate_l2` ramp capped at −0.3 by 750 | B2 |
| uncap | `progress` pays forward speed past the command on green, up to 2.0 m/s | A2 / E3 |
| onesided | `track_linear_velocity` one-sided on green: faster than the command costs nothing | D1 |
| brake | A stopping reward through the head's 0.4 s turn, which nothing pays today | new |
