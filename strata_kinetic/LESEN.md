# strata_kinetic_all.patch — Session-Lookup-Drafter (Kinetic-Port)

**Basis: `dbb2d168` (Engine 0.1.59.1).** Der Patch passt auch auf Bäume, die einen der
sieben Launcher-Commits dahinter noch nicht haben: auf `7726f80c` und `f33c8c30` ist er
geprüft konfliktfrei (upstream ändert in diesen Commits keine Engine-Datei).

Er ist **einschaltbar neben** `strata/strata_all.patch` (turbo/k3v8) und
`strata_split4/strata_split4_all.patch`. Beide Richtungen wurden geprüft: erst turbo dann
kinetic, erst kinetic dann turbo — jeweils konfliktfrei. Gemeinsam berührte Dateien:
`src/program/generate.cpp` (bei strata_all.patch), sonst keine.

**Ohne Einschaltung (Abschnitt 5) ändert der Patch nichts am Verhalten** — die neue Quelle
wird nur registriert, wenn `STRATA_LOOKUP_SESSION=1` gesetzt ist.

## 1) Prüfen, ob der Patch passt (nichts wird geändert)

```bash
cd ~/Machen/strata
bash ../strata_patch/apply_patch.sh check kinetic
```

`KP: konfliktfrei auf diesem Stand.` = passt. Er sagt etwas anderes = bitte den Text hier her.

## 2) Anwenden

```bash
cd ~/Machen/strata
bash ../strata_patch/apply_patch.sh apply kinetic
```

Zurücknehmen jederzeit:

```bash
cd ~/Machen/strata
bash ../strata_patch/apply_patch.sh revert kinetic
```

## 3) Bauen

```bash
cd ~/Machen/strata
./setup.sh --build --no-start
```

`setup.py` vergleicht den Quell-Hash mit `engine/BUILD.json` und baut nur die geänderten
Dateien, danach liegen `engine/strata` und `engine/libstrata_kq.so` frisch dort.
Hinweis: wenn `engine/strata` gerade läuft, kann der Zurückschiebe-Schritt mit
„Text file busy“ fehlschlagen — erst die Engine stoppen, dann bauen (oder manuell bauen
und die Datei mit `mv` austauschen, Abschnitt 3b).

3b) Manuell (nur wenn setup.sh nicht passt):

```bash
cd ~/Machen/strata
cmake -S . -B build -DCMAKE_CUDA_ARCHITECTURES=86 -DCMAKE_BUILD_TYPE=Release
.venv/bin/ninja -C build strata suffix_index_test suffix_drafter_test
```

`-DCMAKE_CUDA_ARCHITECTURES=86` ist auf einer A4000/RTX-3060-Pflicht: CMake stellt dort
von selbst auf 120, dann sterben die Kernel mit „no kernel image is available“.
Beim manuellen Bauen bleibt der alte Hash in `BUILD.json` stehen — das nächste
`setup.sh` baut dann einmal unnötig nach.

## 4) Testen

```bash
cd ~/Machen/strata
.venv/bin/ctest --test-dir build -R 'suffix_index_test|suffix_drafter_test|draft_policy_test' --output-on-failure
```

Erwartet: drei grüne Tests. `suffix_index_test` vergleicht den Automaton über 400
Zufallsschritte mit einer naiven O(n²)-Referenz und prüft zusätzlich die
Mindest-Treffer-Latte.

## 5) Einschalten (erst damit wirkt der Patch)

In der Config der Engine (z. B. `coder_local.json`):

```json
"env": { "STRATA_LOOKUP_SESSION": "1" },
```

und in `"args"` zwei Einträge mehr:

```json
"--lookup-chain", "6",
```

(`--lookup-chain` ist auf 0..7 begrenzt, `--lookup-chain-min` auf mindestens 3.)
Danach die Engine neu starten. Ohne diese beiden Stücke läuft die Engine wie vorher.

Auf 8gb gemessen: wiederholter Text wird etwa 7 % schneller (49,45 → 53,12 t/s), kurze neue
Prompts bleiben gleich oder etwas langsamer (32,00 → 31,10).

## 6) Vor `update.sh`

Reihenfolge immer: `revert` → `./update.sh` → `apply`. Nie `git stash pop` nach dem Update.
