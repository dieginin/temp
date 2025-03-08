import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile


def apply_update(update_zip) -> None:
    system = platform.system().lower()
    temp_dir = tempfile.mkdtemp()

    time.sleep(3)

    try:
        with zipfile.ZipFile(update_zip, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        os.remove(update_zip)

        if system == "windows":
            for item in os.listdir(temp_dir):
                source = os.path.join(temp_dir, item)
                destiny = os.path.join(os.getcwd(), item)
                if os.path.isdir(source):
                    shutil.copytree(source, destiny, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, destiny)
        elif system == "darwin":
            new_app = os.path.join(temp_dir, "MyApp.app")
            if os.path.exists(new_app):
                shutil.move(new_app, os.getcwd())
    except Exception as e:
        print("Error al aplicar la actualización:", e)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    if system == "windows":
        subprocess.Popen([os.path.join(os.getcwd(), "MyApp.exe")])
    elif system == "darwin":
        subprocess.Popen(["open", os.path.join(os.getcwd(), "MyApp.app")])


if __name__ == "__main__":
    update_zip = sys.argv[1]
    apply_update(update_zip)
