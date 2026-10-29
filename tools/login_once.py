"""
Login mara moja na kuhifadhi session (cookies + localStorage) kwenye .sessions/<app>/.
Tests zitatumia session hii badala ya kulogin kila mara.

    python -m tools.login_once --app ongeza
    python -m tools.login_once --app all
"""

import argparse

from core.config import APPS, get_app
from core.driver import create_driver
from core.session import login


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True, choices=list(APPS) + ["all"])
    args = parser.parse_args()

    for app_key in (APPS if args.app == "all" else [args.app]):
        driver = create_driver()
        try:
            login(driver, get_app(app_key))
        finally:
            driver.quit()


if __name__ == "__main__":
    main()
