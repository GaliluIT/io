#!/usr/bin/env python3
"""Build the website into the _site folder.

    python build.py            # the site as it will be published
    python build.py --drafts   # also show placeholders and "to do" notes

Preview it afterwards with:

    python -m http.server --directory _site
    (then open http://localhost:8000)

GitHub runs `python build.py` automatically every time you push
(see .github/workflows/pages.yml), so you never have to upload _site.
"""
import argparse
import datetime
import re
import shutil
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUT = ROOT / "_site"
NOTES = []  # things to fill in or fix, printed at the end of the build


def note(where, message):
    NOTES.append(f"{where}: {message}")


def load_yaml(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def md_block(text):
    return Markup(markdown.markdown(text or "", extensions=["extra", "smarty"]))


def md_inline(text):
    if text is None or text == "":
        return Markup("")
    html = markdown.markdown(str(text), extensions=["extra", "smarty"]).strip()
    match = re.fullmatch(r"<p>(.*)</p>", html, flags=re.S)
    return Markup(match.group(1) if match else html)


def plain(text):
    return re.sub(r"[*_`\[\]]|\(http[^)]*\)", "", str(text or "")).strip()


def is_external(path):
    return re.match(r"^(https?:|mailto:|tel:|#|data:)", str(path)) is not None


def asset(path, root, where):
    """Link to a file inside the site, relative to the current page."""
    if not path:
        return ""
    path = str(path)
    if is_external(path):
        return path
    path = path.lstrip("/")
    generated = path.endswith((".html", "/"))  # pages are built, not stored in the repo
    if not generated and not (ROOT / path).exists():
        note(where, f"file not found: {path}")
    return root + path


def rewrite_body_links(html, root):
    """Make assets/... links written in Markdown work from any page."""
    return Markup(
        re.sub(r'(src|href)="(assets/[^"]+)"',
               lambda m: f'{m.group(1)}="{root}{m.group(2)}"', str(html))
    )


def video_for(item, root, where, default_title=""):
    """A video from a YouTube or Vimeo link, or a file in assets/.
    item is a link, or a block with url, title and (for files) poster and description."""
    if not isinstance(item, dict):
        item = {"url": item}
    src = str(item.get("url") or item.get("src") or "")
    video = {"title": item.get("title") or default_title,
             "description": md_inline(item.get("description")),
             "poster": asset(item["poster"], root, where) if item.get("poster") else ""}
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/|youtube\.com/live/)([\w-]{11})", src)
    if m:
        return {**video, "kind": "iframe", "src": f"https://www.youtube-nocookie.com/embed/{m.group(1)}", "site": "YouTube"}
    m = re.search(r"vimeo\.com/(?:video/)?(\d+)", src)
    if m:
        return {**video, "kind": "iframe", "src": f"https://player.vimeo.com/video/{m.group(1)}", "site": "Vimeo"}
    return {**video, "kind": "file", "src": asset(src, root, where)}


