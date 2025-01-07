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
from utils import find_closest_string, folder_start_with, glob_file_in_folder
from .apis import (
    add_vip_goods,
    create,
    get_category,
    get_goods_detail,
    get_goods_list,
    get_vip_goods_list,
    login,
    search_goods,
    set_vip_price,
)
from .cos import upload_files
from .utils import get_keyword_category, get_loc_by_goods_detail, get_price_category, get_price_by_goods_detail


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


async def check_goods_exists(data):
    """检查商品是否已存在

    Args:
        data: 商品数据列表

    Returns:
        bool: 商品是否已存在
    """
    goods_list = await search_goods(data[4])  # 使用商品名称搜索
    return bool(goods_list)


class DataForm(QWidget):
    def __init__(self, path_data):
        super().__init__()
        self.selected_category = None
        self.category_label = None
        self.category_dialog = None
        self.category_button = None
        self.start_edit = LineEdit()
        self.end_edit = LineEdit()
        self.reset_button = PushButton(text="重置")
        self.load_button = PushButton(text="加载")
        self.jump_button = PushButton(text="跳转到")
        self.jump_edit = LineEdit()
        self.pre_button = PushButton(text="上一条")
        self.next_button = PushButton(text="下一条")
        self.upload_button = PushButton(text="上传")
        self.batch_upload_button = PushButton(text="批量上传")
        self.stop_upload_button = PushButton(text="停止上传")
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
        self.category = None
        self.details = None
        self.posts = None
        self.image_folder = None

        self.end = None
        self.start = None
        self.is_upload = False
        self.stop_upload = False
        
        self.file_name, self.image_path = path_data

        self.category_widget = None

        self.image_folder_list = list(pathlib.Path(self.image_path).iterdir())

        self.loc = -1

        asyncio.ensure_future(self.initialize())

    async def initialize(self):
        await self.init_data()
        self.init_ui()

        # 尝试识别图片文件夹的范围
        try:
            a, b = pathlib.Path(self.image_path).name.split('-')[-2:]
            self.start = int(a.strip())
            self.end = int(b.strip())

            self.start_edit.setText(str(self.start))
            self.end_edit.setText(str(self.end))
            self.jump_edit.setText(f"{self.start}")

            self.jmp(self.start)
        except Exception as e:
            self.start = 0
            self.end = 0

        # get the first goods, try to recover the last upload
        goods_list = await get_goods_list(page=1, limit=1)
        good = goods_list[0]
        name = good.get('name', '')
        bar_code = good.get('goodsSn', '')

        # FIXME: magic, why loc is exactly the same as the last upload + 1
        loc = get_loc_by_goods_detail(self.table_data, name, bar_code)
        if loc is not None:
            # 检查这个位置的商品是否可以跳转
            valid = await self.check_loc_valid(loc)
            if valid:
                self.start_edit.setText(str(loc))
                self.jump_edit.setText(str(loc))

                self.jmp(loc)

    def upload(self):
        if self.is_upload:
            InfoBar.error(title="Error", content="正在上传中，请稍等", parent=self)
            return

        asyncio.ensure_future(self._upload())

    async def _do_upload(self, ids, data, weight, show_error=True):
        """执行基础的上传逻辑
        
        Args:
            ids: 商品ID
            data: 商品数据列表
            weight: 商品重量
            show_error: 是否显示错误提示
            
        Returns:
            bool: 上传是否成功
        """
        try:
            # 检查商品是否已存在
            if await check_goods_exists(data):
                loguru.logger.info(f"[{data[4]}] 商品已存在")
                if show_error:
                    InfoBar.error(title="Error", content="商品已存在", parent=self)
                return False

            # 检查图片是否存在且完整
            images_exist, image_folder = self.check_images_exists(int(ids), data[4])  # data[4]是商品名称
            if not images_exist:
                loguru.logger.error(f"[{data[4]}] 未找到商品图片或图片不完整")
                if show_error:
                    InfoBar.error(title="Error", content="未找到商品图片或图片不完整", parent=self)
                return False

            # 获取已验证过的图片路径
            self.posts, self.details = glob_file_in_folder(image_folder)

            # 并行上传所有图片
            posts_url = await upload_files(list(self.posts)[:10])
            details_url = await upload_files(self.details)

            # 解析数据
            _, _, _, _, goods_name, bar_code, cost_price, market_price, counter_price, _, _, _, _ = data

            # 创建商品
            await create(
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

            # 处理会员商品逻辑
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

            # 设置会员价格
            goods_details = []
            flag = True
            page = 1
            size = 50
            while flag:
                vip_goods_list = await get_vip_goods_list(page=page, size=size, status=True)
                for i in vip_goods_list:
                    detail = await get_goods_detail(i.get('Id'))
                    price = [detail.get('products', [])[0].get(f'vip{j}Price', 0) for j in range(1, 5)]
                    if not all(price):
                        goods_details.append(detail)
                    else:
                        flag = False
                        break
                page += 1

            tasks = []
            for detail in goods_details:
                name = detail.get('goods', {}).get('name', '')
                for product in detail.get('products', []):
                    bar_code = product.get('specificationCode', '')
                    price = get_price_by_goods_detail(self.table_data, name, bar_code)
                    if price is None:
                        loguru.logger.error(f"[{ids}] 商品 {name} {bar_code}的会员价未录入，未找到价格")
                        raise Exception(f"[{ids}] 商品 {name} {bar_code}的会员价未录入，未找到价格")

                    tasks.append(
                        set_vip_price(
                            product.get('id'),
                            *price.tolist()
                        )
                    )
            await asyncio.gather(*tasks)

            return True

        except Exception as e:
            if show_error:
                InfoBar.error(title="Error", content=str(e), parent=self)
            raise e

    async def _upload(self):
        """单个商品上传"""
        try:
            data = [self.table_widget.item(0, i).text() for i in range(self.table_widget.columnCount())]
            ids = data[0]
            weight = self.weight_edit.text()

            if await self._do_upload(ids, data, weight):
                self.nxt()
                loguru.logger.info(f"[{ids}] 上传成功")

        finally:
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
            i for i in self.image_folder_list if folder_start_with(i, str(idx))
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
            # 先用idx分隔
            item_name = i.split(str(int(idx)))[-1][1:]
            # 再用文件夹名分隔
            item_name = item_name.split(self.image_folder.name)[-1]
            self.poster_url_list.addItem(item_name)

        for i in self.details:
            i = str(i)
            # 先用idx分隔
            item_name = i.split(str(int(idx)))[-1][1:] # 还要去掉一个 /
            # 再用文件夹名分隔
            item_name = item_name.split(self.image_folder.name)[-1][1:]
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

    async def init_data(self):
        # flush category
        self.category = await get_category()

        # self.category_widget = Tree(self.category, [])

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
            lambda: self.jmp(self.jump_edit.text() if self.jump_edit.text() else self.start_edit.text()))

        self.pre_button.clicked.connect(self.pre)
        self.next_button.clicked.connect(self.nxt)

        self.upload_button.clicked.connect(self.upload)
        self.batch_upload_button.clicked.connect(self.batch_upload)
        self.stop_upload_button.clicked.connect(self.stop_batch_upload)

        header_layout.addWidget(self.reset_button)
        header_layout.addWidget(self.load_button)
        header_layout.addWidget(self.upload_button)
        header_layout.addWidget(self.batch_upload_button)
        header_layout.addWidget(self.stop_upload_button)
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

    def check_images_exists(self, idx, goods_name):
        """检查商品图片是否存在且正常
        
        Args:
            idx: 商品序号
            goods_name: 商品名称
            
        Returns:
            tuple: (是否存在图片, 图片文件夹路径)
        """
        image_folder = [
            i for i in self.image_folder_list if folder_start_with(i, str(idx))
        ]
        
        if not image_folder:
            return False, None
            
        # 找到最匹配的文件夹
        image_folder = image_folder[
            find_closest_string(goods_name, [i.name for i in image_folder])
        ]
        
        # 检查是否有主图和详情图
        posts, details = glob_file_in_folder(image_folder)
        if not posts or not details:
            return False, None
            
        return True, image_folder

    async def check_loc_valid(self, loc):
        """检查指定位置的商品是否可以跳转
        
        Args:
            loc: 商品在表格中的位置索引
            
        Returns:
            tuple: (是否可以跳转, 错误信息)
        """
        try:
            row = self.table_data.loc[loc]
            data = row[valid_headers].tolist()
            
            # 检查商品是否已存在
            if await check_goods_exists(data):
                return False
                
            # 检查图片是否存在
            images_exist, _ = self.check_images_exists(row["序号"], row["商品名称"])
            if not images_exist:
                return False
                
            return True
            
        except Exception as e:
            return False

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
        InfoBar.info(title="Success", content=f"已经切换到数据 {idx}", parent=self)

    def batch_upload(self):
        if self.is_upload:
            InfoBar.error(title="Error", content="正在上传中，请稍等", parent=self)
            return
        
        if not self.start_edit.text() or not self.end_edit.text():
            InfoBar.error(title="Error", content="请输入开始序号和结束序号", parent=self)
            return
        
        asyncio.ensure_future(self._batch_upload())

    async def _batch_upload(self):
        """批量上传"""
        self.is_upload = True
        self.stop_upload = False
        start_idx = int(self.start_edit.text())
        end_idx = int(self.end_edit.text())
        
        error_list = []
        success_count = 0
        
        InfoBar.info(title="批量上传开始", content=f"开始序号: {start_idx}, 结束序号: {end_idx}", parent=self)
        
        try:
            for idx in range(start_idx, end_idx + 1):
                if self.stop_upload:
                    error_list.append("用户手动停止上传")
                    break
                    
                try:
                    # 跳转到指定序号
                    self.jmp(idx)
                    if self.loc == -1:
                        error_list.append(f"序号 {idx} 未找到对应数据")
                        continue
                        
                    # 执行上传逻辑
                    data = [self.table_widget.item(0, i).text() for i in range(self.table_widget.columnCount())]
                    ids = data[0]

                    weight = self.weight_edit.text()
                    
                    if await self._do_upload(ids, data, weight, show_error=False):
                        success_count += 1
                        loguru.logger.info(f"[{ids}] 上传成功")
                    
                except Exception as e:
                    error_msg = f"序号 {idx} 上传失败: {str(e)}"
                    error_list.append(error_msg)
                    loguru.logger.error(error_msg)
                    continue
                    
        finally:
            self.is_upload = False
            self.stop_upload = False
            
        # 显示最终结果
        result_message = f"批量上传{'完成' if not self.stop_upload else '已停止'}\n成功: {success_count}条\n失败: {len(error_list)}条"
        if error_list:
            result_message += "\n\n失败详情:\n" + "\n".join(error_list)
        
        InfoBar.info(title="批量上传结果", content=result_message, parent=self)
        loguru.logger.info(result_message)

    def stop_batch_upload(self):
        if not self.is_upload:
            InfoBar.error(title="Error", content="咱还没开始上传呢...", parent=self)
            return
        self.stop_upload = True
        InfoBar.info(title="停止上传", content="正在停止上传...", parent=self)
        loguru.logger.info("用户手动停止上传")


class CategoryDialog(QDialog):
    def __init__(self, categories, selected_categories):
        super().__init__()
        self.categories = categories
        self.selected_categories = selected_categories
        self.checkboxes = []  # 存储所有的复选框
        self.checkbox_data = {}  # 存储复选框与数据的映射关系

        self.price_category = []
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
            else:
                for child_name, child_data in category_data.get("children", {}).items():
                    self.price_category.append(child_data["level"])
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
        for i in self.selected_categories:
            if i.get("level") in self.price_category:
                selected.append(i)
        
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
