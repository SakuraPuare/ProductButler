import asyncio
import pathlib
import sys
import time

import loguru
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QTableWidgetItem,
    QWidget,
    QDialog,
)
from pandas import DataFrame
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    InfoBar,
    LineEdit,
    ListWidget,
    PushButton,
    TableWidget,
    VBoxLayout,
    ScrollArea,
    CheckBox,
    SubtitleLabel,
    HorizontalSeparator,
    FlowLayout
)

from files import managed_exists, managed_open
from utils import find_closest_string, glob_file_in_folder
from .apis import (
    add_vip_goods,
    create,
    get_category,
    get_goods_detail,
    get_vip_goods_list,
    login,
    set_vip_price,
)
from .cos import upload_file
from .utils import get_keyword_category, get_price_category


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

        await login()

        self.data_form = DataForm((self.file_name, self.image_path))
        self.close()
        self.data_form.show()

    def select_excel_file(self):
        self.file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel Files (*.xls,*.xlsx);All Files (*)",
        )
        if self.file_name:
            self.excel_label.setText(f"已选择Excel文件: {self.file_name}")

    def select_image_directory(self):
        self.image_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if self.image_path:
            self.image_label.setText(f"已选择图片文件夹: {self.image_path}")


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

        self.table_data = None
        self.black_list = None
        self.category = None
        self.details = None
        self.posts = None
        self.image_folder = None

        self.end = None
        self.start = None
        self.is_upload = False
        self.file_name, self.image_path = path_data

        self.category_widget = None

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
        self.is_upload = False
        if (
                not self.image_folder
                or self.loc == -1
                or not self.posts
                or not self.details
        ):
            InfoBar.error(title="Error", content="图片未载入", parent=self)
            return

        data = [self.table_widget.item(0, i).text()
                for i in range(self.table_widget.columnCount())]
        # 含税代发价	市场价	职友团平台价	普通会员价格	高级会员价	VIP会员价	至尊VIP会员价
        # 26.50 	39.8 	39.8	35.8 	32.5 	29.8 	28.6
        ids, category_1, category_2, brand, goods_name, bar_code, cost_price, market_price, counter_price, _, _, _, _ = data

        weight = self.weight_edit.text()

        InfoBar.info(title="上传中", content="请稍等", parent=self)

        try:
            # if True:
            posts_url = await asyncio.gather(
                *[upload_file(i) for i in list(self.posts)[:10]]
            )
            details_url = await asyncio.gather(
                *[upload_file(i) for i in self.details]
            )
            # "市场价","含税代发价","平台价"
            create_response = await create(
                posts_url,
                self.selected_category,
                counter_price,
                market_price,
                cost_price,
                details_url,
                goods_name,
                bar_code,
                weight
            )

            none_vip_goods_list = []
            page = 1
            size = 10
            while True:
                none_vip_goods_list.extend(await get_vip_goods_list(page=page, size=size))
                if len(none_vip_goods_list) % size != 0 or not none_vip_goods_list:
                    break
                page += 1

            await asyncio.gather(
                *[add_vip_goods(i.get('Id')) for i in none_vip_goods_list if i.get('Id', None)]
            )

            goods_details = []

            flag = True
            page = 1
            size = 100
            while flag:
                vip_goods_list = await get_vip_goods_list(page=page, size=size, status=True)
                for i in vip_goods_list:
                    detail = await get_goods_detail(i.get('Id'))
                    price = [detail.get('products', [])[0].get(
                        f'vip{j}Price', None) for j in range(1, 5)]
                    if not all(price):
                        goods_details.append(detail)
                    else:
                        flag = False
                        break
                page += 1

            index_of_goods_detail = []
            for i in goods_details:
                name = i.get('goods', {}).get('name', '')
                if not self.table_data[self.table_data["商品名称"].str.contains(name, regex=False)].empty:
                    index_of_goods_detail.append(
                        self.table_data[self.table_data["商品名称"].str.contains(
                            name, regex=False)].index[0]
                    )

            tasks = []
            for index, detail in zip(index_of_goods_detail, goods_details):
                for product in detail.get('products', []):
                    tasks.append(
                        set_vip_price(
                            product.get('id'),
                            *list(self.table_data.loc[index][[
                                "普通会员价格",
                                "高级会员价",
                                "VIP会员价",
                                "至尊VIP会员价",
                            ]])
                        )
                    )
            await asyncio.gather(*tasks)

        except Exception as e:
            InfoBar.error(title="Error", content=str(e), parent=self)
            loguru.logger.error(f"[{ids}] {str(e)}")
            return
        else:
            self.nxt()
            loguru.logger.info(f"[{ids}] success")
        finally:
            with managed_open("black_list.txt", "a+", encoding='u8') as f:
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

    def show_category(self):
        # Create and show the category selection dialog
        self.category_dialog = CategoryDialog(self.category, self.selected_category)
        if self.category_dialog.exec():
            # Update selected categories when dialog is accepted
            self.selected_category = self.category_dialog.get_selected_categories()
            self.update_category()

    def update_ui(self):
        self.detail_label.setText(f"详细信息: 已载入{len(self.table_data)}条数据")

        # get the line
        row = self.table_data.loc[self.loc]

        temp_cat = get_price_category(
            self.category, float(row["职友团平台价"]))
        temp_cat.extend(get_price_category(
            self.category, float(row["市场价"])))
        temp_cat.extend(
            get_keyword_category(self.category, row["品牌"]))
        temp_cat.extend(
            get_keyword_category(self.category, row["商品名称"]))
        temp_cat.extend(
            get_keyword_category(self.category, row["二级分类"]))

        # 去重，使用字典的level字段作为唯一标识
        self.selected_category = list({cat['level']: cat for cat in temp_cat}.values())

        self.update_category()

        # update table
        for i, header in enumerate(valid_headers):
            self.table_widget.setItem(
                0, i, QTableWidgetItem(str(row[header]).strip()))

        self.table_widget.resizeColumnsToContents()

        # update image
        self.update_image_path_list()

    def update_category(self):
        # update category
        self.category_label.setText(
            ', '.join([i['name'] for i in self.selected_category]))

    def update_image_path_list(self):
        self.poster_url_list.clear()
        self.detail_url_list.clear()

        idx = self.table_data.loc[self.loc]["序号"]
        goods_name = self.table_data.loc[self.loc]["商品名称"]
        self.image_folder = [
            i for i in self.image_folder_list if i.name.startswith(str(idx))
        ]

        if not self.image_folder:
            InfoBar.error(title="Error", content="未找到图片文件夹", parent=self)
            return

        # self.image_folder = self.image_folder[-1]
        # find the closest folder
        self.image_folder = self.image_folder[
            find_closest_string(goods_name, [i.name for i in self.image_folder])
        ]

        start_time = time.time()
        self.posts, self.details = glob_file_in_folder(self.image_folder)
        loguru.logger.info(f"glob_file_in_folder cost {
        time.time() - start_time:.2f}s")

        for i in self.posts:
            i = str(i)
            item_name = i[i.find(str(int(idx))) + len(str(idx)):]
            self.poster_url_list.addItem(item_name)

        for i in self.details:
            i = str(i)
            item_name = i[i.find(str(int(idx))) + len(str(idx)):]
            self.detail_url_list.addItem(item_name)

    @staticmethod
    def read_table_data(file_name) -> DataFrame:
        df = pd.read_excel(file_name, header=0)

        df.columns = table_headers
        data = df[
            valid_headers
        ]

        # 重新设置索引
        data.index = range(len(data))

        return data

    def get_price_by_goods_name(self, goods_name):
        # find 品名 contains goods_name
        row = self.table_data[self.table_data["商品名称"].str.contains(goods_name, regex=False)]
        data = (self.table_data.loc[row.index[0]][[
            "普通会员价格",
            "高级会员价",
            "VIP会员价",
            "至尊VIP会员价",
        ]])
        return list(data)

    async def init_data(self):
        # flush category
        self.category = await get_category()

        # self.category_widget = Tree(self.category, [])

        if not managed_exists("black_list.txt"):
            with managed_open("black_list.txt", "w", encoding='u8') as f:
                f.write("")

        with managed_open("black_list.txt", "r", encoding='u8') as f:
            self.black_list: list[int] = list(map(int, f.readlines()))

        # with managed_open("category.json", "r", encoding='u8') as f:
        #     category = json.load(f)

        self.table_data = self.read_table_data(self.file_name)

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

        category_header_layout = QHBoxLayout()
        category_header_layout.addWidget(BodyLabel(text="当前选择类别: "))
        self.category_label = BodyLabel(text="无")

        self.category_button = PushButton("选择类别", self)
        self.category_button.clicked.connect(self.show_category)

        category_header_layout.addWidget(self.category_label)
        category_header_layout.addWidget(self.category_button)

        category_layout.addLayout(category_header_layout)
        category_layout.addLayout(weight_layout)

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
        headers = valid_headers

        self.table_widget.setMaximumHeight(100)
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(len(headers))

        self.table_widget.setHorizontalHeaderLabels(headers)

        # Add the table to the layout
        table_layout.addWidget(self.table_widget)

        body_layout.addLayout(table_layout)

        # init layout
        layout.addLayout(header_layout)
        layout.addLayout(body_layout)

        # Set layout to the widget
        self.setLayout(layout)
        self.resize(1200, 800)

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