def read_page(path):
    """Split a Markdown file into its settings block (between ---) and its text."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, flags=re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def start_year(years):
    """The first year in a field like "2019 – present" or "2023" (0 if there is none)."""
    m = re.search(r"\d{4}", str(years or ""))
    return int(m.group()) if m else 0


def by_start_year(items, years_of, order_of, newest_first=True):
    """Sort by starting year; projects that started the same year keep their `order`."""
    def key(item):
        y = start_year(years_of(item))
        return (-y if newest_first else (y or 9999), order_of(item))
    return sorted(items, key=key)


def year_key(entry):
    m = re.search(r"\d{4}", str(entry.get("year") or ""))
    return int(m.group()) if m else 9999  # undated entries (forthcoming) go first


def authors_html(authors, me):
    text = escape(authors or "")
    if me:
        text = Markup(str(text).replace(str(escape(me)), f"<strong>{escape(me)}</strong>"))
    return text


def load_publications(site, drafts):
    entries = load_yaml(CONTENT / "publications.yml") or []
    pubs = []
    for i, p in enumerate(entries, 1):
        where = f"publications.yml, entry {i}"
        if p.get("placeholder"):
            note(where, "placeholder, hidden on the live site")
            if not drafts:
                continue
        if p.get("check"):
            note(where, p["check"])
        lang = str(p.get("lang", "en")).lower()
        if lang not in ("en", "es"):
            note(where, f"lang should be en or es, not '{lang}'")
        link = p.get("url") or (f"https://doi.org/{p['doi']}" if p.get("doi") else "")
        pubs.append({
            **p,
            "lang": lang,
            "link": link,
            "title_html": md_inline(p.get("title")),
            "venue_html": md_inline(p.get("venue")),
            "authors_html": authors_html(p.get("authors"), site.get("me")),
        })
    pubs.sort(key=year_key, reverse=True)
    return pubs


def load_press(drafts):
    """Articles, interviews and videos about the work (content/press.yml), newest first."""
    out = []
    for i, p in enumerate(load_yaml(CONTENT / "press.yml") or [], 1):
        if p.get("check"):
            note(f"press.yml, entry {i}", p["check"])
        if p.get("draft") and not drafts:
            continue
        out.append({**p, "year": str(p.get("year") or ""), "lang": str(p.get("lang", "en")).lower(),
                    "title_html": md_inline(p.get("title")), "projects": p.get("projects") or []})
    out.sort(key=year_key, reverse=True)  # undated first
    return out


def load_projects(drafts, newest_first=True):
    projects = []
    for path in sorted((CONTENT / "projects").glob("*.md")):
        if path.name.startswith("_"):
            continue  # _template.md and other files starting with _ are ignored
        meta, body = read_page(path)
        where = f"projects/{path.name}"
        if meta.get("draft") and not drafts:
            continue
        if meta.get("check"):
            note(where, meta["check"])
        projects.append({"slug": path.stem, "meta": meta, "body": body, "where": where})
    # Newest first by starting year (set projects_newest_first: false in site.yml for oldest first)
    return by_start_year(projects, lambda p: p["meta"].get("years"),
                         lambda p: (p["meta"].get("order", 999), str(p["meta"].get("title", "")).lower()),
                         newest_first)


def project_view(p, root, press=()):
    m, where = p["meta"], p["where"]
    title = m.get("title", p["slug"])
    videos = m.get("videos") or ([m["video"]] if m.get("video") else [])
    images = []
    for im in m.get("images") or []:
        if isinstance(im, str):
            im = {"src": im}
        alt = im.get("alt") or plain(im.get("caption"))
        if not alt:
            note(where, f"add an alt (a description for people who can't see it) to {im.get('src')}")
        images.append({
            "src": asset(im.get("src"), root, where),
            "caption": md_inline(im.get("caption")),
            "alt": alt,
            "wide": bool(im.get("wide")),  # wide: true = the full width of the page
        })
    if m.get("cover"):
        cover = {"src": asset(m["cover"], root, where), "alt": m.get("cover_alt") or ""}
        if not cover["alt"]:
            note(where, "add cover_alt, a description of the cover image")
    elif images:
        cover = {"src": images[0]["src"], "alt": images[0]["alt"]}
    else:
        cover = None
    links = []
    for link in m.get("links") or []:
        links.append({"label": link.get("label") or link.get("url"), "url": asset(link.get("url"), root, where)})
    downloads = []
    for d in m.get("downloads") or []:
        path = ROOT / str(d.get("url", "")).lstrip("/")
        size = f"{path.stat().st_size / 1e6:.1f} MB" if path.exists() else ""
        downloads.append({"label": d.get("label") or path.name, "url": asset(d.get("url"), root, where),
                          "kind": path.suffix.lstrip(".").upper(), "size": size, "note": d.get("note") or ""})
    hero = None
    if m.get("hero"):
        hero = {"src": asset(m["hero"].get("src"), root, where), "alt": m["hero"].get("alt") or "",
                "caption": md_inline(m["hero"].get("caption"))}
        if not hero["alt"]:
            note(where, "add an alt to the hero image")
    model = None
    if m.get("model"):
        model = {"src": asset(m["model"].get("src"), root, where), "alt": m["model"].get("alt") or "",
                 "caption": md_inline(m["model"].get("caption"))}
        if not model["alt"]:
            note(where, "add an alt to the 3D model")
    return {
        "slug": p["slug"],
        "title": title,
        "years": str(m.get("years") or ""),
        "status": m.get("status") or "",
        "summary": md_inline(m.get("summary")),
        "summary_text": plain(m.get("summary")),
        "cover": cover,
        "videos": [video_for(v, root, where, f"Video: {title}") for v in videos],
        "images": images,
        "details": [(k, md_inline(v)) for k, v in (m.get("details") or {}).items()],
        "links": links,
        "downloads": downloads,
        "hero": hero,
        "press": [x for x in press if p["slug"] in x["projects"]],
        "model": model,
        "body": rewrite_body_links(md_block(p["body"]), root),
        "check": m.get("check"),
        "draft": m.get("draft"),
        # A project can point somewhere else instead of having its own page
        "link": asset(m.get("link"), root, where) if m.get("link") else "",
    }


# ---------------------------------------------------------------------------
# Intercambios Transorgánicos (content/intercambios/): one page in Spanish and English,
# introducing the program, its students, team and projects, and linking to its own website.
# Any text field can have an English version in a field of the same name ending in _en.
# Markdown files hold Spanish text first, then a line <!-- en -->, then the English text.
# ---------------------------------------------------------------------------
IT = CONTENT / "intercambios"

# Pages of the earlier, larger Intercambios section, and where they are now
MOVED = {
    "intercambios/proyectos.html": "intercambios/index.html",
    "intercambios/actividades.html": "intercambios/index.html",
    "intercambios/publicaciones.html": "intercambios/index.html",
    "intercambios/proyectos/fonocosa.html": "projects/fonocosa.html",
    "intercambios/proyectos/fonocosa-aldo.html": "projects/fonocosa-aldo.html",
    "intercambios/proyectos/archivoz.html": "projects/archivoz.html",
    "intercambios/proyectos/orquesta-telematica.html": "projects/l2ork.html",
    "intercambios/proyectos/c3d.html": "projects/c3d.html",
    "intercambios/proyectos/eterofono.html": "intercambios/index.html",
    "intercambios/proyectos/juego-de-ingenio.html": "intercambios/index.html",
    "intercambios/proyectos/espectro-de-la-voz.html": "projects/el-espectro-de-la-voz.html",
}


def split_langs(text):
    parts = re.split(r"^[ \t]*<!--\s*en\s*-->[ \t]*$", text or "", maxsplit=1, flags=re.M)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def bi(obj, key):
    """Spanish and English versions of an inline field, e.g. title / title_en."""
    return {"es": md_inline(obj.get(key)), "en": md_inline(obj.get(key + "_en"))}


def bi_body(text, root):
    es, en = split_langs(text)
    return {"es": rewrite_body_links(md_block(es), root),
            "en": rewrite_body_links(md_block(en), root) if en else Markup("")}


def build_intercambios(render, drafts, newest_first=True):
    if not IT.exists():
        return
    root = "../"
    meta, body = read_page(IT / "programa.md")
    projects = []
    entries = load_yaml(IT / "proyectos.yml") or []
    entries = by_start_year(entries, lambda p: p.get("years"), lambda p: entries.index(p), newest_first)
    for i, p in enumerate(entries, 1):
        where = f"intercambios/proyectos.yml, entry {i}"
        if p.get("draft") and not drafts:
            continue
        if p.get("check"):
            note(where, p["check"])
        if p.get("image") and not p.get("alt"):
            note(where, "add an alt (a description of the image)")
        projects.append({
            "title": bi(p, "title"),
            "years": bi(p, "years"),
            "summary": bi(p, "summary"),
            "image": asset(p.get("image"), root, where) if p.get("image") else "",
            "alt": plain(p.get("alt")),
            "alt_en": plain(p.get("alt_en")) or plain(p.get("alt")),
            "link": asset(p.get("link"), root, where) if p.get("link") else "",
            "video": p.get("video") or "",
        })
    team = load_yaml(IT / "equipo.yml") or []
    team_groups = [{"title": bi(g, "title"), "note": bi(g, "note"),
                    "people": [{"name": x.get("name"), "role": bi(x, "role")} for x in g.get("people") or []]}
                   for g in team]
    website = meta.get("website") or ""
    common = {"page_lang": "es", "default_lang": "es", "section": "it", "it_website": website}
    title = "Intercambios Transorgánicos"
    render("it_index.html", "intercambios/index.html", root, page_kind="it-home",
           page_title=title, description=plain(meta.get("lede")),
           programa={"lede": bi(meta, "lede"), "body": bi_body(body, root),
                     "recognition": [{"es": md_inline(r.get("es")), "en": md_inline(r.get("en"))}
                                     for r in meta.get("recognition") or []]},
           team=team_groups, projects=projects, **common)
    # Longer texts (content/intercambios/textos/), e.g. the essay on transdisciplinarity
    for path in sorted((IT / "textos").glob("*.md")):
        tmeta, tbody = read_page(path)
        render("it_text.html", f"intercambios/textos/{path.stem}.html", "../../", page_kind="it-text",
               page_title=f"{plain(tmeta.get('title'))} | {title}", description=plain(tmeta.get("summary")),
               text={"title": bi(tmeta, "title"), "author": tmeta.get("author", ""), "date": tmeta.get("date", ""),
                     "note": bi(tmeta, "note"), "body": bi_body(tbody, "../../")},
               **{**common, "it_website": website})


def main():
    parser = argparse.ArgumentParser(description="Build the website into _site/")
    parser.add_argument("--drafts", action="store_true", help="show placeholders and to-do notes")
    parser.add_argument("--fragment-home", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    site = load_yaml(CONTENT / "site.yml") or {}
    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    if (ROOT / "CNAME").exists():  # custom domain (galalucia.com)
        shutil.copy(ROOT / "CNAME", OUT / "CNAME")

    pubs = load_publications(site, args.drafts)
    press = load_press(args.drafts)
    newest_first = site.get("projects_newest_first", True)
    projects = load_projects(args.drafts, newest_first)

    fono = dict(site.get("fono") or {})
    if fono:
        fono["model_url"] = asset(fono.get("model"), "", "site.yml (fono)")
        fono["poster_url"] = asset(fono.get("poster"), "", "site.yml (fono)") if fono.get("poster") else ""
        fono["sound_url"] = asset(fono.get("sound"), "", "site.yml (fono)") if fono.get("sound") else ""
        fono["link_url"] = asset(fono.get("link"), "", "site.yml (fono)") if fono.get("link") else ""
        if fono.get("check"):
            note("site.yml (fono)", fono["check"])

    og_image = ""
    if site.get("url") and fono.get("poster"):
        og_image = site["url"].rstrip("/") + "/" + str(fono["poster"]).lstrip("/")

    common = {
        "site": site,
        "drafts": args.drafts,
        "updated": datetime.date.today().strftime("%B %Y"),
        "og_image": og_image,
    }
    pages = 0

    def render(template, out_path, root, **ctx):
        nonlocal pages
        html = env.get_template(template).render(root=root, **common, **ctx)
        target = OUT / out_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        pages += 1

    # The bio, in English and Spanish. The home page shows its first paragraph,
    # the About page all of it.
    about = {}
    for lang in ("en", "es"):
        path = CONTENT / f"about.{lang}.md"
        text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
        about[lang] = {"full": md_block(text), "intro": md_block(text.split("\n\n")[0]) if text else ""}

    cv_pdf = ""
    if site.get("cv_pdf"):
        if (ROOT / str(site["cv_pdf"]).lstrip("/")).exists():
            cv_pdf = str(site["cv_pdf"]).lstrip("/")
        else:
            note("site.yml (cv_pdf)", f"run python make_cv_pdf.py --save to create {site['cv_pdf']}")
    common["cv_pdf"] = cv_pdf
    portrait = {"src": asset(site.get("portrait"), "", "site.yml (portrait)"),
                "alt": site.get("portrait_alt") or ""} if site.get("portrait") else None
    if portrait and not portrait["alt"]:
        note("site.yml", "add portrait_alt, a description of your photo")

    # Home: the 3D object, a short introduction and the publications
    groups = [
        {"lang": "en", "label": "English", "items": [p for p in pubs if p["lang"] == "en"]},
        {"lang": "es", "label": "Español", "items": [p for p in pubs if p["lang"] == "es"]},
    ]
    render(
        "home.html", "index.html", "",
        page_kind="home",
        page_title=site.get("name", ""),
        fragment=args.fragment_home,
        about=about,
        pub_groups=[g for g in groups if g["items"]],
        press=press,
        fono=fono,
    )

    # About: photo, the whole bio, profiles and CV
    render("about.html", "about.html", "", page_kind="about",
           page_title=f"About | {site.get('name', '')}", about=about, portrait=portrait,
           og_image_override=(site["url"].rstrip("/") + "/" + str(site["portrait"]).lstrip("/"))
           if site.get("url") and site.get("portrait") else "")

    # Projects list and one page per project
    render("projects.html", "projects.html", "",
           page_kind="projects", page_title=f"Projects | {site.get('name', '')}",
           projects=[project_view(p, "", press) for p in projects])
    views = [v for v in (project_view(p, "../", press) for p in projects) if not v["link"]]
    for i, view in enumerate(views):
        render("project.html", f"projects/{view['slug']}.html", "../",
               page_kind="project", page_title=f"{view['title']} | {site.get('name', '')}",
               description=view["summary_text"],
               project=view,
               previous=views[i - 1] if i > 0 else None,
               next=views[i + 1] if i + 1 < len(views) else None)

    # CV
    sections = []
    for s in load_yaml(CONTENT / "cv.yml") or []:
        if s.get("from") == "publications":
            sections.append({"title": s.get("title", "Publications"), "pubs": pubs})
            continue
        if s.get("from") == "press":
            if press:
                sections.append({"title": s.get("title", "Press"), "press": press})
            continue
        items = []
        for it in s.get("items") or []:
            if it.get("check"):
                note(f"cv.yml, {s.get('title')}", f"{it.get('what', '')}: {it['check']}")
            if it.get("placeholder") and not args.drafts:
                continue
            items.append({
                **it,
                "what_html": md_inline(it.get("what")),
                "where_html": md_inline(it.get("where")),
                "note_html": md_inline(it.get("note")),
            })
        sections.append({"title": s.get("title", ""), "items": items})
    render("cv.html", "cv.html", "", page_kind="cv", page_title=f"CV | {site.get('name', '')}",
           sections=sections)

    # Intercambios Transorgánicos section
    build_intercambios(render, args.drafts, newest_first)

    # Addresses that moved: a small page sends visitors on to the new one
    for path, target in MOVED.items():
        depth = path.count("/")
        rel = "../" * depth + target
        page = OUT / path
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(
            f'<!doctype html><html lang="en"><meta charset="utf-8"><title>Moved</title>'
            f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={rel}">'
            f'<link rel="canonical" href="{rel}"><p>This page moved to <a href="{rel}">{rel}</a>.</p></html>',
            encoding="utf-8")

    print(f"Built {pages} pages into _site/")
    unique = list(dict.fromkeys(NOTES))
    if unique:
        print(f"\n{len(unique)} things to fill in or check:")
        for n in unique:
            print("  -", n)


if __name__ == "__main__":
    main()
