# Strata-Patch: der eine Patch für alle Komponenten

**Benutzung: siehe [LESEN.md](LESEN.md)** (Testen, Einspielen, Zurücknehmen).

Ein Groß-Patch pro Basisbaum, der alle gelieferten Komponenten vereint. Vor dem
Update einmal zurückziehen, `./update.sh` laufen lassen, wieder drauf — fertig.

## Patches

| Datei | Basis (Stand des Patches) | Spitze | Inhalt |
|---|---|---|---|
| `strata/strata_all.patch` | Strata main `54828c7e` | `200fe214` | Warnbereinigung + turbo2 + turbo3 + k3v8 + setup-Menü (alle sechs KV-Modi) + Test-Nachzug |
| `polystrata/polystrata_all.patch` | PolyStrata main `a82999fd` | `1c24b8d4` | dasselbe für das `strata`-Target **und** turbo2/turbo3 für die Kolibri-Engine `strata-poly` (`--kv turbo2\|turbo3`, Parity-Test `poly_turbo_parity`) |

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

