#!/usr/bin/env python3 
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math 
import time
from rrtStarCBF import RRTStarCBF
 
class GoToPoint(Node):
    def __init__(self):
        super().__init__('go_to_point')

        # Publisher for sending velocity commands to the robot
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)

        # Read goal positions from a CSV file
        self.goal_list = self.get_goals()

        # Filter out closely spaced points to reduce unnecessary movements
        self.goal_list = self.filter_path_by_distance(self.goal_list, d_thresh=0.2)

        # Begin navigating to the waypoints
        self.go_to_waypoints()

    def go_to_waypoints(self):
        """
        Iterates through each point in the filtered goal list, rotates to face the goal, and moves straight toward it.
        Assumes an initial known pose for the robot.
        """
        current_x, current_y = 1.5, 0.5
        current_theta = 0

        for goal_x, goal_y in self.goal_list:
            # Compute the difference between current and goal positions 
            delta_x = goal_x - current_x
            delta_y = goal_y - current_y
 
            # Calculate the angle required to face the goal
            target_angle = math.atan2(delta_y, delta_x)
            angle_to_rotate = target_angle - current_theta

            # Normalize the angle to be between [-pi, pi]
            angle_to_rotate = math.atan2(math.sin(angle_to_rotate), math.cos(angle_to_rotate))

            # Rotate the robot
            print("Angle to rotate:", angle_to_rotate)
            self.rotate(angle_to_rotate)

            # Compute the straight-line distance to the goal
            distance = math.hypot(delta_x, delta_y)
            print("Distance to move:", distance)

            # Move the robot forward
            self.move_straight(distance)

            # Update the internal robot state
            current_x = goal_x
            current_y = goal_y
            current_theta = target_angle

        # Stop the robot after reaching the final point
        self.stop_robot()

    def rotate(self, angle, angular_speed=0.1):
        """
        Rotates the robot by the given angle using open-loop control.
        Assumes a constant angular speed.
        """
        twist = Twist()
        twist.angular.z = angular_speed if angle > 0 else -angular_speed

        rotated = 0.0
        dt = 0.02  # Duration per loop (in seconds)

        while abs(rotated) < abs(angle):
            self.publisher_.publish(twist)
            rotated += angular_speed * dt
            print(f"Rotated: {rotated:.2f} / {angle:.2f}")
            time.sleep(dt)

        self.stop_robot()

    def move_straight(self, distance, linear_speed=0.1):
        """
        Moves the robot forward by the given distance using open-loop control.
        Assumes a constant linear speed.
        """
        twist = Twist()
        twist.linear.x = linear_speed

        moved = 0.0
        dt = 0.04  # Duration per loop (in seconds)

        while moved < distance:
            self.publisher_.publish(twist)
            moved += linear_speed * dt
            print(f"Moved: {moved:.2f} / {distance:.2f}")
            time.sleep(dt)

        self.stop_robot()

    def stop_robot(self):
        """
        Publishes a zero-velocity command to stop the robot.
        """
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.publisher_.publish(twist)

    def filter_path_by_distance(self, path, d_thresh):
        """
        Filters out points in the path that are closer than d_thresh to the previous retained point.
        Also applies a coordinate transformation to match the simulation frame.
        """
        if not path:
            return []

        filtered = [path[0]]  # Always keep the first point

        for point in path[1:-1]:  # Skip the last point for now
            prev = filtered[-1]
            dist = math.hypot(point[0] - prev[0], point[1] - prev[1])
            if dist >= d_thresh:
                filtered.append(point)

        filtered.append(path[-1])  # Always include the last point

        # Transform coordinates to match simulation reference frame
        filtered_adjusted = [(y,5-x) for x, y in filtered]
        print(filtered_adjusted)
        return filtered_adjusted

    def get_goals(self):   
        # Create RRT* planner and plan path
        rrt_star = RRTStarCBF(start=(4.5, 1.5), goal=(4.5, 4.5), map_size=(5.0, 5.0)) 

        # record the start time
        t0 = time.time()

        # run the planner

        raw_path = rrt_star.plan()

        # record the end time
        t1 = time.time()

        planning_time = t1 - t0
        print(f"Planning took {planning_time:.3f} seconds")
        
        rrt_star.plot(rrt_star, raw_path)      
 
        return raw_path 

def main(args=None):
    """
    Entry point of the program: initializes and spins the node.
    """
    rclpy.init(args=args)
    node = GoToPoint()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
