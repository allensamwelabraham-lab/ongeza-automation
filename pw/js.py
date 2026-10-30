"""Kuendesha JS za core/ (zilizoandikwa kwa Selenium: `return ...`, `arguments[0]`) ndani ya Playwright."""

WRAP = "(args) => (function () {\n%s\n}).apply(null, args)"


def run(target, body, *args):
    """target: Page au Frame. body: JS yenye `return` na `arguments[i]`, kama execute_script."""
    return target.evaluate(WRAP % body, list(args))
