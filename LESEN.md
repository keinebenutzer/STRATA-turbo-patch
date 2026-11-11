# LESEN.md — Bedienung

Am einfachsten: **in den Strata-Ordner wechseln** und das Script mit
relativem Pfad aufrufen. Das Zielverzeichnis ist dann der aktuelle Ordner —
ein drittes Wort braucht es nicht:

```bash
cd ~/Machen/Strata
bash ../strata_patch/apply_patch.sh check strata    # 1) testen
bash ../strata_patch/apply_patch.sh apply   strata  # 2) einspielen
bash ../strata_patch/apply_patch.sh revert  strata  # 3) zurücknehmen
```

(Der Pfad `../strata_patch/` gilt, wenn der Patch-Ordner direkt neben dem
Strata-Ordner liegt — sonst entsprechend anpassen.)

Syntax immer: **zuerst der Modus** (`check` / `apply` / `revert`), **dann die
Basis** (`strata`, `polystrata` oder `split4`), **dann optional das
Zielverzeichnis**.

```bash
bash /pfad/zu/strata_patch/apply_patch.sh check strata ~/Machen/Strata
```

## 1. Testen — passt der Patch auf meinen Stand?

`check` meldet `KP: konfliktfrei auf diesem Stand.` → einspielen.

Fehler mit Konfliktzeilen → der Baum steht nicht auf der Basis des Patches
(strata: main `7726f80c`, polystrata: main `4de79331`), oder ein alter Patch
liegt uncommittet darauf. Dann: `git stash` → `./update.sh` → erneut testen.
**Nie `git stash pop` nach dem update** — der alte Patch kollidiert mit dem
neuen, der ihn ersetzt.

## 2. Einspielen

`KP: angewandt (nicht committet).` — danach neu bauen. Der übliche Weg erkennt
die geänderten Quellen selbst (Hash der Engine-Quellen gegen `src` in
`engine/BUILD.json`) und kompiliert nur, was geändert ist:

```bash
./setup.sh --build --no-start
```

Das legt `engine/strata` (und `libstrata_kq.so`) neu ab und schreibt `BUILD.json`
neu. Von Hand über das vorhandene `build/`:
`cmake --build build --target strata -j"$(nproc)"`, dann
`cp build/strata engine/strata` und, wenn vorhanden,
`cp build/libstrata_kq.so engine/` — dabei bleibt der `src`-Hash in `BUILD.json`
stehen, beim nächsten `./setup.sh` wird also einmal umsonst neu gebaut.

**Beim ersten eigenen Bau (cmake neu konfigurieren):** CMake wählt auf manchen
Maschinen die falsche GPU-Architektur von selbst (auf einer A4000 wurde `120`
gesetzt). Der Bau gelingt, aber jede KV-Kernel-Ausführung endet mit
`no kernel image is available for execution on the device`. Deshalb explizit:
`-DCMAKE_CUDA_ARCHITECTURES=86` (A4000/A5000 = 86).

Nach dem Bau prüfen, dass der Patch wirklich drin ist (`--version` bleibt
unverändert, die Version hebt der Patch nicht):

```bash
./engine/strata --help | grep -o 'turbo2\|turbo3\|k3v8' | sort -u
```

Ohne Patch kommt nichts zurück, mit Patch erscheinen `k3v8 turbo2 turbo3`.
Committen ist optional; uncommittet lässt sich der Patch am saubersten wieder
abnehmen.

## 3. Zurücknehmen

`KP: zurueckgenommen.` — der Baum ist wieder im reinen Upstream-Stand.

## 4. Der Ablauf vor `update.sh` (Regelfall)

```bash
cd ~/Machen/Strata
bash ../strata_patch/apply_patch.sh revert strata    # 1) Patch runter
./update.sh                                          # 2) Upstream ziehen
bash ../strata_patch/apply_patch.sh apply     strata # 3) Patch wieder rauf
```

Meldet der Patch nach einem Upstream-Sprung Konflikte, ist der Upstream über
die gepatchten Stellen hinweggegangen: erst mit `check` prüfen, dann neu
schneiden lassen oder die betroffenen Dateien per `git checkout -- <datei>`
zurücksetzen und erneut `apply` versuchen.

## PolyStrata statt Strata

Überall einfach `strata` durch `polystrata` ersetzen. Der PolyStrata-Patch
deckt beide Engines des Forks ab (`strata`-Target und Kolibri `strata-poly`
mit `--kv turbo2|turbo3`).
