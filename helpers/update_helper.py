import os
import shutil
import subprocess
import sys
import time


def update_app(app_dir: str, source_dir: str, executable: str) -> None:
    time.sleep(2)

    for item in os.listdir(source_dir):
        src_path = os.path.join(source_dir, item)
        dst_path = os.path.join(app_dir, item)

        if os.path.isdir(src_path):
            if os.path.exists(dst_path):
                shutil.rmtree(dst_path, ignore_errors=True)
            shutil.copytree(src_path, dst_path)
        else:
            if os.path.exists(dst_path):
                os.remove(dst_path)
            shutil.copy2(src_path, dst_path)

    if sys.platform == "win32":
        subprocess.Popen([executable])
    elif sys.platform == "darwin":
        app_name = os.path.basename(app_dir).replace(".app", "")
        app_path = os.path.join(app_dir, f"{app_name}.app")
        subprocess.Popen(["open", app_path])


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: updater_helper.py <app_dir> <source_dir> <executable>")
        sys.exit(1)

    app_dir, source_dir, executable = sys.argv[1], sys.argv[2], sys.argv[3]
    update_app(app_dir, source_dir, executable)
