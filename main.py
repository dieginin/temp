import flet as ft

from config import VERSION
from controllers import Updater


def main(page: ft.Page) -> None:
    page.title = "Flet App"

    page.add(ft.Text(f"MyApp v{VERSION}"))

    Updater(page)
