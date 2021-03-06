"""
*
*                  ================================
*
*  Author List: Aniket P
*  Filename: 		edges.py
*  Date:                June 11, 2015
*  Functions:   get_depth()
                return_mean()
                contours_return()
                regular_movement()
                doorway_movement()
                left_right_lines()
*  Global Variables:    mode
			diff
*  Dependent library files:     numpy, freenect, cv2, serial, time
*
*  e-Yantra - An MHRD project under National Mission on Education using
*  ICT(NMEICT)
*
**************************************************************************
"""

import freenect
import cv2
import numpy as np
import serial
import time

kernel = np.ones((5,5),np.uint8) #kernel for filtering
ser = serial.Serial('/dev/ttyUSB0')	#initialization of serial communication
global mode	#variable to provide the mode of movement
mode = 0
global diff	#variable to set a threshold for left and right movement
diff = 0

def get_depth():
    """
    * Function Name:	get_depth
    * Input:		None                        
    * Output:		Returns the depth information from pixel values of 0 to 255
    * Logic:		It gets the depth from kinect whose values lie in range of 0 to above 2000. It clips and left shifts the data to get 				all the values between 0 and 255.
    * Example Call:	get_depth()
    """
    a = freenect.sync_get_depth()[0]
    np.clip(a, 0, 2**10 - 1, a)
    a >>= 2
    a = a.astype(np.uint8)
    return a

def return_mean(a):
    """
    * Function Name:	return_mean
    * Input:		Depth Frame or any other matrix.                        
    * Output:		Returns mean of the frame
    * Logic:		It reduces the noise and calculates the mean of the pixel values in the frame using mean() function
    * Example Call:	return_mean(a)
    """
    mediane = cv2.medianBlur(a,5)
    rect = mediane[0:479, 0:639]
    mean = rect.mean()
    return mean

