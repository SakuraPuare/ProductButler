import asyncio
import importlib
import sys

from PySide6.QtWidgets import QApplication, QWidget
from qasync import QEventLoop
from qfluentwidgets import BodyLabel, ComboBox, InfoBar, PushButton, VBoxLayout

from upload import PLATFORMS


class StartWindow(QWidget):
    def __init__(self):
        super(StartWindow, self).__init__()

        self.label = None
        self.platform_combo = None
        self.start_button = None
        self.new_window = None
        self.setWindowTitle("选择平台")
        self.resize(400, 200)

        self.init_ui()

    def init_ui(self):
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
                # importlib
                module = importlib.import_module(platform_info + '.gui')

                self.close()
                self.new_window = module.Main()
                self.new_window.show()
            else:
                InfoBar.warning(self, "警告", "该平台未定义!")
        else:
            InfoBar.warning(self, "警告", "请先选择一个平台!")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        ex = StartWindow()
        ex.show()

        with loop:
            loop.run_forever()
    except KeyboardInterrupt:
        exit(0)
