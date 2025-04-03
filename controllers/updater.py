import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from random import uniform
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
    raise Exception("El asset para tu sistema operativo no fue encontrado.")


def get_latest_version() -> tuple[str, str]:
    response = requests.get(API_URL)
    response.raise_for_status()

    data = response.json()
    return data["tag_name"].lstrip("v"), get_asset_url(data["assets"])


class Updater:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.latest_version, self.version_url = get_latest_version()
        self.check_for_updates()

    def check_for_updates(self) -> None:
        parse_version = lambda v: tuple(map(int, v.split(".")))
        if parse_version(self.latest_version) > parse_version(VERSION):
            self.dialog = ft.AlertDialog(
                True,
                ft.Text(f"Actualización {self.latest_version} disponible"),
                ft.Text(f"La actualización comenzará automáticamente"),
                [ft.TextButton("Aceptar", on_click=self.start_update)],
            )
            self.page.open(self.dialog)

    def start_update(self, _) -> None:
        def update_progress(value: Optional[float]) -> None:
            progress.value = value
            self.page.update()

        self.page.close(self.dialog)

        self.page.clean()
        self.page.title = "Actualizando..."
        progress = ft.ProgressBar(width=300)
        status = ft.Text("Preparando actualización...")
        self.page.add(status, progress)

        status.value = f"Descargando actualización v{self.latest_version}..."
        self.page.update()

        filename = self.download_update(self.version_url, update_progress)

        status.value = "Actualización descargada. Reiniciando..."
        update_progress(None)
        time.sleep(uniform(0, 3))
        self.apply_update(filename)

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
        try:
            # Determinar la ubicación de la aplicación actual
            app_dir = os.path.dirname(os.path.abspath(sys.executable))
            temp_extract_dir = os.path.join(tempfile.gettempdir(), "update_extract")

            # Crear directorio temporal para extraer el ZIP
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            os.makedirs(temp_extract_dir)

            # Extraer el contenido del ZIP
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(temp_extract_dir)

            # Determinar la carpeta extraída
            extracted_content = os.listdir(temp_extract_dir)
            if not extracted_content:
                raise Exception("El ZIP está vacío")
            source_dir = os.path.join(temp_extract_dir, extracted_content[0])

            # Ruta del ejecutable actual
            executable = sys.executable

            # Ruta del script auxiliar (en helpers/)
            helper_script = os.path.join(app_dir, "helpers", "updater_helper.py")
            if not os.path.exists(helper_script):
                # Si no está presente, mostrar error y salir
                raise Exception(
                    "El script auxiliar 'helpers/updater_helper.py' no se encontró. Asegúrate de que esté empaquetado con la aplicación."
                )

            # Ejecutar el script auxiliar
            if platform.system() == "Windows":
                subprocess.Popen(
                    [sys.executable, helper_script, app_dir, source_dir, executable],
                    shell=False,
                )
            elif platform.system() == "Darwin":
                subprocess.Popen(
                    ["python3", helper_script, app_dir, source_dir, executable]
                )

            # Cerrar la aplicación actual inmediatamente
            self.page.window.close()

        except Exception as e:
            self.page.clean()
            self.page.add(
                ft.Text(f"Error durante la actualización: {str(e)}"),
                ft.TextButton("Cerrar", on_click=lambda _: self.page.window.close()),
            )
            self.page.update()
