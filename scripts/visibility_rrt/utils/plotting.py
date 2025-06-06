

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import visibility_rrt.utils.env as env
from visibility_rrt.utils.utils import calculate_fov_points, linewidth_from_data_units
import math
import numpy as np

class Plotting:
    def __init__(self, x_start, x_goal):
        self.xI, self.xG = x_start, x_goal
        self.env = env.Env()
        self.obs_bound = self.env.obs_boundary
        self.obs_circle = self.env.obs_circle
        self.obs_rectangle = self.env.obs_rectangle

    def animation(self, nodelist, path, name, animation=False):
        self.plot_grid(name)
        self.plot_visited(nodelist, animation)
        self.plot_path_fov(path, cam_range=3.5)
        self.plot_path(path)

    def animation_online(self, nodelist, name, animation=False):
        self.plot_grid(name)
        self.plot_visited(nodelist, animation)
        plt.pause(1.0)
        plt.close()

    def animation_connect(self, V1, V2, path, name):
        self.plot_grid(name)
        self.plot_visited_connect(V1, V2)
        self.plot_path(path)

    def plot_grid(self, name):
        fig, ax = plt.subplots()

        for (ox, oy, w, h) in self.obs_bound:
            ax.add_patch(
                patches.Rectangle(
                    (ox, oy), w, h,
                    edgecolor='white',
                    facecolor='white',
                    fill=True
                )
            )

        for (ox, oy, w, h) in self.obs_rectangle:
            ax.add_patch(
                patches.Rectangle(
                    (ox, oy), w, h,
                    edgecolor='black',
                    facecolor='gray',
                    fill=True
                )
            )

        for (ox, oy, r) in self.obs_circle:
            ax.add_patch(
                patches.Circle(
                    (ox, oy), r,
                    edgecolor='black',
                    facecolor='gray',
                    fill=True
                )
            )

        plt.plot(self.xI[0], self.xI[1], "bs", linewidth=3)
        plt.plot(self.xG[0], self.xG[1], "rs", linewidth=3)

        plt.title(name)
        eps = 0.0
        plt.xlim(self.env.x_range[0] - eps, self.env.x_range[1] + eps)
        plt.ylim(self.env.y_range[0] - eps, self.env.y_range[1] + eps)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.tight_layout()

        return ax, fig

    @staticmethod
    def plot_visited(nodelist, animation):
        if animation:
            count = 0
            for node in nodelist:
                count += 1
                if node.parent:
                    plt.plot([node.parent.x, node.x], [node.parent.y, node.y], "-g")
                    plt.gcf().canvas.mpl_connect('key_release_event',
                                                 lambda event:
                                                 [exit(0) if event.key == 'escape' else None])
                    if count % 10 == 0:
                        plt.pause(0.001)
        else:
            for node in nodelist:
                if node.parent:
                    plt.plot([node.parent.x, node.x], [node.parent.y, node.y], "-g")

    @staticmethod
    def plot_visited_connect(V1, V2):
        len1, len2 = len(V1), len(V2)

        for k in range(max(len1, len2)):
            if k < len1:
                if V1[k].parent:
                    plt.plot([V1[k].x, V1[k].parent.x], [V1[k].y, V1[k].parent.y], "-g")
            if k < len2:
                if V2[k].parent:
                    plt.plot([V2[k].x, V2[k].parent.x], [V2[k].y, V2[k].parent.y], "-g")

            plt.gcf().canvas.mpl_connect('key_release_event',
                                         lambda event: [exit(0) if event.key == 'escape' else None])

            if k % 2 == 0:
                plt.pause(0.001)

        plt.pause(0.01)

    @staticmethod
    def plot_path(path):
        if len(path) != 0:
            plt.plot([x[0] for x in path], [x[1] for x in path], '-r', linewidth=2)
            plt.pause(0.01)
            plt.savefig("LQR-CBF_result.PNG")
            plt.savefig("LQR-CBF_result.svg")
        plt.show()

    @staticmethod
    def plot_path_fov(path, cam_range):

        path = np.array(path)
        width = linewidth_from_data_units(cam_range/math.sqrt(2), plt.gca(), reference='y')
        plt.plot(path[:, 0], path[:, 1], 'k', alpha=0.5, linewidth=width)

    #def plot_path_fov(path, fov_angle, cam_range):
        """
        this function is ommitted for now. The visualization is not smooth
        """
        # if len(path) < 2:
        #     return  # Need at least two points to define a path

        # lefts = []
        # rights = []
        # for k in range(1, len(path)):
        #     prev_pos = path[k-1]
        #     print(prev_pos)
        #     cur_pos = path[k]
        #     gtheta = cur_pos[2]
        #     gtheta = math.atan2(cur_pos[1] - prev_pos[1], cur_pos[0] - prev_pos[0])
        #     print(cur_pos[2])
        #     if gtheta == None:
        #         gtheta = math.atan2(cur_pos[1] - prev_pos[1], cur_pos[0] - prev_pos[0])

        #     prev_fov_left, prev_fov_right = calculate_fov_points(prev_pos, gtheta, fov_angle=math.pi, cam_range=cam_range)
        #     cur_fov_left, cur_fov_right = calculate_fov_points(cur_pos, gtheta, fov_angle=math.pi, cam_range=cam_range)

        #     # Plot FOV union "tube"
        #     plt.plot([prev_fov_left[0], cur_fov_left[0]], [prev_fov_left[1], cur_fov_left[1]], 'k--', alpha=0.5)  # Left boundary
        #     plt.plot([prev_fov_right[0], cur_fov_right[0]], [prev_fov_right[1], cur_fov_right[1]], 'k--', alpha=0.5)  # Right boundary
        #     plt.fill([prev_fov_left[0], cur_fov_left[0], cur_fov_right[0], prev_fov_right[0]],
        #             [prev_fov_left[1], cur_fov_left[1], cur_fov_right[1], prev_fov_right[1]], 'k', alpha=0.1)  # FOV area
            
        #     lefts.append(prev_fov_left)
        #     rights.append(prev_fov_right)
        # print([lefts, rights])