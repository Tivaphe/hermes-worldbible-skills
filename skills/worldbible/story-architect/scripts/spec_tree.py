#!/usr/bin/env python3
"""
spec_tree.py — Gere l'arbre de specifications d'un projet d'ecriture (raffinement L0 -> L3)
et fait respecter les portes : on ne detaille pas un niveau dont le parent n'est pas gele.

Niveaux:
    L0  livre      1 fichier        concept, promesse, format
    L1  partie     3 a 6 fichiers   un bloc narratif
    L2  chapitre   1 par chapitre   CONTRAT: entree / sortie / cotes
    L3  scene      1 a 4 par chap.  beats, ou on entre, ou on sort

Usage:
    python3 spec_tree.py init   --specs <manuscrit>/specs --title "Titre" --words 90000
    python3 spec_tree.py new    --specs <manuscrit>/specs --level 2 --parent 01-livre/01 --name 03
    python3 spec_tree.py tree   --specs <manuscrit>/specs
    python3 spec_tree.py check  --specs <manuscrit>/specs 02-parties/01
    python3 spec_tree.py freeze --specs <manuscrit>/specs 02-parties/01
    python3 spec_tree.py next   --specs <manuscrit>/specs
    python3 spec_tree.py audit  --specs <manuscrit>/specs

Dependances: bibliotheque standard Python uniquement.

NOTE: ce fichier est presente a l'identique dans les skills story-architect et
chapter-draft, afin que chacun reste installable seul. En cas de modification,
mettre a jour les deux copies (verifier.sh controle qu'elles sont identiques).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from datetime import datetime, timezone

PLACEHOLDERS = ("à remplir", "a remplir", "TODO", "TBD", "xxx", "<...>")

LEVELS = {
    0: {
        "label": "livre",
        "dir": "01-livre",
        "required": ["## Prémisse", "## Public et promesse", "## Thème", "## Format", "## Blocs"],
        "min_words": 150,
    },
    1: {
        "label": "partie",
        "dir": "02-parties",
        "required": ["## Fonction dans le livre", "## Entrée", "## Sortie", "## Chapitres"],
        "min_words": 70,
    },
    2: {
        "label": "chapitre",
        "dir": "03-chapitres",
        "required": [
            "## Objectif",
            "## Où on entre",
            "## Où on sort",
            "## Ce qui change",
            "## Contraintes",
            "## Scenes",
        ],
        "min_words": 60,
    },
    3: {
        "label": "scene",
        "dir": "04-scenes",
        "required": ["## Où on entre", "## Où on sort", "## Beats", "## Ce qui change"],
        "min_words": 40,
    },
}
LEVEL_DIRS = {v["dir"]: k for k, v in LEVELS.items()}


# ---------------------------------------------------------------- spec parsing
def read_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    meta: dict[str, str] = {}
    body = text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            km = re.match(r"^([A-Za-z_][\w\-]*):\s*(.*)$", line.strip())
            if km:
                meta[km.group(1)] = km.group(2).strip().strip("'\"")
        body = m.group(2)
    title = ""
    tm = re.search(r"^#\s+(.+)$", body, re.M)
    if tm:
        title = tm.group(1).strip()
    return {
        "path": path,
        "meta": meta,
        "title": title,
        "body": body,
        "sections": re.findall(r"^##\s+(.+?)\s*$", body, re.M),
        "body_words": len(re.findall(r"[\w'’À-ÿ\-]+", re.sub(r"^#.*$", "", body, flags=re.M))),
        "hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16],
    }


def section_filled(body: str, heading: str) -> bool:
    """Une section est remplie si elle contient du texte qui n'est pas un placeholder."""
    pat = re.compile(rf"^##\s+{re.escape(heading.lstrip('# ').strip())}\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
    m = pat.search(body)
    if not m:
        return False
    content = m.group(1).strip()
    if not content:
        return False
    if any(p.lower() in content.lower() for p in PLACEHOLDERS):
        return False
    return len(re.findall(r"[\w'’À-ÿ\-]+", content)) >= 3


def find_specs(specs_dir: str) -> dict[str, dict]:
    """relpath (sans .md) -> spec."""
    out: dict[str, dict] = {}
    for dirpath, dirnames, filenames in os.walk(specs_dir):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if not name.endswith(".md") or name == "README.md":
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, specs_dir)[:-3]
            out[rel] = read_spec(full)
    return out


