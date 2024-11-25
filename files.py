import builtins
import copy
import os
import pathlib
import traceback
from contextlib import contextmanager

base_dir = pathlib.Path(__file__).parent / 'files'


def get_new_name(name):
    stack = traceback.extract_stack()

    for frame in reversed(stack):
        if frame.filename != __file__:
            break
    file_path = pathlib.Path(frame.filename)

    save_path = copy.deepcopy(base_dir)

    for i in range(len(file_path.parts) - 1, -1, -1):
        if file_path.parts[i] == 'upload':
            save_path = save_path / file_path.parts[i + 1]
            break

    save_path.mkdir(exist_ok=True, parents=True)

    save_path = save_path.with_name(name)

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
