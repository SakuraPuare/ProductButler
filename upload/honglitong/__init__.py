import asyncio
import os
import pathlib
import sys
import time

import loguru
import pandas as pd
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
from pandas import DataFrame
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

from utils import get_category_level_1, get_category_level_2, glob_file_in_folder
from .apis import (
    add_goods,
    get_captcha_image,
    get_category,
    login,
    test_login,
    upload_file,
)


class Main(QWidget):
    def __init__(self):
        super().__init__()

        self.image_path = None
        self.file_name = None
        self.image_path_button = None
        self.file_name_button = None
        self.image_label = None
        self.excel_label = None
        self.enter_button = None
        self.init_ui()

    def init_ui(self):
        # Create layout
        layout = VBoxLayout(self)

        self.enter_button = PushButton("确定", self)
        self.enter_button.clicked.connect(self.enter)
        # listen to the enter key
        self.enter_button.setAutoDefault(True)

        # Create label to display selected files
        self.excel_label = BodyLabel("未选中excel数据文件", self)
        self.image_label = BodyLabel("未选择图片文件夹", self)

        # Create button for selecting file_name
        self.file_name_button = PushButton("选择excel数据文件", self)
        self.file_name_button.clicked.connect(self.select_excel_file)

        # Create button for selecting image_path
        self.image_path_button = PushButton("选择图片文件夹", self)
        self.image_path_button.clicked.connect(self.select_image_directory)

        # Add widgets to layout
        layout.addWidget(self.file_name_button)
        layout.addWidget(self.image_path_button)
        layout.addWidget(self.excel_label)
        layout.addWidget(self.image_label)

        layout.addWidget(self.enter_button)

        # Set the layout for the window
        self.setLayout(layout)

        # Set the main window properties
        self.setWindowTitle("File Selector")
        self.resize(400, 200)

    def enter(self):
        asyncio.ensure_future(self._enter())

    async def _enter(self):
        if self.excel_label.text() == "未选中excel数据文件":
            InfoBar.error(title="Error", content="请选择excel数据文件", parent=self)
            return
        if self.image_label.text() == "未选择图片文件夹":
            InfoBar.error(title="Error", content="请选择图片文件夹", parent=self)
            return

        # test the validity of the cookies
        try:
            await test_login()
        except Exception as e:
            loguru.logger.error(str(e))
            self.login_form = LoginForm((self.file_name, self.image_path))
            self.close()
            self.login_form.show()
        else:
            self.data_form = DataForm((self.file_name, self.image_path))
            self.close()
            self.data_form.show()

    def select_excel_file(self):
        self.file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel Files (*.xlsx);;All Files (*)",
        )
        if self.file_name:
            self.excel_label.setText(f"已选择Excel文件: {self.file_name}")

    def select_image_directory(self):
        self.image_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if self.image_path:
            self.image_label.setText(f"已选择图片文件夹: {self.image_path}")


class LoginForm(QWidget):
    def __init__(self, path_data):
        super().__init__()
        self.captcha_label = None
        self.captcha_input = None
        self.password_input = None
        self.account_input = None
        self.path_data = path_data

        self.init_ui()

    def init_ui(self):
        # Create layout
        layout = VBoxLayout(self)

        # Create a form layout for user input
        form_layout = QFormLayout()

        # Create input fields for account and password
        self.account_input = LineEdit(self)
        self.account_input.setText("gys8")
        self.account_input.setPlaceholderText("输入账号")

        self.password_input = PasswordLineEdit(self)
        self.password_input.setText("881125")
        self.password_input.setPlaceholderText("输入密码")

        self.captcha_input = LineEdit(self)
        self.captcha_input.setPlaceholderText("输入验证码")

        # Add input fields to the form layout
        form_layout.addRow("账号:", self.account_input)
        form_layout.addRow("密码:", self.password_input)
        form_layout.addRow("验证码:", self.captcha_input)

        # Create a label for displaying the captcha image
        self.captcha_label = BodyLabel(self)
        asyncio.ensure_future(self.load_captcha_image())
        self.captcha_label.mousePressEvent = self.reload

        # Create a login button
        login_button = PushButton("Login", self)
        login_button.clicked.connect(self.login)

        # Add widgets to the main layout
        layout.addLayout(form_layout)
        layout.addWidget(self.captcha_label)
        layout.addWidget(login_button)

        # Set the layout for the window
        self.setLayout(layout)

        # Set the main window properties
        self.setWindowTitle("Login Window")
        self.resize(400, 300)
        # self.setGeometry(300, 300, 400, 300)

    def reload(self, _event):
        asyncio.ensure_future(self.load_captcha_image())

    async def load_captcha_image(self):
        try:
            await get_captcha_image()
        except Exception as e:
            # If the captcha image cannot be loaded, warn the user
            InfoBar.warning(
                parent=self, title="Warning", content=f"验证码加载失败，请重试 {e}"
            )

        pixmap = QPixmap("verify.jpg")
        self.captcha_label.setPixmap(pixmap)
        self.captcha_label.setAlignment(Qt.AlignCenter)

    def login(self):
        asyncio.ensure_future(self._login())

    async def _login(self):
        # Placeholder login function
        account = self.account_input.text()
        password = self.password_input.text()

        try:
            await login(account, password, self.captcha_input.text())
        except Exception as e:
            InfoBar.error(title="Error", content=str(e))
        else:
            InfoBar.success(title="Success", content="登录成功")
            self.data_form = DataForm(self.path_data)
            self.close()
            self.data_form.show()


