__author__ = 'aniket'
"""
*
*                  ================================
*
*  Author List:
*  Filename:
*  Date:
*  Functions:
*  Global Variables:
*  Dependent library files:
*
*  e-Yantra - An MHRD project under National Mission on Education using
*  ICT(NMEICT)
*
**************************************************************************
"""

import freenect
import cv2
import numpy as np
import time
import serial
import math
import matplotlib.mlab as lab
from matplotlib import pyplot as plt

global flag
flag = False
global count
count = 0
global axis_plot
axis_plot = 0

ser = serial.Serial('/dev/ttyUSB0')	 # initialization of serial communication


def filter_noise(a, mask, ad, row, col):
    """
    * Function Name:filter_noise()
    * Input:		Original frame, noise mask, Original
                    frame with noise pixels being made to 255 value,
                    no. of row tiles, No. of column tiles.
    * Output:		Filters the noise from the original depth frame.
    * Logic:		The function divides rows and cols of the frame in
                    some number of pixels. It then finds the mean of the
                    tile and assigns the value to the noise pixels in that
                    tile.
    * Example Call:	filter_noise(a,mask,ad,3,4)
    """
    rp = 480/row
    cp = 640/col
    y = 0
    for i in xrange(col):
        x = 0
        for j in xrange(row):
            area = ad[x:x+rp-1, y:y+cp-1]
            mask[x:x+rp-1, y:y+cp-1] *= area.mean()
            a[x:x+rp-1, y:y+cp-1] += mask[x:x+rp-1, y:y+cp-1]
            x += rp
        y += cp
    return a


def filter_smooth(a):
    """
    * Function Name:	filter_smooth
    * Input:		Original Depth frame in mm.
    * Output:		Filters the noise from the depth frame
    * Logic:		It creates a mask for the noise. It makes
                    all the noise pixels to 255 to send to filter noise.
                    The output from filter noise is smoothed using
                    bilateral filter
    * Example Call:	filter_smooth(a)
    """
    ret, mask = cv2.threshold(a, 10, 255, cv2.THRESH_BINARY_INV)
    mask_1 = mask/255
    ad = a + mask
    blur = filter_noise(a, mask_1, ad, 3, 4)
    blur = cv2.bilateralFilter(blur, 5, 50, 100)
    return blur


def get_depth():
    """
    * Function Name:	get_depth
    * Input:		None
    * Output:		Returns the depth information from pixel values of 0 to 255
    * Logic:		It receives the depth information from the Kinect sensor in mm.
                    	The depth range is 40cm to 800cm. The values are brought
                    	down from 0 to 255. It then changes the data type
                    	to 1 bytes. It then smoothed the frame and returns it.
    * Example Call:	get_depth()
    """
    a = freenect.sync_get_depth(format=freenect.DEPTH_MM)[0]
    a /= 30.0
    a = a.astype(np.uint8)
    a = filter_smooth(a)
    a[0:479, 630:639] = a[0:479, 620:629]
    return a