def level_of(specs_dir: str, rel: str) -> int | None:
    top = rel.split(os.sep)[0]
    return LEVEL_DIRS.get(top)


def children_of(specs: dict, rel: str) -> list[str]:
    declared = specs[rel]["meta"].get("children", "")
    if not declared:
        return []
    return [c.strip() for c in declared.split(",") if c.strip()]


def is_frozen(specs_dir: str, rel: str) -> tuple[bool, str]:
    fpath = os.path.join(specs_dir, ".freeze", rel.replace(os.sep, "__") + ".txt")
    if not os.path.isfile(fpath):
        return False, ""
    with open(fpath, "r", encoding="utf-8") as fh:
        return True, fh.read().strip()


def spec_gate(specs_dir: str, specs_map: dict, rel: str, tolerance: float) -> tuple[bool, list[str]]:
    """Retourne (porte_ouverte, liste_des_points_bloquants). Logique unique de la porte."""
    spec = specs_map[rel]
    lvl = level_of(specs_dir, rel)
    if lvl is None:
        return False, [f"dossier de niveau inconnu pour {rel}"]
    errors = []
    for head in LEVELS[lvl]["required"]:
        if not section_filled(spec["body"], head):
            errors.append(f"section vide ou placeholder: {head}")
    parent = spec["meta"].get("parent", "null")
    if parent and parent != "null":
        if parent not in specs_map:
            errors.append(f"parent declare mais absent: {parent}")
        else:
            frozen, fhash = is_frozen(specs_dir, parent)
            if not frozen:
                errors.append(f"parent non gele: {parent}")
            elif fhash != specs_map[parent]["hash"]:
                errors.append(f"parent modifie apres gel — re-geler {parent} puis reverifier")
    try:
        target = int(spec["meta"].get("words_target", "0") or 0)
    except (ValueError, TypeError):
        target = 0
        errors.append("words_target absent ou non numerique")
    kids = children_of(specs_map, rel)
    if target and kids:
        total = 0
        for k in kids:
            if k not in specs_map:
                continue
            try:
                total += int(specs_map[k]["meta"].get("words_target", "0") or 0)
            except (ValueError, TypeError):
                pass
        if total and abs(total - target) / target > tolerance:
            errors.append(
                f"budget incoherent: {target} annonces, {total} repartis "
                f"(ecart {abs(total - target) / target:.0%} > {tolerance:.0%})"
            )
    return (not errors), errors


# ---------------------------------------------------------------- commands
def cmd_init(args) -> int:
    specs = os.path.abspath(os.path.expanduser(args.specs))
    os.makedirs(os.path.join(specs, "01-livre"), exist_ok=True)
    for d in ("02-parties", "03-chapitres", "04-scenes", ".freeze"):
        os.makedirs(os.path.join(specs, d), exist_ok=True)
    l0 = os.path.join(specs, "01-livre", "01-livre.md")
    if os.path.exists(l0) and not args.force:
        print(f"deja present: {l0} (utiliser --force pour ecraser)")
        return 1
    parts = args.parts or 3
    kids = ", ".join(f"02-parties/{i:02d}" for i in range(1, parts + 1))
    per_part = args.words // max(1, parts)
    with open(l0, "w", encoding="utf-8") as fh:
        fh.write(f"""---
level: 0
parent: null
status: draft
title: {args.title}
words_target: {args.words}
children: {kids}
---

# {args.title}

## Prémisse
à remplir — une phrase : qui veut quoi, contre quoi, à quel prix.

## Public et promesse
à remplir — à qui s'adresse le livre, quelle émotion il promet, quel type de fin.

## Thème
à remplir — la question que le livre pose, pas la réponse qu'il donne.

## Format
- longueur visée : {args.words} mots
- parties : {parts} (≈ {per_part} mots chacune)
- POV : à remplir
- temps : à remplir

## Blocs
""" + "".join(f"- 02-parties/{i:02d} — à nommer : fonction narrative de cette partie\n" for i in range(1, parts + 1)))
    print(f"structure creee: {specs}")
    print(f"  L0 a ecrire: {os.path.relpath(l0, specs)[:-3]}")
    print(f"  puis: python3 {os.path.basename(__file__)} next --specs {specs}")
    return 0


