"""
Kila button ya kila module ya ongeza inabofywa: tabs, filters, sort, per page, pagination, View, Edit,
Add (fomu inafunguka tu), Export (file inapakuliwa), dropdowns na links za ukurasa.
Buttons hatari (Delete, Sync, Pay, Send, Approve ...) hazibofywi, na write guard inazuia kusave.
Inaendeshwa tu RUN_BUTTONS=1 (tools.run_module --buttons).
"""

import pytest

from core import controls
from core import list_checks as lc


APP = "ongeza"
pytestmark = pytest.mark.buttons


@pytest.mark.parametrize("module", lc.params(APP, lambda m: not m.get("error")))
def test_all_buttons(driver, app, module):
    controls.check_all_buttons(driver, app, module, lc.open_module)
