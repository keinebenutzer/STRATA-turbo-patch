# Strata-Patch: der eine Patch für alle Komponenten

**Benutzung: siehe [LESEN.md](LESEN.md)** (Testen, Einspielen, Zurücknehmen).

Ein Groß-Patch pro Basisbaum, der alle gelieferten Komponenten vereint. Vor dem
Update einmal zurückziehen, `./update.sh` laufen lassen, wieder drauf — fertig.

**Stand 11.11.2026:** Upstream `main` = `7726f80c` (0.2.13.1 / engine **0.1.59.1**).
`strata/strata_all.patch` und `strata_split4/strata_split4_all.patch` sind auf diesen Stand
geschnitten und gebaut geprüft; `polystrata/polystrata_all.patch` bleibt auf `4de79331`
(PolyStrata-Upstream unverändert). Ein alter Patch auf einem neuen Stand **kollidiert
sichtbar**, nicht still — der Ablauf steht unten unter „Stand 11.11.2026“.

## Patches

| Datei | Basis (Stand des Patches) | Spitze | Inhalt |
|---|---|---|---|
| `strata/strata_all.patch` | Strata main `7726f80c` (0.2.13.1 / engine **0.1.59.1**) | `847040c4` | Warnbereinigung + turbo2 + turbo3 + k3v8 + setup-Menü (alle sechs KV-Modi) + Test-Nachzug |
| `polystrata/polystrata_all.patch` | PolyStrata main `4de79331` (0.1.45-poly.8) | `2fc9bab9` | dasselbe für das `strata`-Target **und** turbo2/turbo3 für die Kolibri-Engine `strata-poly` (`--kv turbo2\|turbo3`, Parity-Test `poly_turbo_parity`) |
| `strata_split4/strata_split4_all.patch` | Strata main `7726f80c` (0.2.13.1 / engine **0.1.59.1**) | `6fd5a3c5` | **4 x 16 GB: die All-Cards-Split-Engine.** IQ2_XS/IQ2_XXS-Leser, IQ3_S-Wandlung, Kartenvergleich und Karten-Fit nach den eigenen Zahlen der Maschine, `EC_POOLS` 4→8 mit `CardW` 896→1024, Q2_0-Shared-Expert-Schutz. **Andere Basis als die beiden oben** — eigene `strata_split4/LESEN.md`. |
| `strata_kinetic/strata_kinetic_all.patch` | Strata main `dbb2d168` (0.2.13.1 / engine **0.1.59.1**; passt geprüft auch auf `7726f80c` und `f33c8c30`) | `403d1267` | **Session-Lookup-Drafter (Kinetic-Port).** Suffix-Automaton über den ganzen Session-Verlauf statt nur über den Request, mit Kinetic's Lag (der neueste Token wird zurückgehalten und erst in die Anfrage genommen, bevor seine Fortsetzung gesagt wird). Wirkt in der `--lookup-chain`-Kette als zweite Quelle, eingeschaltet durch `STRATA_LOOKUP_SESSION=1`. 7 Dateien, +567/-1, eigene `strata_kinetic/LESEN.md`. |

Komponenten im Einzelnen (strata): 13 Build-Warnungen auf 0 · turbo2 (2-Bit,
320 B/Zelle) · turbo3 (3-Bit, 448 B/Zelle) · **k3v8** (asymmetrisch: rotierte
3-Bit-Schlüssel + 8-Bit-Werte, 752 B/Zelle — die llama.cpp `-ctk/-ctv`-Idee) ·
Launcher/`setup.py` auf alle Modi, inkl. interaktivem Menü · Parity bitgleich,
Engine-Läufe kohärent, Volltests grün (vorbestehende, ortsabhängige Ausnahmen
im README des Austauschordners nachgeliefert).

## Ablauf rund um `update.sh`

```bash
# im Strata-Arbeitsverzeichnis (main, unveränderte Upstream-Stände):
bash <dieses-repo>/apply_patch.sh revert strata .   # 1) Patch runter
./update.sh                                          # 2) Upstream ziehen
bash <dieses-repo>/apply_patch.sh apply  strata .   # 3) Patch wieder drauf
```

`check` vor `apply` zeigt konfliktfreie Anwendung an. Nach einem Upstream-Sprung
kann der Patch Konflikte melden — dann neu schneiden (Quellwahrheit sind die
Äste, siehe unten).

## Kolibri (`strata-poly`) — jetzt mit turbo