def cmd_new(args) -> int:
    specs = os.path.abspath(os.path.expanduser(args.specs))
    if args.level not in LEVELS:
        raise SystemExit(f"ERREUR: niveau invalide {args.level} (0 a 3)")
    lvl = LEVELS[args.level]
    if args.level > 0 and not args.parent:
        raise SystemExit("ERREUR: --parent obligatoire au-dela du niveau 0")
    parent_rel = args.parent
    if args.level > 0:
        pfile = os.path.join(specs, parent_rel + ".md")
        if not os.path.isfile(pfile):
            raise SystemExit(f"ERREUR: parent introuvable: {parent_rel}")
        frozen, _ = is_frozen(specs, parent_rel)
        if not frozen:
            print(f"PORTE FERMEE: le parent « {parent_rel} » n'est pas gele.")
            print("  Un niveau ne se detaille pas avant que son parent soit fige.")
            print(f"  Verifier d'abord: python3 {os.path.basename(__file__)} check --specs {specs} {parent_rel}")
            return 2
    name = args.name or "01"
    rel = os.path.join(lvl["dir"], name)
    out = os.path.join(specs, rel + ".md")
    if os.path.exists(out) and not args.force:
        print(f"deja present: {rel} (utiliser --force)")
        return 1
    os.makedirs(os.path.dirname(out), exist_ok=True)
    words = args.words or 0
    if words == 0 and args.level > 0 and args.parent:
        pspec = read_spec(os.path.join(specs, parent_rel + ".md"))
        try:
            budget = int(pspec["meta"].get("words_target", "0") or 0)
        except (ValueError, TypeError):
            budget = 0
        if budget:
            # repartir le budget du parent entre le nombre de freres announces
            n = args.siblings
            if n <= 0:
                declared = children_of({parent_rel: pspec}, parent_rel)
                n = len(declared) if declared else 1
            words = budget // max(1, n)
    sections = {
        0: ["## Prémisse", "## Public et promesse", "## Thème", "## Format", "## Blocs"],
        1: ["## Fonction dans le livre", "## Entrée", "## Sortie", "## Chapitres"],
        2: ["## Objectif", "## Où on entre", "## Où on sort", "## Ce qui change", "## Contraintes", "## Scenes"],
        3: ["## Où on entre", "## Où on sort", "## Beats", "## Ce qui change"],
    }[args.level]
    hints = {
        "## Où on entre": "état exact au premier mot : qui, où, quand, ce que le lecteur sait déjà.",
        "## Où on sort": "état exact au dernier mot : ce qui a changé, ce que le lecteur sait de plus.",
        "## Ce qui change": "une ligne, vérifiable. Si rien ne change, ce niveau ne sert à rien.",
        "## Contraintes": "ce que ce niveau a l'interdiction de faire (hérité du parent + canon).",
        "## Beats": "4 à 8 puces, une par mouvement. Chaque beat a une entrée et une sortie.",
        "## Scenes": "liste des scenes (04-scenes/xx) avec leur budget de mots.",
        "## Chapitres": "liste des chapitres (03-chapitres/xx) avec leur budget de mots.",
    }
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f"""---
level: {args.level}
parent: {parent_rel or 'null'}
status: draft
words_target: {words}
children:
---

# {args.title or name}

""" + "\n\n".join(f"{s}\n{hints.get(s, 'à remplir')}" for s in sections) + "\n")
    print(f"cree: {rel}  (niveau {args.level} — {lvl['label']})")
    if words:
        print(f"  budget herite: {words} mots")
    return 0


