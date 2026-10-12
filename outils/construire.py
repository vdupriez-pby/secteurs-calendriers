"""Construit l'outil de suivi pour un ou plusieurs secteurs de la carte « Calendriers Pompiers Meylan ».

Usage :
    python3 outils/construire.py 4          # un secteur
    python3 outils/construire.py 4 5 12     # plusieurs
    python3 outils/construire.py tous       # les 15
    --sans-rues : construit quand même si OpenStreetMap ne répond pas (carte sans fond de rues)

Résultat : secteurs/secteur-N/ avec Code.gs, Index.html et LISEZMOI.md, prêts à coller dans Apps Script.
Les téléchargements (carte, Base Adresse Nationale, rues OpenStreetMap) sont gardés dans outils/cache/.
"""
import csv, gzip, json, re, shutil, subprocess, sys, time, unicodedata, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
CACHE = ICI / "cache"
KML_URL = "https://www.google.com/maps/d/kml?mid=1hj46infUJx8b8XN9YQwTatU6ZZGnixk&forcekml=1"
BAN_URL = "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-38.csv.gz"
OVERPASS = ["https://overpass.private.coffee/api/interpreter",
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]
B_LON, B_LAT, Q = 5.70, 45.18, 1e5  # tracés de rues : écarts entiers de 1e-5 degré à partir de ce point


