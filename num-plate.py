import cv2
import os
import glob
import tempfile
import numpy as np
from skimage.measure import shannon_entropy
from PIL import ImageFont, ImageDraw, Image
from matplotlib import pyplot as plt
import shutil
from agentclpr import CLPSystem
classifier = CLPSystem()

input_dir = 'input'

output_dir = 'plate-output'

# 定义目标矩形的顶点
rect_width = 440
rect_height = 140

#切割数字时第一位的初始位置
first_digit_x = 128

#切割数字时最后位的初始位置
last_digit_x = rect_width - 8

#切割数字时的宽度
digit_width = (last_digit_x - first_digit_x)  // 5

#切割数字时的高度
digit_height = 100
lower_margin = (rect_height - digit_height) // 2
upper_margin = rect_height - digit_height - lower_margin

#clean the output directory
if os.path.exists(output_dir):
    #Dangerous operation, be careful
    shutil.rmtree(output_dir)

# mkdir if not exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

#遍历input文件夹下的所有图片
image_paths = glob.glob(os.path.join(input_dir, '*.jpg'))

image_paths = [os.path.basename(image_path) for image_path in image_paths]

total_count = len(image_paths)
err_count = 0

character_count = 0
for files in image_paths:
    print("\nWorking on "+ files+ "...")
    
    input_image = cv2.imread(os.path.join(input_dir, files))
    output = classifier(input_image)
    if output== None or len(output) == 0:
        print("[ERROR]: No plate detected")
        err_count += 1
        continue

    if len(output) > 1:
        # find the plate with the highest recognition score
        scores = [output[i][1][1] for i in range(len(output))]
        index = scores.index(max(scores))
        output = [output[index]]

    [[quad_pts , [text, rec_score]]] = output

    if text == None or len (text) <5:
        print("[ERROR]: No text detected")
        err_count += 1
        continue

    print("Location of the plate: " + str(quad_pts ))
    print("Text on the plate: " + text)
    print("Recognition score: " + str(rec_score))


    # cut the plate from the image based on the points
    quad_pts = np.array(quad_pts, dtype=np.float32).reshape(4, 2)

    rect_pts = np.array([
        [rect_width - 1, rect_height - 1], 
        [0, rect_height - 1],      
        [0, 0],                   
        [rect_width - 1, 0]       
    ], dtype=np.float32)


    # 计算透视变换矩阵
    M = cv2.getPerspectiveTransform(quad_pts, rect_pts)

    # 应用透视变换
    warped_image = cv2.warpPerspective(input_image, M, (rect_width, rect_height))


    # 保存结果
    current_output_dir = os.path.join(output_dir, files)
    # draw the region of interest based on the points
    image_with_plate = cv2.polylines(input_image, [quad_pts.astype(np.int32)], True, (0, 255, 0), 2)
    
    os.makedirs(current_output_dir, exist_ok=True)
    cv2.imwrite(os.path.join(current_output_dir, str('origin.jpg')), image_with_plate)
    cv2.imwrite(os.path.join(current_output_dir, str('plate.jpg')), warped_image)
    # grey scale
    warped_image = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)
    # binarize
    _, warped_image = cv2.threshold(warped_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    while len(text) > 5:
        text = text[1:]
    

    for i in range(5):
        # crop the digit
        digit = warped_image[lower_margin:rect_height - upper_margin, 
                             first_digit_x + i * digit_width: first_digit_x + (i + 1) * digit_width]
        cv2.imwrite(os.path.join(current_output_dir, str('plate_') + str(i+1) + '.jpg'), digit)
        # 保存为hex，有问题
        # resize to 24x50
        height, width = 50, 24
        digit = cv2.resize(digit, (width, height), interpolation=cv2.INTER_NEAREST)
        


        # save as hex
        pixels = list(digit.flatten())

        for j in range(len(pixels)):
            if pixels[j] != 0:
                pixels[j] = 1

        with open(os.path.join(current_output_dir, str(i+1) + '.hex'), 'w') as  hex_file:
            for y in range(height):
                hex_values = []
                for x in range(0, width, 4):  # 每4个像素处理一次
                    # 取4个像素值
                    group = pixels[y * width + x:y * width + x + 4]
                    # 计算该组的16进制值
                    hex_value = sum(val << (3 - i) for i, val in enumerate(group))  # 计算每4个的十六进制值
                    hex_values.append(f"{hex_value:X}")  # 转换为十六进制字符串

                # 写入文件，每行6个十六进制数
                hex_file.write("".join(hex_values) + "\n")
            # what is this for?
            hex_file.write(str(text[i]))
    # save the text

    with open(os.path.join(current_output_dir, 'recognized.txt'), 'w') as f:
        f.write(text)
    

print("\nAll done!")
print("Total images: " + str(total_count))
print("Error count: " + str(err_count))
print("Success rate: " + str((total_count - err_count) / total_count * 100) + "%")



#  旋转框在FPGA上的实现
# 进一步优化切分
# 硬件代码优化
# 优选数据集