def cmd_check(args) -> int:
    specs = os.path.abspath(os.path.expanduser(args.specs))
    specs_map = find_specs(specs)
    if args.node not in specs_map:
        raise SystemExit(f"ERREUR: spec introuvable: {args.node}")
    spec = specs_map[args.node]
    lvl = level_of(specs, args.node)
    if lvl is None:
        raise SystemExit(f"ERREUR: dossier de niveau inconnu pour {args.node}")

    open_gate, errors = spec_gate(specs, specs_map, args.node, args.tolerance)

    warnings = []
    if spec["body_words"] < LEVELS[lvl]["min_words"]:
        warnings.append(f"corps court ({spec['body_words']} mots, minimum conseille {LEVELS[lvl]['min_words']})")
    declared = children_of(specs_map, args.node)
    missing = [k for k in declared if k not in specs_map]
    if missing:
        warnings.append(f"enfants declares mais absents: {', '.join(missing)}")

    print(f"=== CHECK {args.node} (niveau {lvl} — {LEVELS[lvl]['label']}) ===")
    print(f"  titre: {spec['title'] or '(sans titre)'} | corps: {spec['body_words']} mots | hash: {spec['hash']}")
    print(f"  parent: {spec['meta'].get('parent', 'null')} | enfants declares: {len(declared)}")
    for w in warnings:
        print(f"  [!] {w}")
    for e in errors:
        print(f"  [X] {e}")
    if not open_gate:
        print(f"\nPORTE FERMEE — {len(errors)} point(s) bloquant(s). Niveau suivant interdit.")
        return 1
    print("\nPORTE OUVERTE — ce niveau peut etre gele.")
    return 0


def cmd_freeze(args) -> int:
    specs = os.path.abspath(os.path.expanduser(args.specs))
    p = os.path.join(specs, args.node + ".md")
    if not os.path.isfile(p):
        raise SystemExit(f"ERREUR: spec introuvable: {args.node}")
    spec = read_spec(p)
    if not args.force:
        rc = cmd_check(argparse.Namespace(specs=args.specs, node=args.node, tolerance=args.tolerance))
        if rc != 0:
            print("\ngel refuse (utiliser --force pour passer outre, a vos risques)")
            return rc
    fdir = os.path.join(specs, ".freeze")
    os.makedirs(fdir, exist_ok=True)
    fpath = os.path.join(fdir, args.node.replace(os.sep, "__") + ".txt")
    with open(fpath, "w", encoding="utf-8") as fh:
        fh.write(spec["hash"] + "\n")
    # statut
    text = open(p, encoding="utf-8").read()
    text = re.sub(r"^status:\s*.*$", "status: frozen", text, count=1, flags=re.M)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"GELE: {args.node} (hash {spec['hash']})")
    print("  toute modification de ce fichier sera detectee par check/audit.")
    return 0


def cmd_tree(args) -> int:
    specs = os.path.abspath(os.path.expanduser(args.specs))
    specs_map = find_specs(specs)
    if not specs_map:
        print(f"aucune spec dans {specs} — lancer: init")
        return 1
    by_level: dict[int, list[str]] = {}
    for rel in specs_map:
        lvl = level_of(specs, rel)
        if lvl is not None:
            by_level.setdefault(lvl, []).append(rel)
    print(f"=== ARBRE DE SPECIFICATIONS : {specs} ===")
    for lvl in sorted(by_level):
        label = LEVELS[lvl]["label"]
        items = sorted(by_level[lvl])
        n_frozen = sum(1 for r in items if is_frozen(specs, r)[0])
        print(f"\nL{lvl} — {label} ({len(items)} spec(s), {n_frozen} gelee(s))")
        for rel in items:
            spec = specs_map[rel]
            frozen, fhash = is_frozen(specs, rel)
            flag = "GELE" if frozen else "brouillon"
            drift = ""
            if frozen and fhash != spec["hash"]:
                drift = "  <<< MODIFIE APRES GEL"
            wt = spec["meta"].get("words_target", "")
            print(f"  [{flag:>9}] {rel}  « {spec['title'] or '?'} »  {wt} mots{drift}")
    return 0


