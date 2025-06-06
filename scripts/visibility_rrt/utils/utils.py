import math
import numpy as np

import visibility_rrt.utils.env as env
from visibility_rrt.utils.node import Node

"""
Created on Jan 23, 2024
@author: Taekyung Kim

@description: majority of this code if for collision checking with obstacles (rect, circle, boundary)

@required-scripts: env.py, node.py

"""

def angular_diff(a, b):
    """Angle difference from b to a (a - b)"""
    d = a - b
    if d > math.pi:
        d -= 2 * math.pi
    elif d < -math.pi:
        d += 2 * math.pi
    return d

def angle_normalize(x):
    return (((x + math.pi) % (2 * math.pi)) - math.pi)

# Function to calculate the FOV triangle points
def calculate_fov_points(position, yaw, fov_angle =  70 * (math.pi/180), cam_range = 3):
    half_fov = fov_angle/2
    left_angle = yaw - half_fov
    right_angle = yaw + half_fov

    # Calculate points for the edges of the FOV
    left_point = (position[0] + cam_range * math.cos(left_angle), position[1] + cam_range * math.sin(left_angle))
    right_point = (position[0] + cam_range * math.cos(right_angle), position[1] + cam_range * math.sin(right_angle))

    return left_point, right_point


def linewidth_from_data_units(linewidth, axis, reference='y'):
    """
    Convert a linewidth in data units to linewidth in points.

    Parameters
    ----------
    linewidth: float
        Linewidth in data units of the respective reference-axis
    axis: matplotlib axis
        The axis which is used to extract the relevant transformation
        data (data limits and size must not change afterwards)
    reference: string
        The axis that is taken as a reference for the data width.
        Possible values: 'x' and 'y'. Defaults to 'y'.

    Returns
    -------
    linewidth: float
        Linewidth in points
    """
    fig = axis.get_figure()
    if reference == 'x':
        length = fig.bbox_inches.width * axis.get_position().width
        value_range = np.diff(axis.get_xlim())
    elif reference == 'y':
        length = fig.bbox_inches.height * axis.get_position().height
        value_range = np.diff(axis.get_ylim())
    # Convert length to points
    length *= 72
    # Scale linewidth to value range
    return linewidth * (length / value_range)


class Utils:
    def __init__(self):
        self.env = env.Env()

        self.delta = 0.5
        self.obs_circle = self.env.obs_circle
        self.obs_rectangle = self.env.obs_rectangle
        self.obs_boundary = self.env.obs_boundary

    def update_obs(self, obs_cir, obs_bound, obs_rec):
        self.obs_circle = obs_cir
        self.obs_boundary = obs_bound
        self.obs_rectangle = obs_rec

    def get_obs_vertex(self):
        delta = self.delta
        obs_list = []

        for (ox, oy, w, h) in self.obs_rectangle:
            vertex_list = [[ox - delta, oy - delta],
                           [ox + w + delta, oy - delta],
                           [ox + w + delta, oy + h + delta],
                           [ox - delta, oy + h + delta]]
            obs_list.append(vertex_list)

        return obs_list

    def is_intersect_rec(self, start, end, o, d, a, b):
        v1 = [o[0] - a[0], o[1] - a[1]]
        v2 = [b[0] - a[0], b[1] - a[1]]
        v3 = [-d[1], d[0]]

        div = np.dot(v2, v3)

        if div == 0:
            return False

        t1 = np.linalg.norm(np.cross(v2, v1)) / div
        t2 = np.dot(v1, v3) / div

        if t1 >= 0 and 0 <= t2 <= 1:
            shot = Node((o[0] + t1 * d[0], o[1] + t1 * d[1]))
            dist_obs = self.get_dist(start, shot)
            dist_seg = self.get_dist(start, end)
            if dist_obs <= dist_seg:
                return True

        return False

    def is_intersect_circle(self, o, d, a, r):
        d2 = np.dot(d, d)
        delta = self.delta

        if d2 == 0:
            return False

        t = np.dot([a[0] - o[0], a[1] - o[1]], d) / d2

        if 0 <= t <= 1:
            shot = Node((o[0] + t * d[0], o[1] + t * d[1]))
            if self.get_dist(shot, Node(a)) <= r + delta:
                return True
        return False

    def is_collision(self, start, end):
        if self.is_inside_obs(start) or self.is_inside_obs(end):
            return True

        o, d = self.get_ray(start, end)
        obs_vertex = self.get_obs_vertex()

        for (v1, v2, v3, v4) in obs_vertex:
            if self.is_intersect_rec(start, end, o, d, v1, v2):
                return True
            if self.is_intersect_rec(start, end, o, d, v2, v3):
                return True
            if self.is_intersect_rec(start, end, o, d, v3, v4):
                return True
            if self.is_intersect_rec(start, end, o, d, v4, v1):
                return True

        for (x, y, r) in self.obs_circle:
            if self.is_intersect_circle(o, d, [x, y], r):
                return True

        return False

    def is_inside_obs(self, node):
        delta = self.delta

        for (x, y, r) in self.obs_circle:
            if math.hypot(node.x - x, node.y - y) <= r + delta:
                return True

        for (x, y, w, h) in self.obs_rectangle:
            if 0 <= node.x - (x - delta) <= w + 2 * delta \
                    and 0 <= node.y - (y - delta) <= h + 2 * delta:
                return True

        for (x, y, w, h) in self.obs_boundary:
            if 0 <= node.x - (x - delta) <= w + 2 * delta \
                    and 0 <= node.y - (y - delta) <= h + 2 * delta:
                return True

        return False

    @staticmethod
    def get_ray(start, end):
        orig = [start.x, start.y]
        direc = [end.x - start.x, end.y - start.y]
        return orig, direc

    @staticmethod
    def get_dist(start, end):
        return math.hypot(end.x - start.x, end.y - start.y)
    @staticmethod
    def integrate_single_integrator(self, x_init, u, dt):
        # dimension 2, position [x1,x2]^T, control u = [u1,u2]^T, dt comes from control updates
        x_traj = np.array([x_init])
        x_current = x_traj.copy()
        num_steps = len(u)

        for i in range(num_steps):
            u_current = u[i]
            x_current[0, 0] = x_current[0, 1] + dt * u_current[0]
            x_current[0, 1] = x_current[0, 1] + dt * u_current[1]
            x_traj = np.concatenate((x_traj, x_current), axis=0)
        return x_traj


    @staticmethod
    def integrate_double_integrator(x_init, u, dt):
        # dimension 4, [x1,x2,x3,x4]^T [pos_1, vel_1, pos_2, vel_2]^T, control u = [u1,u2]^T, dt comes from control updates
        x_traj = np.array([x_init],dtype=np.float32)
        x_current = x_traj.copy()
        num_steps = len(u)

        for i in range(num_steps):
            u_current = u[i]
            x_current[0,0] = x_current[0,0] + x_current[0,1] * dt + 0.5 * u_current[0] * dt ** 2
            x_current[0,1] = x_current[0,1] + dt * u_current[0]
            x_current[0,2] = x_current[0,2] + x_current[0,3] * dt + 0.5 * u_current[1] * dt ** 2
            x_current[0,3] = x_current[0,3] + dt * u_current[1]
            x_traj = np.concatenate((x_traj, x_current), axis=0)

        return x_traj