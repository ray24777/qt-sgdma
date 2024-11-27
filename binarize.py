import os
import cv2
import numpy as np
def binarize_seg (rect_width, rect_height, text, current_output_dir):
    # load the image
    warped_image = cv2.imread(os.path.join(current_output_dir, str('plate.jpg')))

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
            # 
            hex_file.write(str(text[i]))