def telecharger(url, dest, data=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "calendriers-pompiers/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        dest.write_bytes(r.read())


def en_cache(nom, url):
    f = CACHE / nom
    if not f.exists():
        print(f"  téléchargement de {nom}…")
        telecharger(url, f)
    return f


def secteurs_kml():
    kml = en_cache("carte.kml", KML_URL).read_text(encoding="utf-8")
    secs = defaultdict(list)
    for p in re.findall(r"<Placemark>(.*?)</Placemark>", kml, re.S):
        nom = re.search(r"<name>(.*?)</name>", p).group(1).strip()
        for c in re.findall(r"<coordinates>(.*?)</coordinates>", p, re.S):
            secs[nom].append([tuple(map(float, x.split(",")[:2])) for x in c.split()])
    return secs


def dedans(x, y, pts):
    c = False
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def cle(s):
    s = unicodedata.normalize("NFKD", s.replace("’", "'")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def accentue(n):
    return n != unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()


def adresses(polys, bbox):
    rows = []
    with gzip.open(en_cache("adresses-38.csv.gz", BAN_URL), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            x, y = float(r["lon"]), float(r["lat"])
            if bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3] and any(dedans(x, y, p) for p in polys):
                rows.append(r)
    # Une graphie par rue : la plus fréquente, à égalité celle qui porte des accents.
    variantes = defaultdict(Counter)
    for r in rows:
        variantes[cle(r["nom_voie"])][r["nom_voie"].replace("’", "'")] += 1
    canon = {k: max(c, key=lambda n: (c[n], accentue(n))) for k, c in variantes.items()}
    tri = lambda n: cle(re.sub(r"^(avenue|allee|chemin|impasse|route|rue|place|montee|square|boulevard|quai) (de la |de l |des |du |de |d )?", "", cle(n)))
    rues = sorted(set(canon.values()), key=lambda n: (tri(n), n))
    communes = [c for c, _ in Counter(r["nom_commune"] for r in rows).most_common()]
    ir, ic = {n: i for i, n in enumerate(rues)}, {n: i for i, n in enumerate(communes)}
    vus, out = set(), []
    for r in rows:
        if r["id"] in vus:
            continue
        vus.add(r["id"])
        num = "" if r["numero"] in ("", "99999") else r["numero"] + ((" " + r["rep"]) if r["rep"] else "")
        out.append([r["id"], num, ir[canon[cle(r["nom_voie"])]], ic[r["nom_commune"]],
                    round(float(r["lon"]), 6), round(float(r["lat"]), 6)])
    out.sort(key=lambda a: (a[2], int(re.match(r"\d*", a[1]).group() or 0), a[1]))
    return rues, communes, out


def routes(n, bbox):
    f = CACHE / f"routes-secteur-{n}.json"
    if not f.exists():
        s, w, nn, e = bbox[1] - 0.002, bbox[0] - 0.003, bbox[3] + 0.002, bbox[2] + 0.003
        q = f'[out:json][timeout:90];way["highway"]({s:.4f},{w:.4f},{nn:.4f},{e:.4f});out geom;'
        # Les serveurs OpenStreetMap publics sont souvent saturés : plusieurs tours, avec des pauses croissantes.
        for essai in range(4):
            for url in OVERPASS:
                try:
                    print(f"  rues OpenStreetMap via {url.split('/')[2]}…", flush=True)
                    telecharger(url, f, data=urllib.parse.urlencode({"data": q}).encode(), timeout=120)
                    json.loads(f.read_text(encoding="utf-8"))["elements"]
                    break
                except Exception as err:
                    print(f"    échec ({type(err).__name__})", flush=True)
                    f.unlink(missing_ok=True)
            if f.exists():
                break
            time.sleep(30 * (essai + 1))
    if not f.exists():
        if SANS_RUES:
            print("  ATTENTION : rues indisponibles, la carte n'affichera que le contour et les adresses.")
            return []
        sys.exit("  Rues OpenStreetMap indisponibles pour l'instant : relancez plus tard, "
                 "ou ajoutez --sans-rues pour une carte sans fond de rues.")
    out = []
    for e in json.loads(f.read_text(encoding="utf-8"))["elements"]:
        g, t = e.get("geometry"), e.get("tags", {})
        hw = t.get("highway", "")
        if not g or hw in ("proposed", "construction", "platform", "bus_stop", "elevator"):
            continue
        kind = 2 if hw in ("primary", "secondary", "tertiary", "trunk") else (
            0 if hw in ("footway", "path", "steps", "cycleway", "track", "pedestrian", "service") else 1)
        out.append([kind, t.get("name", ""), [[p["lon"], p["lat"]] for p in g]])
    return out


def encode(pts):
    out, px, py = [], 0, 0
    for lon, lat in pts:
        x, y = round((lon - B_LON) * Q), round((lat - B_LAT) * Q)
        out += [x - px, y - py]
        px, py = x, y
    return ",".join(map(str, out))


def donnees_js(d):
    """Données sur des lignes courtes : un collage dans Apps Script coupe les lignes très longues."""
    J = lambda v: json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    liste = lambda items: [x + "," for x in items[:-1]] + items[-1:]
    lignes = ["{", '"poly":' + J(d["poly"]) + ",", '"center":' + J(d["center"]) + ",",
              '"commune":' + J(d["commune"]) + ",", '"streets":['] + liste([J(s) for s in d["streets"]]) + [
              "],", '"communes":' + J(d["communes"]) + ",", '"addrs":['] + liste([J(a) for a in d["addrs"]]) + [
              "],", f'"roadBase":[{B_LON},{B_LAT},{int(Q)}],', '"roads":['] + liste(
              [J([k, nom, encode(p)]) for k, nom, p in d["roads"]]) + ["]", "}"]
    return "\n".join(lignes)


def construire(n, secs):
    nom = f"Secteur {n}"
    if nom not in secs:
        sys.exit(f"{nom} n'existe pas sur la carte (secteurs : {', '.join(sorted(secs, key=lambda s: int(s.split()[-1])))})")
    polys = secs[nom]
    pts = [p for poly in polys for p in poly]
    bbox = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
    print(f"{nom} :", flush=True)
    rues, communes, addrs = adresses(polys, bbox)
    d = {"poly": [[round(x, 6), round(y, 6)] for x, y in polys[0]],
         "center": [round((bbox[0] + bbox[2]) / 2, 5), round((bbox[1] + bbox[3]) / 2, 5)],
         "commune": communes[0], "streets": rues, "communes": communes, "addrs": addrs, "roads": routes(n, bbox)}
    if len(polys) > 1:
        print(f"  ATTENTION : {nom} a {len(polys)} contours, seul le premier est dessiné sur la carte.")

    data = donnees_js(d)
    assert "//" not in data and "</" not in data, "caractères interdits dans les données"
    html = (ICI / "modele-index.html").read_text(encoding="utf-8").replace("{{SECTEUR}}", nom)
    assert html.count("/*DATA*/") == 1
    html = html.replace("/*DATA*/", data)
    plus_longue = max(len(l) for l in html.split("\n"))
    assert plus_longue < 5000, f"ligne de {plus_longue} caractères"

    dossier = RACINE / "secteurs" / f"secteur-{n}"
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "Index.html").write_text(html, encoding="utf-8")
    nb_lignes = html.count("\n") + 1
    valeurs = {"{{SECTEUR}}": nom, "{{ADRESSES}}": str(len(addrs)), "{{LIGNES}}": str(nb_lignes),
               "{{COUPURE}}": str(nb_lignes // 2)}  # point de découpe si le collage doit se faire en deux fois
    for src, dst in (("modele-code.gs", "Code.gs"), ("modele-lisezmoi.md", "LISEZMOI.md")):
        texte = (ICI / src).read_text(encoding="utf-8")
        for k, v in valeurs.items():
            texte = texte.replace(k, v)
        (dossier / dst).write_text(texte, encoding="utf-8")

    if shutil.which("node"):
        js = re.findall(r"<script>(.*?)</script>", html, re.S)
        tmp = CACHE / "verif.js"
        tmp.write_text("\n;\n".join(js), encoding="utf-8")
        subprocess.run(["node", "--check", str(tmp)], check=True)
    print(f"  {len(addrs)} adresses, {len(rues)} rues, {len(d['roads'])} tronçons de rues, commune principale {communes[0]}")
    print(f"  -> {dossier.relative_to(RACINE)}/ ({len(html) // 1024} Ko, {html.count(chr(10)) + 1} lignes)")


SANS_RUES = "--sans-rues" in sys.argv

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--sans-rues"]
    if not args:
        sys.exit(__doc__)
    CACHE.mkdir(exist_ok=True)
    secs = secteurs_kml()
    nums = sorted(int(s.split()[-1]) for s in secs) if args[0] == "tous" else [int(a) for a in args]
    for n in nums:
        construire(n, secs)
