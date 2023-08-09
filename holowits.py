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
from skimage.metrics import structural_similarity


def getDataLocation(connection, id):
    mycursor = connection.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM locations WHERE id = " + str(id) )
    myresult = mycursor.fetchall()
    mycursor.close()
    return myresult[0]

def checkingLastEvent(mydb, loc_id, event_id):
    print('checking last event')
    mycursor3 = mydb.cursor()
    mycursor3.execute("SELECT CURRENT_TIMESTAMP() as _now, waktu, TIMESTAMPDIFF(MINUTE, waktu, CURRENT_TIMESTAMP()) AS difference FROM capture WHERE location_id = "+str(loc_id)+" AND event_id = "+str(event_id)+" ORDER BY waktu DESC LIMIT 1")
    myresult = mycursor3.fetchall()
    numrow = mycursor3.rowcount
    mycursor3.close()
    if numrow > 0:
        difference = int(myresult[0][2])
        if difference > 1 :
            return True
        else:
            return False
    
    return True

def writeToLive(conn, loc_id, event_id, blobdata, record_path):
    print('write data to live')
    
    mydb = conn

    if checkingLastEvent(mydb, loc_id, event_id) :
        mycursor1 = mydb.cursor()
        sSQLExist = "DELETE FROM live WHERE location_id = " + str(loc_id)
        mycursor1.execute(sSQLExist)
        mydb.commit()
        mycursor1.close()

        mycursor2 = mydb.cursor()
        sSQL = "INSERT INTO live (location_id, event_id, capture, record_path, waktu) VALUES (%s, %s, _binary %s, %s, CURRENT_TIMESTAMP)"
        val = (loc_id, event_id, blobdata, record_path)
        mycursor2.execute(sSQL, val)
        mydb.commit()
        mycursor2.close()
        
        mycursor3 = mydb.cursor()
        mycursor3.execute("SELECT id FROM capture ORDER BY id DESC LIMIT 1")
        myresult = mycursor3.fetchall()
        mycursor3.close()
        # return myresult[0][0]
        id_capture = myresult[0][0]
            
        print('done')
        return id_capture
    
    print('skip')
    return 0

def writeToDataTrain(conn, loc_id, event_id, blobdata):
    print('write data to data train')
    
    mydb = conn

    mycursor2 = mydb.cursor()
    sSQL = "INSERT INTO live (location_id, event_id, capture, waktu) VALUES (%s, %s, _binary %s, CURRENT_TIMESTAMP)"
    val = (loc_id, event_id, blobdata)
    mycursor2.execute(sSQL, val)
    mydb.commit()
    mycursor2.close()

    print('done data train')

def writeToSpeed(conn, loc_id, speed, car_id):
    print('write data to speed')
    
    mydb = conn

    mycursor2 = mydb.cursor()
    sSQL = "INSERT IGNORE INTO speed (id, location_id, waktu, speed) VALUES (%s, %s, CURRENT_TIMESTAMP(), %s)"
    val = (car_id, loc_id, speed)
    mycursor2.execute(sSQL, val)
    mydb.commit()
    mycursor2.close()

    print('done speed')
    

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def writeToMsgLog(conn, msg):
    mydb = conn
    mycursor2 = mydb.cursor()
    query = 'INSERT INTO log_message (waktu, message, flag1) VALUES ( CURRENT_TIMESTAMP(), "'+str(msg)+'" , 1) '
    # sSQL = "INSERT INTO live (location_id, event_id, capture, waktu) VALUES (%s, %s, _binary %s, CURRENT_TIMESTAMP)"
    mycursor2.execute(query)
    mydb.commit()
    mycursor2.close()

