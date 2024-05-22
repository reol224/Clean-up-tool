import ctypes
from ctypes import windll, byref, wintypes, Structure, c_ulonglong
import os
import shutil

def print_ascii_logo():
    logo = """
     ____       _        _       _       _               
    / ___|  ___| |_ __ _| | __ _| |_ ___| |__   ___ _ __ 
    \___ \ / _ \ __/ _` | |/ _` | __/ __| '_ \ / _ \ '__|
     ___) |  __/ || (_| | | (_| | || (__| | | |  __/ |   
    |____/ \___|\__\__,_|_|\__,_|\__\___|_| |_|\___|_|   
    """
    print(logo)

def get_temp_folder():
    return os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Temp')

def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def cleanup_temp_folder(folder):
    initial_size = get_folder_size(folder)

    for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
        for name in filenames:
            file_path = os.path.join(dirpath, name)
            try:
                os.remove(file_path)
            except PermissionError:
                print(f"Cannot delete file in use: {file_path}")
            except FileNotFoundError:
                continue

        for name in dirnames:
            dir_path = os.path.join(dirpath, name)
            try:
                shutil.rmtree(dir_path)
            except PermissionError:
                print(f"Cannot delete directory in use: {dir_path}")
            except FileNotFoundError:
                continue

    final_size = get_folder_size(folder)
    cleaned_size = initial_size - final_size

    return cleaned_size

class SHQUERYRBINFO(Structure):
    _fields_ = [
        ("cbSize", c_ulonglong),
        ("i64Size", c_ulonglong),
        ("i64NumItems", c_ulonglong)
    ]

def is_recycle_bin_empty():
    qinfo = SHQUERYRBINFO()
    qinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = windll.shell32.SHQueryRecycleBinW(None, byref(qinfo))
    if result == 0 and qinfo.i64NumItems > 0:
        return False
    else:
        print("Recycle Bin is empty, skipping emptying..")
        return True

def empty_recycle_bin():
    SHERB_NOCONFIRMATION = 0x00000001
    SHERB_NOPROGRESSUI = 0x00000002
    SHERB_NOSOUND = 0x00000004

    if not is_recycle_bin_empty():
        result = windll.shell32.SHEmptyRecycleBinW(None, None, SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND)
        print(f"Emptying Recycle Bin...")
        if result != 0:
            print(f"Failed to empty Recycle Bin. Error code: {result}")

def notify_user(message):
    windll.user32.MessageBoxW(0, message, "Cleanup Utility", 0x40 | 0x1)

def main():
    print_ascii_logo()
    
    temp_folder = get_temp_folder()

    initial_free_space = shutil.disk_usage(temp_folder).free
    cleaned_temp_size = cleanup_temp_folder(temp_folder)
    final_free_space = shutil.disk_usage(temp_folder).free

    cleaned_temp_size_mb = cleaned_temp_size / (1024 * 1024)
    temp_space_freed_mb = (final_free_space - initial_free_space) / (1024 * 1024)

    # Empty the Recycle Bin if it's not empty
    empty_recycle_bin()

    notify_user(f"Cleaned up {cleaned_temp_size_mb:.2f} MB from Temp folder.\n"
                f"Free space increased by {temp_space_freed_mb:.2f} MB.")
    print(f"Cleaned up {cleaned_temp_size_mb:.2f} MB from Temp folder.")
    print(f"Free space increased by {temp_space_freed_mb:.2f} MB.")

if __name__ == "__main__":
    main()

