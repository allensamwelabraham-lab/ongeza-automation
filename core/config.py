import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# LOAD .env (bila dependency ya ziada)
# ============================================================

def _load_dotenv():
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


# ============================================================
# APPS
# ============================================================

APPS = {
    "jumla": {
        "name": "JUMLA",
        "base_url": os.getenv("JUMLA_URL", "https://jumla.ongeza.net"),
        "env_prefix": "JUMLA",
        "light_page": "/crud/ticket/index",
    },
    "ongeza": {
        "name": "ONGEZA",
        "base_url": os.getenv("ONGEZA_URL", "https://staging.ongeza.net"),
        "env_prefix": "ONGEZA_STAGING",
        "light_page": "/crud/ticket/index",
    },
    "ongezapro": {
        "name": "ONGEZA PRO",
        "base_url": os.getenv("ONGEZAPRO_URL", "https://ongezapro.ongeza.net"),
        "env_prefix": "ONGEZAPRO",
        # Reports za ONGEZA PRO ziko kwenye dashboard, si kwenye sidebar
        "extra_link_prefixes": ["/reports/"],
        "extra_pages": ["/reports"],
        # Kila login inatuma OTP; tests zitumie session iliyohifadhiwa
        "login_sends_otp": True,
    },
}


# Project mpya bila kubadilisha code: weka apps/<jina>.json (angalia apps/mfano.json.example).
# Fields: name, base_url, env_prefix, light_page, na (kama login si ya kawaida) login: {username, password, submit}.
def _load_app_files():
    import json

    for path in sorted((ROOT / "apps").glob("*.json")):
        config = json.loads(path.read_text())
        key = config.pop("key", path.stem)
        env_url = os.getenv(f"{config.get('env_prefix', key.upper())}_URL")
        if env_url:
            config["base_url"] = env_url
        APPS[key] = {**APPS.get(key, {}), **config}


_load_app_files()


def get_app(app_key):
    app = dict(APPS[app_key])
    app["key"] = app_key
    app["base_url"] = app["base_url"].rstrip("/")
    return app


def get_credentials(app_key):
    prefix = APPS[app_key]["env_prefix"]

    username = os.getenv(f"{prefix}_USERNAME") or os.getenv("ONGEZA_USERNAME")
    password = os.getenv(f"{prefix}_PASSWORD") or os.getenv("ONGEZA_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "Credentials hazijawekwa. Weka ONGEZA_USERNAME na "
            "ONGEZA_PASSWORD kwenye .env au environment."
        )

    return username, password


HEADLESS = os.getenv("HEADLESS", "0") == "1"
RUN_CRUD = os.getenv("RUN_CRUD", "0") == "1"
RUN_BUTTONS = os.getenv("RUN_BUTTONS", "0") == "1"
TIMEOUT = int(os.getenv("TIMEOUT", "20"))
LOGIN_TIMEOUT = int(os.getenv("LOGIN_TIMEOUT", "180"))
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "90"))

SESSIONS_DIR = ROOT / ".sessions"
MODULES_DIR = Path(os.getenv("MODULES_DIR", ROOT / "modules"))
REPORTS_DIR = ROOT / "reports"
