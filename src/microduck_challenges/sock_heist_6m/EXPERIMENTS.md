# Sock Heist 6 m: experiment log

Every training run of this folder, with its hypothesis and the Arena evaluator's numbers for it
(`arena score` on every exported checkpoint, run on this machine: indicative, not official).
**Score** = best mean time over 5 seeds at the best commanded vx; a fall, a catch or no finish within
40 s costs 40 s. **CHECK** = `python -m microduck_challenges.sock_heist_6m.check` over 25 seeds at the
scored speed.

How runs work: one change per run, on top of the best run so far (a change is kept if its best
checkpoint beats the best so far). 4096 envs, seed 1, local RTX 3090, a checkpoint every 100
iterations. The run name says the change.

## Outcome

**10.532 s → 7.616 s, 5/5** locally (base 999 → headfree 2999), against 24.159 s for the walker and
16.98 s for the shipped reference on this machine. The folder holds headfree's recipe: the shipped one, plus
the smoothness ramp capped at −0.3 (long), `progress` paid past the command up to 2.0 m/s (uncap), forward
tracking one-sided on green (onesided) and no head reward (headfree), at 5000 iterations. brake, rollfree and
vref25 were not kept.

Published: onesided 1900 (`2026-11-03_14-33-50_onesided`, commit 74974ac) as
`heyskylark/microduck-heist-onesided`, **8.516 s, 5/5 at 1.20 m/s on the Space**, the same as locally
([result](https://huggingface.co/spaces/pollen-robotics/microduck-arena#/r/01M6JHG51C1X9X22YS0H0R)).

Bars on this machine: the walker 24.159 s at 1.00 m/s 5/5; heist5-300 (the shipped reference)
16.98 s at 1.20 m/s 5/5.

## Runs

| Run | Commit | Change | Iterations | Best | Score | CHECK 25 seeds at the best |
|---|---|---|---|---|---|---|
| base | 0633566 | The recipe as shipped (heist5's) | 1000 | 999 | 10.532 s 5/5 @1.20 | 25/25, mean 10.68 s, worst drift 1.4 cm, 1.02–1.07 m/s on green |
| long | 14d5327 | 2000 iterations, `action_rate_l2` ramp capped at −0.3 | 2000 | 1500 | 10.244 s 5/5 @1.20 | 25/25, mean 9.95 s, worst drift 1.3 cm, 1.08–1.13 m/s on green |
| uncap | 68796c3 | `progress` past the command, up to 2.0 m/s | 2000 | 1800 | 8.677 s 5/5 @1.20 | 25/25, mean 8.66 s, worst drift 1.2 cm, 1.24–1.33 m/s on green |
| onesided | 74974ac | `track_linear_velocity` one-sided forward on green | 2000 | 1900 | 8.516 s 5/5 @1.20 | 25/25, mean 8.46 s, worst drift 1.2 cm, 1.27–1.35 m/s on green |
| brake | f9c0dd0 | Stillness paid on the turn's last 0.1 s | 2000 | 1800 | 8.591 s 5/5 @1.20 | 25/25, mean 8.49 s, worst drift 0.9 cm, 1.27–1.35 m/s on green |
| ctrl | 3950713 | none: onesided at 3000 iterations | 3000 | 2800 | 8.310 s 5/5 @1.15 | 25/25, mean 8.24 s, worst drift 1.7 cm |
| **headfree** | ffe4797 | no `head_pose_tracking`, no `head_pose_bias` | 3000 | 2999 | **7.616 s 5/5 @1.20** | 25/25, mean 7.00 s, worst drift 1.9 cm |
| rollfree | ee4b20f | `upright` roll std² 0.05 → 0.5 with speed, `body_ang_vel` −0.01 | 3000 | 1800 | 8.263 s 5/5 @1.05 | 25/25, mean 8.21 s, worst drift 1.5 cm |
| vref25 | 1d97e21 | `progress` up to 2.5 m/s | 3000 | 2400 | 8.528 s 5/5 @1.20 | 25/25, mean 8.46 s, worst drift 1.2 cm |

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

How it stops (a trace of the Arena's `run_once` over seeds 1–10 at 1.20 m/s, 20 reds): 1.34 m/s as the red
begins, it coasts ~29 cm (up to 37 cm) into the turn and reaches the mark still moving on 18 of 20 reds
(0.22 m/s on average over the last 0.1 s, up to 0.50); it then stops within a few watched steps, worst
drift 0.9 cm. uncap-1800 reached it moving on 10 of 20. Nothing in training pays the coast (`progress` is
zero on red); it is free distance on the Arena, but the margin at the mark thins as green speed rises.

### brake — not kept

Hypothesis: onesided reaches its marks still moving; paying stillness on the turn's last 5 steps (0.1 s,
the mark the last of them; `brake` = exp(−(speed / 0.1 m/s)²), weight 4) settles it at the mark, without
paying an early stop: the coast before those steps is free distance.

| Checkpoint | 100 | 300 | 500 | 700 | 900 | 1100 | 1300 | 1500 | 1700 | 1800 | 1900 | 1999 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Score (s) | 25.05 | 17.06 | 13.75 | 12.16 | 10.24 | 9.60 | 9.44 | 9.32 | 9.29 | **8.59** | 8.60 | 9.21 |

Every checkpoint from 100 finishes 5/5. +0.075 s on onesided's best (CHECK mean +0.03 s): not kept, by the
rule. It did what it was paid for, modestly. Stops over seeds 1–25 at 1.20 m/s, 50 reds each:

| | onesided-1900 | brake-1800 |
|---|---|---|
| Speed as the red begins | 1.33 m/s | 1.32 m/s |
| Coast into the turn, mean / max | 28.6 / 38.1 cm | 27.6 / 36.0 cm |
| Speed over the last 0.1 s before the mark, mean / max | 0.212 / 0.573 m/s | 0.147 / 0.386 m/s |
| Drift while watched, mean / worst | 0.45 / 1.16 cm | 0.56 / 0.92 cm |

Neither comes near the 3 cm rule here; brake's value would be margin on the Space's physics, which drifts
from this machine's. Its code is in f9c0dd0.

## What the faster plain networks do (board analysis, 2026-11-04)

The board's top 20 (4.89–5.08 s) are all lookup graphs (ArgMin/Where/Gather over recorded seeds). The best plain
networks, same 61→14 MLP as ours: RSanchez996 (6.09 s, 6.15 s; checkpoint 5000 of a 15000-iteration run, "no
attention to the head"), lphatnguyen v3 (7.18 s; ~4000 iterations). Measured in the Arena's race, seeds 1–10, each
at its scored speed (`logs/heist/gait.py`); cruise = green from 0.8 s after its start:

| | RS_2350 | RS_0951 | lphat_v3 | ours (onesided-1900) |
|---|---|---|---|---|
| Score (seeds 1–10) | 6.00 s | 6.11 s | 6.76 s | 8.48 s |
| Cruise speed | 1.94 m/s | 1.90 m/s | 1.65 m/s | 1.33 m/s |
| Stride length / rate | 0.54 m / 3.61 Hz | 0.54 m / 3.53 Hz | 0.46 m / 3.61 Hz | 0.39 m / 3.45 Hz |
| Hip pitch / hip roll range | 66° / 45° | 61° / 32° | 46° / 32° | 47° / 25° |
| Trunk roll σ | 7.5° | 8.0° | 5.0° | 3.6° |
| Neck from home / head lean | −27° / +11° | −12° / +17° | −17° / +2° | −6° / −12° |
| Trunk pitch | −0.3° | +12.7° | −2.1° | −0.4° |
| Reach 0.5 m/s after a red | 0.18 s | 0.19 s | 0.17 s | 0.20 s |
| Distance 1 s after a red | 1.22 m | 1.23 m | 1.17 m | 1.01 m |
| Speed as the red begins / coast / at the mark | 1.78 / 37 cm / 0.25 | 1.84 / 40 cm / 0.30 | 1.69 / 47 cm / 0.49 | 1.31 / 29 cm / 0.22 |

- **Speed is stride length**: same cadence, 40 % longer strides with wider hips and twice the trunk roll. The head
  leans forward; the trunk need not (RS_2350 runs upright).
- **The restart is not slow**: every policy reaches 0.5 m/s ~0.2 s after a green; the 0.2 m we lose by 1 s is top speed.
- **Stopping from 1.9 m/s is fine**: 37–40 cm coast, ≤1.8 cm drift.
- **A cliff at ~1.9 m/s**: a model fitted to the five scored timetables (constant acceleration, cruise, a coast
  through the turn; 0.09 s rms on our and RS's seeds) gives 8.41 s at 1.33 m/s, 7.54 s at 1.75 and 5.96 s at 1.95:
  seeds 3–5 then cross in the second red's turn and save a whole red. `progress` stops paying at 2.0 m/s.
- **What onesided's terms charge their cruise**, per step (`logs/heist/price.py`): `progress` ours 10.9 / RS_2350
  15.2; everything else ours +3.0 / RS_2350 +1.5: head terms −0.8 (`head_pose_tracking` 1.72 → 1.37,
  `head_pose_bias` −0.55 → −0.94), roll −0.75 (`upright` 1.81 → 1.42, `body_ang_vel` −0.08 → −0.43). Their gait
  is still worth ~+2.8 a step here: a better optimum not found, taxed on the way. The leg `pose` term is ~0 for
  every gait (hip roll std 0.05 rad): not a lever.

## Posture batch (3000 iterations, seed 1, four at once)

Each one change on onesided's recipe, to find a recipe with room to grow; the promising one is then run longer
(5000 or more while still improving).

| Run | Change |
|---|---|
| ctrl | none: onesided at 3000 iterations |
| headfree | `head_pose_tracking` and `head_pose_bias` (and its ramp) removed: the head does what it likes |
| rollfree | `upright` roll std² 0.05 → 0.5 as forward speed goes 0.3 → 0.8 m/s (sprint W1), with `body_ang_vel` −0.05 → −0.01 (W2): both price the rocking |
| vref25 | `progress` paid up to 2.5 m/s (was 2.0), same pay per m/s |

Scores every 100 iterations (all 5/5 unless noted):

| Run | 500 | 1000 | 1500 | 2000 | 2200 | 2400 | 2600 | 2800 | 2900 | 2999 |
|---|---|---|---|---|---|---|---|---|---|---|
| ctrl | 15.13 | 9.94 | 9.25 | 8.71 | 8.38 | 8.43 | 8.32 | **8.31** | 8.45 | 8.39 |
| headfree | 12.05 | 14.40 (4/5) | 8.13 | 8.08 | 7.84 | 7.87 | 7.80 | 7.86 | 7.74 | **7.62** |
| rollfree | 13.63 | 9.97 | 8.53 | 8.42 | 8.42 | 8.41 | 8.38 | 8.32 | 8.35 | 8.30 (best 8.26 @1800) |
| vref25 | 15.22 | 9.49 | 9.22 | 8.73 | 9.26 | **8.53** | 8.58 | 8.59 | 9.25 | 8.71 |

Gait of each best, seeds 1–10 (`logs/heist/gait.py`, as in the board analysis):

| | ctrl-2800 | headfree-2999 | rollfree-1800 | vref25-2400 | RS_2350 |
|---|---|---|---|---|---|
| Cruise speed | 1.39 m/s | **1.74 m/s** | 1.42 m/s | 1.36 m/s | 1.94 m/s |
| Stride length / rate | 0.41 m / 3.42 Hz | **0.60 m** / 2.90 Hz | 0.43 m / 3.30 Hz | 0.39 m / 3.50 Hz | 0.54 m / 3.61 Hz |
| Neck from home / head lean | +1° / −19° | **−41° / +38°** | +10° / −25° | 0° / −19° | −27° / +11° |
| Trunk roll σ | 3.9° | 3.4° | **7.5°** | 3.9° | 7.5° |
| Coast / speed at the mark | 30 cm / 0.19 | 39 cm / 0.42 | 36 cm / 0.42 | 27 cm / 0.12 | 37 cm / 0.25 |
| Distance 1 s after a red | 1.06 m | 1.16 m | 1.04 m | 1.02 m | 1.22 m |

- **headfree is the lever**: −0.69 s on ctrl, still improving at 2999 (−0.22 s over the last 800 iterations). The
  head goes 38° forward and the stride to 0.60 m (longer than RS's, at a slower cadence): 1.74 m/s. Stops stay
  clean (25/25, worst drift 1.9 cm).
- **rollfree gets RS's roll (7.5° σ) but not its speed** (1.42 m/s): rocking is not what makes the stride.
- **vref25 does nothing**: nothing reaches the 2.0 m/s cap yet.
- **Run-to-run noise is ~0.7 s**: ctrl is onesided's recipe for its first 2000 iterations (the curricula are
  keyed to the step), yet it scored 9.2 s at 1700 where onesided scored 8.52 s. One seed decides nothing small.

## headfree5k: headfree at 5000 iterations, seed 2

The recipe with room to grow, run fresh to 5000 iterations (not resumed, so the recipe reproduces). Seed 2:
its first 3000 iterations are also headfree's seed replicate. Extended further if still improving at 5000.

Commit eda395b, run `2026-11-04_22-02-09_headfree5k`. Score on seeds 1–5 / CHECK over 25 seeds (finished, mean):

| Checkpoint | 2500 | 2600 | 3000 | 3500 | 3800 | 3900 | 4300 | 4400 | 4600 | **4700** | 4800 | 4999 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Score | 8.12 | 7.96 | 7.93 | 7.72 | 7.62 | 6.75 | 13.25 (4/5) | 6.68 | **6.675** | 7.07 | 7.02 | 7.14 |
| CHECK 25 | 25/25 8.03 | 25/25 7.77 | 25/25 7.52 | 22/25 | 22/25 | 21/25 | 21/25 | 21/25 | 19/25 | **25/25 6.55** | 24/25 | 24/25 |

Of 26 checkpoints from 2500, only 2500, 2600, 3000 and 4700 finish all 25 seeds; every other loses 1–7, all
**caught early** (0.02–0.18 s into the watch, 1.7–2.0 m/s as the red began), most on the first red after a 0.6–1 s
first green run at 2.2–2.5 m/s. Seeds 1–5 hide it: 4600's 6.675 s is 19/25.

- **Seed replicate**: at 3000 seed 2 scores 7.93 s (CHECK 25/25, 7.52) against seed 1's 7.62 (7.00): the recipe
  holds across seeds, within the ~0.5 s run-to-run noise.
- **Still improving past 3000**: cruise 1.62 m/s at 3000 → 1.80 at 4700 (RS_2350 1.95), the neck 54° forward.
- **Stopping is now the limit**: from 1.8 m/s it coasts 41–43 cm (RS 39) and reaches the mark at 0.51–0.61 m/s,
  against RS's 0.27 (seeds 1–25). In training `caught` holds at 1.1–1.7 per step and `fell_over` climbs 0.2 → 1.1:
  a catch only ends the episode, so the occasional one is worth the speed.
