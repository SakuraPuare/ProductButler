import builtins
import copy
import os
import pathlib
import traceback
from contextlib import contextmanager

base_dir = pathlib.Path(__file__).parent / 'files'


def get_new_name(name):
    stack = traceback.extract_stack()
    found = False
    for frame in reversed(stack):
        if 'upload' in frame.filename:
            found = True
            break
    file_path = pathlib.Path(frame.filename)

    save_path = copy.deepcopy(base_dir)

    if found:
        idx = file_path.parts.index('upload')
        save_path = save_path / file_path.parts[idx + 1]

    save_path.mkdir(exist_ok=True, parents=True)

    save_path = save_path / name

    return save_path


def custom_open(name, *args, **kwargs):
    new_name = get_new_name(name)
    return builtins.open(new_name, *args, **kwargs)


@contextmanager
def managed_open(name, *args, **kwargs):
    file = custom_open(name, *args, **kwargs)
    try:
        yield file
    finally:
        file.close()


def managed_exists(name):
    new_name = get_new_name(name)
    return os.path.exists(new_name)


if __name__ == "__main__":
    with managed_open("test.txt", "w") as f:
        f.write("Hello, world!")
