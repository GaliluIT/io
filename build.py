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


def video_for(src, root, where):
    src = str(src)
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/|youtube\.com/live/)([\w-]{11})", src)
    if m:
        return {"kind": "iframe", "src": f"https://www.youtube-nocookie.com/embed/{m.group(1)}"}
    m = re.search(r"vimeo\.com/(?:video/)?(\d+)", src)
    if m:
        return {"kind": "iframe", "src": f"https://player.vimeo.com/video/{m.group(1)}"}
    return {"kind": "file", "src": asset(src, root, where)}


def read_page(path):
    """Split a Markdown file into its settings block (between ---) and its text."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, flags=re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


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


def load_projects(drafts):
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
    projects.sort(key=lambda p: (p["meta"].get("order", 999), str(p["meta"].get("title", "")).lower()))
    return projects


def project_view(p, root):
    m, where = p["meta"], p["where"]
    videos = m.get("videos") or ([m["video"]] if m.get("video") else [])
    images = []
    for im in m.get("images") or []:
        if isinstance(im, str):
            im = {"src": im}
        images.append({
            "src": asset(im.get("src"), root, where),
            "caption": md_inline(im.get("caption")),
            "alt": im.get("alt") or re.sub(r"[*_`\[\]]", "", str(im.get("caption") or "")),
        })
    links = []
    for link in m.get("links") or []:
        links.append({"label": link.get("label") or link.get("url"), "url": asset(link.get("url"), root, where)})
    return {
        "slug": p["slug"],
        "title": m.get("title", p["slug"]),
        "years": m.get("years") or "",
        "summary": md_inline(m.get("summary")),
        "summary_text": re.sub(r"[*_`\[\]]", "", str(m.get("summary") or "")),
        "cover": asset(m.get("cover"), root, where) if m.get("cover") else "",
        "videos": [video_for(v, root, where) for v in videos],
        "images": images,
        "details": [(k, md_inline(v)) for k, v in (m.get("details") or {}).items()],
        "links": links,
        "body": rewrite_body_links(md_block(p["body"]), root),
        "check": m.get("check"),
        "draft": m.get("draft"),
        # A project can point somewhere else instead of having its own page
        "link": asset(m.get("link"), root, where) if m.get("link") else "",
    }


# ---------------------------------------------------------------------------
# Intercambios Transorgánicos section (content/intercambios/), in Spanish and English.
# Any text field can have an English version in a field of the same name ending in _en.
# Markdown files hold Spanish text first, then a line <!-- en -->, then the English text.
# ---------------------------------------------------------------------------
IT = CONTENT / "intercambios"
MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"]


def plain(text):
    return re.sub(r"[*_`\[\]]|\(http[^)]*\)", "", str(text or "")).strip()


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


def date_labels(value):
    s = str(value or "")
    m = re.fullmatch(r"(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", s)
    if not m:
        return {"es": s, "en": s}
    y, mo, d = m.groups()
    if not mo:
        return {"es": y, "en": y}
    mo = int(mo)
    if d:
        return {"es": f"{int(d)} de {MONTHS_ES[mo - 1]} de {y}", "en": f"{MONTHS_EN[mo - 1]} {int(d)}, {y}"}
    return {"es": f"{MONTHS_ES[mo - 1]} de {y}", "en": f"{MONTHS_EN[mo - 1]} {y}"}


def it_media(items, root, where):
    out = []
    for im in items or []:
        if isinstance(im, str):
            im = {"src": im}
        alt_es = plain(im.get("alt") or im.get("caption"))
        out.append({
            "src": asset(im.get("src"), root, where),
            "caption": bi(im, "caption"),
            "alt": alt_es,
            "alt_en": plain(im.get("alt_en") or im.get("caption_en")) or alt_es,
        })
    return out


def it_links(items, root, where):
    return [{"label": bi(l, "label"), "url": asset(l.get("url"), root, where)} for l in items or []]


def it_load_projects(drafts):
    items = []
    for path in sorted((IT / "proyectos").glob("*.md")):
        if path.name.startswith("_"):
            continue
        meta, body = read_page(path)
        where = f"intercambios/proyectos/{path.name}"
        if meta.get("draft") and not drafts:
            continue
        if meta.get("check"):
            note(where, meta["check"])
        items.append({"slug": path.stem, "meta": meta, "body": body, "where": where})
    items.sort(key=lambda p: (p["meta"].get("order", 999), p["slug"]))
    return items


def it_project_view(p, root):
    m, where = p["meta"], p["where"]
    videos = m.get("videos") or ([m["video"]] if m.get("video") else [])
    images = it_media(m.get("images"), root, where)
    return {
        "slug": p["slug"],
        "title": bi(m, "title"),
        "title_text": plain(m.get("title")),
        "years": bi(m, "years"),
        "summary": bi(m, "summary"),
        "summary_text": plain(m.get("summary")),
        "cover": images[0] if images else None,
        "images": images,
        "videos": [video_for(v, root, where) for v in videos],
        "details": [{"label": bi(d, "label"), "value": bi(d, "value")} for d in m.get("details") or []],
        "links": it_links(m.get("links"), root, where),
        "body": bi_body(p["body"], root),
        "check": m.get("check"),
    }


def it_load_list(name, drafts):
    entries = load_yaml(IT / name) or []
    out = []
    for i, e in enumerate(entries, 1):
        if e.get("check"):
            note(f"intercambios/{name}, entry {i}", e["check"])
        if e.get("draft") and not drafts:
            continue
        out.append(e)
    return out


def build_intercambios(render, drafts):
    if not IT.exists():
        return
    programa_meta, programa_body = read_page(IT / "programa.md")
    projects = it_load_projects(drafts)
    by_slug = {p["slug"]: p for p in projects}
    common = {"page_lang": "es", "default_lang": "es", "section": "it"}

    # Activities
    activities = []
    for a in it_load_list("actividades.yml", drafts):
        root = "../"
        where = "intercambios/actividades.yml"
        proj = a.get("project")
        if proj and proj not in by_slug:
            note(where, f"project '{proj}' not found")
        activities.append({
            "date": str(a.get("date", "")),
            "year": str(a.get("date", ""))[:4],
            "when": date_labels(a.get("date")),
            "title": bi(a, "title"),
            "place": bi(a, "place"),
            "text": {"es": md_block(a.get("text")), "en": md_block(a.get("text_en")) if a.get("text_en") else Markup("")},
            "links": it_links(a.get("links"), root, where),
            "images": it_media(a.get("images"), root, where),
            "project": proj if proj in by_slug else "",
            "project_title": bi(by_slug[proj]["meta"], "title") if proj in by_slug else None,
            "check": a.get("check"),
        })
    activities.sort(key=lambda a: a["date"], reverse=True)
    seen = {}
    for a in activities:  # unique anchors, e.g. 2015-12 and 2015-12-2
        seen[a["date"]] = seen.get(a["date"], 0) + 1
        a["anchor"] = a["date"] if seen[a["date"]] == 1 else f"{a['date']}-{seen[a['date']]}"
    years = []
    for a in activities:
        if not years or years[-1]["year"] != a["year"]:
            years.append({"year": a["year"], "items": []})
        years[-1]["items"].append(a)

    # Publications
    pubs = []
    for p in it_load_list("publicaciones.yml", drafts):
        where = "intercambios/publicaciones.yml"
        pubs.append({
            "year": p.get("year") or "",
            "authors": p.get("authors") or "",
            "lang": p.get("lang") or "es",
            "title": md_inline(p.get("title")),
            "title_en": md_inline(p.get("title_en")),
            "venue": bi(p, "venue"),
            "pdf": asset(p.get("pdf"), "../", where) if p.get("pdf") else "",
            "page": f"textos/{p['page']}.html" if p.get("page") else "",
            "url": p.get("url") or "",
            "check": p.get("check"),
        })
    pubs.sort(key=lambda e: year_key(e) if e["year"] else 0, reverse=True)  # undated last

    team = load_yaml(IT / "equipo.yml") or []
    team_groups = [{"title": bi(g, "title"),
                    "people": [{"name": x.get("name"), "role": bi(x, "role")} for x in g.get("people") or []]}
                   for g in team]

    title = "Intercambios Transorgánicos"
    list_views = [it_project_view(p, "../") for p in projects]
    render("it_index.html", "intercambios/index.html", "../", page_kind="it-home",
           page_title=title, description=plain(programa_meta.get("lede")),
           programa={"lede": bi(programa_meta, "lede"), "quote": bi(programa_meta, "quote"),
                     "quote_by": programa_meta.get("quote_by", ""),
                     "questions": programa_meta.get("questions") or [],
                     "questions_en": programa_meta.get("questions_en") or [],
                     "body": bi_body(programa_body, "../")},
           team=team_groups, projects=list_views, recent=activities[:4], **common)
    render("it_projects.html", "intercambios/proyectos.html", "../", page_kind="it-projects",
           page_title=f"Proyectos | {title}", projects=list_views, **common)
    views = [it_project_view(p, "../../") for p in projects]
    for i, v in enumerate(views):
        related = [a for a in activities if a["project"] == v["slug"]]
        render("it_project.html", f"intercambios/proyectos/{v['slug']}.html", "../../",
               page_kind="it-project", page_title=f"{v['title_text']} | {title}",
               description=v["summary_text"], project=v, related=related,
               previous=views[i - 1] if i > 0 else None,
               next=views[i + 1] if i + 1 < len(views) else None, **common)
    render("it_activities.html", "intercambios/actividades.html", "../", page_kind="it-activities",
           page_title=f"Actividades | {title}", years=years, **common)
    render("it_publications.html", "intercambios/publicaciones.html", "../", page_kind="it-publications",
           page_title=f"Publicaciones | {title}", pubs=pubs, **common)
    for path in sorted((IT / "textos").glob("*.md")):
        meta, body = read_page(path)
        render("it_text.html", f"intercambios/textos/{path.stem}.html", "../../", page_kind="it-text",
               page_title=f"{plain(meta.get('title'))} | {title}", description=plain(meta.get("summary")),
               text={"title": bi(meta, "title"), "author": meta.get("author", ""), "date": meta.get("date", ""),
                     "note": bi(meta, "note"), "body": bi_body(body, "../../")}, **common)


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
    projects = load_projects(args.drafts)

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

    # Home: about + publications
    about_en = (CONTENT / "about.en.md")
    about_es = (CONTENT / "about.es.md")
    groups = [
        {"lang": "en", "label": "English", "items": [p for p in pubs if p["lang"] == "en"]},
        {"lang": "es", "label": "Español", "items": [p for p in pubs if p["lang"] == "es"]},
    ]
    render(
        "home.html", "index.html", "",
        page_kind="home",
        page_title=site.get("name", ""),
        fragment=args.fragment_home,
        about_en=md_block(about_en.read_text(encoding="utf-8")) if about_en.exists() else "",
        about_es=md_block(about_es.read_text(encoding="utf-8")) if about_es.exists() else "",
        pub_groups=[g for g in groups if g["items"]],
        fono=fono,
    )

    # Projects list and one page per project
    render("projects.html", "projects.html", "",
           page_kind="projects", page_title=f"Projects | {site.get('name', '')}",
           projects=[project_view(p, "") for p in projects])
    views = [v for v in (project_view(p, "../") for p in projects) if not v["link"]]
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
    cv_pdf = ""
    if site.get("cv_pdf"):
        if (ROOT / str(site["cv_pdf"]).lstrip("/")).exists():
            cv_pdf = asset(site["cv_pdf"], "", "site.yml (cv_pdf)")
        else:
            note("site.yml (cv_pdf)", f"add your CV as {site['cv_pdf']} to show the download button")
    render("cv.html", "cv.html", "", page_kind="cv", page_title=f"CV | {site.get('name', '')}",
           sections=sections, cv_pdf=cv_pdf)

    # Intercambios Transorgánicos section
    build_intercambios(render, args.drafts)

    print(f"Built {pages} pages into _site/")
    unique = list(dict.fromkeys(NOTES))
    if unique:
        print(f"\n{len(unique)} things to fill in or check:")
        for n in unique:
            print("  -", n)


if __name__ == "__main__":
    main()
