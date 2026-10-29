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
