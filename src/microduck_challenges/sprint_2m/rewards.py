"""The sprint's own reward and termination terms (see EXPERIMENTS.md for the run that introduced each).

Speed here is `lane_speed`: the trunk's world velocity along the heading the robot spawned with.
That is progress down the lane the Arena measures, not along wherever the nose points, so walking
crabwise earns less. `speed_gate` turns that speed into 0..1 (smoothstep), the share of a balance
term's tolerance that is relaxed: a term relaxes only once the robot is actually running.
"""

from __future__ import annotations

import math

import torch
from mjlab.envs import ManagerBasedRlEnv
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.utils.lab_api.math import quat_apply_inverse

from mjlab_microduck.tasks import mdp as microduck_mdp

_ROBOT = SceneEntityCfg("robot")


def _yaw(quat: torch.Tensor) -> torch.Tensor:
    w, x, y, z = quat.unbind(-1)
    return torch.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def lane_wall(env: ManagerBasedRlEnv, half_width: float, length: float) -> torch.Tensor:
    """True once the trunk is more than `half_width` off the spawn line within the first `length` m of it.

    The Arena's lane has walls at ±0.4 m that a drifting duck hits and falls on; training is an open
    plane. This ends the episode where that wall would. The line is the spawn position and heading,
    captured on an episode's first step; past `length` m down it the lane is over, as in the race.
    """
    asset = env.scene[_ROBOT.name]
    pos = asset.data.root_link_pos_w[:, :2]
    yaw = _yaw(asset.data.root_link_quat_w)
    if not hasattr(env, "_wall_origin") or env._wall_origin.shape[0] != env.num_envs:
        env._wall_origin = pos.clone()
        env._wall_heading = yaw.clone()
    fresh = env.episode_length_buf <= 1
    env._wall_origin = torch.where(fresh.unsqueeze(-1), pos, env._wall_origin)
    env._wall_heading = torch.where(fresh, yaw, env._wall_heading)
    d = pos - env._wall_origin
    c, s = torch.cos(env._wall_heading), torch.sin(env._wall_heading)
    along = d[:, 0] * c + d[:, 1] * s
    lateral = -d[:, 0] * s + d[:, 1] * c
    return (lateral.abs() > half_width) & (along < length) & ~fresh


def lane_speed(env: ManagerBasedRlEnv) -> torch.Tensor:
    """Trunk velocity along the spawn heading (m/s), the heading captured as heading_hold captures it."""
    asset = env.scene[_ROBOT.name]
    yaw = _yaw(asset.data.root_link_quat_w)
    if not hasattr(env, "_lane_heading") or env._lane_heading.shape[0] != env.num_envs:
        env._lane_heading = yaw.clone()
    env._lane_heading = torch.where(env.episode_length_buf <= 1, yaw, env._lane_heading)
    vel = asset.data.root_link_lin_vel_w[:, :2]
    return vel[:, 0] * torch.cos(env._lane_heading) + vel[:, 1] * torch.sin(env._lane_heading)


