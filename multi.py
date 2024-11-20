import asyncio
import os
import pathlib
import sys
import time

import loguru
import pandas as pd
from pandas import DataFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QTableWidgetItem,
    QWidget,
)
from qasync import QEventLoop
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    Dialog,
    InfoBar,
    LineEdit,
    ListWidget,
    PasswordLineEdit,
    PushButton,
    TableWidget,
    VBoxLayout,
)

from upload import PLATFORMS


class StartWindow(QWidget):
    def __init__(self):
        super(StartWindow, self).__init__()

        self.setWindowTitle("选择平台")
        self.resize(400, 200)

        self.initUI()

    def initUI(self):
        layout = VBoxLayout(self)

        self.label = BodyLabel("请选择要对接的平台:")
        layout.addWidget(self.label)

        platforms = PLATFORMS.keys()

        # 创建下拉框
        self.platform_combo = ComboBox()
        self.platform_combo.addItems(platforms)
        layout.addWidget(self.platform_combo)

        # 创建开始按钮
        self.start_button = PushButton("开始")
        self.start_button.clicked.connect(self.start_upload)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def start_upload(self):
        selected_platform = self.platform_combo.currentText()
        if selected_platform:
            platform_info = PLATFORMS.get(selected_platform)
            if platform_info:
                # 创建对应平台的实例
                platform_instance = platform_info()  # 这里可能传入参数，视需要而定

                self.close()
                self.new_window = platform_instance
                self.new_window.show()
            else:
                InfoBar.warning(self, "警告", "该平台未定义!")
        else:
            InfoBar.warning(self, "警告", "请先选择一个平台!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    ex = StartWindow()
    ex.show()

    with loop:
        loop.run_forever()
