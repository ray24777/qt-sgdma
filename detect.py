from agentclpr import CLPSystem
import cv2
import numpy as np

def detect (files):

    print("\nWorking on "+ files+ "...")
    classifier = CLPSystem()
    input_image = cv2.imread(files)
    output = classifier(input_image)
    if output== None or len(output) == 0:
        print("[ERROR]: No plate detected")

    if len(output) > 1:
        # find the plate with the highest recognition score
        scores = [output[i][1][1] for i in range(len(output))]
        index = scores.index(max(scores))
        output = [output[index]]

    [[quad_pts , [text, rec_score]]] = output

    if text == None or len (text) <5:
        print("[ERROR]: No text detected")

    # print("Location of the plate: " + str(quad_pts ))
    # print("Text on the plate: " + text)
    # print("Recognition score: " + str(rec_score))
    print("识别车牌完成")
    quad_pts = np.array(quad_pts, dtype=np.float32).reshape(4, 2)
    image_with_plate = cv2.polylines(input_image, [quad_pts.astype(np.int32)], True, (0, 255, 0), 2)

    return quad_pts, text, rec_score, image_with_plate