Der Patch bringt die Kolibri-Engine selbst mit: `--kv turbo2` (160 B/Zeile)
und `--kv turbo3` (224 B/Zeile) statt q8_0 (544 B/Zeile), mit Hadamard-
Rotation nach Strata-Vertrag, bitgleich parity-getestet (`poly_turbo_parity`).
Gemessen auf der A4000, volles 65k-Kontext (`--kv-whole`): q8_0 11714
residente Experten, turbo3 12176 (+462), turbo2 12267 (+553). Nur kolibri1;
qwen35moe/Gemma/GLM bleiben bei ihren Formaten.
- Die Patches sind an ihre Basis-Commits geheftet (Kontextzeilen). Auf
  fremden Ständen erst `check`en.
- k3v8 (asymmetrisch) gibt es für `strata`; die Kolibri-Engine hat stattdessen
  turbo2/turbo3 gerade — ihr KV-Umtauschkurs liegt dort schon im Optimum der
  gelieferten Stufen.

## Stand 08.11.2026 — neu geschnitten auf den neuen Upstream

Der Upstream sprang über die patchierten Stellen hinweg; der alte Patch
(Basis `54828c7e` / `a82999fd`) meldete deshalb auf Strata `setup.py:269` +
`src/core/verify.cpp:3725` und auf PolyStrata `engine.hpp:44` +
`kernels.cu:3815` + `main.cpp:1082` Konflikte. Beide Patches sind jetzt auf den
neuen Ständen geschnitten; die Äste wurden dafür auf den neuen main rebaseiert.

**Strata, zwei Fundstellen:**
- `verify.cpp` `raise_flag`: Upstream hat dieselbe Warnung selbst behoben und
  nach `include/strata/core/flag_order.hpp` (`flag_raise_max`) ausgelagert — der
  `volatile long* f`-Alias liegt dort innerhalb des `_WIN32`-Zweigs. Unser Hunk
  ist damit überholt und entfällt; die Datei folgt an dieser Stelle Upstream.
- `setup.py` `MIN_ENGINE`: Upstream schrieb die Versions-Historie-Zeile um
  (`v0.1.58`-Eintrag). Unsere Änderung betrifft nur die zwei darunterliegenden
  `KV_CELL_BYTES`-Zeilen — die sind unverändert drin, die Kontextzeile ist jetzt
  die Upstream-Zeile.

**PolyStrata, drei Fundstellen:**
- `engine.hpp` `KvFmt`: Upstream ergänzte `kAuto = -1` (Metal löst es vor der
  Allokation aus der Modellgeometrie auf), wir hatten `kTurbo2 = 4` /
  `kTurbo3 = 5` — beide Werte stehen jetzt in einer Zeile.
- `main.cpp` `--kv`-Hilfe: unser turbo2/turbo3-Text und Upstreams
  Metal-Standard-Zeile stehen direkt hintereinander.
- `kernels.cu` `attend_batch`: Upstream baute dort die HIP-Pfade `own`
  (eigene `hip_prefill_gemm`-Kernel) und `f32` (FP32-Produkte) ein; beide lesen
  den Cache als q8_0-Blöcke. Ein gepackter turbo2/turbo3-Cache ist das nicht
  (10/14 B je 32 Werte statt 16), deshalb ist `kq8.fmt == 1 && vq8.fmt == 1` als
  Bedingung ergänzt — Turbo-Caches nehmen auf HIP den fp16-Weg mit den
  Turbo-Dequant-Kernels. Auf CUDA sind `own`/`f32` ohnehin abgeschaltet.

**Prüfung des neuen Schnitts:** `check` konfliktfrei auf frischem main, `apply`
= Baum identisch zum Ast (Diff leer), `revert` = Baum sauber. Vollbau der Engine
(Release, CUDA 12.8, arch native, target `strata`): Exit 0, 0 Warnungen im Log.
`kv_turbo_parity`: alle 11 Prüfungen bitgleich (turbo2, turbo3, k3v8;
Rekonstruktionsfehler turbo3 1.3042, k3v8-V 0.0325).

## Stand 11.11.2026 — neu geschnitten auf 0.1.59.1 (`7726f80c`)

Der Upstream sprang erneut über die gepatchten Stellen hinweg (0.1.58 → 0.1.59.1,
900 geänderte Dateien). Der alte Schnitt (Basis `146df3c4`) meldete Konflikte in
`CMakeLists.txt` und `setup.py`. Neuer Schnitt: **23 der 25 Stellen fielen konfliktfrei**,
zwei brauchten Handarbeit:

