import os
import platform
import shutil
import subprocess
import zipfile

import flet as ft
import requests

from config import VERSION

# Configuración de GitHub
GITHUB_REPO = "dieginin/temp"  # Cambia esto a tu repo
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_latest_version():
    """Obtiene la última versión disponible en GitHub"""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        return data["tag_name"].lstrip("v"), data["assets"]
    except requests.RequestException as e:
        print("Error al verificar actualizaciones:", e)
        return None, None


def find_update_asset(assets):
    """Busca el archivo de actualización correspondiente al sistema operativo"""
    system = platform.system().lower()
    for asset in assets:
        if "build-macos" in asset["name"].lower() and system == "darwin":
            return asset["browser_download_url"], asset["name"]
        elif "build-windows" in asset["name"].lower() and system == "windows":
            return asset["browser_download_url"], asset["name"]
    return None, None


def download_update(url, filename, progress_callback):
    """Descarga el archivo de actualización con progreso"""
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


def apply_update(filename):
    """Extrae y reemplaza la aplicación con la nueva versión"""
    system = platform.system().lower()
    extract_path = os.getcwd()

    if filename.endswith(".zip"):
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        os.remove(filename)

    # Reemplazar archivos antiguos
    if system == "windows":
        new_exe = os.path.join(extract_path, "MyApp.exe")
        old_exe = os.path.join(extract_path, "MyApp_old.exe")

        if os.path.exists(new_exe):
            os.rename("MyApp.exe", old_exe)
            os.rename(new_exe, "MyApp.exe")
            os.remove(old_exe)

    elif system == "darwin":
        new_app = os.path.join(extract_path, "MyApp.app")
        old_app = os.path.join(extract_path, "MyApp_old.app")

        if os.path.exists(new_app):
            if os.path.exists(old_app):
                shutil.rmtree(old_app)
            os.rename("MyApp.app", old_app)
            os.rename(new_app, "MyApp.app")
            shutil.rmtree(old_app)


def update_app(page: ft.Page):
    """Interfaz gráfica de actualización con barra de progreso"""
    page.clean()
    page.title = "Actualizando..."
    progress = ft.ProgressBar(width=300)
    status = ft.Text("Buscando actualización...")
    page.add(status, progress)

    latest_version, assets = get_latest_version()
    if not latest_version or not assets:
        status.value = "Error al buscar actualizaciones."
        page.update()
        return

    parse_version = lambda v: tuple(map(int, v.split(".")))
    if parse_version(latest_version) <= parse_version(VERSION):
        status.value = "Ya tienes la última versión."
        page.update()
        return

    url, filename = find_update_asset(assets)
    if not url:
        status.value = "No se encontró una actualización para tu sistema operativo."
        page.update()
        return

    status.value = f"Descargando actualización v{latest_version}..."
    page.update()

    def update_progress(value):
        progress.value = value
        page.update()

    download_update(url, filename, update_progress)

    status.value = "Instalando actualización..."
    page.update()
    apply_update(filename)

    status.value = "Actualización completada. Reiniciando..."
    page.update()

    # Reiniciar la aplicación
    if platform.system().lower() == "windows":
        subprocess.Popen(["MyApp.exe"])
    else:
        subprocess.Popen(["open", "./MyApp.app"])
    os._exit(0)


def main(page: ft.Page):
    """Interfaz principal con botón de verificación de actualizaciones"""
    page.title = "Flet App"

    def check_for_updates(e):
        latest_version, _ = get_latest_version()
        if latest_version and latest_version > VERSION:
            page.add(ft.Text(f"¡Nueva versión {latest_version} disponible!"))
            page.add(
                ft.ElevatedButton(
                    "Actualizar ahora", on_click=lambda _: update_app(e.page)
                )
            )
        else:
            page.add(ft.Text("Estás en la última versión."))

    # page.add(ft.Text("MyApp Sin Actualizar"))
    page.add(ft.Text("MyApp Actualizada"))
    page.add(ft.ElevatedButton("Buscar actualizaciones", on_click=check_for_updates))


ft.app(main)
ft.app(main)
