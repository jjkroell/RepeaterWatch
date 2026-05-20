from __future__ import annotations

import logging
import threading
import urllib.request

import base64

import config

logger = logging.getLogger(__name__)


def send_notification(title: str, message: str, priority: str = "default") -> None:
    if not config.NTFY_URL:
        return

    def _post():
        try:
            headers = {
                "Title": title,
                "Priority": priority,
                "Tags": "satellite_antenna",
            }
            if config.NTFY_USER and config.NTFY_PASSWORD:
                creds = base64.b64encode(f"{config.NTFY_USER}:{config.NTFY_PASSWORD}".encode()).decode()
                headers["Authorization"] = f"Basic {creds}"
            req = urllib.request.Request(
                config.NTFY_URL,
                data=message.encode(),
                headers=headers,
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
            logger.info("ntfy notification sent: %s", title)
        except Exception as e:
            logger.warning("ntfy notification failed: %s", e)

    threading.Thread(target=_post, daemon=True).start()