class CategoryDialog(QDialog):
    def __init__(self, categories, selected_categories):
        super().__init__()
        self.categories = categories
        self.selected_categories = selected_categories
        self.checkboxes = []  # 存储所有的复选框
        self.checkbox_data = {}  # 存储复选框与数据的映射关系
        self.init_ui()

    def init_ui(self):
        layout = VBoxLayout(self)

        # 创建滚动区域
        scroll_widget = QWidget()
        scroll_layout = VBoxLayout(scroll_widget)
        scroll_area = ScrollArea()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        # 按一级分类组织二级分类
        for category_name, category_data in self.categories.items():
            if category_name != "价格区间":  # 跳过价格区间
                # 创建分类组标题
                group_layout = QVBoxLayout()
                title = SubtitleLabel(category_name)
                group_layout.addWidget(title)

                # 创建复选框网格布局
                checkbox_layout = FlowLayout()

                # 添加该分类下的所有二级分类
                for child_name, child_data in category_data.get("children", {}).items():
                    checkbox = CheckBox(child_name)

                    # 存储复选框与数据的关系
                    self.checkbox_data[checkbox] = child_data

                    # 检查是否在已选择列表中
                    if any(cat["level"] == child_data["level"] for cat in self.selected_categories):
                        checkbox.setChecked(True)

                    self.checkboxes.append(checkbox)
                    checkbox_layout.addWidget(checkbox)

                group_layout.addLayout(checkbox_layout)
                scroll_layout.addLayout(group_layout)

                # 添加分隔线
                scroll_layout.addWidget(HorizontalSeparator())

        # 添加按钮
        button_layout = QHBoxLayout()
        ok_button = PushButton("确定")
        cancel_button = PushButton("取消")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)

        # 设置布局
        layout.addWidget(scroll_area)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.resize(800, 600)
        self.setWindowTitle("选择类别")

    def get_selected_categories(self):
        selected = []
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                category_data = self.checkbox_data[checkbox]
                selected.append({
                    "level": category_data["level"],
                    "name": category_data["name"]
                })
        return selected


table_headers = [
    "序号",
    "一级分类",
    "二级分类",
    "品牌",
    "商品名称",
    "商品代码",
    "含税集采价",
    "含税代发价",
    "市场价",
    "职友团平台价",
    "最终利润率",
    "标准利润率",
    "利润完成比",
    "利润线",
    "满足价格",
    "等级满足比",
    "普通会员价格",
    "利润线",
    "满足价格",
    "等级满足比",
    "高级会员价",
    "利润线",
    "满足价格",
    "等级满足比",
    "VIP会员价",
    "利润线",
    "满足价格",
    "等级满足比",
    "至尊VIP会员价",
]
valid_headers = [
    "序号",
    "一级分类",
    "二级分类",
    "品牌",
    "商品名称",
    "商品代码",
    "含税代发价",
    "市场价",
    "职友团平台价",
    "普通会员价格",
    "高级会员价",
    "VIP会员价",
    "至尊VIP会员价",
]

if __name__ == "__main__":
    from qasync import QEventLoop

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    ex = Main()
    ex.show()

    with loop:
        loop.run_forever()