def contours_return(a, num):
    """
    * Function Name:	contours_return
    * Input:		Depth Frame and a number for shifting left or right the matrix.
    * Output:		Returns the left or right edges contours
    * Logic:		It does noise removal process on the frame and
                    	shifts the frame matrix by num places so that
                    	change in values are highlighted in the
                    	image by Binary Threshold it.
    * Example Call:	contours_return(a,5)
    """
    b = np.roll(a, num)
    res = np.subtract(b, a)
    res = cv2.medianBlur(res, 11)
    mask = res > 200
    res[mask] = 0
    mask = res < 100
    res[mask] = 0
    ret, th3 = cv2.threshold(res, 50, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours\
        (th3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def potential_right_edge(c):
    """
    * Function Name:	potential_right_edge
    * Input:		A contour
    * Output:		Returns a potential right edge which fulfills all the conditions
                    	returns topmost, bottommost and centroid of the contour.
    * Logic:		If area of the contour crosses a threshold than the
                    	extreme points are calculated of the contour. If
                    	the difference 	in opposite extreme points lies
                    	in the given threshold and the width and height
                    	of the bounding rectangle lies in the threshold
                    	than the contour is a potential contour and a line
                    	is drawn as an edge. The centroid is calculated for
                    	further use
    * Example Call:	potential_right_edge(c)
    """
    area = 1000
    ys = 250
    xs = 60
    if cv2.contourArea(c) > area:
        leftmost = tuple(c[c[:, :, 0].argmin()][0])
        rightmost = tuple(c[c[:, :, 0].argmax()][0])
        topmost = tuple(c[c[:, :, 1].argmin()][0])
        bottommost = tuple(c[c[:, :, 1].argmax()][0])
        x1 = leftmost[0]
        x2 = rightmost[0]
        x3 = topmost[0]
        x4 = bottommost[0]
        y1 = topmost[1]
        y2 = bottommost[1]
        w = 50
        if (y2 - y1 > ys) and (abs(x2 - x1) < xs) and x3 < 620 and x4 < 620:
            pts1 = np.float32([[topmost[0]-w, y1], [topmost[0], y1],
                               [bottommost[0]-w, y2], [bottommost[0], y2]])
            pts2 = np.float32([[0, 0], [w, 0], [0, y2-y1], [w, y2-y1]])
            m = cv2.getPerspectiveTransform(pts1, pts2)
            dst = cv2.warpPerspective(z, m, (w, y2-y1))
            mean_dst = dst.mean()
            if mean_dst > 50:
                cv2.line(z, topmost, bottommost, (0, 255, 0), 5)
                rt = topmost
                rb = bottommost
                m = cv2.moments(c)
                cxr = int(m['m10'] / m['m00'])
                return rt, rb, cxr
    return 0, 0, 0


def potential_left_edge(c):
    """
    * Function Name:	potential_left_edge
    * Input:		A contour
    * Output:		Returns a potential left edge which fulfills all the conditions
                    	returns topmost, bottommost and centroid of the contour.
    * Logic:		If area of the contour crosses a threshold than the
                    	extreme points are calculated of the contour. If
                    	the difference in opposite extreme points lies
                    	in the given threshold and the width and height
                    	of the bounding rectangle lies in the threshold
                    	than the contour is a potential contour and a
                    	line is drawn as an edge. The centroid is
                    	calculated for further use
    * Example Call:	potential_left_edge(c)
    """
    area = 1000
    ys = 250
    xs = 60
    if cv2.contourArea(c) > area:
        leftmost = tuple(c[c[:, :, 0].argmin()][0])
        rightmost = tuple(c[c[:, :, 0].argmax()][0])
        topmost = tuple(c[c[:, :, 1].argmin()][0])
        bottommost = tuple(c[c[:, :, 1].argmax()][0])
        x1 = leftmost[0]
        x2 = rightmost[0]
        x3 = topmost[0]
        x4 = bottommost[0]
        y1 = topmost[1]
        y2 = bottommost[1]
        w = 50
        if (y2 - y1 > ys) and (abs(x2 - x1) < xs) and x3 > 20 and x4 > 20:
            pts1 = np.float32([[topmost[0], y1], [topmost[0]+w, y1],
                               [bottommost[0], y2], [bottommost[0]+w, y2]])
            pts2 = np.float32([[0, 0], [w, 0], [0, y2-y1], [w, y2-y1]])
            m = cv2.getPerspectiveTransform(pts1, pts2)
            dst = cv2.warpPerspective(z, m, (w, y2-y1))
            mean_dst = dst.mean()
            if mean_dst > 50:
                cv2.line(z, topmost, bottommost, (0, 255, 0), 5)
                lt = topmost
                lb = bottommost
                m = cv2.moments(c)
                cxl = int(m['m10'] / m['m00'])
                return lt, lb, cxl
    return 0, 0, 0


def is_door(lb, lt, rb, rt, cxr, cxl):
    """
    * Function Name:	doorway_movement
    * Input:		left_bottom, left_top, right_bottom,
                    	right_top, right_edge_centroid,
                    	left_edge_centroid
    * Output:		Movement of the robot on door detection
    * Logic:		Pixel Heights of the edges are calculated.
                    	If the pixel height difference and centroid
                    	of left and right edge difference crosses a
                    	threshold than the edges are door edges.
                    	The midpoint is calculated. If midpoint lies
                    	in middle frame than robot moves forward and
                    	if it lies on the left or right part than the
                    	robot takes a turn. When mode is 1 the door is
                    	detected and in mode 0 mode regular movement is
                    	followed.
    * Example Call:	doorway_movement(lb,lt,rb,rt,cxr,cxl)
    """
    diff_l = lb[1]-lt[1]
    diff_r = rb[1]-rt[1]
    if abs(diff_l - diff_r) < 150 \
            and(not 50 >= (cxr - cxl) and(cxr - cxl) < 400):
        cv2.line(z, lt, lb, (128, 255, 0), 10)
        cv2.line(z, rt, rb, (128, 255, 0), 10)
        return 1
    return 0


def left_right_lines(contours_right_line, contours_left_line):
    """
    * Function Name:	left_right_lines
    * Input:		right contours, left contours, original depth frame
    * Output:		detects left and right edges and accordingly calls
                    	the door movement function.
    * Logic:		creates an array of all the required parameters
                    	of all the potential left and right edges and
                    	sends them two at a time to doorway_movement function.
    * Example Call:	left_right_lines(contours_right,contours_left,z)
    """
    temp_l = 0
    temp_r = 0
    lt_l = []
    lb_l = []
    cxl_l = []
    rt_l = []
    rb_l = []
    cxr_l = []
    for c in contours_left_line:
        lt, lb, cxl = potential_left_edge(c)
        if cxl != 0:
            lt_l.append(lt)
            lb_l.append(lb)
            cxl_l.append(cxl)
            temp_l += 1
    for c in contours_right_line:
        rt, rb, cxr = potential_right_edge(c)
        if cxr != 0:
            rt_l.append(rt)
            rb_l.append(rb)
            cxr_l.append(cxr)
            temp_r += 1
    return lt_l, lb_l, cxl_l, rt_l, rb_l, cxr_l, temp_l, temp_r


def horizontal_lines():
    """
    * Function Name:	horizontal_lines()
    * Input:		right contours, left contours, original depth frame
    * Output:		detects left and right edges and accordingly calls
                    	the door movement function.
    * Logic:		creates an array of all the required parameters
                    	of all the potential left and right edges and
                    	sends them two at a time to doorway_movement function.
    * Example Call:	left_right_lines(contours_right,contours_left,z)
    """
    contour = contours_return(z, 6400)
    temp_h = 0
    hl_l = []
    hr_l = []
    cxh_l = []
    for c in contour:
        hl, hr, cxh = horizontal_edge(c)
        if cxh != 0:
            hl_l.append(hl)
            hr_l.append(hr)
            cxh_l.append(cxh)
            temp_h += 1
    return hl_l, hr_l, cxh_l, temp_h


def actual_width_in_mm(lb, lt, rb, rt, cxr, cxl):
    """
    * Function Name:actual_width_in_mm()
    * Input:	    	co-ordinates of left bottom, left top, right bottom, right top,
                    	right contour centroid, left contour centroid
    * Output:		returns actual width of the door
    * Logic:		It takes the actual depth and using filters the black noise spaces are made white
                    	The 20 pixels of the area of left and right edges are processed.
                    	the minimum value in them is found and the depth is that value.
                    	Using pixel knowledge we find the angle and then using cosine rule
                    	we find the actual width of the door.
    * Example Call:	actual_width_in_mm(lb, lt, rb, rt, cxr, cxl)
    """
    a = freenect.sync_get_depth(format=freenect.DEPTH_MM)[0]
    a /= 30.0
    a = a.astype(np.uint8)
    ret, mask = cv2.threshold(a, 1, 255, cv2.THRESH_BINARY_INV)
    ad = a + mask
    pts1 = np.float32([[lt[0]-30, lt[1]], [lt[0], lt[1]],
                       [lb[0]-30, lb[1]], [lb[0], lb[1]]])
    pts2 = np.float32([[0, 0], [30, 0], [0, lb[1]-lt[1]], [30, lb[1]-lt[1]]])
    m = cv2.getPerspectiveTransform(pts1, pts2)
    dst = cv2.warpPerspective(ad, m, (30, lb[1]-lt[1]))
    left_depth = np.amin(dst)*30
    pts1 = np.float32([[rt[0], rt[1]], [rt[0]+30, rt[1]],
                       [rb[0], rb[1]], [rb[0]+30, rb[1]]])
    pts2 = np.float32([[0, 0], [30, 0], [0, rb[1]-rt[1]], [30, rb[1]-rt[1]]])
    m = cv2.getPerspectiveTransform(pts1, pts2)
    dst = cv2.warpPerspective(ad, m, (30, rb[1]-rt[1]))
    right_depth = np.amin(dst)*30
    pixel_width = cxr-cxl
    angle = (pixel_width/640.0)*(57/180.0)*math.pi
    width = (left_depth*left_depth) + (right_depth*right_depth) \
            - (2*left_depth*right_depth*math.cos(angle))
    width = math.sqrt(width)
    return width


def actual_height_in_mm(lb, lt, rb, rt):
    """
    * Function Name:actual_height_in_mm()
    * Input:	    	co-ordinates of left bottom, left top, right bottom, right top
    * Output:		returns the heights of the left and right door edges
    * Logic:		It takes the actual depth and using filters the black noise spaces are made white
                    	than top and bottom points area is accessed and minimum value is selected from it.
                    	Then after getting the depth of the points, than the height of the egde is calculated using
                    	cosine rule.
    * Example Call:	actual_height_in_mm(lb, lt, rb, rt)
    """
    a = freenect.sync_get_depth(format=freenect.DEPTH_MM)[0]
    a /= 30.0
    a = a.astype(np.uint8)
    ret, mask = cv2.threshold(a, 1, 255, cv2.THRESH_BINARY_INV)
    ad = a + mask
    left_top = ad[lt[1]:lt[1]+10, lt[0]-30:lt[0]]
    left_top_depth = np.amin(left_top)*30
    left_bottom = ad[lb[1]-10:lb[1], lb[0]-30:lb[0]]
    left_bottom_depth = np.amin(left_bottom)*30
    right_top = ad[rt[1]:rt[1] + 10, rt[0]:rt[0] + 30]
    right_top_depth = np.amin(right_top)*30
    right_bottom = ad[rb[1]-10:rb[1], rb[0]:rb[0] + 30]
    right_bottom_depth = np.amin(right_bottom)*30
    left_pixel_height = lb[1] - lt[1]
    right_pixel_height = rb[1] - rt[1]
    left_angle = (left_pixel_height/480.0)*(47/180.0)* math.pi
    right_angle = (right_pixel_height/480.0)*(47/180.0)* math.pi
    left_height = left_top_depth * left_top_depth\
                  + left_bottom_depth * left_bottom_depth - \
                  2 * left_bottom_depth * left_top_depth \
                  * math.cos(left_angle)
    right_height = right_top_depth * right_top_depth \
                   + right_bottom_depth * right_bottom_depth - \
                   2 * right_bottom_depth * right_top_depth * \
                   math.cos(right_angle)
    left_height = math.sqrt(left_height)
    right_height = math.sqrt(right_height)
    return left_height, right_height


def return_height_in_mm(lb, lt, rb, rt):
    """
    * Function Name: return_height_in_mm()
    * Input:	    co-ordinates of left bottom, left top, right bottom, right top
    * Output:		returns the heights of the left and right door edges
    * Logic:		It takes the actual depth and using filters the black noise spaces are made white
                    than top and bottom points area is accessed and minimum value is selected from it.
                    Then after getting the depth of the points, than the height of the egde is calculated using
                    cosine rule.
    * Example Call:	return_height_in_mm(lb, lt, rb, rt)
    """
    a = freenect.sync_get_depth(format=freenect.DEPTH_MM)[0]
    left_bottom_x, left_bottom_y = lb[0], lb[1]
    left_top_x, left_top_y = lt[0], lt[1]
    right_bottom_x, right_bottom_y = rb[0], rb[1]
    right_top_x, right_top_y = rt[0], rt[1]
    left_top_area = a[left_top_y:left_top_y+10, left_top_x-10:left_top_x]
    mask = left_top_area == 0
    left_top_area[mask] = 8000
    top = np.amin(left_top_area)
    bound_rect = a[left_top_y:left_bottom_y, left_top_x - 20:left_top_x]
    mask = bound_rect == 0
    bound_rect[mask] = 8000
    bottom = np.amin(bound_rect)
    left_height = math.sqrt(top**2 - bottom**2)
    right_top_area = a[right_top_y:right_top_y+10, right_top_x:right_top_x+10]
    mask = right_top_area == 0
    right_top_area[mask] = 8000
    top = np.amin(right_top_area)
    bound_rect_right = \
        a[right_top_y:right_bottom_y, right_top_x:right_top_x + 20]
    mask = bound_rect_right == 0
    bound_rect_right[mask] = 8000
    bottom = np.amin(bound_rect_right)
    right_height = math.sqrt(top**2 - bottom**2)
    cv2.line(z, lt, lb, (128, 255, 0), 10)
    cv2.line(z, rt, rb, (128, 255, 0), 10)
    return left_height, right_height


def rectangle_door_test(lb, lt, rb, rt, cxl, cxr, hl, hr, cxh):
    """
    * Function Name:rectangle_door_test()
    * Input:		left bottom, left top, right bottom, left_centroid, right centroid, left horizontal,
                    right horizontal, center of the line
    * Output:		returns the average probability of the door
    * Logic:		using three points on the edges we found the distance between the door widths.
                    We than compared the errors and found the probability of it.
                    The average of the three probabilities is returned
    * Example Call:	rectangle_door_test(lb, lt, rb, rt, cxl, cxr, hl, hr, cxh)
    """
    if cxh > cxl and cxh < cxr:
        top_edge_pixel_length = hr[0] - hl[0]
        top = rt[0] - lt[0]
        middle = cxr - cxl
        bottom = rb[0] - lb[0]
        top_error = top - top_edge_pixel_length
        middle_error = middle - top_edge_pixel_length
        bottom_error = bottom - top_edge_pixel_length
        prob_top = probability(0, 200, top_error)
        prob_middle = probability(0, 200, middle_error)
        prob_bottom = probability(0, 200, bottom_error)
        prob_avg = (prob_top + prob_middle + prob_bottom) / 3
        return prob_avg


def probability(std_value, sigma, data):
    """
    * Function Name:probability()
    * Input:		standard value(mean), Deviation, data
    * Output:		returns the probability of the data
    * Logic:		It forms a Gaussian curve of the range of data. From the
                    curve it returns the probability of the data
    * Example Call:	probability(40, 20, 50)
    """
    p = int(round(data))
    x = np.linspace(std_value-sigma, std_value+sigma, 2*sigma)
    a = lab.normpdf(x, std_value, sigma)
    a = a/(a[len(a)/2])*100
    new_value = []
    for i in xrange(2*sigma):
        new_value.append(((a[i] - 60) * 100) / 40)
    if p >= std_value-sigma and p <= std_value+sigma:
        return new_value[p - (std_value - sigma)]
    else:
        return 0


def actual_width_test(width):
    """
    * Function Name:actual_width_test()
    * Input:		width of the door
    * Output:		returns probability of door detection
    * Logic:		probability of the door width is calculated
    * Example Call:	actual_width_test(500)
    """
    prob = probability(1000, 1000, width)
    return prob


def actual_height_test(left_height, right_height):
    """
    * Function Name:actual_height_test()
    * Input:		left edge height, right edge height
    * Output:		returns probability of door detection
    * Logic:		probability of heights of left and right edges are
                    calculated and the average is returned.
    * Example Call:	actual_height_test(500,600)
    """
    left_prob = probability(1500, 1500, left_height)
    right_prob = probability(1000, 1000, right_height)
    return (left_prob+right_prob)/2.0


def door_detection(contours_right_door, contours_left_door, test_cases_door):
    """
    * Function Name:door_detection()
    * Input:		right door contours, left door contours, tests flag
    * Output:		Detects the door.
    * Logic:		left and right lines are detected
                    than the door is detected through the test which will be selected by the user
                    Probability of all the tests are calculated and the if the door is detected it will beep
                    the flag is set to true when the door is detected a number of times.
    * Example Call:	door_detection(contours_right, contours_left, test_cases)
    """
    global flag
    global count
    global axis_plot
    weighted_probability = 0
    prob_1 = 0
    lt_l, lb_l, cxl_l, rt_l, rb_l, cxr_l, temp_l, temp_r = \
        left_right_lines(contours_right_door, contours_left_door)
    hl_l, hr_l, cxh_l, temp_h = horizontal_lines()
    test_1, test_2, test_3 = test_cases_door
    for i in xrange(temp_l):
        for j in xrange(temp_r):
            if is_door(lb_l[i], lt_l[i], rb_l[j], rt_l[j], cxr_l[j], cxl_l[i]):
                left_height, right_height = \
                    return_height_in_mm(lb_l[i], lt_l[i], rb_l[j], rt_l[j])
                width = actual_width_in_mm(lb_l[i], lt_l[i], rb_l[j],
                                           rt_l[j], cxr_l[j], cxl_l[i])
                if test_2:
                    prob_2 = actual_height_test(left_height, right_height)
                else:
                    prob_2 = 0
                if test_3:
                    prob_3 = actual_width_test(width)
                else:
                    prob_3 = 0
                for k in xrange(temp_h):
                    if test_1:
                        max_prob = rectangle_door_test(lb_l[i], lt_l[i], rb_l[j], rt_l[j], cxl_l[i], cxr_l[j], hl_l[k], hr_l[k], cxh_l[k])
                    else:
                        max_prob = 0
                    if max_prob > prob_1:
                        prob_1 = max_prob
                weighted_probability = 0.1 * prob_1 + 0.5 * prob_2 + 0.4 * prob_3
                print "Door Detected with confidence: " + str(weighted_probability)
                if weighted_probability > 60:
                    mid_point = (cxr_l[j]+cxl_l[i])/2.
                    doorway_movement(mid_point)
                    count += 1
                    for i in xrange(5):
                        ser.write('\x37')
                    time.sleep(0.5)
                    for i in xrange(5):
                        ser.write('\x39')
    a.append(axis_plot)
    b.append(weighted_probability)
    axis_plot += 1
    plt.plot(a,b)
    plt.draw()
    if axis_plot == 100:
        axis_plot = 0
        a[:]=[]
        b[:]=[]
        plt.clf()
    if count == 1:
        flag = True


def take_right():
    """
    * Function Name:take_right
    * Input:		None
    * Output:		Takes Right turn
    * Logic:		This function takes a right turn until
                    the mean of the middlearea crosses the threshold value
    * Example Call:	take_right()
    """
    while 1:
        z_right = get_depth()
        back_movement(z_right)
        middle_area = z_right[200:479, 200:439]
        middle_val = middle_area.mean()
        ser.write("\x44")
        if middle_val > 30:
            return


def take_left():
    """
    * Function Name:take_left
    * Input:		None
    * Output:		Takes Left turn
    * Logic:		This function takes a left turn until the mean
                    of the middle_area crosses the threshold value
    * Example Call:	take_left()
    """
    while 1:
        z_left = get_depth()
        back_movement(z_left)
        middle_area = z_left[200:479, 200:439]
        middle_val = middle_area.mean()
        ser.write("\x45")
        if middle_val > 30:
            return


def take_right_near():
    """
    * Function Name:take_right_near
    * Input:		None
    * Output:		Takes Right turn
    * Logic:		This function takes a Right turn until the
                    obstacle is not detected i.e. If the obstacle is in range
                    it will turn until it is out of its sight
    * Example Call:	take_right_near()
    """
    while 1:
        z_near = get_depth()
        back_movement(z_near)
        middle_area = z_near[0:479, 240:399]
        contours_right_near = contours_return(z_near, -10)
        contours_left_near = contours_return(z_near, 10)
        door_detection(contours_right_near, contours_left_near, test_cases)
        ser.write("\x44")
        if count_near_pixels(middle_area, 900) < 1000:
            return


def take_left_near():
    """
    * Function Name:take_left_near
    * Input:		None
    * Output:		Takes Left turn
    * Logic:		This function takes a Left turn until
                    the obstacle is not detected i.e. If the
                    obstacle is in range
                    it will turn until it is out of its sight
    * Example Call:	take_left_near()
    """
    while 1:
        z_near = get_depth()
        back_movement(z_near)
        middle_area = z_near[0:479, 240:399]
        contours_right_near = contours_return(z_near, -10)
        contours_left_near = contours_return(z_near, 10)
        door_detection(contours_right_near, contours_left_near, test_cases)
        ser.write("\x45")
        if count_near_pixels(middle_area, 900) < 1000:
            return


def stuck_pos_movement():
    """
    * Function Name:stuck_pos_movement
    * Input:		None
    * Output:		Removes robot from a stuck position
    * Logic:		When both the middle left and middle right
                    detect an obstacle it takes the mean of the left and right
                    area and the area with lesser mean is the preferable
                    area to go
    * Example Call:	stuck_pos_movement()
    """
    z_pos = get_depth()
    left_area = z_pos[0:479, 0:200]
    right_area = z_pos[0:479, 439:639]
    left_val = left_area.mean()
    right_val = right_area.mean()
    if left_val > right_val:
        take_left_near()
    else:
        take_right_near()


def data_send(x, y):
    """
    * Function Name:data_send
    * Input:		left and right speed mode
    * Output:		Sends speed mode of the robot wheels to the
                    Fire bird V for further analysis
    * Logic:		Total 25 different possibilities of speed modes are
                    their according to the vertical frame in which the
                    obstacle is	detected and using if else statements proper
                    speed mode is sent
    * Example Call:	data_send(speed_left,speed_right)
    """
    if x == 0:
        if y == 0:
            ser.write('\x00')
        elif y == 1:
            ser.write('\x01')
        elif y == 2:
            ser.write('\x02')
        elif y == 3:
            ser.write('\x03')
        elif y == 4:
            ser.write('\x04')
    elif x == 1:
        if y == 0:
            ser.write('\x10')
        elif y == 1:
            ser.write('\x11')
        elif y == 2:
            ser.write('\x12')
        elif y == 3:
            ser.write('\x13')
        elif y == 4:
            ser.write('\x14')
    elif x == 2:
        if y == 0:
            ser.write('\x20')
        elif y == 1:
            ser.write('\x21')
        elif y == 2:
            ser.write('\x22')
        elif y == 3:
            ser.write('\x23')
        elif y == 4:
            ser.write('\x24')
    elif x == 3:
        if y == 0:
            ser.write('\x30')
        elif y == 1:
            ser.write('\x31')
        elif y == 2:
            ser.write('\x32')
        elif y == 3:
            ser.write('\x33')
        elif y == 4:
            ser.write('\x34')
    elif x == 4:
        if y == 0:
            ser.write('\x40')
        elif y == 1:
            ser.write('\x41')
        elif y == 2:
            ser.write('\x42')
        elif y == 3:
            ser.write('\x43')
        elif y == 4:
            stuck_pos_movement()


def count_near_pixels(area, dist):
    """
    * Function Name:Count_near_pixels
    * Input:		area and the distance up to which the obstacle should be detected
    * Output:		Returns the number of obstacle pixels that are
                    in the distance range.
    * Logic:		The depth data is Binary threshold according
                    to the obstacle detected in its range. Than the NonZeros
                    are counted as they are the obstacle
    * Example Call:	Count_near_pixels(area,900)
    """
    ret, th3 = cv2.threshold(area, dist/30, 255, cv2.THRESH_BINARY_INV)
    count_pixel = cv2.countNonZero(th3)
    return count_pixel


def door_movement():
    """
    * Function Name:door_movement()
    * Input:		None
    * Output:		Robot follows where the door is.
    * Logic:		The region is divided in three regions.
                    The middle region is checked for its value and
                    the left and right area are analyzed if the middle
                    region is too close to the door.
    * Example Call:	door_movement(c)
    """
    middle_area = z[200:479, 200:439]
    middle_val = count_near_pixels(middle_area, 900)
    left_area = z[0:479, 0:100]
    right_area = z[0:479, 539:639]
    left_val = left_area.mean()
    right_val = right_area.mean()
    if middle_val < 1000:
        ser.write("\x00")
        time.sleep(0.1)
    else:
        if left_val > right_val:
            take_left()
        else:
            take_right()


def search_wall(wall):
    """
    * Function Name:search_wall
    * Input:		left/right wall
    * Output:		follows left or right wall
    * Logic:		If left wall is selected for instance then
                    the robot moves along the wall. The robot keeps track of
                    the objects on the left side of frame for left
                    wall and if the frame does not have any object in the
                    range than the robot moves left until it is detected
    * Example Call:	search_wall(0)
    """
    if wall == 0:
        while True:
            z_wall = get_depth()
            back_movement(z_wall)
            area = z_wall[0:479, 0:319]
            contours_right_wall = contours_return(z_wall, -10)
            contours_left_wall = contours_return(z_wall, 10)
            door_detection(contours_right_wall, contours_left_wall, test_cases)
            ser.write("\x03")
            if count_near_pixels(area, 1800) > 1000:
                break
    elif wall == 1:
        while True:
            z_wall = get_depth()
            back_movement(z_wall)
            area = z_wall[0:479, 320:639]
            contours_right_wall = contours_return(z_wall, -10)
            contours_left_wall = contours_return(z_wall, 10)
            door_detection(contours_right_wall, contours_left_wall, test_cases)
            ser.write("\x30")
            if count_near_pixels(area, 1800) > 1000:
                break


def regular_movement():
    """
    * Function Name:regular_movement
    * Input:		Original depth frame
    * Output:		robot moves without bumping into any obstacle
    * Logic:		The frame is divided in 8 vertical sections.
                    Speed mode is selected from the speed_right and speed_left.
                    There are 4	left frames and 4 right frames.
                    The frame loop starts from middle and if any frame
                    detects any obstacle break the loop	and the
                    corresponding data is saved in the speed_left or
                    speed_right variable
    * Example Call:	regular_movement(original)
    """
    x = 320
    speed = 4
    for i in xrange(4):
        area = z[0:479, x:x+79]
        if count_near_pixels(area, 900) > 1000:
            break
        speed -= 1
        x += 80
    speed_right = speed
    x = 319
    speed = 4
    for i in xrange(4):
        area = z[0:479, x-79:x]
        if count_near_pixels(area, 900) > 1000:
            break
        speed -= 1
        x -= 80
    speed_left = speed
    if speed_left != 0 or speed_right != 0:
        data_send(speed_left, speed_right)
    else:
        search_wall(wall)
        ser.write("\x00")


def horizontal_edge(c):
    """
    * Function Name:horizontal_edge()
    * Input:		A Contour
    * Output:		Detects horizontal edge in the frame
    * Logic:		The contour is checked for its area
                    The extreme points are calculated for each contour.
                    The pixel width and height of the contour should fall in a given range.
                    If the values fall in a given range then the horizontal edge is detected
                    The centroid is calculated and the co-ordinates are returned
    * Example Call:	horizontal_edge(c)
    """
    area = 500
    ys = 50
    xs = 100
    if cv2.contourArea(c) > area:
        leftmost = tuple(c[c[:, :, 0].argmin()][0])
        rightmost = tuple(c[c[:, :, 0].argmax()][0])
        topmost = tuple(c[c[:, :, 1].argmin()][0])
        bottommost = tuple(c[c[:, :, 1].argmax()][0])
        x1 = leftmost[0]
        x2 = rightmost[0]
        y1 = topmost[1]
        y2 = bottommost[1]
        if (y2 - y1 < ys) and (abs(x2 - x1) > xs):
            cv2.line(z, leftmost, rightmost, (0, 255, 0), 5)
            hl = leftmost
            hr = rightmost
            m = cv2.moments(c)
            cxh = int(m['m10']/m['m00'])
            return hl, hr, cxh
    return 0, 0, 0


def doorway_movement(mid_point):
    if mid_point > 80 and mid_point < 200:
        for i in xrange(5):
            data_send(0,4)
        time.sleep(0.1)
    if mid_point > 200 and mid_point < 320:
        for i in xrange(5):
            data_send(0,2)
        time.sleep(0.1)
    if mid_point > 320 and mid_point < 440:
        for i in xrange(5):
            data_send(4,0)
        time.sleep(0.1)
    if mid_point >440 and mid_point < 560:
        for i in xrange(5):
            data_send(2,0)
        time.sleep(0.1)


def back_movement(z_back):
    if z_back[0:479,200:439].mean() > 200 or z_back[0:479,0:199].mean() > 200 or z_back[0:479,440:639].mean() > 200:
        ser.write('\x50')
        time.sleep(3)


plt.ion()
plt.figure()
a = []
b = []
ctx = freenect.init()
dev = freenect.open_device(ctx, freenect.num_devices(ctx) - 1)

freenect.set_tilt_degs(dev, 20)
freenect.close_device(dev)
test_cases = [True, True, True]
#for i in xrange(5):
#    z = get_depth()
#left_mean = z[0:479,0:319].mean()
#right_mean = z[0:479,320:639].mean()
#if left_mean > right_mean:
#    wall = 1
#else: wall = 0
for i in xrange(5):
    zp = get_depth()
wall = 0
while True:
    z = get_depth()	 # returns the depth frame
    back_movement(z)
    contours_right = contours_return(z, -10)
    contours_left = contours_return(z, 10)
    door_detection(contours_right, contours_left, test_cases)
    if flag:
        door_movement()
    else:
        regular_movement()
    cv2.imshow('final', z)
    if cv2.waitKey(1) != -1:
        ser.write('\x35')
        ser.close()
        break

cv2.destroyAllWindows()
