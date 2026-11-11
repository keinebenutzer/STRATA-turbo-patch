# strata_split4_all.patch — 4 x 16 GB (4 x RTX A4000): die All-Cards-Split-Engine zum Laufen bringen

**Basis: `7726f80c` = Engine 0.1.59.1 (Tag v0.2.13.1).** Getestet und produktiv auf 2gb
(4 x A4000 16 GB, sm_86). Ältere Fassung auf `f33c8c30` (0.1.59) ist überholt — die
EC_POOLS-Korrektur (Abschnitt 9) fehlt dort, ohne sie startet die Engine nicht.

Der Patch liegt in diesem Repo **neben** `strata/strata_all.patch` und berührt keine einzige
Datei von dem (nachgezählt: gemeinsame Dateien = keine). Beide sind kombinierbar, haben aber
verschiedene Basen — erst prüfen, ob der eigene Stand passt.

## 1) Prüfen, ob der Patch passt (nichts wird geändert)

```bash
cd ~/Machen/strata
bash ../strata_patch/apply_patch.sh check split4
```

`KP: konfliktfrei auf diesem Stand.` = passt. Er sagt etwas anderes = bitte den Text hier her.

## 2) Anwenden

```bash
cd ~/Machen/strata
bash ../strata_patch/apply_patch.sh apply split4
```

Zurücknehmen jederzeit:

```bash
cd ~/Machen/strata
bash ../strata_patch/apply_patch.sh revert split4
```

## 3) Das 4-Karten-Binary bauen (sm_86)

`setup.sh --build --no-start` baut den normalen Engine-Zweig, aber **nicht** die Split-Engine
(die ist opt-in). Deshalb einmal direkt:

```bash
cd ~/Machen/strata
export PATH=/usr/local/cuda-12.8/bin:$PATH
cmake -B build-split4 -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=ON \
  -DSTRATA_BUILD_SPLIT=ON -DSTRATA_SPLIT_CARDS="4" -DSTRATA_SPLIT_ARCH=86 \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc
cmake --build build-split4 --target strata-split-4 -j"$(nproc)"
```

Das Ergebnis heißt `strata-split-4` und muss neben die Engine, die die Run-Config nennt:

```bash
cp build-split4/src/split/strata-split-4 engine/strata-split-4-sm86
```

(Der Suchpfad der Run-Config ist `engine/strata-split-4-sm86`, dann `engine/strata-split-4`.)

## 4) Umgeschrieben werden muss die Run-Config trotzdem

`serve` wendet `split_engine: "on"` nicht selbst um — das macht nur der Terminal-Launcher. Für
serve direkt:

```bash
cd ~/Machen/strata
STRATA_SPLIT_CARD_OVERHEAD_GIB=4 .venv/bin/python split_rewrite.py strata-iq3_xxs_v7b_timing.json
```

- `use_split: True` + `WRITTEN:` → Serve neu starten.
- `use_split: False` → die `reasons:`-Zeile wörtlich hier her.
- Backup legt das Skript selbst an: `<config>.pre-split.json`; zurück: `cp <config>.pre-split.json <config>.json`.

## 5) Was der Patch ändert, und warum

1. **`IQ2_XS` / `IQ2_XXS` werden gelesen** (ggmls `vec_dot_iq2_xs_q8_1` / `vec_dot_iq2_xxs_q8_1`,
   schon in `vecdotq.cuh`): gguf-Typ-Enum + Blockgrößen (256 Werte in 66 / 74 Bytes) +
   Decode-Dispatch in `kernels.cu`. Nur CUDA — für HIP bleibt der Zweig aus (kein HIP-Leser).
2. **`IQ3_S` kann umgewandelt werden**: `tensor_convert.hpp` bekommt ggmls
   `dequantize_row_iq3_s` (mit ggmls eigener `iq3s_grid`). Damit sind die IQ3_S-Einbettungen
   und die 40 IQ3_S-Shared-Expert-Tensoren nicht mehr blockiert.
   Verifiziert: 16384 Zufallswerte, bitgenau identisch zu ggmls Referenz.