def sender(conn, loc, events, idcapture, loc_id):
    # https://chat.whatsapp.com/DHciUA6VyZbFAydU8rSPEs
    # https://chat.whatsapp.com/Ket2h94zTcNAQCndwJbwNk => grup test
    if idcapture != 0:
        loc_path = loc.replace(" ", "_")
        events_path = events.replace(" ", "_")
        img_path = "http://serbaraja-tollroad.co.id:20444/Show/" + str(loc_path) + "/" + str(idcapture) + "/" + str(events_path)
        stream = getStreamLink(conn, loc_id)
        msg = "*ALERT NOTIFY*\n\n"
        msg = msg + " - Location : " + str(loc) + "\n"
        msg = msg + " - Event : " + str(events) + "\n"
        msg = msg + " - Image : " + str(img_path) + "\n"
        msg = msg + " - Streaming : " + str(stream) + "\n"
        token = getToken(conn)
        ApiUrl = 'http://116.203.191.58/api/async_send_message_group_id'
        phone = "Ket2h94zTcNAQCndwJbwNk" 
        headers={'Content-type': 'application/json'}
        data = {'group_id': str(phone), 'key': str(token), 'message': str(msg), 'skip_link': True}
        # print(arrAlat)
        hit = requests.post(ApiUrl, data=json.dumps(data), headers=headers)
        response = hit.content.decode("utf-8")
        writeToMsgLog(conn, str(msg))
        return response

def getToken(connection):
    mycursor = connection.cursor()
    mycursor.execute("SELECT token_id FROM token ORDER BY `update` DESC LIMIT 1")
    myresult = mycursor.fetchall()
    mycursor.close()
    return myresult[0][0]

def getStreamLink(connection, id_loc):
    mycursor = connection.cursor()
    mycursor.execute("SELECT stream_link FROM locations WHERE id = "+str(id_loc)+" LIMIT 1")
    myresult = mycursor.fetchall()
    mycursor.close()
    return myresult[0][0]

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

def writeImage(filename, box, image, caption):
    if os.path.exists(filename):
        os.remove(filename)
    # Start coordinate, here (0, 0)
    x1 = int(box[0])
    x2 = int(box[2])
    y1 = int(box[1])
    y2 = int(box[3])
    
    start_point = (x1 - 20, y1 - 20)
    
    # End coordinate
    end_point = (x1, y1)
    
    # Red color in BGR 
    color = (0, 0, 255)
    
    # Line thickness of 9 px 
    thickness = 3
    
    # Using cv2.arrowedLine() method 
    # with thickness of 9 px 
    if caption != '-':
        image = cv2.putText(image, str(caption), (int(x1) , int(y2 + 15)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0), 4)
        image = cv2.putText(image, str(caption), (int(x1) , int(y2 + 15)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255), 2)
    image = cv2.arrowedLine(image, start_point, end_point, color, 2, 8, 0, 0.5)
    cv2.imwrite(filename,image)

    blob = convertToBinaryData(filename)

    return blob

def drawArea(img, area, colors):
    polygon = Polygon(area)
    int_coords = lambda x: np.array(x).round().astype(np.int32)
    exterior = [int_coords(polygon.exterior.coords)]

    overlay = img.copy()
    cv2.fillPoly(overlay, exterior, color=colors)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    return img

def mse(img1, img2):
   h, w = img1.shape
   diff = cv2.subtract(img1, img2)
   err = np.sum(diff**2)
   mse = err/(float(h*w))
   return mse, diff

def createRoi(img):
    pts = np.array(const_roi.area_utama)
    rect = cv2.boundingRect(pts)
    x,y,w,h = rect
    roi = img[y:y+h, x:x+w].copy()

    ## (2) make mask
    pts = pts - pts.min(axis=0)

    mask = np.zeros(roi.shape[:2], np.uint8)
    cv2.drawContours(mask, [pts], -1, (255, 255, 255), -1, cv2.LINE_AA)

    ## (3) do bit-op
    dst = cv2.bitwise_and(roi, roi, mask=mask)

    ## (4) add the white background
    bg = np.ones_like(roi, np.uint8)*255
    cv2.bitwise_not(bg,bg, mask=mask)
    dst2 = bg+ dst
    return dst2



os.environ['CUDA_LAUNCH_BLOCKING'] = "1"

location_id = sys.argv[1]
connection = mysql.connector.connect(host='192.168.1.90', database='smartcctv', user='pcs', password='123456')
data_loc = getDataLocation(connection, location_id)
stream_address = data_loc['link_address']
stream_forwarding = data_loc['link_address_forwading']
# model = YOLO("/home/module/yolov8/tracking/yolov8n.pt")
model = YOLO("/home/module/yolov8/yolov8x.pt")
cap = cv2.VideoCapture(stream_address)

