from ultralytics import YOLO
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import cv2
import tensorflow as tf
import math
import time
import datetime
import os, sys, re
import mysql.connector
import json
import importlib
from shapely.geometry import Polygon

# location_id = sys.argv[1]
model = YOLO("yolov8x.pt")
# alpha = 0.3 # that's your transparency factor
# const_roi = importlib.import_module('roi.const_roi_'+ location_id)

# def drawArea(img, area, colors):
#     polygon = Polygon(area)
#     int_coords = lambda x: np.array(x).round().astype(np.int32)
#     exterior = [int_coords(polygon.exterior.coords)]

#     overlay = img.copy()
#     cv2.fillPoly(overlay, exterior, color=colors)
#     cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
#     return img

def plot_bboxes(frame, box, obj_data, track_id):
    # Define xyxy
    x1 = int(box[0])
    x2 = int(box[2])
    y1 = int(box[1])
    y2 = int(box[3])
    #Define colors
    #colors = [(6, 112, 83), (253, 246, 160), (40, 132, 70), (205, 97, 162), (149, 196, 30), (106, 19, 161), (127, 175, 225), (115, 133, 176), (83, 156, 8), (182, 29, 77), (180, 11, 251), (31, 12, 123), (23, 6, 115), (167, 34, 31), (176, 216, 69), (110, 229, 222), (72, 183, 159), (90, 168, 209), (195, 4, 209), (135, 236, 21), (62, 209, 199), (87, 1, 70), (75, 40, 168), (121, 90, 126), (11, 86, 86), (40, 218, 53), (234, 76, 20), (129, 174, 192), (13, 18, 254), (45, 183, 149), (77, 234, 120), (182, 83, 207), (172, 138, 252), (201, 7, 159), (147, 240, 17), (134, 19, 233), (202, 61, 206), (177, 253, 26), (10, 139, 17), (130, 148, 106), (174, 197, 128), (106, 59, 168), (124, 180, 83), (78, 169, 4), (26, 79, 176), (185, 149, 150), (165, 253, 206), (220, 87, 0), (72, 22, 226), (64, 174, 4), (245, 131, 96), (35, 217, 142), (89, 86, 32), (80, 56, 196), (222, 136, 159), (145, 6, 219), (143, 132, 162), (175, 97, 221), (72, 3, 79), (196, 184, 237), (18, 210, 116), (8, 185, 81), (99, 181, 254), (9, 127, 123), (140, 94, 215), (39, 229, 121), (230, 51, 96), (84, 225, 33), (218, 202, 139), (129, 223, 182), (167, 46, 157), (15, 252, 5), (128, 103, 203), (197, 223, 199), (19, 238, 181), (64, 142, 167), (12, 203, 242), (69, 21, 41), (177, 184, 2), (35, 97, 56), (241, 22, 161)]
    colors = [(89, 161, 197),(67, 161, 255),(19, 222, 24),(186, 55, 2),(167, 146, 11),(190, 76, 98),(130, 172, 179),(115, 209, 128),(204, 79, 135),(136, 126, 185),(209, 213, 45),(44, 52, 10),(101, 158, 121),(179, 124, 12),(25, 33, 189),(45, 115, 11),(73, 197, 184),(62, 225, 221),(32, 46, 52),(20, 165, 16),(54, 15, 57),(12, 150, 9),(10, 46, 99),(94, 89, 46),(48, 37, 106),(42, 10, 96),(7, 164, 128),(98, 213, 120),(40, 5, 219),(54, 25, 150),(251, 74, 172),(0, 236, 196),(21, 104, 190),(226, 74, 232),(120, 67, 25),(191, 106, 197),(8, 15, 134),(21, 2, 1),(142, 63, 109),(133, 148, 146),(187, 77, 253),(155, 22, 122),(218, 130, 77),(164, 102, 79),(43, 152, 125),(185, 124, 151),(95, 159, 238),(128, 89, 85),(228, 6, 60),(6, 41, 210),(11, 1, 133),(30, 96, 58),(230, 136, 109),(126, 45, 174),(164, 63, 165),(32, 111, 29),(232, 40, 70),(55, 31, 198),(148, 211, 129),(10, 186, 211),(181, 201, 94),(55, 35, 92),(129, 140, 233),(70, 250, 116),(61, 209, 152),(216, 21, 138),(100, 0, 176),(3, 42, 70),(151, 13, 44),(216, 102, 88),(125, 216, 93),(171, 236, 47),(253, 127, 103),(205, 137, 244),(193, 137, 224),(36, 152, 214),(17, 50, 238),(154, 165, 67),(114, 129, 60),(119, 24, 48),(73, 8, 110)]
    # font
    font = cv2.FONT_HERSHEY_SIMPLEX
    # org
    org = (x1,y1 - 10)
    # fontScale
    fontScale = 1/2
    # Line thickness of 2 px
    thickness = 2

    frm = cv2.putText(frame, str(obj_data[0]) + " : " + str(obj_data[2]), org, font, fontScale, colors[obj_data[1]], thickness, cv2.LINE_AA)
    frm = cv2.circle(frame, (x2,y2), 3, colors[obj_data[1]], -1)
    result = cv2.rectangle(frm, (x1,y1), (x2,y2), colors[obj_data[1]], 1)

    return result

def mse(img1, img2):
   h, w = img1.shape
   diff = cv2.subtract(img1, img2)
   err = np.sum(diff**2)
   mse = err/(float(h*w))
   return mse, diff

contraflow_in = {}
contraflow_out = {}

# results = model.track(source='rtsp://admin:Holowits123@192.168.1.132:554/LiveMedia/ch1/Media2', stream=True, show=False, conf=0.3, tracker="bytetrack.yaml")
results = model.track(source='rtsp://root:cctv123456@192.168.203.106:554/live1s2.sdp', stream=True, show=False, conf=0.3, tracker="bytetrack.yaml")
for r in results:

    boxes = r.boxes  # Boxes object for bbox outputs
    masks = r.masks  # Masks object for segment masks outputs
    probs = r.probs  # Class probabilities for classification outputs
    frame = r.orig_img
    print('shape = ' + str(frame.shape)) # Print image shape
    roi = frame[300:576, 200:320]
    or_roi = cv2.imread('or_roi.png')
    img1 = cv2.cvtColor(or_roi, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # cv2.imwrite('/home/module/yolov8/or_roi.png', roi)
    error, diff = mse(img1, img2)
    print("Image matching Error between the two images:",error)

    if boxes.id is not None:
        for c, xyxy, conf, track_id in zip(r.boxes.cls, r.boxes.xyxy, r.boxes.conf, r.boxes.id):
            obj_class = model.names[int(c)]
            obj_classId = int(c)
            score = float(conf.item())
            score = round(score, 2)
            obj_data = [obj_class, obj_classId, score]
            # xyxy = pt  # get box coordinates in (top, left, bottom, right) format
            x1 = int(xyxy[0].item())
            y1 = int(xyxy[1].item())
            x2 = int(xyxy[2].item())
            y2 = int(xyxy[3].item())
            box = [x1, y1, x2, y2]
            track_id = int(track_id.item())
            obj_point = (int(x2), int(y2))
            frame = plot_bboxes(frame, box, obj_data, track_id)

    if len(contraflow_in) > 100 :
        contraflow_in.pop(next(iter(contraflow_in)))
    
    cv2.imshow("difference", diff)
    cv2.imshow("roi", roi)
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(30)
    if key == 27:
        break