- **`CMakeLists.txt` ist upstream ausgelagert.** Der ganze GPU-Engine-Block steht jetzt in
  `cmake/strata_gpu_engine.cmake` (`strata_gpu_engine()` / `strata_cpu_kernels()`). Unsere
  zwei Ergänzungen wandern dorthin: `kv_turbo.cu` + `kv_turbo3.cu` in die
  `strata_kernels`-Quelliste (neben `kv_q4.cu`) und der `kv_turbo_parity`-Test nach dem
  `kv_q4_parity`-Block. `CMakeLists.txt` selbst bleibt unverändert.
- **`setup.py` `MIN_ENGINE`:** Upstream schrieb die Versions-Historie-Zeile um
  (`v0.1.59`-Eintrag). Wir übernehmen Upstreams Zeile und behalten unsere zwei
  `KV_CELL_BYTES`-Zeilen darunter. Die übrigen `setup.py`-Stellen (`--kv`-Auswahl,
  `KV_WORDS`, `UD_FIT_KV_BYTES`, das interaktive Menü) fielen konfliktfrei.

**Prüfung dieses Schnitts** (A4000 sm_86, CUDA 12.8, Release): `check` konfliktfrei auf
frischem `7726f80c`, `apply` = Baum identisch zum Ast `0f2321d3` (Diff leer), `revert` sauber.
Vollbau `strata` + `kv_turbo_parity`: Exit 0, **0 Fehler, 0 Warnungen** — die
Warnbereinigung des Patches hält also auch auf 0.1.59.1. `kv_turbo_parity`: **alle 11
Prüfungen bitgleich** (turbo2, turbo3, k3v8; turbo3-Rekonstruktion 1,3042, k3v8-V 0,0325 —
dieselben Werte wie auf 0.1.58). Nachweis im Binary: `./engine/strata --help` zeigt
`k3v8 turbo2 turbo3`.

**Neu in 0.1.59: der Stack-Wächter — und wie unser Patch darin sauber wird.**
0.1.59 bringt `tools/check_cuda_spills.py`: jeder Kernel muss `STACK 0 LOCAL 0` haben,
sonst braucht er einen Mess-Eintrag in der `ALLOWED`-Tabelle. Unsere beiden
turbo3-Append-Kerneln verloren 16 Byte auf den Stack — Ursache war das address-genommene
`uint8_t bytes[12]` in `kv_turbo3.cu`. Der Patch gibt die 96 Bit Codestrom jetzt als zwei
Hälften (`Turbo3Group{d, lo, hi}`) zurück, `turbo3_store` zieht das einzelne Byte daraus;
kein Array, kein Stack. **Dieselben Werte**: alle 11 Parity-Prüfungen bleiben bitgleich, und
der Wächter meldet aus unseren Dateien **keinen einzigen Verstoß** mehr. Die vier, die auf
einer sm_86-Maschine bleiben, liegen in `dflash2.cu.o` (`gemm_rows_kernel` ×3,
`rope_table_inv_kernel`) — Upstream-Quellen, die unser Patch nicht anfasst; der
`cuda_spill_guard`-Test ist auf diesem Stand also auch ohne unseren Patch rot.

**Testsuite auf diesem Stand** (Vollbau 429/429, `ctest -j4`, 280 Tests): 172 bestanden,
108 fehlgeschlagen — und die ausgelesenen Gründe sind Ortsprobleme, keine Patchbrechen.
Der häufigste ist eine fehlgeschlagene Allokation (`out of memory`, `invalid argument` beim
Anlegen; die Testkarte trug einen laufenden Engine-Laden): er erwischt auch Upstream-eigene
Tests wie `kv_q4_parity`, `kv_q8_parity`, `kv_window_parity`, `kv_hybrid_parity` und die
`native_expert_parity_*`-Reihe, deren Parity-Zeilen selbst vorher durchgehen
(„0 of 36 token-sets differ in any bit“). Dazu Tests, die ein Modell brauchen, das hier nicht
liegt (`ple_parity`, `ple_iq4nl_dequant_test`) und die vier Upstream-Stack-Verstöße oben.
Unsere Tests laufen alle: `kv_turbo_parity` und `draft_kv_plan_test` bestanden.

**Fall beim Bauen (behoeben, betrifft jeden Build auf einer A4000):** CMake setzte
`CMAKE_CUDA_ARCHITECTURES` von selbst auf `120`. Der Lauf endete dann mit
`kv_append_turbo2 launch: no kernel image is available for execution on the device` —
gebaut war Blackwell, nicht sm_86. Explizit setzen: `-DCMAKE_CUDA_ARCHITECTURES=86`.

## Split4 (4 x 16 GB) — Stand 11.11.2026, läuft produktiv auf 2gb