def contours_return(a,num):
    """
    * Function Name:	contours_return
    * Input:		Depth Frame and a number for shifting left or right the matrix                        
    * Output:		Returns the left or right edges contours
    * Logic:		It does noise removal process on the frame and shifts the frame matrix by num places so that change in values are 	     		highlighted in the image by Binary Thresholding it.
    * Example Call:	contours_return(a,5)
    """
    b = np.roll(a,num)
    res = np.subtract(b,a)
    res = np.multiply(res,255)
    res = cv2.medianBlur(res,5)
    ret,th3 = cv2.threshold(res,50,255,cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(th3,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return contours

def regular_movement(z):
    """
    * Function Name:	regular_movement
    * Input:		Depth Frame                       
    * Output:		Just normal movement of the robot
    * Logic:		The robot moves by first calculating the mean of the pixel values of left, middle and right part of frames. If the left 			or the right part crosses a threshold than the robot will move left or right as it has to avoid the obstacles from 				bumping. While taking a left or a right the robot takes left/right until and unless the middlearea value crosses the 				threshold. If the it does not than the diff variable avoids the localization of robot in a corner by taking a big left 				until middlearea value is recieved. 
    * Example Call:	regular_movement(z)
    """
    global mode
    global diff
    middlearea = z[200:479,200:439]
    middleval = middlearea.mean()
    leftarea = z[0:479,0:100]
    rightarea = z[0:479,539:639]
    leftval = leftarea.mean()
    rightval = rightarea.mean()

    if mode == 0:
        if middleval > 220:
            print "forward"
            ser.write("\x38")
            diff = 0
            time.sleep(0.1)
        else:
            if leftval - rightval > diff:
                print "left"
                diff+=1
                ser.write("\x34")
            else:
                print "right"
                ser.write("\x36")
                diff+=1
    if leftval < 175:
        print "righta"
        ser.write("\x36")
        diff+=1
    elif rightval < 175:
            print "lefta"
            ser.write("\x34")
            diff+=1

def doorway_movement(lb,lt,rb,rt,cxr,cxl):
    """
    * Function Name:	doorway_movement
    * Input:		left_bottom, left_top, right_bottom, right_top, right_edge_centroid, left_edge_centroid                       
    * Output:		Movement of the robot on door detection
    * Logic:		Pixel Heights of the edges are calculated. If the pixel height difference and centroid of left and right edge 				difference crosses a threshold than the edges are door edges. The midpoint is calculated. If midpoint lies in middle 				frame than robot moves forward and if it lies on the left or right part than the robot takes a turn. When mode is 1 				the door is detected and in mode 0 mode regular movement is followed.
    * Example Call:	doorway_movement(lb,lt,rb,rt,cxr,cxl)
    """
    global mode
    diffl = lb[1]-lt[1]
    diffr = rb[1]-rt[1]
    if abs(diffl - diffr) < 50 and (cxr - cxl) > 50:
        mode = 1
        mid = (cxr + cxl)/2
        print "haha"
        if mid < 500 and mid > 200:
            print "forward"
            ser.write("\x38")
        elif mid < 200:
            print "left"
            ser.write("\x34")
        else:
            print "right"
            ser.write("\x36")
    else : mode = 0

def left_right_lines(contoursright,contoursleft,z):
    """
    * Function Name:	left_right_lines
    * Input:		left_contours, right_contours and the depth frame.                   
    * Output:		left and right edges of the door.
    * Logic:		For the list of left and right contours if left contour or right contour has an area greater than the threshold than 				processing is done on the contour. the leftmost, bottommost, rightmost and leftmost. If the height of the door edges 				falls in a given edge than the given program is followed. Even if the edge is tilted or has some angle than also it 				will take proper area of its left or right using warpperspective function. If only two edges are detected than the 				robot will move accordingly to the door movement
    * Example Call:	left_right_lines(contoursright,contoursleft,z)
    """
    count = 0
    Area = 1000
    ys = 250
    xs = 60
    tempr = 0
    templ = 0
    for c in contoursright:
        if(cv2.contourArea(c)>Area):
            #cv2.drawContours(original, contours, count, (128,255,0), 3)
            leftmost = tuple(c[c[:,:,0].argmin()][0])
            rightmost = tuple(c[c[:,:,0].argmax()][0])
            topmost = tuple(c[c[:,:,1].argmin()][0])
            bottommost = tuple(c[c[:,:,1].argmax()][0])
            x1 = leftmost[0]
            x2 = rightmost[0]
            y1 = topmost[1]
            y2 = bottommost[1]
            w = 50
            if (y2 - y1 > ys) and (abs(x2 - x1) < xs):
                pts1 = np.float32([[topmost[0]-w,y1],[topmost[0],y1],[bottommost[0]-w,y2],[bottommost[0],y2]])
                pts2 = np.float32([[0,0],[w,0],[0,y2-y1],[w,y2-y1]])
                M = cv2.getPerspectiveTransform(pts1,pts2)
                dst = cv2.warpPerspective(z,M,(w,y2-y1))
                meandst = dst.mean()
                #print meandst
                if meandst > 240:
                    cv2.line(z,topmost,bottommost,(0,255,0),5)
                    tempr+=1
                    rt = topmost
                    rb = bottommost
                    M = cv2.moments(c)
                    cxr = int(M['m10']/M['m00'])
        count+=1
    count = 0
    for c in contoursleft:
        if(cv2.contourArea(c)>Area):
            #cv2.drawContours(original, contoursc, count, (128,255,0), 3)
            leftmost = tuple(c[c[:,:,0].argmin()][0])
            rightmost = tuple(c[c[:,:,0].argmax()][0])
            topmost = tuple(c[c[:,:,1].argmin()][0])
            bottommost = tuple(c[c[:,:,1].argmax()][0])
            x1 = leftmost[0]
            x2 = rightmost[0]
            y1 = topmost[1]
            y2 = bottommost[1]
            w = 50
            if (y2 - y1 > ys) and (abs(x2 - x1) < xs):
                pts1 = np.float32([[topmost[0],y1],[topmost[0]+w,y1],[bottommost[0],y2],[bottommost[0]+w,y2]])
                pts2 = np.float32([[0,0],[w,0],[0,y2-y1],[w,y2-y1]])
                M = cv2.getPerspectiveTransform(pts1,pts2)
                dst = cv2.warpPerspective(z,M,(w,y2-y1))
                meandst = dst.mean()
                #print meandst
                if meandst > 240:
                    cv2.line(z,topmost,bottommost,(0,255,0),5)
                    templ+=1
                    lt = topmost
                    lb = bottommost
                    M = cv2.moments(c)
                    cxl = int(M['m10']/M['m00'])
        count+=1
    if templ == 1 and tempr == 1:
        doorway_movement(lb,lt,rb,rt,cxr,cxl)
    return z


while(True):
    np.set_printoptions(threshold=np.nan)	
    a = get_depth()	#gets the depth of the frame
    z = a	#assign the frame to a original variable so that original frame can be used later
    a = cv2.bilateralFilter(a, 10, 50, 100)	#filters out the noise in the frame
    contoursright = contours_return(a,2)	#returns left edges contours
    contoursleft = contours_return(a,-2)	#returns right edges contours
    regular_movement(z)	#follows regular movement
    linesz = left_right_lines(contoursright,contoursleft,z)	#draws the lines in the contours
    cv2.imshow('gray',linesz)	#displays the final matrix with lines on it
    if cv2.waitKey(1)!=-1:	#executes the while loop until a key is pressed
        ser.write('\x35')	
        ser.close()
        freenect.Kill
        break
cv2.destroyAllWindows()
