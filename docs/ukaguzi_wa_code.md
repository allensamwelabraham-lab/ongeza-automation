# Ukaguzi wa code ya ongeza-automation (30 Oktoba 2026)

Ukaguzi huu umefanywa kwa zana za ECC (`affaan-m/ECC`): maelekezo ya `python-reviewer`,
`security-reviewer` na `e2e-testing`, pamoja na `ruff` juu ya code yote (core/, tools/, tests/).
Kila file limesomwa. Makosa yaliyothibitishwa yamerekebishwa kwenye PR hii; mengine ni mapendekezo.

## Muhtasari

| Kipimo | Matokeo |
|---|---|
| Usalama (password, token, shell, eval) | Safi. Password inasomwa kutoka `.env` tu, `.env` na `.sessions` haziko kwenye git, token ya tester ina ruhusa 600 |
| Ruff (makosa ya Python) | Hakuna kosa la kweli. Imports 3 zisizotumika tu |
| Makosa ya usahihi wa matokeo | 5 yamepatikana na kurekebishwa (chini) |
| Hatari kwa watu halisi | 1: namba za simu za AUTO zinaweza kuwa za watu halisi (pendekezo 1) |

## Yaliyorekebishwa kwenye PR hii

### 1. `--module X` iliendesha pia modules zenye jina linaloanza na X (JUU)
`run_module` inachagua tests kwa `pytest -k <id>`, na `-k` inalinganisha sehemu ya jina.
Kwa hiyo `--module crud_ticket_index` iliendesha pia `crud_ticket_indexall`, na kwa `--crud`
iliunda records za AUTO kwenye module ambayo hukuiomba. Jozi zilizothibitishwa: ONGEZA 4,
JUMLA 4, PRO 2 (k.m. `zoho_sync` na `zoho_sync_reports`, `reports` na `crud_stock_stockreports`).
Imethibitishwa: tests 23 badala ya 11 kwa `crud_stockactivity_index`.
**Rekebisho:** `run_module` inapitisha `MODULE_IDS`, na `conftest.py` inaacha tests za modules nyingine.

### 2. Run iliyokufa ingeripoti matokeo ya run iliyopita (KATI)
Jina la file la matokeo (`results_1-176.xml`) ni lilelile kila run. pytest ikifa kabla ya
kuliandika, ripoti na `--push` vingesoma file la zamani kama matokeo mapya.
**Rekebisho:** file la zamani linafutwa kabla ya run; lisipoandikwa, run inasimama bila kutuma chochote.

### 3. Test iliyokuwa ERROR ilionekana Pass kwenye project tester (JUU)
Project tester inanakili Pass za test iliyopita kwenye test mpya. Test ikiwa ERROR (browser/muda),
push iliiruka, kwa hiyo Pass ya zamani ilibaki, kinyume na sheria yako "ERROR = Not tested".
**Rekebisho:** kwa ERROR, push inafuta result iliyonakiliwa ya scenario hiyo.

### 4. Push ingeweza kuunda results mbili (KATI)
POST iliyorudishwa 5xx au timeout ilirudiwa hadi mara 4, hata kama server ilishasave.
**Rekebisho:** POST/PUT/DELETE zinarudiwa kwa 429 (throttle) tu; GET bado zinarudiwa.

### 5. Filter ya ID ilikubali ID zisizo sahihi (KATI)
Test ya filter iliangalia kama ID "inayo" thamani, kwa hiyo filter ya ID 12 ikirudisha 112 na 120
ilipita. **Rekebisho:** kwa ID lazima ilingane kamili. Tahadhari: modules ambazo filter yao ya ID
inatafuta "inayofanana" sasa zitaonyesha Fail; hilo ni kosa la app linalostahili kuripotiwa.

### 6. Filter ilisomwa kabla ya jibu la server (KATI)
Baada ya "Apply Filter" test ilisubiri table ibadilike hadi sekunde 30 tu. Staging ikichelewa,
test ya "thamani isiyokuwepo" ilisoma rows za zamani na kuandika Fail ya uongo.
**Rekebisho:** inasubiri ombi la filter (Inertia) liishe kama Sort inavyofanya, hadi sekunde 60.

Haya hayajajaribiwa dhidi ya staging hapa (chromedriver inayolingana na browser haikuweza
kupakuliwa kwenye mazingira haya). Yamejaribiwa kwa: kukusanya tests (#1) na test ndogo ya push (#3).
Jaribu kwenye laptop yako kwanza: `bash run.sh --app ongeza --module agents --tests filter`.

## Mapendekezo (hayajabadilishwa)

1. **Namba za simu za AUTO (JUU, faragha).** `--crud` inajaza simu kama `07` + tarakimu 8 za muda
   (k.m. `0715xxxxxx`). Siku 10 hadi 19 za mwezi hizo ni namba za Tigo halisi. Fomu kama Create Agent
   zikituma SMS (password, karibu), mtu asiyehusika anaweza kupokea. Pendekezo: tumia namba yako ya
   majaribio kutoka `.env` (k.m. `AUTO_PHONE`), au uthibitishe na watu wa staging kuwa SMS zimezimwa.
2. **Buttons: `DANGER_PATH` ni fupi kuliko `DANGER_TEXT`.** Link ya icon tu (bila maandishi) yenye
   njia kama `/populate`, `/process`, `/calculate` ingebofywa kwa GET. Ongeza maneno hayo kwenye
   `DANGER_PATH` (core/controls.py).
3. **Export haina write guard na inakubali confirm.** Export ikiuliza "una uhakika?" inajibiwa Ndiyo.
   Ni salama kwa Export za kawaida, lakini Export inayotuma email ingeweza kutumwa.
4. **Sort inahakikisha mpangilio wa ID tu.** Columns nyingine zinapimwa kuwa table haiko tupu tu.
   Hili liko tayari kwenye `reports/mapungufu_ya_automation.md`.
5. **Server responses zote zinarekodiwa.** `_server_says_saved` inaangalia kila POST ya ukurasa;
   ombi lingine la nyuma lenye `"status":true` lingeweza kufanya fomu tupu ionekane imesave.
   Pendekezo: angalia majibu ya URL ya fomu tu.
6. **README inaonyesha `python`** badala ya `bash run.sh`. Kwenye laptop yako `python` haipo.
7. **Usafi:** `.idea/` imo kwenye git (mipangilio ya PyCharm), imports 3 zisizotumika
   (core/controls.py, core/list_checks.py).
