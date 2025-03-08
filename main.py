import flet as ft

from config import VERSION
from controllers import Updater


def main(page: ft.Page):
    """Interfaz principal con botón de verificación de actualizaciones"""
    page.title = "Flet App"

    def check_for_updates(e):
        updater.check_for_updates()

    page.add(ft.Text(f"MyApp v{VERSION}"))
    page.add(ft.ElevatedButton("Buscar actualizaciones", on_click=check_for_updates))

    updater = Updater(page)


ft.app(main)
