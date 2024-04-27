# lens.py
import cv2
import numpy as np
import ezdxf

REAL_SIZE = 53
LOWER_THRESH = 60
THICKNESS_mm = 5

def convert_to_dxf(input_file, output_file):
    im = cv2.imread(input_file)

    hsv_image = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds for the blue color
    lower_blue = np.array([100, 50, 50])  # HSV values for lower blue
    upper_blue = np.array([130, 255, 255])  # HSV values for upper blue

    # Threshold the HSV image to get only blue colors
    blue_mask = cv2.inRange(hsv_image, lower_blue, upper_blue)
    blue_pixels = cv2.bitwise_and(im, im, mask=blue_mask)
    blue_bbox = cv2.boundingRect(blue_mask)

    # find the size of the blue circle in pixels to calibrate final size
    pixel_size = ((blue_bbox[2]+blue_bbox[3])//2)
    pixels2mm = REAL_SIZE / pixel_size

    imCopy = im.copy()

    # convert to grayscale and detect edges of lens
    imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(imgray, (3, 3), 0)
    edges = cv2.Canny(blurred, LOWER_THRESH, 200)

    # remove blue pixels from image
    edges[max(blue_bbox[1]-5,0):blue_bbox[1]+blue_bbox[3]+10, max(blue_bbox[0]-5,0):blue_bbox[0]+blue_bbox[2]+10] = 0
    ret, thresh = cv2.threshold(edges, 127, 255, 0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    ## Extend contour to get frame 
    contour_image = np.zeros(im.shape, dtype=np.uint8)

    cv2.drawContours(contour_image, contours, 0, (0,255,0), 3)

    dilation_pixels = int(THICKNESS_mm / pixels2mm * 2)

    # Dilate the contour
    kernel = np.ones((dilation_pixels, dilation_pixels), np.uint8)
    dilated_contour = cv2.dilate(contour_image, kernel, iterations=1)
    dilated_contour = cv2.cvtColor(dilated_contour, cv2.COLOR_BGR2GRAY)
    _, dil_thresh = cv2.threshold(dilated_contour, 127, 255, 0)
    dil_contours, dil_hierarchy = cv2.findContours(dil_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    squeezed = [np.squeeze(cnt, axis=1) for cnt in [contours[0]]]
    squeezed.extend([np.squeeze(cnt, axis=1) for cnt in [dil_contours[0]]])

    # Save contours as dxf vector file
    dwg = ezdxf.new('R2010')
    msp = dwg.modelspace()
    dwg.layers.new(name='lens_outline', dxfattribs={'color': 7})

    for ctr in squeezed:
        for n in range(len(ctr) - 1):
            x_coord_start, y_coord_start = ctr[n] * pixels2mm
            x_coord_end, y_coord_end = ctr[n+1] * pixels2mm
            msp.add_line((x_coord_start, y_coord_start), (x_coord_end, y_coord_end), dxfattribs={'layer': 'lens_outline', 'lineweight': -3})

    dwg.saveas(output_file)

# The convert_to_dxf function can now be imported and called from backend.py
