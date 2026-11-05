"""Sock Heist's own terms: freezing while the giant watches, walking on green, being caught, and what the critic alone is
told of the light and the lane. Each reads the LightsCommand (lights.py) named `command_name`."""

import torch
from mjlab.utils.lab_api.math import quat_apply_inverse

from . import lights


def freeze(env, command_name: str, std: float) -> torch.Tensor:
    """(n,): exp(-(drift / std)²) on the steps the giant watches, else 0. At std = the tolerance, a duck
    on its mark earns 1 and one at the edge of being caught e^-1."""
    term = env.command_manager.get_term(command_name)
    _, _, watch = term.stepped()
    return torch.where(watch, torch.exp(-((term.drift() / std) ** 2)), 0.0)


def progress(env, command_name: str, v_ref: float) -> torch.Tensor:
    """Forward speed up to `v_ref` on green, past the command (the sprint's lane_progress, A2/E3): the
    command no longer caps it. Nothing on red (the command is zero)."""
    vx = env.scene["robot"].data.root_link_lin_vel_b[:, 0].clamp(0.0, v_ref)
    return vx * (env.command_manager.get_command(command_name)[:, 0] > 0.0)


def track_linear_velocity_at_least(env, command_name: str, std: float) -> torch.Tensor:
    """mjlab's track_linear_velocity, one-sided forward on green (the sprint's D1): falling short of the
    command costs as the bell curve always did, going faster costs nothing. On red (a zero command) it
    still tracks v_x = 0 both ways: that is what teaches the stop.
    exp(-(e_x² + (cmd_y - v_y)² + v_z²) / std²)."""
    command = env.command_manager.get_command(command_name)
    v = env.scene["robot"].data.root_link_lin_vel_b
    short = command[:, 0] - v[:, 0]
    err_x = torch.where(command[:, 0] > 0.0, short.clamp(min=0.0), short)
    err = err_x.square() + (command[:, 1] - v[:, 1]).square() + v[:, 2].square()
    return torch.exp(-err / std**2)


def upright_roll_free(env, std: float, roll_std: float, speed_lo: float, speed_hi: float, asset_cfg) -> torch.Tensor:
    """mjlab's `upright` whose tolerance for ROLL widens from `std` to `roll_std` as forward speed goes `speed_lo` →
    `speed_hi` (smoothstep; the sprint's W1): exp(-g_x² / std² - g_y² / σ²), g the trunk's projected gravity. A
    stopped duck (a red, the settle) keeps `std` both ways; pitch always does."""
    asset = env.scene[asset_cfg.name]
    quat = asset.data.body_link_quat_w[:, asset_cfg.body_ids, :].squeeze(1)
    g = quat_apply_inverse(quat, asset.data.gravity_vec_w.expand(quat.shape[0], 3))
    t = ((asset.data.root_link_lin_vel_b[:, 0] - speed_lo) / (speed_hi - speed_lo)).clamp(0.0, 1.0)
    var_roll = std**2 + t * t * (3.0 - 2.0 * t) * (roll_std**2 - std**2)
    return torch.exp(-g[:, 0].square() / std**2 - g[:, 1].square() / var_roll)


def caught(env, command_name: str) -> torch.Tensor:
    """(n,) bool: watched, and more than TOLERANCE_M from its mark, as run_once catches a duck."""
    term = env.command_manager.get_term(command_name)
    _, _, watch = term.stepped()
    return watch & (term.drift() > lights.TOLERANCE_M)


def off_lane(env, command_name: str, half_width: float) -> torch.Tensor:
    """(n,) bool: the trunk more than `half_width` off its lane. The training floor has no walls, so this
    stands for them: heist3 learned to ignore its turn command and veered, which the Arena's wall ends
    within a second, caught or fallen, where nothing in training did."""
    term = env.command_manager.get_term(command_name)
    return (term.trunk[:, 1] - term.lane_y).abs() > half_width


def light_state(env, command_name: str) -> torch.Tensor:
    """(n, 4), for the step about to run: standing (the settle or a red), watched, the seconds until the
    twist next changes (the settle ends, a red starts or ends), and the drift over TOLERANCE_M once
    marked (0 before the mark: in the settle, on green and while the head turns)."""
    term = env.command_manager.get_term(command_name)
    standing, watch = term.ahead()
    k = env.episode_length_buf[:, None]
    settle = torch.full_like(term.onset[:, :1], lights.steps(lights.SETTLE_S))
    changes = torch.cat([settle, term.onset, term.onset + term.length], dim=1)
    until = (changes - k).masked_fill(changes <= k, torch.iinfo(changes.dtype).max).amin(dim=1)
    drift = torch.where(watch, term.drift() / lights.TOLERANCE_M, 0.0)
    return torch.stack([standing.float(), watch.float(), until * lights.CTRL_DT, drift], dim=-1)


def lane_state(env, command_name: str) -> torch.Tensor:
    """(n, 2): the trunk's y off its lane (+ left of it) and its yaw, what the lane's hold steers by."""
    term = env.command_manager.get_term(command_name)
    trunk = term.trunk
    return torch.stack([trunk[:, 1] - term.lane_y, lights.yaw_of(trunk[:, 3:7])], dim=-1)
