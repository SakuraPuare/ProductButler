import importlib
import os
import platform
import time

import loguru


def get_browser_path(browser_name):
    paths = {
        "chrome": {
            "Windows": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "Linux": "/usr/bin/google-chrome"
        },
        "firefox": {
            "Windows": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "Linux": "/usr/bin/firefox"
        },
        "edge": {
            "Windows": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "Linux": "/usr/bin/microsoft-edge"
        }
    }
    return paths.get(browser_name, {}).get(platform.system())


def is_browser_installed(browser_name):
    browser_path = get_browser_path(browser_name)
    return browser_path if browser_path and os.path.exists(browser_path) else None


def launch_browser():
    browsers = {
        "chrome": (
            "selenium.webdriver.chrome.service", "selenium.webdriver.chrome.options", "webdriver_manager.chrome"),
        "firefox": (
            "selenium.webdriver.firefox.service", "selenium.webdriver.firefox.options", "webdriver_manager.firefox"),
        "edge": ("selenium.webdriver.edge.service", "selenium.webdriver.edge.options", "webdriver_manager.microsoft"),
    }

    for browser_name, (service_module, options_module, manager_module) in browsers.items():
        if is_browser_installed(browser_name):
            # print(f"{browser_name.capitalize()} 浏览器已安装，正在启动...")
            loguru.logger.info(f"{browser_name.capitalize()} 浏览器已安装，正在启动...")

            start_time = time.time()
            # 动态加载模块
            service = importlib.import_module(service_module)
            options = importlib.import_module(options_module)
            manager = importlib.import_module(manager_module)

            # 获取服务和选项类
            service_class = getattr(service, f'Service')
            options_class = getattr(options, f'Options')
            driver_manager = getattr(manager, f'{browser_name.capitalize()}DriverManager')

            # 创建选项和服务实例
            options_instance = options_class()
            # options_instance.add_argument("--headless")  # 无头模式
            driver_service = service_class(driver_manager().install())

            end_time = time.time()

            loguru.logger.info(f"{browser_name.capitalize()} 浏览器启动完成，耗时 {end_time - start_time:.2f} 秒")
            # 启动浏览器
            return getattr(importlib.import_module('seleniumwire.webdriver'), browser_name.capitalize())(
                service=driver_service, options=options_instance)

    loguru.logger.error("没有检测到可用的浏览器。")
    return None


if __name__ == "__main__":
    # 启动浏览器
    driver = launch_browser()

    if driver:
        try:
            # 在这里执行你的操作
            driver.get("https://www.example.com")
            print("当前页面标题:", driver.title)
        finally:
            driver.quit()
