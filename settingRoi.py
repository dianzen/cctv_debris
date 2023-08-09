# import the required library
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


def getDataLocation(connection, id):
    mycursor = connection.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM locations WHERE id = " + str(id) )
    myresult = mycursor.fetchall()
    mycursor.close()
    return myresult[0]

# define a function to display the coordinates of

# of the points clicked on the image
def click_event(event, x, y, flags, params):
   if event == cv2.EVENT_LBUTTONDOWN:
      coordinates.append(f'({x},{y})')
      # print(f'({x},{y})')
      print(coordinates)
      
      # put coordinates as text on the image
      cv2.putText(img, f'({x},{y})',(x,y),
      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
      
      # draw point on the image
      cv2.circle(img, (x,y), 3, (0,255,255), -1)
 
# read the input image
# img = cv2.imread('temp/cam2_antrean.jpg')
location_id = sys.argv[1]
connection = mysql.connector.connect(host='192.168.1.90', database='smartcctv', user='pcs', password='123456')
data_loc = getDataLocation(connection, location_id)
# print(data_loc['link_address'])
coordinates = []
stream_address = data_loc['link_address']
cap = cv2.VideoCapture(stream_address)
ret, img = cap.read() # Extract image from stream

# create a window
cv2.namedWindow('Point Coordinates')

# bind the callback function to window
cv2.setMouseCallback('Point Coordinates', click_event)

# display the image
while True:
   cv2.imshow('Point Coordinates',img)
   k = cv2.waitKey(1) & 0xFF
   if k == 27:
      break
cv2.destroyAllWindows()
