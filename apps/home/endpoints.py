import os

import jinja2
from starlette.endpoints import HTTPEndpoint
from starlette.responses import HTMLResponse

from core.config import settings

ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        searchpath=os.path.join(os.path.dirname(__file__), "templates")
    )
)


class HomeEndpoint(HTTPEndpoint):
    async def get(self, request):
        template = ENVIRONMENT.get_template("home.html.jinja")

        content = template.render(
            title="ZIM-ZIM HR Boshqaruv Tizimi",
            subtitle="Xodimlar boshqaruvi uchun zamonaviy yechim",
            dev_telegram=settings.OPENAPI_CONTACT["url"],
            docs_url="/api/docs",
            web_app_url=settings.WEB_APP_URL,
            hcb_web_control_url="/static/HCBWebControl.exe",
        )

        return HTMLResponse(content)
