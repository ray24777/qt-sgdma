import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.image_files = []
        self.current_image_index = 0

    def initUI(self):
        self.setWindowTitle('图像浏览器')

        # 创建布局
        self.layout = QVBoxLayout()

        # 显示图像的标签
        self.image_label = QLabel('没有图像')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_label)

        # 上一张、下一张按钮
        self.button_layout = QHBoxLayout()

        self.prev_button = QPushButton('上一张')
        self.prev_button.clicked.connect(self.show_prev_image)
        self.button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton('下一张')
        self.next_button.clicked.connect(self.show_next_image)
        self.button_layout.addWidget(self.next_button)

        self.layout.addLayout(self.button_layout)

        # 打开文件夹按钮
        self.open_button = QPushButton('打开文件夹')
        self.open_button.clicked.connect(self.open_folder)
        self.layout.addWidget(self.open_button)

        self.setLayout(self.layout)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder_path:
            # 获取文件夹中的所有 JPG 文件
            self.image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                                if f.lower().endswith('.jpg')]
            if self.image_files:
                self.current_image_index = 0
                self.show_image()
            else:
                self.image_label.setText('文件夹中没有 JPG 图像。')

    def show_image(self):
        image_path = self.image_files[self.current_image_index]
        pixmap = QPixmap(image_path)
        # 调整图像大小以适应标签
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))

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
    viewer.resize(800, 600)
    viewer.show()
    sys.exit(app.exec_())
