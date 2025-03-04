import os
import sys
import time

import flet as ft
import requests
from config import VERSION

local_version = VERSION

def get_latest_release():
    # URL de la API para obtener la última versión del release de tu repositorio
    url = "https://api.github.com/repos/dieginin/temp/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        release_data = response.json()
        return release_data["tag_name"], release_data["assets"]
    else:
        return "No disponible", []


def download_asset(asset_url, file_name):
    # Realiza la solicitud para descargar el archivo
    response = requests.get(asset_url, stream=True)
    if response.status_code == 200:
        # Guarda el archivo descargado (reemplazando el existente)
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        return True
    else:
        return False


def restart_app():
    """Reinicia la aplicación"""
    time.sleep(1)  # Espera un poco antes de reiniciar
    os.execv(sys.executable, ["python"] + sys.argv)  # Reinicia el script


def compare_versions(current_version, latest_version):
    # Compara dos versiones en formato 'X.Y.Z'
    current_version_parts = [int(part) for part in current_version.split(".")]
    latest_version_parts = [int(part) for part in latest_version.split(".")]
    return latest_version_parts > current_version_parts


def main(page: ft.Page):
    page.title = "Flet Counter Example"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)

    # Obtener la última versión del release de GitHub
    latest_version, assets = get_latest_release()

    # Comparar las versiones
    if compare_versions(local_version, latest_version):
        # Si la versión más reciente es mayor que la local, habilitar la descarga
        update_available = True
    else:
        # Si la aplicación ya está actualizada
        update_available = False

    def minus_click(e):
        txt_number.value = str(int(txt_number.value) - 1)
        page.update()

    def plus_click(e):
        txt_number.value = str(int(txt_number.value) + 1)
        page.update()

    def download_click(e):
        if assets:
            # Tomamos el primer asset (puedes modificar esto si hay más de un asset)
            asset_url = assets[0]["browser_download_url"]
            file_name = assets[0]["name"]

            # Descargar y reemplazar el archivo
            success = download_asset(asset_url, file_name)
            if success:
                page.add(
                    ft.Text(
                        f"Archivo {file_name} descargado y reemplazado exitosamente.",
                        size=18,
                    )
                )

                # Reiniciar la aplicación
                restart_app()
            else:
                page.add(ft.Text("Error al descargar el archivo.", size=18))
        else:
            page.add(ft.Text("No hay archivos disponibles para descargar.", size=18))

    # Mostrar mensaje si la app está actualizada o no
    if update_available:
        update_message = ft.Text(
            f"Hay una nueva versión disponible: {latest_version}",
            size=20,
            weight=ft.FontWeight.BOLD,
        )
        update_button = ft.ElevatedButton(
            "Descargar última versión", on_click=download_click
        )
    else:
        update_message = ft.Text(
            f"Tu aplicación está actualizada. Versión actual: {local_version}",
            size=20,
            weight=ft.FontWeight.BOLD,
        )
        update_button = ft.ElevatedButton(
            "No hay actualizaciones disponibles", disabled=True
        )

    page.add(
        ft.Row(
            [
                ft.IconButton(ft.Icons.REMOVE, on_click=minus_click),
                txt_number,
                ft.IconButton(ft.Icons.ADD, on_click=plus_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        update_message,
        update_button,
    )


ft.app(main)
