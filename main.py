import os
import glob
import shutil
import argparse
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from PIL import Image, ImageOps
from libs.helper_func import vid2images, images2vid
from libs.face import FaceDetector, FaceLandmarksDetector
from libs.iris import IrisDetector

# def main(args):
#     video_name = args.source.split('/')[-1].split('.')[0]

#     if os.path.exists('./tmp'):
#         shutil.rmtree('./tmp')
#     os.mkdir('./tmp')
    
#     vid2images(args.source, out_path='./tmp')

#     if not os.path.exists('./results'):
#         os.mkdir('./results')
#     output_dir = './results/{}'.format(video_name)
#     if not os.path.exists(output_dir):
#         os.mkdir(output_dir)
#     if not os.path.exists(output_dir+'/images'):
#         os.mkdir(output_dir+'/images')

#     face_landmarks_detector = FaceLandmarksDetector()    
#     iris_detector = IrisDetector()
#     for image_path in tqdm(sorted(glob.glob('./tmp/*.png'))):
#         # im = ImageOps.exif_transpose(im)
#         # input_image = np.array(Image.open(image_path).convert('RGB'))
#         input_image = np.array(ImageOps.exif_transpose(Image.open(image_path)).convert('RGB'))

#         face_landmarks_detections = face_landmarks_detector.predict(input_image)

#         for face_landmarks_detection in face_landmarks_detections:
#             left_eye_image, right_eye_image, left_config, right_config = iris_detector.preprocess(input_image, face_landmarks_detection)

#             left_eye_contour, left_eye_iris = iris_detector.predict(left_eye_image)
#             right_eye_contour, right_eye_iris = iris_detector.predict(right_eye_image, isLeft=False)
            
#             ori_left_eye_contour, ori_left_iris = iris_detector.postprocess(left_eye_contour, left_eye_iris, left_config)
#             ori_right_eye_contour, ori_right_iris = iris_detector.postprocess(right_eye_contour, right_eye_iris, right_config)
#             plt.imshow(input_image)
#             # plt.scatter(ori_left_eye_contour[:, 0], ori_left_eye_contour[:, 1], s=3)
#             plt.scatter(ori_left_iris[:, 0], ori_left_iris[:, 1], s=2)
#             # plt.scatter(ori_right_eye_contour[:, 0], ori_right_eye_contour[:, 1], s=3)
#             plt.scatter(ori_right_iris[:, 0], ori_right_iris[:, 1], s=2)
#             plt.axis('off')
#             plt.savefig(output_dir+'/images/{}'.format(image_path.split('/')[-1]))
#             plt.close()

#     images2vid(output_dir+'/images', output_dir=output_dir)
#     if os.path.exists('./tmp'):
#         shutil.rmtree('./tmp')

