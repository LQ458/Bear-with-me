"""Vercel entrypoint for the Whoops Tag API."""

from code.mvp.api import create_app
from code.mvp.config import Settings
from code.mvp.container import create_services


app = create_app(create_services(Settings.from_env()))
