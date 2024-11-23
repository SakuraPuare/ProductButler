import pathlib
import re

import httpx

post_re = re.compile(r'主图')
detail_re = re.compile(r'详情')
image_re = re.compile(r'images')

large_bound = 1024 * 1024 * 2


def is_image(byte: bytes) -> bool:
    import io

    from PIL import Image

    try:
        Image.open(io.BytesIO(byte))
        return True
    except Exception as e:
        import loguru
        loguru.logger.error(e)
        return False


def get_imagehash(byte: bytes) -> str:
    import io

    import imagehash
    from PIL import Image

    img = Image.open(io.BytesIO(byte))
    return str(imagehash.average_hash(img))


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
    # with ProcessPoolExecutor(max_workers=4) as executor:
    #     hash_list = list(executor.map(get_imagehash, [bytes_ for bytes_, is_img in zip(byte_list, is_image_list) if is_img]))

    hash_map = {}
    for file, hash_ in zip(image_list, hash_list):
        for hash_a, (existing_file, size) in hash_map.items():
            similarity = imagehash.hex_to_hash(
                hash_a) - imagehash.hex_to_hash(hash_)
            if abs(similarity) < 5:
                if size < file_stats[file]:
                    hash_map[hash_a] = (file, file_stats[file])
                break
        else:
            hash_map[hash_] = (file, file_stats[file])

    file_set = {file for file, _ in hash_map.values()}

    posts = {file for file in file_set if post_re.search(str(file))}
    details = {file for file in file_set if detail_re.search(
        str(file)) and file not in posts}
    details.update(file for file in file_set if image_re.search(
        str(file)) and file not in posts)

    if not posts and details:
        posts = file_set - details
    elif not details and posts:
        details = file_set - posts

    posts.update(file for file in file_set if is_square_image(
        file) and file not in details)
    if not details and posts:
        details = file_set - posts

    # filter height / width > 3 in details
    if len(details) > 1:
        details = {file for file in details if get_ratio(file) < 6}

    if not posts or not details:
        large_file_list.sort(key=lambda file: file_stats[file])
        if not posts:
            posts = {file for file in large_file_list if is_square_image(
                file) and file not in details}

        for post in posts:
            resize_to_large_bound(post)

        if not details:
            large_file_list_not_squares = {
                file for file in large_file_list if not is_square_image(file) and file not in posts}
            if len(large_file_list_not_squares) > 1:
                details = {
                    file for file in large_file_list_not_squares if get_ratio(file) < 6}
            else:
                details = large_file_list_not_squares

            for detail in details:
                resize_to_large_bound(detail)

    return sorted(posts, key=custom_sort), sorted(details, key=custom_sort)


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

    with open(file_path, 'w', encoding='u8') as f:
        json.dump(dict(httpx_cookies), f)


def load_cookies(file_path: str = "cookies.json") -> 'httpx.Cookies':
    import json
    import os

    import httpx

    if not os.path.exists(file_path):
        return httpx.Cookies()

    with open(file_path, 'r', encoding='u8') as f:
        return httpx.Cookies(json.load(f))
