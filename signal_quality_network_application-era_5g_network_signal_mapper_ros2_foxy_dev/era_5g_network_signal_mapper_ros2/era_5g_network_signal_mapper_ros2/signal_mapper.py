#!/usr/bin/env python3
import os
import rclpy
import numpy as np
import std_msgs.msg as std_msgs
import struct
import tf2_ros
import sensor_msgs_py.point_cloud2 as pcl2
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import String
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from tf2_ros import TransformException

import era_5g_network_signal_mapper_ros2.declare_param as paramm


class FramePublisher(Node):

    def __init__(self):
        
        super().__init__('robot_tf2_frame_publisher')
        

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)


        # Retreive parameters from ENV/ launch/params.yaml file or set default values automaticaly
        self.robot_base_frame = paramm.param_set_string(self,"my_base_link", "robot_base_link")
        self.semantic_map_frame = paramm.param_set_string(self,"my_semantic_map_frame", "semantic_map")
        self.map_frame = paramm.param_set_string(self,"my_map_frame", "map")

        global r, g, b, height, lenght, lamba
        r = 124 # 124
        g = 252 # 252
        b = 0   # 0

        height = 0.3
        lenght = 0.3
        lamba = 0.05

        self.current_pcl_pub = self.create_publisher(PointCloud2, '/current_semantic_pcl', 10)        
        self.pcl_colour_subscriber = self.create_subscription(String, "/pcl_colour",self.signal_color_callback,1)

        # Initialize the transform broadcaster

        self.tf_broadcaster = TransformBroadcaster(self)
        self.timer = self.create_timer(1.0, self.on_timer)


    def on_timer(self):
            try:
                
                trans = self.tf_buffer.lookup_transform(self.map_frame, self.robot_base_frame, rclpy.time.Time())
                self.publish_pointcloud_while_broadcasting(trans)
                self.create_simple_pointcloud()

            except TransformException as ex:
                    self.get_logger().info(str(ex))
                    #return        

    
    def publish_pointcloud_while_broadcasting(self,trans):
            
            t = TransformStamped()

            # Read message content and assign it to
            # corresponding tf variables
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = 'map'
            t.child_frame_id = self.semantic_map_frame
            # Robot only exists in 2D, thus we get x and y translation
            # coordinates from the message and set the z coordinate to 0

            t.transform.translation.x =   trans.transform.translation.x
            t.transform.translation.y = trans.transform.translation.y
            t.transform.translation.z = trans.transform.translation.z

            # For the same reason, robot can only rotate around one axis
            # and this why we set rotation in x and y to 0 and obtain
            # rotation in z axis from the message
            # q = tf_transformations.quaternion_from_euler(0, 0, msg.theta)
            t.transform.rotation.x = trans.transform.rotation.x
            t.transform.rotation.y = trans.transform.rotation.y
            t.transform.rotation.z = trans.transform.rotation.z
            t.transform.rotation.w = 1.0

            # Send the transformation
            self.tf_broadcaster.sendTransform(t)


    # Set pcl colour callback
    def signal_color_callback(self, msg):
        self.get_logger().info("COLOR CHANGED!!")
        self.get_logger().info(msg.data)
        '''
        Yellow = Colour([255, 255, 0])
        Orange = Colour([255, 165, 0])
        '''
        global r, g, b
        if msg.data == "GREEN":
            self.get_logger().info("CHANGE TO GREEN")
            r = 124
            g = 252
            b = 0
        elif msg.data == "RED":
            self.get_logger().info("CHANGE TO RED")
            r = 255
            g = 0
            b = 0
        elif msg.data == "BLUE":
            self.get_logger().info("CHANGE TO BLUE")
            r = 128
            g = 0
            b = 0
        elif msg.data == "YELLOW":
            self.get_logger().info("CHANGE TO BLUE")
            r = 255
            g = 255
            b = 0
        elif msg.data == "ORANGE":
            self.get_logger().info("CHANGE TO BLUE")
            r = 255
            g = 165
            b = 0
    

    def create_simple_pointcloud(self):

        rgb = struct.unpack('I', struct.pack('BBBB', b, g, r, 0))[0]
        print(rgb)

        cloud_points = []
        for x in np.arange(0,height,lamba):
            for y in np.arange(-lenght,lenght,lamba):
                cloud_points.append([x, y, 0.0, rgb])
                cloud_points.append([-x, y, 0.0, rgb])

        # ROS DATATYPE 
        ros_dtype = PointField.FLOAT32

        # The PointCloud2 message also has a header which specifies which 
        # coordinate frame it is represented in.
        header = std_msgs.Header()
        
        # The fields specify what the bytes represents. The first 4 bytes 
        # represents the x-coordinate, the next 4 the y-coordinate, etc.
        fields = [
            PointField(name='x', offset=0, datatype=ros_dtype, count=1),
            PointField(name='y', offset=4, datatype=ros_dtype, count=1),
            PointField(name='z', offset=8, datatype=ros_dtype, count=1),
            PointField(name='rgb', offset=12, datatype=PointField.UINT32, count=1)
        ]

        pcl_msg = pcl2.create_cloud(header, fields, cloud_points)
        pcl_msg.header.stamp = self.get_clock().now().to_msg()
        pcl_msg.header.frame_id = self.semantic_map_frame
        self.current_pcl_pub.publish(pcl_msg)


def main(args=None):
    rclpy.init(args=args)
    node = FramePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()