import os
import random

def secure_delete(path, passes=3):
    if os.path.isfile(path):
        length = os.path.getsize(path)
        with open(path, "ba+") as f:
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(length))
        os.remove(path)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for file in files:
                secure_delete(os.path.join(root, file), passes)
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(path)