# LESEN.md — Bedienung

Am einfachsten: **in den Strata-Ordner wechseln** und das Script mit
relativem Pfad aufrufen. Das Zielverzeichnis ist dann der aktuelle Ordner :

```bash
cd ~/Strata
bash ../strata_patch/apply_patch.sh check strata    # 1) testen
bash ../strata_patch/apply_patch.sh apply   strata  # 2) einspielen
bash ../strata_patch/apply_patch.sh revert  strata  # 3) zurücknehmen
```

(Der Pfad `../strata_patch/` gilt, wenn der Patch-Ordner direkt neben dem
Strata-Ordner liegt — sonst entsprechend anpassen.)

Syntax immer: **zuerst der Modus** (`check` / `apply` / `revert`), **dann die
Basis** (`strata` oder `polystrata`), **dann optional das Zielverzeichnis**.
 Von jedem beliebigen Ordner aus funktioniert auch:

```bash
bash /pfad/zu/strata_patch/apply_patch.sh check strata ~/Strata
```

## 1. Testen — passt der Patch auf meinen Stand?

`check` meldet `KP: konfliktfrei auf diesem Stand.` → einspielen.

Fehler mit Konfliktzeilen → der Baum steht nicht auf der Basis des Patches
(strata: main `146df3c4`, polystrata: main `4de79331`), oder ein alter Patch
liegt uncommittet darauf. Dann: `git stash` → `./update.sh` → erneut testen.
**Nie `git stash pop` nach dem update** — der alte Patch kollidiert mit dem
neuen, der ihn ersetzt.

## 2. Einspielen

`KP: angewandt (nicht committet).` — danach wie üblich bauen
(`./build.sh` bzw. das eigene Build-Kommando). Committen ist optional;
uncommittet lässt sich der Patch am saubersten wieder abnehmen.

## 3. Zurücknehmen

`KP: zurueckgenommen.` — der Baum ist wieder im reinen Upstream-Stand.

## 4. Der Ablauf vor `update.sh` (Regelfall)

```bash
cd ~/Strata
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