# Initialize output file
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
size = (width, height)
fps = 30

# Define the gstreamer sink
os.environ['GST_DEBUG'] = "*:1"  # log gstreamer Errors (https://stackoverflow.com/questions/3298934/how-do-i-view-gstreamer-debug-output)
# out = cv2.VideoWriter(
#     'appsrc ! videoconvert ! '
#     'vp8enc threads=4 deadline=1 ! webmmux streamable=true ! '
#     'tcpserversink host=0.0.0.0 port=10120',
#     0, fps, size
# )
out = cv2.VideoWriter("appsrc ! videoconvert ! video/x-raw,format=I420 ! x264enc speed-preset=ultrafast tune=zerolatency ! rtspclientsink location=" + stream_forwarding, cv2.CAP_GSTREAMER, fps, size)

const_roi = importlib.import_module('roi.const_roi_'+ location_id)

alpha = 0.3 # that's your transparency factor

path_temp = '/home/module/yolov8/tracking/temp/cam' + str(location_id)
vehicle_entering = {}
vehicle_elapsed_time = {}
stuck_entering = {}
object_entering = {}

results = model.track(source=stream_address, stream=True, show=False, conf=0.3, tracker="bytetrack.yaml") 
# results = model.predict(source=stream_address, stream=True, show=False, conf=0.3) 
for r in results:

    boxes = r.boxes  # Boxes object for bbox outputs
    masks = r.masks  # Masks object for segment masks outputs
    probs = r.probs  # Class probabilities for classification outputs
    # print(boxes.id)
    # ret, frame = cap.read() # Extract image from stream
    frame = r.orig_img
    
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

            if obj_class in ['car', 'truck', 'bus']:
                # Speed analitycs entering
                if const_roi.speed_recognition :
                    left_lane_entering = cv2.pointPolygonTest(np.array(const_roi.area_bawah, np.int32) , obj_point,  False)
                    if left_lane_entering >= 0:
                        vehicle_entering[track_id] = time.time()
            
            if const_roi.motorcycle :
                if obj_class in ['motorcycle'] and score >= 0.8:
                    is_in_area = cv2.pointPolygonTest(np.array(const_roi.area_utama, np.int32) , obj_point,  False)
                    if is_in_area >= 0:
                        if track_id not in stuck_entering: 
                            stuck_entering[track_id] = time.time()

            if const_roi.other_objects :
                if obj_class not in ['car', 'truck', 'bus', 'person', 'motorcycle', 'train', 'suitcase']  and score >= 0.7:
                    is_in_area = cv2.pointPolygonTest(np.array(const_roi.area_utama, np.int32) , obj_point,  False)
                    if is_in_area >= 0:
                        if track_id not in object_entering: 
                                object_entering[track_id] = time.time()
                        # filename = path_temp + "other_object.jpg"
                        # record_path = '-'
                        # blob = writeImage(filename, box, frame, obj_class)
                        # responId = writeToLive(connection, location_id, 7, blob, record_path)
                        # sender(connection, data_loc['location'], 'other_object', responId, location_id)

            # speed analytics calculating
            if const_roi.speed_recognition :
                if track_id in vehicle_entering:
                    left_lane_elapsed = cv2.pointPolygonTest(np.array(const_roi.area_atas, np.int32) , obj_point,  False)
                    if left_lane_elapsed >= 0 :
                        elapsed_time = time.time() - vehicle_entering[track_id]
                        elapsed_time = round(elapsed_time, 2)

                        if track_id not in vehicle_elapsed_time:
                            vehicle_elapsed_time[track_id] = elapsed_time
                        if track_id in vehicle_elapsed_time:
                            elapsed_time = vehicle_elapsed_time[track_id]

                        # calculate average speed
                        jarak = const_roi.area_distance  # meters
                        a_speed_ms = jarak / elapsed_time
                        a_speed_kh = a_speed_ms * 3.6
                        a_speed_kh = round(a_speed_kh, 2)

                        writeToSpeed(connection, location_id, a_speed_kh, track_id)
                        
                        if a_speed_kh > 130:
                            if a_speed_kh > 150 :
                                a_speed_kh = 150
                            frame = cv2.putText(frame, str(a_speed_kh) + ' km/h', (int(x1) , int(y2 + 15)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255), 4)
                            frame = cv2.putText(frame, str(a_speed_kh) + ' km/h', (int(x1) , int(y2 + 15)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (50,50,255), 2)
                            filename = path_temp + "_speed_overlimit.jpg"
                            record_path = '-'
                            blob = writeImage(filename, vehicle_entering[track_id], frame, '-')
                            responId = writeToLive(connection, location_id, 8, blob, record_path)
                            # sender(connection, data_loc['location'], 'speed_overlimit', responId, location_id)
                        else :
                            frame = cv2.putText(frame, str(a_speed_kh) + ' km/h', (int(x1) , int(y2 + 15)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0), 4)
                            frame = cv2.putText(frame, str(a_speed_kh) + ' km/h', (int(x1) , int(y2 + 15)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255), 2)
            
            if const_roi.motorcycle :
                if track_id in stuck_entering:
                    stuck_time = time.time() - stuck_entering[track_id]
                    stuck_time = round(stuck_time, 2)
                    if stuck_time > 3:
                        filename = path_temp + "_motorcycle.jpg"
                        record_path = '-'
                        blob = writeImage(filename, box, frame, 'motorcycle')
                        responId = writeToLive(connection, location_id, 6, blob, record_path)
                        sender(connection, data_loc['location'], 'motorcycle', responId, location_id)
                        stuck_entering[track_id] = time.time()

            if const_roi.other_objects :
                if track_id in object_entering:
                    obj_time = time.time() - object_entering[track_id]
                    obj_time = round(obj_time, 2)
                    if obj_time > 5:
                        filename = path_temp + "_other_object.jpg"
                        record_path = '-'
                        blob = writeImage(filename, box, frame, 'other_object')
                        responId = writeToLive(connection, location_id, 7, blob, record_path)
                        sender(connection, data_loc['location'], 'other_object', responId, location_id)
                        object_entering[track_id] = time.time()

    if len(stuck_entering) > 100 :
        stuck_entering.pop(next(iter(stuck_entering)))
    if len(vehicle_entering) > 100 :
        vehicle_entering.pop(next(iter(vehicle_entering)))
    if len(object_entering) > 100 :
        object_entering.pop(next(iter(object_entering)))


    
    img = frame.copy()
    roi = createRoi(frame.copy())
    og_roi = cv2.imread("/home/module/yolov8/roi/og/og_roi_"+str(location_id)+".png")
    img1 = cv2.cvtColor(og_roi, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # cv2.imwrite('/home/module/yolov8/or_roi.png', roi)

    # error, diff = mse(img1, img2)
    # Compute SSIM between the two images
    # diff contains the actual image differences between the two images
    (score, diff) = structural_similarity(img1, img2, full=True)
    diff = 255 - (diff * 255).astype("uint8")
    print("Image Similarity: {:.4f}%".format(score * 100))

    # Search for all pixels that are different 
    # Type is <class 'numpy.ndarray'>, you can optionally convert to a list
    coords = np.argwhere(diff > 0)
    # coords = coords.tolist() 
    # print('difference coords : ' + str(coords))


    # show stream
    img = drawArea(img, const_roi.area_bawah,(175, 255, 175))
    img = drawArea(img, const_roi.area_atas,(175, 175, 255))
    img = drawArea(img, const_roi.area_utama,(255,250,250))
    cv2.imshow("Frame", img)
    cv2.imshow("ROI", roi)
    cv2.imshow("Diff", diff)
    # cv2.imwrite("/home/module/yolov8/roi/og/og_roi_"+str(location_id)+".png", roi)

    out.write(img)

    key = cv2.waitKey(30)
    if key == 27:
        break

cap.release()
out.release()
cv2.destroyAllWindows()
