"""
Msingi mpya wa automation (Playwright). Unaendeshwa na:  bash run.sh --app ongeza --all --engine pw

Tofauti na core/ (Selenium):
* login moja kwa run nzima (storage state), kisha kila worker anatumia session hiyo
* write guard iko kwenye network (page.route): POST/PUT/DELETE inazuiwa kabla haijatoka
* tunasubiri jibu la server lenyewe badala ya time.sleep
* kosa likitokea: screenshot ya wakati huo + trace (hatua zote, network, console)
"""
