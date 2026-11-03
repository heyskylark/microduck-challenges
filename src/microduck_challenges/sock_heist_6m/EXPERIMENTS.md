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
| long | 14d5327 | 2000 iterations, `action_rate_l2` ramp capped at −0.3 | 2000 | 1500 | 10.244 s 5/5 @1.20 | 25/25, mean 9.95 s, worst drift 1.3 cm, 1.08–1.13 m/s on green |
| uncap | 68796c3 | `progress` past the command, up to 2.0 m/s | 2000 | 1800 | 8.677 s 5/5 @1.20 | 25/25, mean 8.66 s, worst drift 1.2 cm, 1.24–1.33 m/s on green |
| onesided | 74974ac | `track_linear_velocity` one-sided forward on green | 2000 | 1900 | 8.516 s 5/5 @1.20 | 25/25, mean 8.46 s, worst drift 1.2 cm, 1.27–1.35 m/s on green |
| brake | | Stillness paid on the turn's last 0.1 s | 2000 | | | |

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

### long — kept

Hypothesis: base was still improving at 999; twice the iterations, with the smoothness ramp capped at
−0.3 so it does not brake the longer run, gives a faster best checkpoint.

| Checkpoint | 100 | 300 | 500 | 700 | 900 | 1100 | 1300 | 1500 | 1700 | 1900 | 1999 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Score (s) | 25.01 | 16.75 | 15.09 | 12.35 | 11.84 | 10.53 | 10.39 | **10.24** | 10.38 | 10.34 | 10.42 |

Every checkpoint from 100 finishes 5/5, scored at 1.15–1.20 m/s. −0.29 s on base's best; it plateaus at
10.2–10.5 s from 1100 on, walking 1.08–1.13 m/s on green of a 1.20 command: the command caps it.

### uncap — kept

Hypothesis: long walked 1.1 m/s of a 1.20 command because `progress` paid nothing past the command;
paying forward speed up to 2.0 m/s on green, whatever the command, makes it walk faster.

| Checkpoint | 100 | 300 | 500 | 700 | 900 | 1100 | 1300 | 1500 | 1700 | 1800 | 1900 | 1999 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Score (s) | 21.89 | 16.06 | 15.08 | 12.17 | 9.70 | 9.43 | 9.38 | 9.14 | 9.25 | **8.68** | 8.77 | 9.19 |

Every checkpoint from 100 finishes 5/5 (scored at 0.85–1.20 m/s). −1.57 s on long's best. It now walks
past its command (1.24–1.33 m/s on green of 1.20) and still stops cleanly: 0 caught, 0 fell, worst drift
1.2 cm. The bell curve of `track_linear_velocity` still charges it for that excess.

### onesided — kept

Hypothesis: uncap ran 1.24–1.33 m/s on a 1.20 command, where the two-sided bell curve of
`track_linear_velocity` charges for the excess; making it one-sided on green (red still tracks 0 both
ways) lets it walk faster.

| Checkpoint | 100 | 300 | 500 | 700 | 900 | 1100 | 1300 | 1500 | 1700 | 1800 | 1900 | 1999 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Score (s) | 24.05 | 16.94 | 14.11 | 12.33 | 10.34 | 9.57 | 9.38 | 8.65 | 8.52 | 8.56 | **8.52** | 8.56 |

Every checkpoint from 100 finishes 5/5 (scored at 0.75–1.20 m/s). −0.16 s on uncap's best, one seed: small,
but the late checkpoints are steadier (1700–1999 all 8.52–8.56 s; uncap's 8.68–9.19 s).

How it stops (`logs/stopping.py`-style trace over seeds 1–10 at 1.20 m/s, 20 reds): 1.34 m/s as the red
begins, it coasts ~29 cm (up to 37 cm) into the turn and reaches the mark still moving on 18 of 20 reds
(0.22 m/s on average over the last 0.1 s, up to 0.50); it then stops within a few watched steps, worst
drift 0.9 cm. uncap-1800 reached it moving on 10 of 20. Nothing in training pays the coast (`progress` is
zero on red); it is free distance on the Arena, but the margin at the mark thins as green speed rises.

## Next

Four runs in order, 2000 iterations each, each on top of the best so far:

| Run | Change | Sprint source |
|---|---|---|
| long | 2000 iterations, `action_rate_l2` ramp capped at −0.3 by 750 | B2 |
| uncap | `progress` pays forward speed past the command on green, up to 2.0 m/s | A2 / E3 |
| onesided | `track_linear_velocity` one-sided on green: faster than the command costs nothing | D1 |
| brake | `brake` (weight 4): exp(−(speed / 0.1 m/s)²) on the turn's last 5 steps, the mark the last; the coast before them stays free | new |
