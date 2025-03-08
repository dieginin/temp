import os
import platform
import shutil
import subprocess
import tempfile
import zipfile
from typing import Callable, Optional

import flet as ft
import requests

from config import VERSION

GITHUB_REPO = "dieginin/temp"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_asset_url(assets: dict) -> str:
    system = platform.system().lower()
    platform_assets = {"darwin": "build-macos", "windows": "build-windows"}

    for asset in assets:
        if platform_assets.get(system, "") in asset["name"].lower():
            return asset["browser_download_url"]
    raise Exception("Asset not found for your operating system.")


class Updater:
    def __init__(self, page: ft.Page) -> None:
        self.page = page

        self.check_for_updates()

    def get_latest_version(self) -> tuple[str, str]:
        response = requests.get(API_URL)
        response.raise_for_status()

        data = response.json()
        return data["tag_name"].lstrip("v"), get_asset_url(data["assets"])

    def check_for_updates(self) -> None:
        parse_version = lambda v: tuple(map(int, v.split(".")))
        latest_version, _ = self.get_latest_version()
        if parse_version(latest_version) > parse_version(VERSION):
            self.dialog = ft.AlertDialog(
                True,
                ft.Text(f"Actualización {latest_version} disponible"),
                ft.Text(f"La actualización comenzará automáticamente"),
                [ft.TextButton("Aceptar", on_click=self.update_app)],
            )
            self.page.open(self.dialog)

    def update_app(self, _) -> None:
        def update_progress(value: Optional[float]) -> None:
            progress.value = value
            self.page.update()

        self.page.close(self.dialog)
        latest_version, url = self.get_latest_version()

        self.page.clean()
        self.page.title = "Actualizando..."
        progress = ft.ProgressBar(width=300)
        status = ft.Text("Buscando actualización...")
        self.page.add(status, progress)

        status.value = f"Descargando actualización v{latest_version}..."
        self.page.update()

        filename = self.download_update(url, update_progress)

        status.value = "Instalando actualización..."
        update_progress(None)

        self.apply_update(filename)

        status.value = "Actualización completada. Reiniciando..."
        self.page.update()

        system = platform.system().lower()
        if system == "windows":
            subprocess.Popen([os.path.join(os.getcwd(), "MyApp.exe")])
        elif system == "darwin":
            subprocess.Popen(["open", os.path.join(os.getcwd(), "MyApp.app")])

        os._exit(0)

    def download_update(self, url: str, progress_callback: Callable) -> str:
        filename = os.path.join(tempfile.gettempdir(), "update.zip")
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress_callback(downloaded / total_size)

        return filename

    def apply_update(self, filename: str) -> None:
        system = platform.system().lower()
        temp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            os.remove(filename)

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