3. **Kartenvergleich nicht mehr wörtlich**: gleiche Karte und gleiche Compute-Fähigkeit, Größen
   bis 1,5 GiB auseinander, sind erlaubt. (Nachtrag: auf 2gb sind alle vier Karten gleich —
   16376 MiB, ECC aus. Die Toleranz bleibt als Absicherung, sie war dort nicht nötig.)
4. **Speicherbedarf darf gemessen statt geraten werden**:
   `STRATA_SPLIT_CARD_OVERHEAD_GIB=<zahl>` überschreibt die Kalibrierung von 9 GiB.
   Auf 2gb gemessen: 15,4 GiB pro Karte im laufenden Layer-Split, davon 11,64 GiB Experten
   (46,56 GiB / 4) → rund 3,8 GiB dichte Gewichte, Puffer und K/V-Pool. Ohne die Variable
   bleibt es beim alten Wert 9.

## 6) Warum es trotzdem mit „16 GiB nötig, 15 GiB frei“ ablehnte (aufgeklärt)

Nachmessen auf 2gb: **alle vier Karten sind gleich — 16376 MiB, ECC aus** (Karte 3 ebenfalls). Die
frühere Annahme, Karte 3 halte wegen ECC 1 GiB weniger, war falsch; die 15352 MiB waren ein Lesefehler
von mir (Spalte „used“ statt „total“).

Der eigentliche Grund ist die Rechenregel selbst. Sie zahlte **alle 46,56 GiB routed experts in die
Karten** — 11,64 GiB pro Karte — und legte 4 GiB Puffer drauf: 15,64 GiB. Die Karte bietet aber nur
16376 − 700 MiB Reserve = **15,31 GiB Raum**. Abweichung: 0,33 GiB.

Dabei legt der Engine-Loader gar nicht alle Experten in die VRAM: `src/split/src/model.cpp`
(`choose_residency`) parkt standardmäßig **3 GiB der kältesten Experten in festem Host-RAM**
(`FNX_EXPERT_RAM_GIB`, Standard 3,0; `off` + `FNX_ARENA=0` = nichts). Die Prüfregel wusste das nicht.
Der Patch rechnet denselben Anteil heraus:

| Host-Anteil Experten | Overhead | braucht pro Karte | Ergebnis |
|---|---|---|---|
| aus (`FNX_EXPERT_RAM_GIB=off`) | 4 GiB | 15,64 GiB | `use_split=False` (Ihre Meldung wörtlich reproduziert) |
| **3 GiB (Standard des Loaders)** | **4 GiB** | **14,89 GiB** | **`use_split=True`** |
| 8 GiB | 4 GiB | 13,64 GiB | `use_split=True` |
| 3 GiB | 9 GiB (alter Standard) | 19,89 GiB | `use_split=False` |

Nachziehen lässt sich das mit `fit_check_2gb.py` im selben Ordner:
`cd ~/Machen/strata && .venv/bin/python ~/Machen/strata_split4/fit_check_2gb.py`

Wichtig für den Testlauf: der Host-Anteil ist keine freie Leistung — die 3 GiB Experten werden bei
Bedarf über PCIe nachgeladen. Auf 2gb ist PCIe aber gemessen frei (0,00–0,08 ms pro Fenster), und der
laufende Layer-Split hält ohnehin 3 GiB kälteste Experten im RAM. Es ist also dieselbe Anordnung, die
bereits läuft, nur auf vier Karten verteilt.

## 7) Was jetzt zu tun ist

1. Patch neu ziehen (er enthält jetzt die Host-Anteil-Regel): `git apply -R` der alten Fassung, dann
   `git apply ~/Machen/strata_split4/strata_split4.patch` — oder die Patch-Datei überschreiben lassen.
2. Engine stoppen (die Karten müssen frei sein — die Regel rechnet mit dem *freien* Speicher).
3. `STRATA_SPLIT_CARD_OVERHEAD_GIB=4 .venv/bin/python split_rewrite.py strata-iq3_xxs_v7b_timing.json`
4. Kontext auf `131072`, `FNX_PF_MOE_Q8=1` in den `env`-Block, Serve starten.

