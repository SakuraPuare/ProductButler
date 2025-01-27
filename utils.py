import pathlib
import re

import httpx
from files import managed_exists, managed_open

from typehints import Category

post_re = re.compile(r'主(图|页)')
detail_re = re.compile(r'详情(图|页)')
image_re = re.compile(r'images')

large_bound = 1024 * 1024 * 2


def is_image(byte: bytes) -> bool:
    import io

    from PIL import Image

    try:
        Image.open(io.BytesIO(byte))
        return True
    except Exception as e:
        return False


def get_imagehash(byte: bytes) -> str:
    import io

    import imagehash
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(byte))
        return str(imagehash.average_hash(img))
    except Exception as e:
        return None


def custom_sort(file_path: 'pathlib.Path'):
    part = file_path.parts
    sort = []
    for p in part:
        find = re.findall(r'\d+', p)
        if find:
            remain = filter(lambda x: not x.isdigit(), re.split(r'\d+', p))
            sort.append(list(map(int, find)) +
                        list(map(ord, list(''.join(remain)))))
        else:
            sort.append(list(map(ord, p)))
    return sort


def is_square_image(file_path) -> bool:
    from PIL import Image

    img = Image.open(file_path)
    return img.height == img.width


def resize_to_large_bound(file_path: 'pathlib.Path'):
    from PIL import Image

    img = Image.open(file_path)
    while file_path.stat().st_size > large_bound:
        img = img.resize((int(img.width * 0.9), int(img.height * 0.9)))
        img.save(file_path)


def get_ratio(file_path: 'pathlib.Path'):
    from PIL import Image

    img = Image.open(file_path)
    return img.height / img.width


def is_start_with_number(string: str, number: int) -> bool:
    import re
    match = re.match(r'^[0-9]+', string)

    if match:
        return int(match.group(0)) == number
    return False


def get_folder_actual_name(folder: 'pathlib.Path'):
    import configparser
    # Check for desktop.ini and LocalizedResourceName
    ini_path = folder / 'desktop.ini'
    if ini_path.exists():
        try:
            config = configparser.ConfigParser()
            config.read(ini_path, encoding='gbk')
            localized_name = config['.ShellClassInfo']['LocalizedResourceName']
            if localized_name := localized_name.strip():
                return localized_name
        except Exception as e:
            pass

    return folder.name.strip()


def folder_start_with(folder: 'pathlib.Path', string: str) -> bool:
    name = folder.name.strip()
    if is_start_with_number(name, int(string)):
        return True

    # 如果开头不是数字，则检查desktop.ini
    import re
    match = re.match(r'^[0-9]+', name)

    if not match:
        import configparser
        # Check for desktop.ini and LocalizedResourceName
        ini_path = folder / 'desktop.ini'
        if ini_path.exists():
            try:
                config = configparser.ConfigParser()
                config.read(ini_path, encoding='gbk')
                localized_name = config['.ShellClassInfo']['LocalizedResourceName']
                if localized_name := localized_name.strip():
                    if is_start_with_number(localized_name, int(string)):
                        return True
            except:
                return False
    return False


