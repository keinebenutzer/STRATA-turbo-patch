"""Regelpruefung mit den nachgemessenen Fakten (09.11.2026, 2gb): vier gleiche Karten 16376 MiB, ECC aus.
Zeigt, woran es lag: die Regel zahlte alle 46,56 GiB Experten in die Karten, obwohl der Loader 3 GiB davon
in Host-RAM legt (FNX_EXPERT_RAM_GIB)."""
import os
import sys

sys.path.insert(0, "/work/hermes/home/strata_clone")
import strata_control.split_engine as SE

GIB = 1024 ** 3
model = SE.ModelFacts(
    routed_types={"IQ4_NL": 18, "IQ2_XS": 20, "Q2_0": 30, "IQ2_XXS": 18, "IQ3_S": 26, "IQ2_S": 20, "IQ3_XXS": 12},
    routed_bytes=int(46.56 * GIB),
    embd_type="IQ3_S",
    shexp_types={"IQ4_NL": 40, "BF16": 48, "IQ4_XS": 31, "IQ3_S": 40, "Q4_K": 19, "Q5_K": 2, "Q2_0": 8, "Q6_K": 4},
    embd_ram_bytes=int(13.67 * GIB),
    layers=48, experts=512, ple_type="IQ4_NL", output_type="Q5_K",
)

cards = [SE.Card(index=i, name="NVIDIA RTX A4000", vram_mib=16376, cc=86, vendor="nvidia", arch="", free_mib=16376)
         for i in range(4)]

print("Karten: vier Mal 16376 MiB, ECC aus (nachgemessen); Raum je Karte = 16376 - 700 Reserve = 15,31 GiB")
print("Experten gesamt: %.2f GiB\n" % (model.routed_bytes / GIB))
for label, env in (("Host-Anteil aus (FNX_EXPERT_RAM_GIB=off)", {"FNX_EXPERT_RAM_GIB": "off", "FNX_ARENA": "0"}),
                   ("Host-Anteil 3 GiB (Standard des Loaders)", {}),
                   ("Host-Anteil 8 GiB", {"FNX_EXPERT_RAM_GIB": "8"})):
    for overhead in ("9", "4"):
        os.environ.clear()
        os.environ.update({"PATH": "/usr/bin:/bin", "HOME": "/tmp"})
        os.environ["STRATA_SPLIT_CARD_OVERHEAD_GIB"] = overhead
        os.environ.update(env)
        d = SE.decide(enabled=True, system="linux", cards=cards, ram_total_gib=251.6, ram_available_gib=168.0,
                      model=model, context=131072, allow_untested=True)
        print("%-42s Overhead %2s GiB -> use_split=%-5s  braucht %5.2f GiB/Karte, %4.1f GiB RAM  %s"
              % (label, overhead, str(d.use_split), d.need_vram_gib, d.need_ram_gib, "; ".join(d.reasons) or ""))
