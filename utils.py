import os
import random
from recycle_bin import RecycleBin

def secure_delete(path, passes=3):
    try:
        # Move to recycle bin first
        recycle_bin = RecycleBin()
        recycle_bin.move_to_bin(path)
    except Exception as e:
        print(f"Failed to move to recycle bin: {str(e)}")
        # If recycling fails, proceed with secure deletion
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