def demo():
    print("demo??)")
    # input_image = np.array(Image.open('me.jpeg').convert('RGB'))
    input_image = np.array(ImageOps.exif_transpose(Image.open('me.jpeg')).convert('RGB')) # (row, columns, depth)
    
    # first image
    # face_detector = FaceDetector()
    # face_detections = face_detector.predict(input_image)
    # face_detector.visualize(input_image, face_detections)

    # second image
    face_landmarks_detector = FaceLandmarksDetector()
    face_landmarks_detections = face_landmarks_detector.predict(input_image)
    face_landmarks_detector.visualize(input_image, face_landmarks_detections) # (1, 478, 3) # (person, landmarks, xyz)
    
    
    
    left_temple_idx = face_landmarks_detections[0][:, 0].argmin() # (1, 0, 0)
    left_temple = face_landmarks_detections[0][left_temple_idx] # (1, 2, 3)
    right_temple_idx = face_landmarks_detections[0][:, 0].argmax() # (1, 0, 0)
    right_temple = face_landmarks_detections[0][right_temple_idx]
    temples = [np.array([left_temple, right_temple])]
    # breakpoint()
    face_landmarks_detector.visualize(input_image, temples)
    # (1, 2, 3)
    temple_to_temple_distance = np.abs(left_temple[0] - right_temple[0])
    print("temple_to_temple_distance", temple_to_temple_distance)
    # face_landmarks_detections[0][]    
    
    
    
    key_leye = ["leftEyeUpper0", "leftEyeLower0"]
    key_reye = ["rightEyeUpper0", "rightEyeLower0"]
    left_eye_indices = face_landmarks_detector.get_face_landmarks_indices_by_regions(key_leye)
    right_eye_indices = face_landmarks_detector.get_face_landmarks_indices_by_regions(key_reye)
    left_eye_region = face_landmarks_detections[0][left_eye_indices, :]
    right_eye_region = face_landmarks_detections[0][right_eye_indices, :]
    left_eye_right = left_eye_region[np.argmin(left_eye_region[:, 0])]
    right_eye_left = right_eye_region[np.argmax(right_eye_region[:, 0])]
    eyes = [np.array([left_eye_right, right_eye_left])]
    face_landmarks_detector.visualize(input_image, eyes)
    eye_to_eye_d = np.abs(left_eye_right[0] - right_eye_left[0])
    print("eye_to_eye_d", eye_to_eye_d)
    
    

    for face_landmarks_detection in face_landmarks_detections:
        iris_detector = IrisDetector()
        left_eye_image, right_eye_image, left_config, right_config = iris_detector.preprocess(input_image, face_landmarks_detection)
  

        left_eye_contour, left_eye_iris = iris_detector.predict(left_eye_image)
        right_eye_contour, right_eye_iris = iris_detector.predict(right_eye_image, isLeft=False)

        # third image
        # fig, [ax1, ax2] = plt.subplots(1,2)        
        # ax1.imshow(right_eye_image)
        # ax1.scatter(right_eye_iris[:, 0], right_eye_iris[:, 1], s=3)
        # ax1.scatter(right_eye_contour[:, 0], right_eye_contour[:, 1], s=3)
        # ax1.set(title='right eye')
        # ax2.imshow(left_eye_image)
        # ax2.scatter(left_eye_iris[:, 0], left_eye_iris[:, 1], s=3) # (5, 3)
        # ax2.scatter(left_eye_contour[:, 0], left_eye_contour[:, 1], s=3)
        # ax2.set(title='left eye')
        # plt.show()
        
        
        # left_eye_left = left_eye_iris[left_eye_iris[:, 0].argmax()]
        # left_eye_right = left_eye_iris[left_eye_iris[:, 0].argmin()]
        # left_eye_pts = np.array([left_eye_left, left_eye_right])
        
        # right_eye_left = right_eye_iris[right_eye_iris[:, 0].argmax()]
        # right_eye_right = right_eye_iris[right_eye_iris[:, 0].argmin()]
        # right_eye_pts = np.array([right_eye_left, right_eye_right])
        
        # iris_diameter = np.mean([np.abs(left_eye_right[0] - left_eye_left[0]) * left_config[1], np.abs(right_eye_left[0] - right_eye_right[0]) * right_config[1]])
        
        # print(left_config[1], right_config[1])
        # print("iris_diameter", iris_diameter)
        
        # fig, [ax1, ax2] = plt.subplots(1,2)
        # ax1.imshow(right_eye_image)
        # ax1.scatter(right_eye_pts[:, 0], right_eye_pts[:, 1], s=3)
        # ax1.set(title='right eye')        
        # ax2.imshow(left_eye_image)
        # ax2.scatter(left_eye_pts[:, 0], left_eye_pts[:, 1], s=3)
        # ax2.set(title='left eye')
        # plt.show()
        
        
        
        # fourth image
        ori_left_eye_contour, ori_left_iris = iris_detector.postprocess(left_eye_contour, left_eye_iris, left_config)
        ori_right_eye_contour, ori_right_iris = iris_detector.postprocess(right_eye_contour, right_eye_iris, right_config)
        # plt.imshow(input_image)
        # plt.scatter(ori_left_eye_contour[:, 0], ori_left_eye_contour[:, 1], s=3)
        # plt.scatter(ori_left_iris[:, 0], ori_left_iris[:, 1], s=2)
        # plt.scatter(ori_right_eye_contour[:, 0], ori_right_eye_contour[:, 1], s=3)
        # plt.scatter(ori_right_iris[:, 0], ori_right_iris[:, 1], s=2)
        # plt.show()
        
        left_eye_left = ori_left_iris[left_eye_iris[:, 0].argmax()]
        left_eye_right = ori_left_iris[left_eye_iris[:, 0].argmin()]
        left_eye_pts = np.array([left_eye_left, left_eye_right])
        
        right_eye_left = ori_right_iris[right_eye_iris[:, 0].argmax()]
        right_eye_right = ori_right_iris[right_eye_iris[:, 0].argmin()]
        right_eye_pts = np.array([right_eye_left, right_eye_right])
        
        plt.imshow(input_image)
        plt.scatter(left_eye_pts[:, 0], left_eye_pts[:, 1], s=3)
        plt.scatter(right_eye_pts[:, 0], right_eye_pts[:, 1], s=2)
        plt.show()
        
        
        iris_diameter = np.mean([np.abs(left_eye_right[0] - left_eye_left[0]), np.abs(right_eye_left[0] - right_eye_right[0])])
        
        print("iris_diameter", iris_diameter)
        
        
        # which image for
        # temple-to-temple distance:  2nd image
        # eye-to-eye distance:  3rd image
        # iris diameter: 3rd image
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', '-s', default="", help="Path to the video")
    args = parser.parse_args()

    if args.source is "":
        demo()
    else:
        main(args)
