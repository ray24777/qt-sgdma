import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog,
                             QHBoxLayout, QTextEdit, QSizePolicy)
from PyQt5.QtGui import QPixmap, QTextCursor, QImage
from PyQt5.QtCore import Qt

import cv2
import os
import glob
import tempfile
import numpy as np
import shutil
from agentclpr import CLPSystem

from detect import detect

from pers import perspective_transform

from binarize import binarize_seg


# 自定义类，用于将标准输出重定向到 QTextEdit
class EmittingStream(object):
    def __init__(self, text_edit):
        self.text_edit = text_edit

    def write(self, text):
        # 将文本追加到 QTextEdit
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.insertPlainText(text)
        self.text_edit.moveCursor(QTextCursor.End)

    def flush(self):
        pass

class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_image_index = 0
        self.quad_pts = []
        self.detected_text = ''
        self.score=0
        self.rect_width = 440
        self.rect_height = 140
        self.folder_path = 'input'
        self.cache_path = 'cache'
        self.image_files = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path)
                                if f.lower().endswith('.jpg')]
        if self.image_files:
            self.current_image_index = 0
            self.show_image()
            
        #clean cache and create new cache
        shutil.rmtree(self.cache_path, ignore_errors=True)
        os.makedirs(self.cache_path)

    def initUI(self):
        self.setWindowTitle('DMA’s Frontend')

        # 创建主布局为水平布局
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        # 左侧布局（原有组件）
        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)

        # 右侧布局（空按钮）
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_layout)

        # 显示图像的标签
        self.image_label = QLabel('DMA 2024')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_layout.addWidget(self.image_label)

        # 上一张、下一张按钮布局
        self.button_layout = QHBoxLayout()

        self.prev_button = QPushButton('上一张')
        self.prev_button.clicked.connect(self.show_prev_image)
        self.button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton('下一张')
        self.next_button.clicked.connect(self.show_next_image)
        self.button_layout.addWidget(self.next_button)

        self.left_layout.addLayout(self.button_layout)

        # 打开文件夹按钮
        self.open_button = QPushButton('打开文件夹')
        self.open_button.clicked.connect(self.open_folder)
        self.left_layout.addWidget(self.open_button)

        # 日志窗口
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 设置日志窗口的高度，只显示5行文本
        font_metrics = self.log_text.fontMetrics()
        line_height = font_metrics.lineSpacing()
        number_of_lines = 5
        self.log_text.setFixedHeight(line_height * number_of_lines + 10)  # +10用于一些内边距

        self.left_layout.addWidget(self.log_text)

        # 将标准输出重定向到日志窗口
        sys.stdout = EmittingStream(self.log_text)

        # 在右侧添加一列按钮
        text_on_right = ['识别车牌',                '透视变换',         '二值化与切分',           'PCIe发送',         '一键执行全部']
        defs_on_right = [self.detect_plate, self.perspective_transform, self.binarize_segmentation, self.pcie, self.one_click]
        #defs_on_right = [self.detect_plate, self.perspective_transform, self.binarize, self.character_segmentation, self.pcie_send]
        for i in range(len(text_on_right)):
            button = QPushButton(text_on_right[i])
            button.clicked.connect(defs_on_right[i])
            self.right_layout.addWidget(button)

        # 添加一个伸展，以将按钮靠上排列
        self.right_layout.addStretch()


    def detect_plate(self):
        print('识别车牌')
        # 调用 detect 函数
        self.quad_pts, self.detected_text, self.score, image_with_plate = detect(self.image_files[self.current_image_index])
        # 显示image_with_plate
        cv2.imwrite(os.path.join(self.cache_path, str('origin.jpg')), image_with_plate)
        pixmap = QPixmap(os.path.join(self.cache_path, str('origin.jpg')))
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def perspective_transform(self):
        print('透视变换')
        # 调用 perspective_transform 函数
        warped_image=perspective_transform(self.image_files[self.current_image_index],
                              self.quad_pts,
                              self.rect_width,
                              self.rect_height)
        cv2.imwrite(os.path.join(self.cache_path, str('plate.jpg')), warped_image)
        pixmap = QPixmap(os.path.join(self.cache_path, str('plate.jpg')))
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def binarize_segmentation(self):
        print('二值化与切分')
        # 调用 binarize_seg 函数
        binarize_seg(self.rect_width, 
                     self.rect_height, 
                     self.detected_text,
                     self.cache_path)
        
        # 显示切分后的字符-拼接5张图
        image = np.zeros((200, 1200, 3), dtype=np.uint8)
        for i in range(5):
            digit = cv2.imread(os.path.join(self.cache_path, str('plate_') + str(i+1) + '.jpg'))
            digit_resized = cv2.resize(digit, (240, 200))
            image[:, i*240:(i+1)*240] = digit_resized
        cv2.imwrite(os.path.join(self.cache_path, str('all-digits.jpg')), image)
        pixmap = QPixmap(os.path.join(self.cache_path, str('all-digits.jpg')))
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        

    def pcie(self):
        print('PCIe发送')
        # 调用 PCIe 发送函数
        # 读取5张字符图
        for i in range(5):
            with open(os.path.join(self.cache_path, str(i+1) + '.hex'), 'r') as hex_file:
                hex_values = hex_file.read()
                print(f"{hex_values}\n")
        while len(self.detected_text) > 5:
            self.detected_text = self.detected_text[1:]
        print('识别到的车牌号码为：', self.detected_text)

    def one_click(self):
        self.detect_plate()
        self.perspective_transform()
        self.binarize_segmentation()
        self.pcie()

    def open_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if self.folder_path:
            print(f"选择的文件夹: {self.folder_path}")
            # 获取文件夹中的所有 JPG 文件
            self.image_files = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path)
                                if f.lower().endswith('.jpg')]
            if self.image_files:
                self.current_image_index = 0
                print(f"找到 {len(self.image_files)} 张图像。")
                self.show_image()
            else:
                self.image_label.setText('文件夹中没有 JPG 图像。')
                print("文件夹中没有 JPG 图像。")

    def show_image(self):
        image_path = self.image_files[self.current_image_index]
        pixmap = QPixmap(image_path)
        # 调整图像大小以适应标签
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        print(f"显示图像: {image_path}")

    def resizeEvent(self, event):
        # 当窗口大小变化时，更新图像显示
        if self.image_files:
            self.show_image()
        super().resizeEvent(event)

    def show_next_image(self):
        if self.image_files:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.show_image()

    def show_prev_image(self):
        if self.image_files:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
            self.show_image()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.resize(1080, 724)
    viewer.show()
    sys.exit(app.exec_())
