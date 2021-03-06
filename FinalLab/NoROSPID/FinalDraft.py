import picamera.array
import picamera
import RPi.GPIO as GPIO
import time
import cv2
import cv2.cv as cv
import numpy as np
import random

#Motor Pins
in1=12
in2=13
in3=20
in4=21
ena=6
enb=26
	
IN1 = in1 #(In case I mess up spelling, I'm bad at this)
IN2 = in2
IN3 = in3
IN4 = in4
ENA = ena
ENB = enb
	
#Obstacle Avoidance pins
DR = 16
DL = 19

#initialization
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(IN1,GPIO.OUT)
GPIO.setup(IN2,GPIO.OUT)
GPIO.setup(IN3,GPIO.OUT)
GPIO.setup(IN4,GPIO.OUT)

GPIO.setup(ENA,GPIO.OUT)
GPIO.setup(ENB,GPIO.OUT)

GPIO.setup(DR,GPIO.IN,GPIO.PUD_UP)
GPIO.setup(DL,GPIO.IN,GPIO.PUD_UP)

PWMA = GPIO.PWM(ENA,500)
PWMB = GPIO.PWM(ENB,500)

PWMA.start(29.214) #calculated by taking circumference and dividing by time
PWMB.start(25.017) #then compared to the other servo and compensated with

#Defining Motor parameters

def forward():
	GPIO.output(IN1,GPIO.HIGH)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.HIGH)

def stop():
	GPIO.output(IN1,GPIO.LOW)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.LOW)

def backward():
	GPIO.output(IN1,GPIO.LOW)
	GPIO.output(IN2,GPIO.HIGH)
	GPIO.output(IN3,GPIO.HIGH)
	GPIO.output(IN4,GPIO.LOW)

def left():
	GPIO.output(IN1,GPIO.LOW)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.HIGH)

def right():
	GPIO.output(IN1,GPIO.HIGH)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.LOW)
		
def setPWMA(value):
	PWMA.ChangeDutyCycle(value)

def setPWMB(value):
	PWMB.ChangeDutyCycle(value)

def stopPWM():
	PWMA.ChangeDutyCycle(0)	
	PWMB.ChangeDutyCycle(0)
	
#Obstacle Avoidance (Alphabot library)
def charge():
	while True:
		DR_status = GPIO.input(DR)
		DL_status = GPIO.input(DL)
		print(DL_status)
		print(DR_status)
		start = time.time() #start

		if((DL_status == 1) and (DR_status == 1)): #nothing is here
			forward()
			print("forward")
		elif((DL_status == 1) and (DR_status == 0)): #something is to the right
			left()
			print("left")
		elif((DL_status == 0) and (DR_status == 1)): #something is to the left
			right()
			print("right")
		else: #if both sensors are triggere
			backward() 
			time.sleep(2.0)
			left()
			time.sleep(1.0)
			stop()
			print("backward")
			#I treated this like parking, 
#where a person would start backing then turning

		end = time.time() #stop
		timegap = (stop - end) #time gap
		
#Taking Width/Height from resolution and making a origin
w = 256
h = 160
origin_x= int(0.5*w) #Negatives count
origin_y = int(0.5*h) #Y is included because I don’t want to mess up moments command

#Object Tracking part

with picamera.PiCamera() as camera:
	camera.resolution = (256,160)
	while(True):
		with picamera.array.PiRGHArray(camera) as stream:
			camera.exposure_mode = 'auto'
			camera.awb_mode = 'auto'
			camera.capture(stream, format = 'bgr')
			image = stream.array
			blur = cv2.GaussainBlur(image,(11,11),0)
			hsv = cv2.cvtColor(blur,cv2.COLOR_BGR2HSV)
			pixAverage = int(np.average(stream.array[...,1]))
			cv2.waitKey(1)
			
			blue_lower=np.array([100,150,0],np.uint8)
			blue_upper=np.array([140,255,255],np.uint8)
			
			mask = cv2.inRange(hsv,blue_lower,blue_upper)
			mask = cv2.erode(mask, None, iterations = 2)
			mask = cv2.dilate(mask, Non, iterations = 2)
			#Blur, Erode and dilate to create a “blob” easier to locate
			
			contmask = cv2.inRange(hsv, blue_lower, blue_upper)
			#Making a mask for contour making (removed)
			moments = cv2.moments(contmask, True)
			
			if (timegap > 4.0): #Scan lock-on
				stop()
				if moments('m00']>=10:
					x = moments['m10']/moments['m00'] #Taking object
					y = moments['m01']/moments['m00'] #center

					cv2.circle(image,(int(x),int(y)), 5, (0,0,255),-1)
					delta_x = x - origin_x

					if (x-cent_x) > 14: #Object is to the right
						stop()
						time.sleep(1.0)
						right()
						time.sleep(0.3)
					elif (cent_x-x) > 14: #Object is to the left
						stop()
						time.sleep(1.0)
						left()
						time.sleep(0.3)
					#If Object is in range of middle
					elif ((x-cent_x) < 14) and ((cent_x-x) < 14):
						stop()
						time.sleep(1.0)
						charge()
						time.sleep(0.3)
					else: #if nothing is found
						stop()
						time.sleep(2.0)
						rdirection = random.randint(1,2)
#direction randomizer 
						#(This was honestly a bad idea)
						rangle = random.random(0.3,0.5)
						if(rdirection == 1): #low
							left()
							time.sleep(rangle)
							stop()
						if(rdirection == 2): #right
							right()
							time.sleep(rangle)
							stop()
						time.sleep(.5)

			start = time.time() #resetting the clock
			cv2.imshow('Frame',image) #accuracy
			cv2.imshow('Mask',mask) #seeing if opencv detects objects
