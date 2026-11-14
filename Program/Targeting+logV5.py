# -*- coding: utf-8 -*-
"""
Created on Sat Oct  7 09:19:32 2023

@author: Blin_guy

to do list:
1. Kurangi flickering dari GUI
2. TARGETING RUNOFF, VALUE LEWAT LIMIT DAN TERUS NAIK
3. limit value targeting
4. perbaiki target selection, maintain last tracks

"""

#Import the tkinter library
import numpy as np
import cv2
from ultralytics import YOLO
import RPi.GPIO as GPIO
import time
import sys
import os
from adafruit_servokit import ServoKit

GPIO.cleanup()
'Setup kontrol GPIO'
pin = 7 #nomor PIN menggunakan referensi nomor pada jetson
GPIO.setmode(GPIO.BOARD) #perintah menggunakan nomor PIN Jetson
GPIO.setup(pin, GPIO.OUT)

'setting servokit dengan kontroler'
kit = ServoKit(channels=16)
azim=90
elev=45
kit.servo[0].angle= azim
kit.servo[2].angle= elev

'variable awal'
AET=40 #Auto Engage Threshold
minA = int(AET * -1)
track_select = int()

'laporan Proses'
trying= 'trying to detect....'
noconf= 'non-confident result, passing....'
report= "Please Wait, Processing......"

'path model YOLO'
model = YOLO('droneACC.pt')

'file data logging'
f = open("Detectlog.txt", "w")
f.write("Timestamp,"+"Deviation X, "+"Deviation Y, "+"Confidence, "+"Objectname,"+"Azimuth/Elevation,"+"runtime"+",lASER I/O"+"\n")

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=2,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv interpolation-method=1 compute-hw=GPU"
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d,format=(string)I420 ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink drop=true sync=false"
 
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def detect(track_select):
    #print("selected target= ",track_select)
    Nowtime= time.time()
    global azim
    global elev
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2), cv2.CAP_GSTREAMER)
    while cap.isOpened():
        # Read a frame from the video
        success, rawframe = cap.read()
    
        if success:
            # Run YOLOv8 tracking on the frame, persisting tracks between frames
            
            frame = cv2.resize(rawframe, (1280, 720))
            results = model.track(frame, persist=True, conf=0.6)
            
            # Visualize the results on the frame
            annotated_frame = results[0].plot(conf=False, line_width= 2)
    
            'menentukan aimpoint dari frame'
            dimension = annotated_frame.shape
            height = (annotated_frame.shape[0])
            width = (annotated_frame.shape[1])
            centreY = int(height/2)
            centreX = int(width/2)
            finished = cv2.circle(annotated_frame, (centreX,centreY), 2, (0,50,255), 5)
              
            try:
                "mengambil object Results (hasil dari deteksi)"
                conf = results[0].boxes.conf.tolist()
                coords = results[0].boxes.xywh.tolist()
                obj_cls = results[0].boxes.cls.int()
                track_ids = results[0].boxes.id.tolist()
                names= results[0].names
                "membandingkan nilai Obj_cls dengan Names" 
                listName=[]
                for n in obj_cls:
                    listName.append(names[int(n)])
                #print("targets!",listName)
                'pemilahan koordinat target'
                trackCoord= coords[track_select]
                track_X= int(trackCoord[0]) #ini koordinat X ada di row pertama
                track_Y= int(trackCoord[1]) #ini koordinat Y ada di row kedua
                #print('ini track X', track_X)
                #print('ini track Y', track_Y)
                
                diffX= centreX-track_X
                diffY= centreY-track_Y
                'display aimpoint, centre of rame, dan trackpoint'
                selectshow = cv2.circle(finished,(track_X,track_Y), 3, (255,0,0) , 3)
                finished = selectshow
                
                #------------engage using deviation-----------
                try:
                  if diffY > AET :
                    elev = elev + 0.1 + (diffY*0.04)
                  if diffY < minA :
                    elev = elev - 0.1 + (diffY*0.04)
                  else:
                    elev = int(elev + 0)
                    
                  if diffX > AET :
                    azim = azim + 0.1 + (diffX*0.04)
                  if diffX < minA :
                    azim = azim - 0.1 + (diffX*0.04)
                  else:
                    azim = int(azim + 0)
                  
                  
                  if azim > 180 :
                    azim = 180
                  elif azim < 0 :
                    azim = 0
                    
                  if elev > 180 :
                    elev = 180
                  elif elev < 0 :
                    elev = 0
                  print("servo values, azimuth= ", azim,", elevation= ", elev)
                  kit.servo[0].angle= azim
                  kit.servo[2].angle= elev
                  curtime= time.ctime()
                  endtime= time.time()
                  runtime= endtime-Nowtime
                  f.write(str(curtime)+', '+str(diffX)+', '+str(diffY)+', '+str(conf)+', '+str(listName)+', '+str(azim)+'| '+str(elev)+", "+str(runtime))
                  #LASER NYALA MATI
                  if ((diffX < AET and diffY < AET) and (diffX > minA and diffY > minA)):
                      GPIO.output(pin, GPIO.HIGH)
                      f.write(", 1"+"\n")
                      #print("engaging!")
                  else:
                    	GPIO.output(pin,GPIO.LOW)
                    	f.write(", 0"+"\n")
                    	#print("LAS OFF!")
                except:
                  pass
                  print("ERROR IN SERVO CONTROL!")
                
                #print('deviation X.Y =', diffX , diffY, ', confidence= ', conf, ', objectname= ', listName) 
                #print(trying)
            except:
                pass
                print(noconf)
                
            cv2.imshow("YOLOv8 Inference", annotated_frame)
            #time.sleep(0.5)
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Break the loop if the end of the video is reached
            break



if __name__ == '__main__':
    try:
        detect(track_select)  
#'Release the video capture object and close the display window'
    except:
        cap.release()
        cv2.destroyAllWindows()
    finally:
        f.close()      
        print("QUITTED!")
        GPIO.cleanup()
        os._exit(00)       
        sys.exit()
