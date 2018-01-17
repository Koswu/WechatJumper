#!/usr/bin/python3

#Author:koswu
#Licence:GPL V3
#Version:0.11

import math
import os
import numpy as np
import time
import random
from PIL import Image

BACKGROUND_POS = (40,500)
DISTANCE_TO_TIME_RATIO = 1.4
SCREENSHOT_PATH = './screenshot.png'
DOLL_HEAD_COLOR = (52,53,65)
DOLL_HALF_LENGTH = 30
DOLL_FOOT_COLOR = (56,59,100)

IS_DEBUG = False
DEBUG_LEVEL = 0

COUNT = 0

def isSimilar(color1, color2, mistake=10):
    return math.sqrt((color1[0]-color2[0])**2+(color1[1]-color2[1])**2+(color1[2]-color2[2])**2) <= mistake*3
    
def getJumpDistance():
    img = Image.open(SCREENSHOT_PATH)
    background_color = img.getpixel(BACKGROUND_POS)
    vertex1_pos = None
    vertex2_pos = None
    is_vertex2_set = False
    doll_pos = None
    doll_left_foot_pos = None
    doll_right_foot_pos = None
    box_color = None
    for y in range(BACKGROUND_POS[1], img.height-400):
        x = 40
        background_color = img.getpixel((x, y))
        while x < img.width: #不使用for，因为有跳过小人的需求
            current_color = img.getpixel((x, y))
            if isSimilar(background_color, current_color):
                background_color = current_color
            if vertex1_pos == None and not isSimilar(background_color, current_color):
                if isSimilar(DOLL_HEAD_COLOR, current_color ,20):
                    x = x+100 #跳过小人
                    '''
                    while not isSimilar(DOLL_HEAD_COLOR, current_color):
                        x = x-1
                    x = x+1
                    print ("return to (%d,%d)"%(x,y))
                    
                    '''
                    continue
                vertex1_pos = (x, y)
                vertex2_pos = (x, y)
                box_color = img.getpixel((x,y+1))
                print ("vertex1 is detected. The position is (%d,%d). "%vertex1_pos)
                print ("box color is set. The RGB and alpha value is (%d,%d,%d,%d). "%box_color)
                break
            if vertex2_pos != None and is_vertex2_set == False and isSimilar(current_color, box_color, 9):
                if x <= vertex2_pos[0]:
                    if y > vertex2_pos[1]:
                        if x == vertex2_pos[0]:
                            #回溯，找到最上方颜色相似的一点
                            last_pix = (x,y-1)
                            while isSimilar(img.getpixel((x,y)),box_color):
                                y = y-1
                            y = y+1
                            vertex2_pos = (x, y+(last_pix[1]-y)/2)
                        else:
                            vertex2_pos=(x,y)
                    break
                else:
                    if vertex1_pos == vertex2_pos:
                        raise Exception("Vertex2 is not detected, now pos is (%d, %d) ."%(x, y))
                    is_vertex2_set = True
                    print ("vertex2 is detected. The position is (%d,%d)"%vertex2_pos)
            if isSimilar(current_color, DOLL_FOOT_COLOR, 5):
                    doll_pos = (x, y)
            x = x+1
    if vertex1_pos == None:
        raise Exception("vertex1 is not detected. Please check settings.")
    if is_vertex2_set == False:
        raise Exception("vertex2 is not detected. Please check settings.")
    if doll_pos == None:
        raise Exception("doll is not detected. Please check settings. ")
    else:
        #计算人偶实际位置
        doll_right_foot_pos = (0,0)
        #计算右脚位置
        while True:
            if isSimilar(DOLL_FOOT_COLOR, img.getpixel((doll_pos[0]+1, doll_pos[1]))):
                doll_pos = (doll_pos[0]+1, doll_pos[1])
            else:
                if doll_pos[0] >= doll_right_foot_pos[0] and isSimilar(DOLL_FOOT_COLOR, img.getpixel((doll_pos[0], doll_pos[1]-1))):
                    doll_right_foot_pos = doll_pos
                    doll_pos = (doll_pos[0], doll_pos[1] -1)
                else:
                    break
        while isSimilar(DOLL_FOOT_COLOR, img.getpixel((doll_right_foot_pos[0], doll_right_foot_pos[1]+1))):
            doll_right_foot_pos = (doll_right_foot_pos[0], doll_right_foot_pos[1]+1)
        #计算左脚位置
        doll_left_foot_pos = doll_right_foot_pos
        while isSimilar(img.getpixel(doll_left_foot_pos), img.getpixel((doll_left_foot_pos[0]-1, doll_left_foot_pos[1]))):
            doll_left_foot_pos = (doll_left_foot_pos[0]-1, doll_left_foot_pos[1])
        doll_pos = (doll_left_foot_pos[0]+(doll_right_foot_pos[0]-doll_left_foot_pos[0])/2,doll_left_foot_pos[1])
        if IS_DEBUG:
            print("doll_left_foot_pos=",doll_left_foot_pos)
            print("doll_right_foot_pos=",doll_right_foot_pos)
            print("Doll is detected. The position is (%d,%d)"%doll_pos)
    if abs(vertex1_pos[0]-doll_pos[0]) < DOLL_HALF_LENGTH:
        raise Exception("vertex1 position is illegal. Please check settings. ")
    center_pos = (vertex1_pos[0], vertex2_pos[1])
    if IS_DEBUG:
        print("The center position of box is (%d,%d)"%center_pos)
    distance = math.sqrt((center_pos[0]-doll_pos[0])**2+(center_pos[1]-doll_pos[1])**2)
    if IS_DEBUG:
        print("The distance of doll to box is %d"%distance)
    return distance

def screenShot():
    global COUNT
    global SCREENSHOT_PATH
    if IS_DEBUG:
        SCREENSHOT_PATH = './screenshot'+str(COUNT)+'.png'
    COUNT = COUNT + 1
    os.system("adb shell screencap -p /sdcard/screencap.png")
    os.system("adb pull /sdcard/screencap.png "+SCREENSHOT_PATH) 

def jump(time):
    os.system("adb shell input swipe 0 0 0 0 "+str(int(time+0.5)))

def main():
    while True:
        global COUNT
        global SCREENSHOT_PATH
        if IS_DEBUG:
            COUNT = 113
            SCREENSHOT_PATH = './screenshot'+str(COUNT)+'.png'
        print ("This turn is round %d"%COUNT) 
        screenShot()
        distance = getJumpDistance()
        touch_time = distance * DISTANCE_TO_TIME_RATIO
        jump(touch_time)
        print("\n\n")
        time.sleep(random.random()+1.5)
        if IS_DEBUG and DEBUG_LEVEL == 1:
            break

if __name__ == '__main__':
    main()