def glob_file_in_folder(folder: 'pathlib.Path') -> tuple[list, list]:
    import imagehash

    file_list = [pathlib.Path(x) for x in find_files(folder)]
    file_stats = {file: file.stat().st_size for file in file_list}

    small_file_list = [
        file for file in file_list if file_stats[file] <= large_bound]
    large_file_list = [
        file for file in file_list if file_stats[file] > large_bound]

    byte_list = [file.read_bytes() for file in small_file_list]
    is_image_list = [is_image(bytes_) for bytes_ in byte_list]

    image_list = [file for file, is_img in zip(
        small_file_list, is_image_list) if is_img]
    hash_list = [get_imagehash(bytes_) for bytes_, is_img in zip(
        byte_list, is_image_list) if is_img]

    # 过滤掉hash为None的
    image_list = [file for file, hash_ in zip(image_list, hash_list) if hash_]
    hash_list = [hash_ for hash_ in hash_list if hash_]

    hash_map = {}
    for file, hash_ in zip(image_list, hash_list):
        for hash_a, (_, size) in hash_map.items():
            similarity = imagehash.hex_to_hash(
                hash_a) - imagehash.hex_to_hash(hash_)
            if abs(similarity) < 5:
                if size < file_stats[file]:
                    hash_map[hash_a] = (file, file_stats[file])
                break
        else:
            hash_map[hash_] = (file, file_stats[file])

    file_set = {file for file, _ in hash_map.values()}
    relative_set = {file.relative_to(folder) for file in file_set}

    # Use relative paths for pattern matching
    posts = {file for file in relative_set if post_re.search(str(file))}
    details = {file for file in relative_set if detail_re.search(
        str(file)) and file not in posts}
    details.update(file for file in relative_set if image_re.search(
        str(file)) and file not in posts)

    if not posts and details:
        posts = relative_set - details
    elif not details and posts:
        details = relative_set - posts

    # Convert back to absolute paths for image operations
    posts_abs = {folder / file for file in posts}
    details_abs = {folder / file for file in details}
    file_set_abs = {folder / file for file in relative_set}

    posts_abs.update(file for file in file_set_abs if is_square_image(
        file) and file not in details_abs)
    if not details_abs and posts_abs:
        details_abs = file_set_abs - posts_abs

    # filter height / width > 3 in details
    if len(details_abs) > 1:
        details_abs = {file for file in details_abs if get_ratio(file) < 6}

    if not posts_abs or not details_abs:
        large_file_list.sort(key=lambda file: file_stats[file])
        if not posts_abs:
            posts_abs = {file for file in large_file_list if is_square_image(
                file) and file not in details_abs}

        for post in posts_abs:
            resize_to_large_bound(post)

        if not details_abs:
            large_file_list_not_squares = {
                file for file in large_file_list if not is_square_image(file) and file not in posts_abs}
            if len(large_file_list_not_squares) > 1:
                details_abs = {
                    file for file in large_file_list_not_squares if get_ratio(file) < 6}
            else:
                details_abs = large_file_list_not_squares

            for detail in details_abs:
                resize_to_large_bound(detail)

    return sorted(posts_abs, key=custom_sort), sorted(details_abs, key=custom_sort)


def find_closest_string(target, string_list):
    from difflib import SequenceMatcher

    closest_idx = -1
    closest_score = 0.0
    for idx, string in enumerate(string_list):
        score = SequenceMatcher(None, target, string).ratio()
        if score > closest_score:
            closest_score = score
            closest_idx = idx
    return closest_idx


def find_files(directory) -> list[str]:
    import os

    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
            # loguru.logger.debug(file_paths[-1])
    return file_paths


def save_cookies(httpx_cookies: 'httpx.Cookies', file_path: str = "cookies.json"):
    import json

    with managed_open(file_path, 'w', encoding='u8') as f:
        json.dump(dict(httpx_cookies), f)


def load_cookies(file_path: str = "cookies.json") -> 'httpx.Cookies':
    import json

    import httpx

    if not managed_exists(file_path):
        return httpx.Cookies()

    with managed_open(file_path, 'r', encoding='u8') as f:
        return httpx.Cookies(json.load(f))


def get_category_level_1(category: 'Category', string: str):
    items = list(category.keys())
    idx = find_closest_string(string, items)
    return items[idx], category[items[idx]].get("level")


def get_category_level_2(category: 'Category', level_1: str, string: str):
    items = list(category[level_1]["children"].keys())
    idx = find_closest_string(string, items)
    return items[idx], category[level_1]["children"][items[idx]].get("level")


async def until_success(func, *args, **kwargs):
    import loguru
    import asyncio

    if asyncio.iscoroutinefunction(func):
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                loguru.logger.error(e)
    else:
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                loguru.logger.error(e)