class DataForm(QWidget):
    def __init__(self, path_data):
        super().__init__()
        self.start_edit = LineEdit()
        self.end_edit = LineEdit()
        self.reset_button = PushButton(text="重置")
        self.load_button = PushButton(text="加载")
        self.jump_button = PushButton(text="跳转到")
        self.jump_edit = LineEdit()
        self.pre_button = PushButton(text="上一条")
        self.next_button = PushButton(text="下一条")
        self.upload_button = PushButton(text="上传")
        self.detail_label = BodyLabel(text="详细信息")
        self.weight_edit = LineEdit()
        self.raw_level_1 = BodyLabel(text="无")
        self.level_1_select = ComboBox()
        self.raw_level_2 = BodyLabel(text="无")
        self.level_2_select = ComboBox()
        self.poster_url_list = ListWidget()
        self.detail_url_list = ListWidget()
        self.table_widget = TableWidget()
        self.current_level_1_name, self.level_1_index = None, None
        self.current_level_2_name, self.level_2_index = None, None
        self.table_data = None
        self.black_list = None
        self.category = None
        self.details = None
        self.posts = None
        self.image_folder = None
        self.level_2_index = None
        self.matched_level_2_name = None
        self.level_1_index = None
        self.matched_level_1_name = None
        self.end = None
        self.start = None
        self.is_upload = False
        self.file_name, self.image_path = path_data

        self.image_folder_list = list(pathlib.Path(self.image_path).iterdir())

        asyncio.ensure_future(self.initialize())

        self.loc = -1

    async def initialize(self):
        await self.init_data()
        self.init_ui()

    def upload(self):
        if self.is_upload:
            InfoBar.error(title="Error", content="正在上传中，请稍等", parent=self)
            return

        asyncio.ensure_future(self._upload())

    async def _upload(self):
        self.is_upload = True
        if (
                not self.image_folder
                or self.loc == -1
                or not self.posts
                or not self.details
        ):
            InfoBar.error(title="Error", content="图片未载入", parent=self)
            return

        ids = self.table_widget.item(0, 0).text()  # 序号
        brand = self.table_widget.item(0, 3).text()  # 品牌
        goods_name = self.table_widget.item(0, 4).text()  # 品名
        bar_code = self.table_widget.item(0, 5).text()  # 条码
        weight = self.weight_edit.text()  # 重量
        bid_price = self.table_widget.item(0, 7).text()  # 对广行达结算价
        market_price = self.table_widget.item(0, 8).text()  # 含税运一件代发价

        matched = (
            self.matched_level_1_name != self.current_level_1_name,
            self.matched_level_2_name != self.current_level_2_name,
        )
        if any(matched):
            raw_level_1 = self.raw_level_1.text()
            raw_level_2 = self.raw_level_2.text()
            dialog = Dialog(
                "你修改了分类信息",
                "你修改了分类信息，是否要以此修改后续所有的内容？\n\n"
                + f"   '{raw_level_1}' -> '{self.current_level_1_name}' \n"
                + f"   '{raw_level_2}' -> '{self.current_level_2_name}' ",
                parent=self,
            )

            if dialog.exec() == Dialog.Accepted:
                if all(matched):
                    self.table_data.loc[
                        (self.table_data["一级分类"] == raw_level_1)
                        & (self.table_data["二级分类"] == raw_level_2),
                        "一级分类",
                    ] = self.current_level_1_name
                    self.table_data.loc[
                        (self.table_data["一级分类"] == self.current_level_1_name)
                        & (self.table_data["二级分类"] == raw_level_2),
                        "二级分类",
                    ] = self.current_level_2_name
                else:
                    if matched[0]:
                        self.table_data.loc[
                            (self.table_data["一级分类"] == raw_level_1)
                            & (self.table_data["二级分类"] == raw_level_2),
                            "一级分类",
                        ] = self.current_level_1_name
                    if matched[1]:
                        self.table_data.loc[
                            (self.table_data["一级分类"] == raw_level_1)
                            & (self.table_data["二级分类"] == raw_level_2),
                            "二级分类",
                        ] = self.current_level_2_name

        InfoBar.info(title="上传中", content="请稍等", parent=self)

        try:
            posts_url = await asyncio.gather(
                *[upload_file("title", i) for i in self.posts]
            )
            details_url = await asyncio.gather(
                *[upload_file("detail", i) for i in self.details]
            )

            resp = await add_goods(
                poster_url=posts_url,
                detail_url=details_url,
                brand=brand,
                goods_name=goods_name,
                market_price=market_price,
                bid_price=bid_price,
                weight=weight,
                level_1=self.level_1_index,
                level_2=self.level_2_index,
                bar_code=bar_code,
            )

            assert resp.get("success"), resp.get("msg")

        except Exception as e:
            InfoBar.error(title="Error", content=str(e), parent=self)
            loguru.logger.error(f"[{ids}] {str(e)}")
            return
        else:
            self.nxt()
            loguru.logger.info(f"[{ids}] success")
        finally:
            with open("black_list.txt", "a+", encoding='u8') as f:
                f.write(f"{ids}\n")
            self.is_upload = False

    def reset(self):
        asyncio.ensure_future(self._reset())

    async def _reset(self):
        self.is_upload = False
        self.image_folder_list = list(pathlib.Path(self.image_path).iterdir())

        await self.init_data()
        self.load()

    def load(self):
        self.start = self.start_edit.text()
        self.end = self.end_edit.text()
        if not self.start or not self.end:
            InfoBar.error(
                title="Error", content="请输入开始序号和结束序号", parent=self
            )
            return
        if not self.start.isdigit() or not self.end.isdigit():
            InfoBar.error(title="Error", content="请输入数字", parent=self)
            return

        self.start = int(self.start)
        self.end = int(self.end)

        if self.start > self.end:
            InfoBar.error(title="Error", content="开始序号大于结束序号", parent=self)
            return

        # find the data that id = start
        self.jmp(self.start)

    def update_ui(self):
        self.detail_label.setText(f"详细信息: 已载入{len(self.table_data)}条数据")

        # get the line
        row = self.table_data.loc[self.loc]

        # update label
        self.raw_level_1.setText(row["一级分类"])
        self.raw_level_2.setText(row["二级分类"])

        # match the category
        self.matched_level_1_name, self.level_1_index = get_category_level_1(
            self.category, row["一级分类"]
        )
        self.matched_level_2_name, self.level_2_index = get_category_level_2(
            self.category, self.matched_level_1_name, row["二级分类"]
        )
        # update combobox
        self.level_1_select.setCurrentText(self.matched_level_1_name)
        self.level_2_select.setCurrentText(self.matched_level_2_name)

        # update table
        self.table_widget.setItem(0, 0, QTableWidgetItem(str(row["序号"])))
        self.table_widget.setItem(0, 1, QTableWidgetItem(str(row["一级分类"])))
        self.table_widget.setItem(0, 2, QTableWidgetItem(str(row["二级分类"])))
        self.table_widget.setItem(0, 3, QTableWidgetItem(str(row["品牌"])))
        self.table_widget.setItem(0, 4, QTableWidgetItem(str(row["品名"])))
        self.table_widget.setItem(0, 5, QTableWidgetItem(str(row["条码"])))
        self.table_widget.setItem(0, 6, QTableWidgetItem(str(row["规格"])))
        self.table_widget.setItem(0, 7, QTableWidgetItem(str(row["对广行达结算价"])))
        self.table_widget.setItem(0, 8, QTableWidgetItem(str(row["含税运一件代发价"])))
        self.table_widget.resizeColumnsToContents()

        # update image
        self.update_image_path_list()

        # do some check
        if str(row["对广行达结算价"]) == "nan":
            InfoBar.error(title="Error", content="结算价不能为空", parent=self)
            return
        if str(row["含税运一件代发价"]) == "nan":
            InfoBar.error(title="Error", content="代发价不能为空", parent=self)
            return

    def update_image_path_list(self):
        self.poster_url_list.clear()
        self.detail_url_list.clear()

        idx = self.table_data.loc[self.loc]["序号"]
        self.image_folder = [
            i for i in self.image_folder_list if i.name.startswith(str(idx))
        ]

        if not self.image_folder:
            InfoBar.error(title="Error", content="未找到图片文件夹", parent=self)
            return

        self.image_folder = self.image_folder[-1]

        start_time = time.time()
        self.posts, self.details = glob_file_in_folder(self.image_folder)
        loguru.logger.info(f"glob_file_in_folder cost {
        time.time() - start_time:.2f}s")

        for i in self.posts:
            i = str(i)
            item_name = i[i.find(str(int(idx))) + len(str(idx)):]
            self.poster_url_list.addItem(item_name)
            # self.poster_url_list.addItem(str(i).split(str(int(idx)))[-1])

        for i in self.details:
            i = str(i)
            item_name = i[i.find(str(int(idx))) + len(str(idx)):]
            self.detail_url_list.addItem(item_name)
            # self.detail_url_list.addItem(str(i).split(str(int(idx)))[-1])

        pass

    @staticmethod
    def read_table_data(file_name) -> DataFrame:
        df = pd.read_excel(file_name, header=3)
        # 重新设置列名
        df.columns = [
            "序号",
            "责任人",
            "一级分类",
            "二级分类",
            "品牌",
            "品名",
            "条码",
            "规格",
            "品牌标价",
            "淘宝",
            "链接",
            "京东",
            "链接",
            "其他平台",
            "链接",
            "对广行达结算价",
            "税率",
            "含税运一件代发价",
            "上线建议",
            "供应商公司名称",
        ]
        # "序号""一级分类", "二级分类", "品牌", "品名""对广行达结算价" "含税运一件代发价", "上线建议"
        data = df[
            [
                "序号",
                "一级分类",
                "二级分类",
                "品牌",
                "品名",
                "条码",
                "规格",
                "对广行达结算价",
                "含税运一件代发价",
                "上线建议",
            ]
        ]
        data = data.loc[data["上线建议"] != "无需上线"]

        # 重新设置索引
        data.index = range(len(data))

        return data

    async def init_data(self):
        # flush category
        self.category = await get_category()

        if not os.path.exists("black_list.txt"):
            with open("black_list.txt", "w", encoding='u8') as f:
                f.write("")

        with open("black_list.txt", "r", encoding='u8') as f:
            self.black_list: list[int] = list(map(int, f.readlines()))

        # with open("category.json", "r", encoding='u8') as f:
        #     category = json.load(f)

        self.table_data = self.read_table_data(self.file_name)

        pass

    def init_ui(self):
        # Create layout

        layout = VBoxLayout(self)

        # Header horizontal layout
        header_layout = QHBoxLayout()

        self.start_edit.setPlaceholderText("开始序号")
        self.end_edit.setPlaceholderText("结束序号")

        self.reset_button.clicked.connect(self.reset)
        self.load_button.clicked.connect(self.load)

        self.jump_edit.setPlaceholderText("跳转到")
        self.jump_button.clicked.connect(
            lambda: self.jmp(self.jump_edit.text()))

        self.pre_button.clicked.connect(self.pre)
        self.next_button.clicked.connect(self.nxt)

        self.upload_button.clicked.connect(self.upload)

        header_layout.addWidget(self.reset_button)
        header_layout.addWidget(self.load_button)
        header_layout.addWidget(self.upload_button)
        header_layout.addWidget(self.start_edit)
        header_layout.addWidget(self.end_edit)
        header_layout.addWidget(self.jump_button)
        header_layout.addWidget(self.jump_edit)
        header_layout.addWidget(self.pre_button)
        header_layout.addWidget(self.next_button)

        body_layout = VBoxLayout(self)

        info_layout = VBoxLayout(self)

        category_layout = VBoxLayout(self)
        category_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.detail_label.setMaximumHeight(20)
        category_layout.addWidget(self.detail_label)

        weight_layout = QHBoxLayout()
        self.weight_edit.setText("1")

        self.weight_edit.setMaximumWidth(100)
        weight_layout.addWidget(BodyLabel(text="重量"))
        weight_layout.addWidget(self.weight_edit)
        category_layout.addLayout(weight_layout)

        level_1_layout = QHBoxLayout()

        self.level_1_select.currentTextChanged.connect(
            self.level_1_select_change)
        self.raw_level_1.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        level_1_layout.addWidget(BodyLabel(text="一级分类"))
        level_1_layout.addWidget(self.raw_level_1)
        level_1_layout.addWidget(self.level_1_select)

        level_2_layout = QHBoxLayout()
        self.level_2_select.currentTextChanged.connect(
            self.level_2_select_change)
        self.raw_level_2.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # update category to combobox
        for i in self.category.keys():
            self.level_1_select.addItem(i)

        level_2_layout.addWidget(BodyLabel(text="二级分类"))
        level_2_layout.addWidget(self.raw_level_2)
        level_2_layout.addWidget(self.level_2_select)

        category_layout.addLayout(level_1_layout)
        category_layout.addLayout(level_2_layout)

        image_info_layout = VBoxLayout(self)
        image_info_layout.addWidget(BodyLabel(text="图片信息"))

        url_info_label_layout = QHBoxLayout()
        url_info_label_layout.addWidget(BodyLabel(text="主图"))
        url_info_label_layout.addWidget(BodyLabel(text="详情图"))

        url_info_layout = QHBoxLayout()
        self.poster_url_list.setMinimumHeight(300)
        self.detail_url_list.setMinimumHeight(300)

        url_info_layout.addWidget(self.poster_url_list)
        url_info_layout.addWidget(self.detail_url_list)

        image_info_layout.addLayout(url_info_label_layout)
        image_info_layout.addLayout(url_info_layout)

        info_layout.addLayout(category_layout)
        info_layout.addLayout(image_info_layout)

        body_layout.addLayout(info_layout)

        table_layout = VBoxLayout(self)
        data_label = BodyLabel(text="数据信息")
        data_label.setMaximumHeight(20)
        table_layout.addWidget(data_label)

        # Create a table widget

        # Set the table headers
        headers = [
            "序号",
            "一级分类",
            "二级分类",
            "品牌",
            "品名",
            "条码",
            "规格",
            "结算价",
            "代发价",
        ]

        self.table_widget.setMaximumHeight(100)
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(len(headers))

        self.table_widget.setHorizontalHeaderLabels(headers)

        # Set the table column width
        width_list = [50, 80, 80, 150, 350, 150, 220, 100, 100]
        for i, width in enumerate(width_list):
            self.table_widget.setColumnWidth(i, width)

        # Add the table to the layout
        table_layout.addWidget(self.table_widget)

        body_layout.addLayout(table_layout)

        # init layout
        layout.addLayout(header_layout)
        layout.addLayout(body_layout)

        # Set layout to the widget
        self.setLayout(layout)
        self.resize(1200, 800)

    def level_1_select_change(self):
        level_1_name = self.level_1_select.currentText()

        self.level_2_select.clear()
        for i in self.category[level_1_name]["children"]:
            self.level_2_select.addItem(i)

        self.current_level_1_name, self.level_1_index = get_category_level_1(
            self.category, level_1_name
        )

    def level_2_select_change(self):
        level_1_name = self.level_1_select.currentText()
        level_2_name = self.level_2_select.currentText()
        self.current_level_2_name, self.level_2_index = get_category_level_2(
            self.category, level_1_name, level_2_name
        )

    def pre(self):
        if self.loc == -1:
            return

        if self.loc - 1 < 0:
            InfoBar.error(title="Error", content="已经是第一条数据", parent=self)
            return

        self.loc -= 1
        self.update_ui()

        InfoBar.info(title="Success", content="已经切换到上一条数据", parent=self)
        loguru.logger.info(f"当前序号: {self.table_data.loc[self.loc]['序号']}")

    def nxt(self):
        if self.loc == -1:
            return

        if self.loc + 1 >= len(self.table_data):
            InfoBar.error(title="Error", content="已经是最后一条数据", parent=self)
            loguru.logger.info("已经是最后一条数据")
            return

        self.loc += 1
        self.update_ui()

        InfoBar.info(title="Success", content="已经切换到下一条数据", parent=self)
        loguru.logger.info(f"当前序号: {self.table_data.loc[self.loc]['序号']}")

    def jmp(self, idx):
        if isinstance(idx, str):
            if not idx.isdigit():
                InfoBar.error(title="Error", content="请输入数字", parent=self)
                return
            idx = int(idx)

        self.loc = self.table_data[self.table_data["序号"] == idx]
        if self.loc.empty:
            InfoBar.error(title="Error", content="未找到数据", parent=self)
            return
        self.loc = self.loc.index[0]

        self.update_ui()

        InfoBar.info(title="Success", content="已经切换到指定数据", parent=self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    ex = Main()
    ex.show()

    with loop:
        loop.run_forever()
