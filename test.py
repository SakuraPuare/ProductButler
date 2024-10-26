import pathlib
import re

import viztracer

from utils import (
    custom_sort,
    find_files,
    get_imagehash,
    get_ratio,
    is_image,
    is_square_image,
    resize_to_large_bound,
)

post_re = re.compile(r'主图')
detail_re = re.compile(r'详情')
image_re = re.compile(r'images')

large_bound = 1024 * 1024 * 2

def glob_file_in_folder(folder: pathlib.Path) -> tuple[list, list]:
    file_list = [pathlib.Path(x) for x in find_files(folder)]
    file_stats = {file: file.stat().st_size for file in file_list}

    small_file_list = [file for file in file_list if file_stats[file] <= large_bound]
    large_file_list = [file for file in file_list if file_stats[file] > large_bound]

    byte_list = [file.read_bytes() for file in small_file_list]
    is_image_list = [is_image(bytes_) for bytes_ in byte_list]

    image_list = [file for file, is_img in zip(small_file_list, is_image_list) if is_img]
    hash_list = [get_imagehash(bytes_) for bytes_, is_img in zip(byte_list, is_image_list) if is_img]

    hash_map = {}
    for file, hash_ in zip(image_list, hash_list):
        for hash_a, (existing_file, size) in hash_map.items():
            similarity = imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_)
            if abs(similarity) < 5:
                if size < file_stats[file]:
                    hash_map[hash_a] = (file, file_stats[file])
                break
        else:
            hash_map[hash_] = (file, file_stats[file])

    file_set = {file for file, _ in hash_map.values()}

    posts = {file for file in file_set if post_re.search(str(file))}
    details = {file for file in file_set if detail_re.search(str(file)) and file not in posts}
    details.update(file for file in file_set if image_re.search(str(file)) and file not in posts)

    if not posts and details:
        posts = file_set - details
    elif not details and posts:
        details = file_set - posts

    posts.update(file for file in file_set if is_square_image(file) and file not in details)
    if not details and posts:
        details = file_set - posts

    # filter height / width > 3 in details
    if len(details) > 1:
        details = {file for file in details if get_ratio(file) < 3}

    if not posts or not details:
        large_file_list.sort(key=lambda file: file_stats[file])
        if not posts:
            posts = {file for file in large_file_list if is_square_image(file) and file not in details}

        for post in posts:
            resize_to_large_bound(post)

        if not details:
            large_file_list_not_squares = {file for file in large_file_list if not is_square_image(file) and file not in posts}
            if len(large_file_list_not_squares) > 1:
                details = {file for file in large_file_list_not_squares if get_ratio(file) < 3}

            for detail in details:
                resize_to_large_bound(detail)

    return sorted(posts, key=custom_sort), sorted(details, key=custom_sort)

tracer = viztracer.VizTracer()
tracer.start()
folder = pathlib.Path("/home/sakurapuare/Desktop/上传兼职/企悦汇选品1869-1961/企悦汇选品1869-1961/1901-牛奶绒多功能床盖（路易）")  # Replace with the actual folder path
glob_file_in_folder(folder)
tracer.stop()
tracer.save("result.json")
