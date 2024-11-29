import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
import hailo
from hailo_rpi_common import (
    get_default_parser,
    QUEUE,
    SOURCE_PIPELINE,
    DETECTION_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE,
    get_caps_from_pad,
    get_numpy_from_buffer,
    GStreamerApp,
    app_callback_class,
    dummy_callback,
    jpg_buffer
)



import paho.mqtt.client as mqtt
import json
import base64
import random
import time

# MQTT Broker 的地址和端口
broker_address = "localhost"
broker_port = 1883
topic = "/yolo/target"
# 定义初始时间戳
global initial_timestamp
initial_timestamp = time.time()

# publish_interval = 0.1  # 每 1 秒发布一次
client = mqtt.Client()

# 连接到 MQTT Broker
client.connect(broker_address, broker_port)


label_colors = {
    "Coco": (0, 255, 0),  # 绿色
    "milk": (255, 0, 0),  # 蓝色
    "chips": (0, 0, 255), # 红色
    "crackers": (255, 255, 0),  # 黄色
    "popcorn": (255, 0, 255),  # 紫色
    "crisps": (0, 255, 255)  # 青色
}


# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.new_variable = 42  # New variable example

    # def new_function(self):  # New function example
    #     return "The meaning of life is: "

# This is the callback function that will be called when data is available from the pipeline
def app_callback(pad, info, user_data):
    global initial_timestamp
    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()
    # Check if the buffer is valid
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Using the user_data to count the number of frames
    user_data.increment()
    string_to_print = f"Frame count: {user_data.get_count()}\n"

    # Get the caps from the pad
    format, width, height = get_caps_from_pad(pad)

    # If the user_data.use_frame is set to True, we can get the video frame from the buffer
    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        # Get video frame
        frame = get_numpy_from_buffer(buffer, format, width, height)

    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # Parse the detections
    Coco_number = 0
    milk_number = 0
    chips_number = 0
    crackers_number = 0
    popcorn_number = 0
    crisps_number = 0
    
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        
        x_min, y_min, x_max, y_max = bbox.xmin(), bbox.ymin(), bbox.xmax(), bbox.ymax()
        
        xmin = int(x_min * width)
        ymin = int(y_min * height)
        xmax = int(x_max * width)
        ymax = int(y_max * height)
        
        text = f"{label}: {confidence:.2f}"
        
        if label == "Coco":
            Coco_number  += 1
        if label == "milk":
            milk_number += 1
        if label =="chips":
            chips_number += 1
        if label =="crackers":
            crackers_number += 1
        if label =="popcorn":
            popcorn_number += 1
        if label =="crisps":
            crisps_number += 1
            
        color = label_colors.get(label, tuple(random.randint(0, 255) for _ in range(3)))
        
        # Draw the bounding box on the frame
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
        
        text_size = cv2.getTextSize(text,cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = xmin
        text_y = ymin - 10 if ymin - 10 > 10 else ymin + 10
        
        # Background rectangle for the text to be readable
        cv2.rectangle(frame, (text_x, text_y - text_size[1]), (text_x + text_size[0], text_y + 5), color, -1)
        
        # Draw the text
        cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
   
    _, buffer = cv2.imencode('.jpg', frame)
    frame = buffer.tobytes()
    # 定义当前时间戳
    current_timestamp = time.time()
    # 判断时间差是否大于1秒
    if current_timestamp - initial_timestamp > 1:
        print("大于1s,publish")
        data = {
            "Coco_number" : Coco_number,
            "milk_number" : milk_number,
            "chips_number" : chips_number,
            "crackers_number" : crackers_number,
            "popcorn_number" : popcorn_number,
            "crisps_number" : crisps_number,
           }

        payload = json.dumps(data)
        client.publish(topic, payload)

        # 更新初始时间戳为当前时间戳
        initial_timestamp = current_timestamp
    else:
        print("小于1s")        
 
    jpg_buffer.put(frame)
    
    # print("callback ok")
    
    return Gst.PadProbeReturn.OK

            
def SEND_PIPELINE(ip='127.0.0.1', port=5000, name='send'):
    send_pipeline = (
        f'{QUEUE(name=f"{name}_hailooverlay_q")} ! '
        f'hailooverlay name={name}_hailooverlay ! '
        f'{QUEUE(name=f"{name}_videoconvert_q")} ! '
        f'videoconvert name={name}_videoconvert n-threads=2 qos=false ! '
        f'{QUEUE(name=f"{name}_q")} ! '
        f'videoconvert ! openh264enc ! rtph264pay ! udpsink host=192.168.49.160 port=2000'
    )
    return send_pipeline


# -----------------------------------------------------------------------------------------------
# User Gstreamer Application
# -----------------------------------------------------------------------------------------------
# This class inherits from the hailo_rpi_common.GStreamerApp class
class GStreamerDetectionApp(GStreamerApp):
    def __init__(self, app_callback, user_data):
        parser = get_default_parser()
        # Add additional arguments here
        parser.add_argument(
            "--network",
            default="yolov6n",
            choices=['yolov6n', 'yolov8s'],
            help="Which Network to use, default is yolov6n",
        )
        parser.add_argument(
            "--hef-path",
            default=None,
            help="Path to HEF file",
        )
        parser.add_argument(
            "--labels-json",
            default=None,
            help="Path to costume labels JSON file",
        )
        args = parser.parse_args()
        # Call the parent class constructor
        super().__init__(args, user_data)
        # Additional initialization code can be added here
        # Set Hailo parameters these parameters should be set based on the model used
        self.batch_size = 8
        self.network_width = 640
        self.network_height = 640
        self.network_format = "RGB"
        nms_score_threshold = 0.3
        nms_iou_threshold = 0.45

        if args.hef_path is not None:
            self.hef_path = args.hef_path
        # Set the HEF file path based on the network
        elif args.network == "yolov6n":
            self.hef_path = os.path.join(self.current_path, '../resources/yolov6n.hef')
        elif args.network == "yolov8s":
            self.hef_path = os.path.join(self.current_path, '../resources/yolov8s_h8l.hef')
        else:
            assert False, "Invalid network type"

        # User-defined label JSON file
        self.labels_json = args.labels_json

        self.app_callback = app_callback

        self.thresholds_str = (
            f"nms-score-threshold={nms_score_threshold} "
            f"nms-iou-threshold={nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        # Set the process title
        setproctitle.setproctitle("Hailo Detection App")

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(self.video_source)
        detection_pipeline = DETECTION_PIPELINE(hef_path=self.hef_path, batch_size=self.batch_size, labels_json=self.labels_json, additional_params=self.thresholds_str)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        send_pipeline = SEND_PIPELINE()
        display_pipeline = DISPLAY_PIPELINE(video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps)
        pipeline_string = (
            f'{source_pipeline} '
            f'{detection_pipeline} ! '
            f'{user_callback_pipeline} !'
            f'{send_pipeline}'
        )
        
        print(pipeline_string)
        return pipeline_string

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = user_app_callback_class()
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
    
    

    

    
   
    
    