def cmd_next(args) -> int:
    specs = os.path.abspath(os.path.expanduser(args.specs))
    specs_map = find_specs(specs)
    if not specs_map:
        print("prochaine etape: python3 spec_tree.py init --specs <manuscrit>/specs --title \"Titre\" --words 90000")
        return 0
    # 1. specs ecrites mais non gelees et valides -> a geler
    ready = []
    blocked = []
    for rel in sorted(specs_map):
        lvl = level_of(specs, rel)
        if lvl is None:
            continue
        frozen, _ = is_frozen(specs, rel)
        if frozen:
            continue
        # verification silencieuse: cmd_next resume, il n'affiche pas le detail
        ok, why = spec_gate(specs, specs_map, rel, args.tolerance)
        if ok:
            ready.append(rel)
        else:
            blocked.append((rel, why))
    # 2. parents geles sans enfants -> a creer
    to_create = []
    for rel in sorted(specs_map):
        lvl = level_of(specs, rel)
        frozen, _ = is_frozen(specs, rel)
        if not frozen or lvl is None or lvl >= 3:
            continue
        if not children_of(specs_map, rel):
            to_create.append(rel)
    print("=== PROCHAINES ETAPES ===")
    if ready:
        print("\nA GELER (spec complete, porte ouverte):")
        for r in ready:
            print(f"  freeze {r}")
    if blocked:
        print("\nA COMPLETER (porte fermee):")
        for r, why in blocked:
            print(f"  {r}")
            for w in why[:3]:
                print(f"      - {w}")
            print(f"      detail: check {r}")
    if to_create:
        print("\nA DETAILLER (parent gele, aucun enfant):")
        for r in to_create:
            lvl = level_of(specs, r)
            print(f"  new --level {lvl + 1} --parent {r} --name 01")
    if not (ready or blocked or to_create):
        print("\nRien a faire au niveau structure : toutes les specs sont gelees.")
        print("Passer a l'ecriture (skill chapter-draft) sur les chapitres de niveau 2.")
    return 0


def cmd_audit(args) -> int:
    specs = os.path.abspath(os.path.expanduser(args.specs))
    specs_map = find_specs(specs)
    drift, orphans, unfrozen_parents = [], [], []
    for rel, spec in sorted(specs_map.items()):
        frozen, fhash = is_frozen(specs, rel)
        if frozen and fhash != spec["hash"]:
            drift.append(rel)
        parent = spec["meta"].get("parent", "null")
        if parent and parent != "null":
            if parent not in specs_map:
                orphans.append((rel, parent))
            elif not is_frozen(specs, parent)[0]:
                unfrozen_parents.append((rel, parent))
    print("=== AUDIT DE L'ARBRE ===")
    print(f"specs: {len(specs_map)}")
    print(f"derive apres gel      : {len(drift)}" + (f" -> {', '.join(drift)}" if drift else ""))
    print(f"parents absents       : {len(orphans)}" + (f" -> {orphans}" if orphans else ""))
    print(f"parents non geles     : {len(unfrozen_parents)}" + (f" -> {unfrozen_parents}" if unfrozen_parents else ""))
    bad = bool(drift or orphans or unfrozen_parents)
    print("\nverdict:", "A CORRIGER" if bad else "COHERENT")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Arbre de specifications et portes de raffinement.")
    ap.add_argument("--specs", required=True, help="Dossier des specs (ex: manuscrit/specs)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="cree la structure et le L0")
    p.add_argument("--title", default="Sans titre")
    p.add_argument("--words", type=int, default=90000)
    p.add_argument("--parts", type=int, default=3)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("new", help="cree une spec de niveau donne")
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--parent", default=None)
    p.add_argument("--name", default=None)
    p.add_argument("--title", default=None)
    p.add_argument("--words", type=int, default=0, help="budget de mots (defaut: budget du parent / freres)")
    p.add_argument("--siblings", type=int, default=0, help="nombre de freres prevus pour repartir le budget")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("check", help="verifie une spec (porte ouverte/fermee)")
    p.add_argument("node")
    p.add_argument("--tolerance", type=float, default=0.15)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("freeze", help="gele une spec (apres check reussi)")
    p.add_argument("node")
    p.add_argument("--tolerance", type=float, default=0.15)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_freeze)

    p = sub.add_parser("tree", help="affiche l'arbre")
    p.set_defaults(func=cmd_tree)

    p = sub.add_parser("next", help="prochaines etapes")
    p.add_argument("--tolerance", type=float, default=0.15)
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("audit", help="derive, orphelins, coherence")
    p.set_defaults(func=cmd_audit)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
