import cv2
import numpy as np

def perspective_transform(input_image_path, quad_pts, rect_width, rect_height):
    input_image = cv2.imread(input_image_path)

    rect_pts = np.array([
        [rect_width - 1, rect_height - 1], 
        [0, rect_height - 1],      
        [0, 0],                   
        [rect_width - 1, 0]       
    ], dtype=np.float32)


    # 计算透视变换矩阵
    matrix = cv2.getPerspectiveTransform(quad_pts, rect_pts)

    # 应用透视变换
    warped_image = cv2.warpPerspective(input_image, matrix, (rect_width, rect_height))
    
    return warped_image