Der Split-Patch wohnt in einem **eigenen Ordner mit eigener LESEN.md**, weil er eine andere
Basis hat (`7726f80c` = 0.1.59.1) und eine andere Engine betrifft (`src/split/`, der
All-Cards-Split statt des Layer-Split). Nachgezählt: er teilt **keine** Datei mit
`strata/strata_all.patch`, beide sind also kombinierbar — aber jeder für sich erst `check`en.

Gemessen auf 2gb (4 x A4000 16 GB, identischer Testlauf, temp 0, 900 Tokens):
Layer-Split 79,7 / 83,0 t/s → **Split 106,5 / 115,4 t/s**; GPU-Last 76/71/45/43 % →
**99/99/99/99 %**; `GPU-reach wait` 9,7–11,0 ms → 0,00–0,08 ms pro Fenster. Preis: Laden
205 s statt rund 60 s, VRAM pro Karte bis auf 230–247 MiB belegt.

Der 4-Karten-Pfad ist upstream unbestätigt — der Engine sagt wörtlich `sfnx: 4 cards builds and
passes the CPU checks but has not been validated on hardware`. Die Zahlen oben sind unser Befund.

## Kinetic (Session-Lookup-Drafter) — Stand 11.11.2026, gebaut und gemessen auf 8gb

Der Port kommt aus Kinetic (`crates/kinetic-models/src/speculative/session.rs`, Rust) und ist
in STRATA **abschaltbar**: ohne `STRATA_LOOKUP_SESSION=1` registriert er nichts, die Engine
verhält sich dann wie ohne Patch (gemessen: 48,89 t/s gegen 48,90 t/s im Original).

Er wirkt nur in der `--lookup-chain`-Kette (`propose_from_sources`): die eigene Request-Kette
bleibt die erste Quelle, der Session-Automaton wird danach gefragt und der längere Treffer
gewinnt. Deshalb gehört zum Einschalten immer beides — env-Variabel **und** `--lookup-chain`.

Gemessen auf 8gb (RTX 3060 12 GB, coder-iq1_m, `--kv k8v4`, `--spec 4` + MTP, temp 0,
Streaming-Decode ohne Prefill, Median aus vier Läufen):

| Zustand | Kurzprompts (117–220 Tokens) | Wiederholung: kalt → warm |
|---|---|---|
| Original (0.1.59.1, keine Kette) | 32,00 / 33,64 t/s | 46,93 → 49,45 |
| Patch drauf, **aus** | 31,48 t/s | 49,23 → 48,68 |
| nur `--lookup-chain 6` (Upstream-Kette, ohne Automaton) | — | 45,82 → 47,33 |
| `--lookup-chain 6` **+ Automaton** | 31,10 t/s | 45,49 → **53,12** |

Der Automaton gewinnt da, wo schon geschriebener Text wiederkehrt: warm **53,12 gegen 49,45 =
+7,4 %** gegenüber dem Original und **+12,2 %** gegenüber der Kette allein. Die Kette selbst
kostet beim Kaltstart etwa 3 % (mehr Zeilen im Verify-Fenster). Auf kurzen neuen Prompts ist
kein Gewinn, eher ein kleiner Verlust (31,10 gegen 32,00–33,64) — dort gibt es nichts
wiederzuerkennen. Der Offline-Test auf den echten Token-Dateien sagt dasselbe:
`benchy-long.ids` 8,67 gegen 8,56 tok/step, `parity_prompts.ids` **6,86 gegen 5,65** (+21 %),
bei neuem Text beieinander (1,09 / 1,58).

kinetic_switch_mode.sh kinetic|chain_only|installed|original`
(stoppt die Engine, tauscht `engine/strata` gegen `engine/strata.kinetic` /
`engine/strata.bak-kinetic`, stellt die Config um, startet neu). Config-Sicherung:
`coder_local.json.bak-pre-kinetic`.

**Fall beim Bauen eines zweiten Build-Ordners :** CMake findet dort weder Ninja noch nvcc
von selbst (Ninja liegt nur in `.venv/bin`, nvcc nur unter `/usr/local/cuda-12.8/bin`). Ein
frischer Ordner braucht deshalb explizit
`-DCMAKE_MAKE_PROGRAM=$PWD/.venv/bin/ninja -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc`
(dazu `-DCMAKE_CUDA_ARCHITECTURES=86`), sonst endet die Konfiguration mit
„No CMAKE_CUDA_COMPILER could be found“. Der vorhandene `build/` hat `STRATA_BUILD_TESTS=OFF`,
liefert also keine Test-Ziele — für `suffix_index_test` einen eigenen Ordner mit
`-DSTRATA_BUILD_TESTS=ON` nehmen und `build/` in Ruhe lassen.


