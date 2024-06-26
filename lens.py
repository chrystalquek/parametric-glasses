import cv2
import numpy as np
import ezdxf
import sys

REAL_SIZE = 53
LOWER_THRESH = 40
THICKNESS_mm = 3

def convert_to_dxf(input_file, output_file):
    im = cv2.imread(input_file)

    hsv_image = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds for the blue color
    lower_blue = np.array([100, 50, 50])  # HSV values for lower blue
    upper_blue = np.array([130, 255, 255]) # HSV values for upper blue

    # Threshold the HSV image to get only blue colors
    blue_mask = cv2.inRange(hsv_image, lower_blue, upper_blue)
    blue_pixels = cv2.bitwise_and(im, im, mask=blue_mask)
    blue_bbox = cv2.boundingRect(blue_mask)

    # find the size of the blue circle in pixels to calibrate final size
    pixel_size = ((blue_bbox[2]+blue_bbox[3])//2)
    pixels2mm = REAL_SIZE/ pixel_size

    imCopy = im.copy()

    # convert to grayscale and detect edges of lens
    imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(imgray, (5, 5), 0)
    blurred = blurred *2
    blurred = np.clip(blurred, 0, 255)
    edges = cv2.Canny(blurred,LOWER_THRESH,200)

    # remove blue pixels from image
    edges[max(blue_bbox[1]-5,0):blue_bbox[1]+blue_bbox[3]+10,max(blue_bbox[0]-5,0):blue_bbox[0]+blue_bbox[2]+10] = 0

    # find contours of lens
    ret,thresh = cv2.threshold(edges,127,255,0)
    contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    # add up long contours and create a convex hull shape
    sorted_contours = sorted(contours, key=lambda x: len(x), reverse = True)
    com_contour = np.empty((0,1,2), dtype=np.uint8)
    for i in range(len(sorted_contours)):
        if len(sorted_contours[i]) > 100:
            com_contour = np.concatenate((com_contour, sorted_contours[i]))

    hull= cv2.convexHull(com_contour, False)

    ## Extend contour to get frame 
    contour_image = np.zeros(im.shape, dtype=np.uint8)
    cv2.drawContours(contour_image, [hull], -1, (0,255,0), 3)
    dilation_pixels = int(THICKNESS_mm/pixels2mm * 2)

    ## Dilate the contour
    kernel = np.ones((dilation_pixels, dilation_pixels), np.uint8)
    dilated_contour = cv2.dilate(contour_image, kernel, iterations=1)

    # Find contours of dilation to get frame outline
    dilated_contour = cv2.cvtColor(dilated_contour,cv2.COLOR_BGR2GRAY)
    _,dil_thresh = cv2.threshold(dilated_contour,127,255,0)
    dil_contours, dil_hierarchy = cv2.findContours(dil_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # find bounding box of contour
    bbox = cv2.boundingRect(dil_contours[0])
    print("bboxes", bbox[0]*pixels2mm," ",bbox[1]* pixels2mm)

    # squeezed = [np.squeeze(cnt, axis=1) for cnt in [contours[0]]]

    squeezed = [np.squeeze(hull, axis=1)]

    # squeezed.extend([np.squeeze(cnt, axis=1) for cnt in [dil_contours[0]]])

    squeezed2 = [np.squeeze(dil_contours[0], axis=1)]

    # Save contours as dxf vector file
    dwg = ezdxf.new("R2010")
    msp = dwg.modelspace()
    dwg.layers.new(name="lens_outline", dxfattribs={"color": 7})
    dwg.layers.new(name="case_outline", dxfattribs={"color": 5})

    for ctr in squeezed:
        for n in range(len(ctr)):
            
            x_coord = ctr[n] * pixels2mm
            y_coord = ctr[(n+1)%len(ctr)] * pixels2mm
            msp.add_line(x_coord, y_coord , dxfattribs={"layer": "lens_outline", "lineweight": -3})

    for ctr in squeezed2:
        for n in range(len(ctr)):
            
            x_coord = ctr[n] * pixels2mm
            y_coord = ctr[(n+1)%len(ctr)] * pixels2mm
            msp.add_line(x_coord, y_coord , dxfattribs={"layer": "case_outline", "lineweight": -3})


            
    dwg.saveas(output_file)
    
    return bbox[0]*pixels2mm, bbox[1]* pixels2mm
