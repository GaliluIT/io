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
    if not (ROOT / path).exists():
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
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([\w-]{11})", src)
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
    }


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
    views = [project_view(p, "../") for p in projects]
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

    print(f"Built {pages} pages into _site/")
    unique = list(dict.fromkeys(NOTES))
    if unique:
        print(f"\n{len(unique)} things to fill in or check:")
        for n in unique:
            print("  -", n)


if __name__ == "__main__":
    main()