## 8) Was der Patch **nicht** kann (ehrlich)

- Die Prompt-Kacheln (`moe_mma_iq.cuh`) gibt es für `IQ2_XS`/`IQ2_XXS` nicht. Der Prompt muss
  deshalb über die q8_1-Pfade laufen: `FNX_PF_MOE_Q8=1` in die Run-Config (`env`-Block).
- Der Speicher ist haarscharf: 11,64 GiB Experten + rund 4 GiB Rest gegen ~15,3 GiB nutzbare
  Karte. Mit 262144 Kontext wird es eng; **`--max-context 131072` ist der empfohlene Testwert**
  (die Split-Engine ist ohnehin nur bis 131072 gefahren).
- Ob der Split schneller ist als der laufende Layer-Split, ist damit noch nicht entschieden.
  Gemessener Engpass auf 2gb ist nicht PCIe, sondern `GPU-reach wait` (rund 44 % der Fensterzeit)
  und ungleiche Last (76 % / 71 % / 45 % / 43 %).

## 9) Der eigentliche Grund des Abbruchs: `EC_POOLS` (11.11., korrigiert)

Der Lauf starb mit `expert cache: more than 4 expert sizes`. Der Expert-Cache hat pro Karte ein
Feld pro **Byte-Größe** (`EC_POOLS`, upstream 4). Dieses Modell braucht **5**: die routed experts
treten in fünf verschiedenen Byte-Größen auf (IQ2_XXS 66, IQ2_XS 74, IQ2_S 88, IQ3_S 104,
IQ3_XXS 121 = IQ4_NL = Q2_0 nach dem Umpacken auf Q4_0). Nachgezählt aus dem GGUF selbst
(`tools/gguf_reader.py`, 10 Typ-Paare gate/up × down).

Der Patch auf `7726f80c` setzt deshalb `EC_POOLS = 8`. Das vergrößert `CardW` um 128 Bytes
(fünf Felder à 4 → 8), und `model.cpp` prüft die Größe hart: `static_assert(sizeof(CardW) == 896)`
→ **1024**. `card_fields` (das Halter-Bild) enthält von diesen fünf Feldern nichts, das Bild ändert sich nicht.

**Zwei Fallen, die den ersten Versuch umsonst machten:**
1. Das ausgelieferte Binary war aus dem **ungepatchten** Hauptbaum gebaut — die EC_POOLS-Änderung
   war nie im Binary, der Lauf zeigte deshalb weiter „more than 4“. Nach dem Patch immer aus dem
   gepatchten Baum bauen und `engine/strata-split-4-sm86` damit ersetzen.
2. `gguf.cpp`: ein **shared** expert in Q2_0 darf nicht den Routed-Expert-Abkürzungspfad
   (Umpacken auf Q4_0) nehmen — Shared-Experten brauchen Q8_0. Der Patch prüft jetzt erst die
   Zielgröße und lässt nur echte Routed-Experten umverpacken.

## 10) Messergebnis auf 2gb (11.11., identischer Testlauf, temp 0, 900 Tokens)

| Engine | decode | Last auf den vier Karten |
|---|---|---|
| Layer-Split (vorher) | 79,7 / 83,0 t/s | 76 % / 71 % / 45 % / 43 % |
| **All-Cards-Split (jetzt)** | **106,5 / 115,4 t/s** | **99 % / 99 % / 99 % / 99 %** |

Load-Zeit: 205 s (Layer-Split: rund 60 s). `GPU-reach wait` 0,00–0,08 ms pro Fenster
(Layer-Split: 9,7–11,0 ms). Experten-Cache-Treffer 99,9 %. Antworten inhaltlich geprüft
(17 · 23 = 391, Fibonacci 0,1,1,2,3,5,8,13, deutscher Satztest), 0 Fehler im Log.
Warnung des Engines, wörtlich: `sfnx: 4 cards builds and passes the CPU checks but has not been
validated on hardware` — der 4-Karten-Pfad ist upstream unbestätigt, die Zahlen oben sind unser Befund.
