"""The sprint's own reward terms (see EXPERIMENTS.md for the run that introduced each).

Speed here is `lane_speed`: the trunk's world velocity along the heading the robot spawned with.
That is progress down the lane the Arena measures, not along wherever the nose points, so walking
crabwise earns less. `speed_gate` turns that speed into 0..1 (smoothstep), the share of a balance
term's tolerance that is relaxed: a term relaxes only once the robot is actually running.
"""

from __future__ import annotations

import torch
from mjlab.envs import ManagerBasedRlEnv
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.utils.lab_api.math import quat_apply_inverse

from mjlab_microduck.tasks import mdp as microduck_mdp

_ROBOT = SceneEntityCfg("robot")


def _yaw(quat: torch.Tensor) -> torch.Tensor:
    w, x, y, z = quat.unbind(-1)
    return torch.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


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


def upright_lean(
    env: ManagerBasedRlEnv,
    std: float,
    lean_std: float,
    speed_lo: float,
    speed_hi: float,
    asset_cfg: SceneEntityCfg = _ROBOT,
) -> torch.Tensor:
    """`upright` whose tolerance for a FORWARD (nose-down) lean widens from `std` to `lean_std` with speed.

    exp(-(g_y² + min(g_x, 0)²) / std² - max(g_x, 0)² / σ_fwd²), g the projected gravity of the body:
    nose-down gives g_x > 0. Roll and a backward lean keep `std` at every speed.
    """
    asset = env.scene[asset_cfg.name]
    quat = asset.data.body_link_quat_w[:, asset_cfg.body_ids, :].squeeze(1)
    g = quat_apply_inverse(quat, asset.data.gravity_vec_w.expand(quat.shape[0], 3))
    gate = speed_gate(env, speed_lo, speed_hi)
    var_fwd = std**2 + gate * (lean_std**2 - std**2)
    fwd = torch.clamp(g[:, 0], min=0.0)
    back = torch.clamp(g[:, 0], max=0.0)
    return torch.exp(-(torch.square(g[:, 1]) + torch.square(back)) / std**2 - torch.square(fwd) / var_fwd)


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
    fast_std: float,
    speed_lo: float,
    speed_hi: float,
    command_name: str = "head_pose",
) -> torch.Tensor:
    """head_pose_tracking whose tolerance widens from `std` to `fast_std` with speed (blend of the two)."""
    gate = speed_gate(env, speed_lo, speed_hi)
    slow = microduck_mdp.head_pose_tracking(env, command_name=command_name, std=std)
    fast = microduck_mdp.head_pose_tracking(env, command_name=command_name, std=fast_std)
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
