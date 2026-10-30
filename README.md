# Ongeza Automation (Selenium + pytest)

Automation tests za **JUMLA**, **ONGEZA (staging)** na **ONGEZA PRO**, kwa mtindo wa
`login_once.py` na `test_agent.py` zako (session ya cookies + localStorage, select2 helpers).

| App | URL | Folder |
|---|---|---|
| JUMLA | https://jumla.ongeza.net | `tests/jumla/` |
| ONGEZA | https://staging.ongeza.net | `tests/ongeza/` |
| ONGEZA PRO | https://ongezapro.ongeza.net | `tests/ongezapro/` |

## 1. Setup (mara moja)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # kisha weka ONGEZA_PASSWORD kwenye .env
```

Password haiko kwenye code. Inasomwa kutoka `.env` au environment variables
(`ONGEZA_USERNAME`, `ONGEZA_PASSWORD`). `.env` iko kwenye `.gitignore`, usiicommit.

## 2. Gundua modules za kila app (baseline)

```bash
python -m tools.discover --app all --workers 2   # au --app jumla / ongeza / ongezapro
python -m tools.discover --app ongeza --only /crud/district /crud/sale   # baadhi tu
```

Script inalogin, inasoma **sidebar** yote, inafungua kila ukurasa (bila kusave) na
inaandika `modules/<app>.json` + `modules/<app>.md`. Kwa kila module inahifadhi:
aina ya ukurasa, heading, columns, idadi ya records, sort keys, filters, link ya
Create/Add na fields za form. Tests zinalinganisha app na baseline hii.

Aina za kurasa (`core/pages.py`):

| Aina | Inapatikana wapi | Mfano |
|---|---|---|
| `vue` | ONGEZA/JUMLA mpya: Filter / Sort / Per Page / Export / + Add | Agents, Customers, Sales |
| `grid` | ONGEZA/JUMLA za zamani (Yii2 GridView, "Showing 1-20 of N") | District, Payg Devices |
| `spa` | ONGEZA PRO (SGL) | Statuses, Logs, Reports |
| `table` / `page` | reports, forms, maps, dashboards | Sales Per Month |

Usitumie `--workers` nyingi: staging inaanza kurudisha **504 Gateway Time-out**
browsers nyingi zikifungua reports nzito pamoja.

Ikiwa app imeongeza module mpya, endesha discover tena. Mipangilio yako kwenye JSON
(`skip`, `notes`, `ignore_error_text`, `add_path`, `validate_empty_submit`) haifutwi.

## 3. Endesha tests

```bash
pytest                                  # apps zote
pytest tests/ongeza                     # app moja
pytest -m smoke                         # kurasa, columns, sort, filter, view
pytest -m forms                         # Create/Add forms
pytest -k agents                        # module moja kwa jina
pytest -n 2 tests/ongeza                # browsers 2 kwa pamoja (pytest-xdist)
HEADLESS=1 pytest --junitxml=reports/results.xml --html=reports/report.html
python -m tools.report reports/results.xml   # -> reports/errors.md (errors kwa kila app)
RUN_CRUD=1 pytest -m crud               # tests zinazounda data (AUTO...)
```

Test ikishindwa, screenshot inahifadhiwa `reports/screenshots/`. Test inayoshindwa
inamaanisha **app ina tatizo** (au imebadilika tangu baseline); ujumbe unaeleza
module, URL na tatizo.

## 3a. Test module moja na ripoti yake (kwa project tester)

**Njia rahisi:** `./run.sh` inawasha venv yenyewe (na kuitengeneza mara ya kwanza), kwa hiyo
huhitaji `source venv/bin/activate` wala `python`:

```bash
bash run.sh --app jumla --list
bash run.sh --app jumla --all --group Worker --crud
```

(Ukifungua zip, run.sh inaweza kukosa ruhusa ya execute, kwa hiyo tumia `bash run.sh ...`.)

Au kwa venv mwenyewe:

```bash
python -m tools.run_module --app ongeza --list            # modules zote na namba zake
python -m tools.run_module --app ongeza --module Agents   # kwa jina, id, path au namba
python -m tools.run_module --app ongeza --module 8
python -m tools.run_module --app ongeza --module "All Customers" --crud   # pamoja na kuunda na kuedit (AUTO)
python -m tools.run_module --app jumla --module "All Customers" --crud --edit-real   # edit customer aliyepo, kisha inamrudisha
```

Kwa `bash run.sh` ni vilevile, k.m. `bash run.sh --app jumla --module "All Customers" --crud --edit-real`.

Inaendesha tests zote za module hiyo tu (kufunguka, columns, records, page 2, sort,
filter, view, fomu ya Add, na tests za mkono kama `test_agents.py`) kisha inaandika
`reports/modules/<app>/<module>/`:

| File | Matumizi |
|---|---|
| `report.html` | fungua kwenye browser au print |
| `report.md` | jedwali la kunakili |
| `report.csv` | fungua kwa Excel / import kwenye project tester |
| `screenshots/` | picha za test zilizoshindwa |

Kila test case ina ID (TC-01...), hatua, matokeo yanayotarajiwa, matokeo halisi na
status (PASS / FAIL / SKIP). Module zilizowekwa `skip` (slow) zinaendeshwa pia ukizichagua.

### Modules zote, kila moja ripoti yake

```bash
python -m tools.run_module --app ongeza --all                      # modules zote (bila slow)
python -m tools.run_module --app ongeza --all --from 1 --to 40     # kwa awamu (namba za --list)
python -m tools.run_module --app ongeza --all --from 41 --to 100
python -m tools.run_module --app ongeza --all --include-slow       # pamoja na slow
python -m tools.run_module --app ongeza --all --include-reports    # pamoja na kurasa za reports (zinarukwa kwa default)
python -m tools.run_module --app ongeza --all --group Worker       # kundi moja la menu tu
python -m tools.run_module --app ongeza --all --failed --crud      # rudia zilizofail run iliyopita tu
python -m tools.run_module --app ongeza --all --only 6,40,116-120  # namba hizi za --list tu
python -m tools.run_module --app ongeza --all --workers 2          # browsers 2 sambamba (usizidi 2)
python -m tools.run_module --app jumla --all --crud --tests edit     # rudia test ya Edit tu (matokeo mengine yanabaki)
python -m tools.run_module --app jumla --all --crud --tests add,edit # Add na Edit tu
python -m tools.run_module --app jumla --module "All Customers" --crud --tests edit --edit-real   # Edit tu ya module moja
python -m tools.run_module --app ongezapro --all --buttons            # bofya kila button ya kila module
python -m tools.run_module --app ongezapro --all --crud --edit-real --buttons   # kila kitu
```

Kila module inapata folder yake ya ripoti kama hapo juu, na pia:

| File | Matumizi |
|---|---|
| `reports/modules/<app>/index.html` | muhtasari: kila module, Pass/Fail, kilichoshindwa, link ya ripoti yake |
| `reports/modules/<app>/all_cases.csv` | test cases za modules zote kwenye file moja |

Ukiendesha kwa awamu (`--from/--to`), index inaunganisha matokeo ya awamu zote
(`summary.json`). Takriban dakika 1 kwa kila module, browser moja.

### Tuma matokeo kwenye project tester

Baada ya `--all` (au `--module`), tuma `reports/modules/<app>/summary.json` kwenye backend ya
project tester (weka `TESTER_API_URL`, `TESTER_USERNAME`, `TESTER_PASSWORD` kwenye `.env`):

```bash
python -m tools.push_to_tester --app jumla --dry-run      # onyesha tu kitakachoundwa (hakuna POST)
python -m tools.push_to_tester --app jumla                # tuma modules zote
python -m tools.push_to_tester --app jumla --module 12    # module moja (namba/id/jina)
```

Project = app, Module = kabla ya ` > `, SubModule = ukurasa, Feature/Scenario = kichwa cha
test case, Expectation = matokeo yanayotarajiwa, Test = push moja, Result = Pass/Fail (SKIP
inarukwa). Kinachokuwepo kinatafutwa kwa jina kwanza, hivyo kuendesha tena hakurudufu.
Login ya backend inatuma OTP: script inauliza OTP (au weka `TESTER_OTP`), kisha token
inahifadhiwa `.sessions/tester_token`. Screenshots za Fail zinajaribiwa; zikikataliwa script
inaendelea.

## Tests zilizopo kwa kila app

| File | Inapima nini | Inasave data? |
|---|---|---|
| `test_login.py` | login sahihi, password mbaya, fields tupu, dashboard | Hapana |
| `test_modules.py` | kwa **kila module**: ukurasa unafunguka bila error (500/504/404/SQL), heading na aina ni zile zile, columns hazijapotea, records zinaonekana, page 2 inafanya kazi, sort ASC/DESC inapanga ID, filter kwa thamani halisi inarudisha rows sahihi tu, filter ya thamani isiyokuwepo inarudisha 0, row inafunguka kwenye view | Hapana |
| `test_forms.py` | kila Create/Add form: inafunguka, fields zote zipo, form tupu inakataliwa | Hapana (write guard) |
| `test_forms.py::test_create_form_saves` | kila Create/Add form: **inajaza kila field kwa data ya AUTO** (text, namba, tarehe, phone, email, select/select2), inabofya Save, inahakikisha hakuna error/validation na record inaonekana kwenye list | Ndiyo, `--crud` / `RUN_CRUD=1` |
| `test_forms.py::test_edit_form_saves` | kila fomu yenye Add: inafungua **Edit** ya record ya AUTO (iliyoundwa na test ya Add; inaitafuta page 1, kisha kwa ID DESC, kisha page ya mwisho), inabadilisha field moja ya maandishi, inabofya Update/Save, kisha inafungua Edit tena kuhakikisha thamani mpya imehifadhiwa na fields nyingine hazijafutwa. Ikiwa fomu ya Edit inaonyesha data ya record nyingine, inasimama bila kusave. Fomu ikidai fields ambazo record haina, inazijaza kwa AUTO, inajaribu tena na kuripoti kama FAIL yenye maelezo | Ndiyo, `--crud` / `RUN_CRUD=1` |
| `ongeza/test_agents.py` | Agents list, fields za Create Agent, Ward inaload baada ya District, **create agent** kamili | Create tu `RUN_CRUD=1` |
| `ongeza/test_customers.py` | filter kwa Phone, filter kwa tarehe (From/To), view ya customer | Hapana |
| `ongeza/test_customer_create.py` | kuunda customer: kujaza fomu yote, Save, kumtafuta kwenye list | Ndiyo, `RUN_CRUD=1` |

Usalama wa data:
- Links za `logout`, `delete`, `export`, `download`, PDF/Excel haziguswi.
- Kabla ya kubofya Save kwenye form tupu, `core/guard.py` inazuia ukurasa kutuma
  POST/PUT/DELETE yoyote. Form ikikosa validation, test inashindwa na kueleza
  ingetuma nini, lakini hakuna kinachosaviwa.
- Data yoyote inayoundwa na `crud` tests ina prefix **AUTO** (k.m. `AUTO1005143012`).
- Edit inagusa records za AUTO tu. Kama hakuna record ya AUTO (k.m. Customer, kwa sababu Add ya
  Customer inaleta error ya server), test inaruka. `--edit-real` (`EDIT_REAL_RECORDS=1`) inaruhusu
  kuedit record ya kwanza ya list: inaongeza `AUTO...` kwenye field moja (k.m. Land Mark), inasave,
  inakagua, kisha **inarudisha thamani zote za zamani** na kuhakikisha zimerudi. Kabla ya kusave inahakikisha
  fomu ni ya row iliyochaguliwa. Isiporudisha, test inashindwa na ujumbe `TAHADHARI` unaosema field gani
  irudishwe kwa mkono. Records halisi za Users, Roles na Permissions haziguswi hata kwa `--edit-real`.
  Matokeo ya Edit ya apps zote tatu na makosa ya app yako kwenye `reports/makosa_ya_edit.md`.
- `--crud` haisavi fomu zinazotuma SMS/notifications, malipo, upload/import au menu za mfumo
  (`CRUD_SAVE_EXCLUDE` kwenye `core/list_checks.py`). Kuruhusu moja: weka `"crud_save": true`
  kwenye module hiyo ndani ya `modules/<app>.json`.
- ONGEZA PRO inatuma **OTP** kila login. Tests zinatumia session iliyohifadhiwa
  (`.sessions/`); `test_login_valid` ya ONGEZA PRO inaendeshwa tu `RUN_OTP_LOGIN=1`.

## Kuongeza test ya kina kwa module

Nakili mtindo wa `tests/ongeza/test_agents.py` ndani ya folder ya app husika
(k.m. `tests/jumla/test_orders.py`), tumia fixtures `driver` (browser iliyologin) na `app`,
na helpers za `core/helpers.py` (`select2_option`, `select2_first_option`,
`wait_for_real_option`, `describe_form`, `find_submit_button`).
Weka `@pytest.mark.crud` kwenye test yoyote inayosave data.

## Mpangilio wa code

```
core/config.py     URLs, credentials (env), timeouts
core/driver.py     Chrome driver (HEADLESS, CHROME_BINARY, CHROMEDRIVER)
core/session.py    login, save/restore session (.sessions/<app>/)
core/helpers.py    select2, error detection, tables, forms
core/modules.py    kugundua menu + modules/<app>.json
core/pages.py      page objects: vue / grid / spa (table, sort, filter, pagination)
core/list_checks.py checks za kina za kila module (tests zinazitumia)
core/guard.py      write guard: inazuia form kutuma data
tools/report.py    ripoti ya errors kutoka results.xml
tools/run_module.py tests + ripoti ya module moja (au zote kwa --all)
tools/discover.py  kugundua modules
tools/login_once.py login na kuhifadhi session tu
tests/<app>/       tests za kila app
```

## Vigeu (environment variables)

| Variable | Default | Maana |
|---|---|---|
| `ONGEZA_USERNAME` / `ONGEZA_PASSWORD` | – | credentials za apps zote |
| `JUMLA_USERNAME`, `ONGEZAPRO_PASSWORD`, `ONGEZA_STAGING_PASSWORD` ... | – | credentials tofauti kwa app moja |
| `JUMLA_URL`, `ONGEZA_URL`, `ONGEZAPRO_URL` | URLs za juu | kubadilisha mazingira |
| `HEADLESS` | `0` | `1` = bila dirisha |
| `RUN_CRUD` | `0` | `1` = endesha tests za `crud` |
| `EDIT_REAL_RECORDS` | `0` | `1` = Edit inaweza kuedit record halisi (kisha kuirudisha) kama hakuna ya AUTO |
| `TIMEOUT` / `LOGIN_TIMEOUT` / `PAGE_LOAD_TIMEOUT` | `20` / `180` / `90` | sekunde za kusubiri |
| `RUN_OTP_LOGIN` | `0` | `1` = endesha login test ya ONGEZA PRO (inatuma OTP) |
| `MODULES_DIR` | `modules/` | folder mbadala ya baseline JSON |
| `CHROME_BINARY` / `CHROMEDRIVER` | – | njia za Chrome/driver maalum |
| `TESTER_API_URL` / `TESTER_USERNAME` / `TESTER_PASSWORD` | – | project tester (`tools.push_to_tester`); hiari `TESTER_OTP`, `TESTER_TOKEN` |

## Kila button (`--buttons`)

`--buttons` (au `--tests buttons`) inaongeza test ya `test_all_buttons`: kila button, tab, link, dropdown,
pagination na Export ya ukurasa wa module inabofywa moja moja (`core/controls.py`). Write guard inazuia
kusave, na buttons hatari (Delete, Sync, Push, Pay, Approve, Send, Populate, Process ...) hazibofywi.
Export lazima ipakue file. Kila module ina muda wa juu wa dakika 6 (`BUTTONS_MODULE_SECONDS`).
Matokeo na makosa yaliyopatikana: `reports/makosa_ya_buttons.md`.
# ongeza-automation

## Msingi mpya: Playwright (inachaguliwa yenyewe)

Huhitaji kuchagua chochote: amri zilezile (`bash run.sh --app ongeza --all`, `--module`, `--failed`,
`--push`) sasa zinatumia Playwright yenyewe kwa JUMLA na ONGEZA, kwa sababu ni ya haraka na sahihi zaidi.
`--crud`, `--buttons` na ONGEZA PRO bado zinatumia Selenium kama mwanzo. Kulazimisha moja:
`--engine selenium` au `--engine pw`.


JUMLA na ONGEZA zinatumia tests zilezile (`tests_pw/`). Selenium inaendelea kufanya kazi bila `--engine pw`.

```bash
bash run.sh --app ongeza --engine pw --all --from 1 --to 10              # tests zote za list
bash run.sh --app jumla --engine pw --all --tests data --workers 2       # hatua ya 2 tu
bash run.sh --app jumla --engine pw --module agents
```

**Hatua ya 1** (`tests_pw/test_lists.py`): page, columns, records, pagination, sort ya UI, filter, view.

**Hatua ya 2** (`tests_pw/test_data.py`, `--tests data`): inalinganisha na data halisi ya server
(Inertia JSON ya ukurasa), si maandishi ya skrini tu:

| Test | Inapima |
|---|---|
| `test_sort_all_columns` | Kila column ambayo server inasema inapangika, ASC na DESC |
| `test_filters_all` | Kila field ya Filter (maandishi, dropdown, From/To): UI inatuma filter, na kila row inayorudi inalingana |
| `test_per_page` | Per Page 10 na 50: server na table zinaonyesha idadi sahihi |
| `test_pagination_data` | Page 2 na ya mwisho: idadi sahihi, hakuna record inayojirudia |
| `test_view_matches_row` | View ya row ya kwanza inafungua record ileile (id) na inaonyesha taarifa zake |

Majina mafupi ya `--tests`: `data`, `sortall`, `filters`, `perpage`.

* Login mara moja kwa run nzima (`.sessions/<app>/pw_state.json`).
* Write guard iko kwenye network: hakuna POST/PUT/DELETE inayotoka (isipokuwa za kusoma list).
* Test isiyomaliza (staging haikujibu) inarudiwa mara 1; ikibaki hivyo ni **Not tested**, si Fail.
* Test ikishindwa: screenshot ya wakati huo (`reports/screenshots/`) na trace (`reports/traces/`).
  Fungua trace: `venv/bin/python -m playwright show-trace reports/traces/<jina>.zip`

### Kutest project mpya kwa code hii hii

1. Nakili `apps/mfano.json.example` kuwa `apps/<jina>.json` na ujaze `name`, `base_url`, `env_prefix`
   (na `login` kama fomu ya login si ya kawaida).
2. Weka `<ENV_PREFIX>_USERNAME` na `<ENV_PREFIX>_PASSWORD` kwenye `.env`.
3. Tengeneza map ya modules: `bash run.sh` haifanyi hili, tumia `venv/bin/python -m tools.discover --app <jina> --workers 2`.
4. Endesha: `bash run.sh --app <jina> --engine pw --all`.

Tests za hatua ya 2 zinasoma kila kitu (sort, filters, pagination) kutoka kwenye ukurasa wenyewe, kwa hiyo
app yoyote ya Inertia/Vue yenye muundo huu inapimwa bila kubadilisha code.
