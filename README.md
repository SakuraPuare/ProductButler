# 商品数据上传管理工具

这是一个基于PySide6开发的GUI应用程序，用于管理和上传商品数据。该工具可以从Excel文件中读取商品信息，并结合图片资源进行商品信息的批量上传管理。

## 功能特点

- Excel数据导入：支持从Excel文件中读取商品数据
- 图片资源管理：支持选择和管理商品图片文件夹
- 商品分类管理：支持灵活的商品分类选择和管理
- 批量上传：支持商品信息的批量上传
- 会员价格管理：支持设置不同等级会员的价格
- 数据验证：提供基本的数据验证功能
- 进度追踪：支持断点续传，记录已上传商品

## 安装要求

主要依赖：
- PySide6
- pandas
- loguru
- qfluentwidgets
- asyncio

## 使用说明

1. 运行程序：
```bash
pip install -r requirements.txt
```

```bash
python gui.py
```

2. 主要操作流程：
   - 选择Excel数据文件
   - 选择商品图片文件夹
   - 设置上传范围（起始序号和结束序号）
   - 选择商品分类
   - 检查并确认商品信息
   - 点击上传按钮进行上传

3. 图片文件夹要求：
   - 图片文件夹需按商品序号命名
   - 每个商品文件夹需包含主图和详情图

## 注意事项

- 上传前请确保网络连接正常
- 建议定期备份Excel数据文件
- 图片命名需要符合规范
- 上传过程中请勿关闭程序

## 错误处理

- 程序会记录上传失败的商品信息
- 可通过black_list.txt查看已处理的商品序号
- 遇到错误时会显示相应的错误提示

## 开发说明

- 使用PySide6构建GUI界面
- 采用异步处理方式提高性能
- 使用qfluentwidgets提供现代化UI组件
- 支持多语言响应