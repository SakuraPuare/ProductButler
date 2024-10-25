import imagehash
import io
import os
import pathlib
import re
from PIL import Image
from bs4 import BeautifulSoup
from difflib import SequenceMatcher


def is_image(byte: bytes) -> bool:
    try:
        Image.open(io.BytesIO(byte))
        return True
    except Exception as e:
        return False


def get_imagehash(byte: bytes) -> str:
    img = Image.open(io.BytesIO(byte))
    return str(imagehash.average_hash(img))


post_re = re.compile(r'主图')
detail_re = re.compile(r'详情')
image_re = re.compile(r'images')


def custom_sort(file_path: pathlib.Path):
    s = ' '.join(file_path.parts[3:])
    # 使用正则表达式从字符串中提取数字部分
    find = re.findall(r'\d+', s)  # list[str]
    if find:
        # 返回找到的数字作为排序关键字
        remain = [s[:s.find(i)] for i in find]
        remain.append(s[s.find(find[-1]) + len(find[-1]):])
        return list(map(int, find)) + list(map(ord, list(''.join(remain))))
    # 如果没有找到数字，则返回一个大数字，确保这些条目排在后面
    return list(map(ord, list(s)))


def is_square_image(file_path) -> bool:
    img = Image.open(file_path)
    return abs(img.width / img.height - 1) < 0.1


def glob_file_in_folder(folder: pathlib.Path) -> tuple[list, list]:
    file_list = find_files(folder)
    # filter image smaller than 1mb
    file_list = filter(lambda x: pathlib.Path(
        x).stat().st_size <= 1024 * 1024 * 2, file_list)
    file_list = [pathlib.Path(file) for file in file_list]
    byte_list = [file.read_bytes() for file in file_list]
    is_image_list = [i for i in map(is_image, byte_list)]

    image_list = list(map(lambda y: y[0], filter(
        lambda x: x[1], zip(file_list, is_image_list))))
    hash_list = list(map(lambda y: get_imagehash(y[0]), filter(
        lambda x: x[1], zip(byte_list, is_image_list))))

    hash_map = {}
    for file, hash_ in zip(image_list, hash_list):
        flag = False
        dst_hash = None
        for hash_a in hash_map.keys():
            # compute the similarity between two hash
            similarity = imagehash.hex_to_hash(hash_a) - \
                         imagehash.hex_to_hash(hash_)
            if abs(similarity) < 5:
                flag = True
                dst_hash = hash_a
                break
        if not flag:
            hash_map[hash_] = (file, file.stat().st_size)
        else:
            if hash_map[dst_hash][1] < file.stat().st_size:
                hash_map[dst_hash] = (file, file.stat().st_size)

    file_set = [file for file, _ in hash_map.values()]

    posts = list(filter(lambda x: post_re.search(str(x)), file_set))
    details = list(filter(lambda x: detail_re.search(
        str(x)) and x not in posts, file_set))

    details += list(filter(lambda x: image_re.search(str(x))
                                     and x not in posts, file_set))
    posts += list(filter(lambda x: is_square_image(x)
                                   and x not in details, file_set))
    posts = list(set(posts))
    details = list(set(details))

    if not posts and details:
        posts = list(set(file_set).difference(set(details)))
    if not details and posts:
        details = list(set(file_set).difference(set(posts)))

    assert posts and details, folder

    return sorted(posts, key=custom_sort), sorted(details, key=custom_sort)


def find_closest_string(target, string_list):
    closest_idx = -1
    closest_score = 0.0
    for idx, string in enumerate(string_list):
        score = SequenceMatcher(None, target, string).ratio()
        if score > closest_score:
            closest_score = score
            closest_idx = idx
    return closest_idx


def parse_html_options(html):
    soup = BeautifulSoup(html, 'lxml')
    options = soup.find_all('option')
    result = {}
    for option in options:
        value = option.get('value')
        if not value:
            continue

        text = option.text.strip()
        result[text] = {
            'level': value,
            'children': []
        }
    return result


def find_files(directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
            # loguru.logger.debug(file_paths[-1])
    return file_paths