def speed_gate(env: ManagerBasedRlEnv, lo: float, hi: float) -> torch.Tensor:
    """0 below `lo` m/s down the lane, 1 above `hi`, smoothstep between."""
    t = torch.clamp((lane_speed(env) - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lane_progress(
    env: ManagerBasedRlEnv,
    v_ref: float,
    command_name: str = "twist",
    command_threshold: float = 0.01,
) -> torch.Tensor:
    """clip(lane_speed, 0, v_ref) / v_ref, whatever the command: speed paid for itself.

    Zero for a standing env (|command| under the threshold), which must keep learning to stand.
    """
    speed = lane_speed(env)
    command = env.command_manager.get_command(command_name)
    active = torch.norm(command[:, :2], dim=1) > command_threshold
    if active.any():
        env.extras["log"]["Metrics/lane_speed_mean"] = speed[active].mean()
    return torch.clamp(speed, 0.0, v_ref) / v_ref * active.float()


def lane_drift(
    env: ManagerBasedRlEnv,
    std: float,
    command_name: str = "twist",
    command_threshold: float = 0.01,
) -> torch.Tensor:
    """exp(-v_lat² / std²), v_lat the trunk's world velocity across the spawn heading (m/s).

    Prices walking off the lane's centre line, whether by yawing or by crabbing. Zero for a
    standing env, which tracks v = 0 already.
    """
    lane_speed(env)  # keeps env._lane_heading current
    asset = env.scene[_ROBOT.name]
    vel = asset.data.root_link_lin_vel_w[:, :2]
    heading = env._lane_heading
    v_lat = -vel[:, 0] * torch.sin(heading) + vel[:, 1] * torch.cos(heading)
    command = env.command_manager.get_command(command_name)
    active = torch.norm(command[:, :2], dim=1) > command_threshold
    if active.any():
        env.extras["log"]["Metrics/lane_drift_abs_mean"] = v_lat[active].abs().mean()
    return torch.exp(-torch.square(v_lat) / std**2) * active.float()


def track_lateral_velocity(
    env: ManagerBasedRlEnv,
    std: float,
    command_name: str = "twist",
    command_threshold: float = 0.01,
) -> torch.Tensor:
    """track_linear_velocity without its forward part while walking: exp(-((cmd_y - v_y)² + v_z²) / std²).

    Forward speed is lane_progress's alone, so the command no longer caps it. A standing env
    (|command| under the threshold) still tracks v_x = 0: that is what teaches it to stand.
    """
    asset = env.scene[_ROBOT.name]
    command = env.command_manager.get_command(command_name)
    v = asset.data.root_link_lin_vel_b
    standing = (torch.norm(command[:, :2], dim=1) <= command_threshold).float()
    err = torch.square(command[:, 1] - v[:, 1]) + torch.square(v[:, 2])
    err = err + standing * torch.square(command[:, 0] - v[:, 0])
    return torch.exp(-err / std**2)


def track_linear_velocity_at_least(
    env: ManagerBasedRlEnv,
    std: float,
    command_name: str = "twist",
    command_threshold: float = 0.01,
) -> torch.Tensor:
    """track_linear_velocity that charges only for falling SHORT of the forward command while walking.

    exp(-(max(cmd_x - v_x, 0)² + (cmd_y - v_y)² + v_z²) / std²): the bell curve's strong pull up to the
    command, without its cap above it. A standing env still tracks v_x = 0 both ways.
    """
    asset = env.scene[_ROBOT.name]
    command = env.command_manager.get_command(command_name)
    v = asset.data.root_link_lin_vel_b
    standing = torch.norm(command[:, :2], dim=1) <= command_threshold
    short = command[:, 0] - v[:, 0]
    err_x = torch.where(standing, short, torch.clamp(short, min=0.0))
    err = torch.square(err_x) + torch.square(command[:, 1] - v[:, 1]) + torch.square(v[:, 2])
    return torch.exp(-err / std**2)


def upright_lean(
    env: ManagerBasedRlEnv,
    std: float,
    lean_std: float,
    speed_lo: float,
    speed_hi: float,
    lean_target_deg: float = 0.0,
    asset_cfg: SceneEntityCfg = _ROBOT,
) -> torch.Tensor:
    """`upright` whose tolerance for a FORWARD (nose-down) lean widens from `std` to `lean_std` with speed.

    exp(-g_y² / std² - e_x² / σ²), g the projected gravity of the body (nose-down gives g_x > 0) and
    e_x = g_x - gate · sin(lean_target): σ² is `lean_std`² (blended in with speed) past the target, `std`²
    short of it. With no target, a backward lean keeps `std`; with one, the trunk is pulled forward to it
    at speed.
    """
    asset = env.scene[asset_cfg.name]
    quat = asset.data.body_link_quat_w[:, asset_cfg.body_ids, :].squeeze(1)
    g = quat_apply_inverse(quat, asset.data.gravity_vec_w.expand(quat.shape[0], 3))
    gate = speed_gate(env, speed_lo, speed_hi)
    var_fwd = std**2 + gate * (lean_std**2 - std**2)
    e_x = g[:, 0] - gate * math.sin(math.radians(lean_target_deg))
    past = torch.clamp(e_x, min=0.0)
    short = torch.clamp(e_x, max=0.0)
    return torch.exp(-(torch.square(g[:, 1]) + torch.square(short)) / std**2 - torch.square(past) / var_fwd)


def track_yaw_rate_loose_rock(
    env: ManagerBasedRlEnv,
    yaw_std: float,
    rock_std: float,
    command_name: str = "twist",
) -> torch.Tensor:
    """track_angular_velocity with its own tolerance for roll/pitch rates (`rock_std`), not the yaw's."""
    asset = env.scene[_ROBOT.name]
    command = env.command_manager.get_command(command_name)
    w = asset.data.root_link_ang_vel_b
    yaw_err = torch.square(command[:, 2] - w[:, 2])
    rock = torch.sum(torch.square(w[:, :2]), dim=1)
    return torch.exp(-yaw_err / yaw_std**2 - rock / rock_std**2)


def head_pose_tracking_at_speed(
    env: ManagerBasedRlEnv,
    std: float,
    fast_std: float | None,
    speed_lo: float,
    speed_hi: float,
    fast_offset: tuple[float, float, float, float] | None = None,
    command_name: str = "head_pose",
) -> torch.Tensor:
    """head_pose_tracking whose tolerance widens from `std` to `fast_std` with speed (blend of the two).

    `fast_std=None` frees the head at speed: the running half pays 1 whatever the neck and head do.
    `fast_offset` (neck_pitch, head_pitch, head_yaw, head_roll deltas, rad) moves the running half's
    target off the command, so at speed the head is pulled to that pose instead.
    """
    gate = speed_gate(env, speed_lo, speed_hi)
    slow = microduck_mdp.head_pose_tracking(env, command_name=command_name, std=std)
    if fast_std is None:
        return (1.0 - gate) * slow + gate
    if fast_offset is None:
        fast = microduck_mdp.head_pose_tracking(env, command_name=command_name, std=fast_std)
    else:
        # Same measurement as microduck_mdp.head_pose_tracking (whose call above cached the joint ids).
        asset = env.scene[_ROBOT.name]
        ids = env._head_pose_neck_ids
        q = asset.data.joint_pos
        measured = q[:, ids] + q[:, env._head_pose_bl_ids] * env._head_pose_bl_mask
        target = env.command_manager.get_command(command_name) + torch.tensor(fast_offset, device=env.device)
        err = measured - asset.data.default_joint_pos[:, ids] - target
        fast = torch.exp(-torch.square(err / fast_std)).mean(dim=-1)
    return (1.0 - gate) * slow + gate * fast


def head_pose_bias_at_rest(
    env: ManagerBasedRlEnv,
    speed_lo: float,
    speed_hi: float,
    command_name: str = "head_pose",
    tau_s: float = 1.0,
) -> torch.Tensor:
    """head_pose_bias_penalty faded out with speed: running, the head may hold an offset as a counterweight."""
    bias = microduck_mdp.head_pose_bias_penalty(env, command_name=command_name, tau_s=tau_s)
    return bias * (1.0 - speed_gate(env, speed_lo, speed_hi))
