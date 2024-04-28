import os
import glob
import shutil
import argparse
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from PIL import Image, ImageOps
from face_landmarks.libs.helper_func import vid2images, images2vid
from face_landmarks.libs.face import FaceDetector, FaceLandmarksDetector
from face_landmarks.libs.iris import IrisDetector

IRIS_DIAMETER_CM = 1.18
LENS_WIDTH_CM = 5.2 # this shouldn't be a constant, get from justin's code

STANDARD_BRIDGE_WIDTH = 2
STANDARD_FRAME_WIDTH = 13.2


def get_temples_width(face_landmarks_detection):
    # left_temple_idx = face_landmarks_detection[:, 0].argmin()
    # left_temple = face_landmarks_detection[left_temple_idx]
    # right_temple_idx = face_landmarks_detection[:, 0].argmax()
    # right_temple = face_landmarks_detection[right_temple_idx]
    
    left_temple = face_landmarks_detection[139]
    right_temple = face_landmarks_detection[368]
    temples = [np.array([left_temple, right_temple])]
    temple_to_temple_distance = np.abs(left_temple[0] - right_temple[0])
    
    # 127, 356
    
    return temples, temple_to_temple_distance
    
def get_eye_corners(face_landmarks_detector, face_landmarks_detection):
    key_leye = ["leftEyeUpper0", "leftEyeLower0"]
    key_reye = ["rightEyeUpper0", "rightEyeLower0"]
    left_eye_indices = face_landmarks_detector.get_face_landmarks_indices_by_regions(key_leye)
    right_eye_indices = face_landmarks_detector.get_face_landmarks_indices_by_regions(key_reye)
    left_eye_region = face_landmarks_detection[left_eye_indices, :]
    right_eye_region = face_landmarks_detection[right_eye_indices, :]
    left_eye_right = left_eye_region[np.argmin(left_eye_region[:, 0])]
    right_eye_left = right_eye_region[np.argmax(right_eye_region[:, 0])]
    eyes = [np.array([left_eye_right, right_eye_left])]
    corner_eyes_distance = np.abs(left_eye_right[0] - right_eye_left[0])
    return eyes, corner_eyes_distance

def get_iris_diameter(iris_detector, input_image, face_landmarks_detection):
    left_eye_image, right_eye_image, left_config, right_config = iris_detector.preprocess(input_image, face_landmarks_detection)
    left_eye_contour, left_eye_iris = iris_detector.predict(left_eye_image)
    right_eye_contour, right_eye_iris = iris_detector.predict(right_eye_image, isLeft=False)
    ori_left_eye_contour, ori_left_iris = iris_detector.postprocess(left_eye_contour, left_eye_iris, left_config)
    ori_right_eye_contour, ori_right_iris = iris_detector.postprocess(right_eye_contour, right_eye_iris, right_config)
    left_eye_left = ori_left_iris[left_eye_iris[:, 0].argmax()]
    left_eye_right = ori_left_iris[left_eye_iris[:, 0].argmin()]
    left_eye_pts = np.array([left_eye_left, left_eye_right])
    right_eye_left = ori_right_iris[right_eye_iris[:, 0].argmax()]
    right_eye_right = ori_right_iris[right_eye_iris[:, 0].argmin()]
    right_eye_pts = np.array([right_eye_left, right_eye_right])
    iris_diameter = np.mean([np.abs(left_eye_right[0] - left_eye_left[0]), np.abs(right_eye_left[0] - right_eye_right[0])])
    return left_eye_pts, right_eye_pts, iris_diameter

def get_face_landmarks_pixels(input_image, is_demo):
    face_landmarks_detector = FaceLandmarksDetector()
    iris_detector = IrisDetector()
    face_landmarks_detections = face_landmarks_detector.predict(input_image)
    face_landmarks_detection = face_landmarks_detections[0]
    
    # 1. compute temples -> width of specs
    temples, temple_to_temple_distance = get_temples_width(face_landmarks_detection)
    if is_demo:
        face_landmarks_detector.visualize(input_image, temples)
        # print("temple_to_temple_distance", temple_to_temple_distance)
    
    # 2. corner of eyes -> width of bridge
    eyes, corner_eyes_distance = get_eye_corners(face_landmarks_detector, face_landmarks_detection)
    if is_demo:
        face_landmarks_detector.visualize(input_image, eyes)
        # print("corner_eyes_distance", corner_eyes_distance)

    # 3. iris diameter -> scale from px to cm
    left_eye_pts, right_eye_pts, iris_diameter = get_iris_diameter(iris_detector, input_image, face_landmarks_detection)
    if is_demo:
        plt.imshow(input_image)
        plt.scatter(left_eye_pts[:, 0], left_eye_pts[:, 1], s=3)
        plt.scatter(right_eye_pts[:, 0], right_eye_pts[:, 1], s=2)
        plt.show()
    # print("iris_diameter", iris_diameter)
    
    if is_demo:
        return temple_to_temple_distance, corner_eyes_distance, iris_diameter
    else:
        return temple_to_temple_distance, corner_eyes_distance, iris_diameter, temples, eyes, left_eye_pts, right_eye_pts

def get_spectacle_parameters(temple_to_temple_distance_px, corner_eyes_distance_px, iris_diameter_px):
    # scale from px to cm
    pixel_to_cm = iris_diameter_px / IRIS_DIAMETER_CM
    temple_to_temple_distance_cm, corner_eyes_distance_cm = temple_to_temple_distance_px / pixel_to_cm, corner_eyes_distance_px / pixel_to_cm
    
    # what we want is the nose bridge length and frame width
    # Are eyes close together? 14-18mm, otherwise >= 18mm 
    # Temple-to-temple frame width +- (2-3mm) = 2 * lens width + bridge width + 6 # 2 * LENS_WIDTH_CM + bridge_width + 6
    bridge_width = corner_eyes_distance_cm - 2
    frame_width = temple_to_temple_distance_cm * 0.95
    
    print("bridge_width", bridge_width, "frame_width", frame_width)
    
    assert 1.4 < bridge_width < 2.4
    assert 12.5 < frame_width < 15.0
    
    return bridge_width, frame_width
    


def demo(filename):
    # try:
    input_image = np.array(ImageOps.exif_transpose(Image.open(filename)).convert('RGB')) # (columns, row, depth)
    
    temple_to_temple_distance_px, corner_eyes_distance_px, iris_diameter_px = get_face_landmarks_pixels(input_image)
    
    bridge_width, frame_width = get_spectacle_parameters(temple_to_temple_distance_px, corner_eyes_distance_px, iris_diameter_px)
    
    return bridge_width, frame_width
    
    # except Exception as e:
        
    #     return STANDARD_BRIDGE_WIDTH, STANDARD_FRAME_WIDTH
    
    
    
def no_demo(img):
    try:
        input_image = np.array(img) # .convert('RGB') # (columns, row, depth)
        
        temple_to_temple_distance_px, corner_eyes_distance_px, iris_diameter_px, temples, eyes, left_eye_pts, right_eye_pts = get_face_landmarks_pixels(input_image, is_demo=False)
        
        bridge_width, frame_width = get_spectacle_parameters(temple_to_temple_distance_px, corner_eyes_distance_px, iris_diameter_px)
        
        return bridge_width, frame_width
    
    except AssertionError as e:
        
        return STANDARD_BRIDGE_WIDTH, STANDARD_FRAME_WIDTH
    
    


        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--is_display', '-d', default=True, help="Display face landmarks.")
    parser.add_argument('--image_filename', '-f', default="me.jpeg", help="What is the filename")
    args = parser.parse_args()
    
    filename = args.image_filename
    print(demo(filename))
