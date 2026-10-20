# Gala Lucia Gonzalez Barrios: website

A small static site for GitHub Pages. All the text lives in `content/`, the images and files in `assets/`. GitHub rebuilds and publishes the site every time you push.

## Where things are

| To change | Edit |
|---|---|
| Name, tagline, links, the 3D object | `content/site.yml` |
| About text | `content/about.en.md` and `content/about.es.md` |
| Publications (home page and CV) | `content/publications.yml` (`lang: en` or `lang: es` picks the column) |
| CV | `content/cv.yml`, and your PDF at `assets/cv/cv.pdf` |
| Projects | one file per project in `content/projects/` |
| Colors and fonts | `assets/style.css` (the variables at the top) |

## Intercambios Transorgánicos section (Spanish and English)

Everything for galalucia.com/intercambios lives in `content/intercambios/`:

| To change | Edit |
|---|---|
| Program page (intro, approach, questions) | `content/intercambios/programa.md` |
| Team | `content/intercambios/equipo.yml` |
| Projects | one file per project in `content/intercambios/proyectos/` (copy `_plantilla.md`) |
| Activities timeline | `content/intercambios/actividades.yml` |
| Publications | `content/intercambios/publicaciones.yml`, PDFs in `assets/intercambios/pdf/` |
| Long texts | `content/intercambios/textos/` |
| Images | `assets/intercambios/<project-or-activity>/` |

Every text field can have an English version with the same name plus `_en` (`title` / `title_en`). In Markdown files, the Spanish text comes first, then a line `<!-- en -->`, then the English text. If there is no English version, the Spanish text shows in both languages. Visitors switch language with the Español / English buttons; the section opens in Spanish.

Before adding photos, check they don't show children's faces, and resize them to about 1600 px wide.

## Add a project

1. Copy `content/projects/_template.md` to `content/projects/your-project.md`.
2. Make a folder `assets/projects/your-project/` and put the images there.
3. Fill in the fields at the top of the file and write the text underneath.
4. Commit and push. The page appears at `projects/your-project.html`.

Videos: a YouTube or Vimeo link is best. Short `.mp4` clips can go in `assets/`, but GitHub rejects any file over 100 MB.

To keep a project hidden while you work on it, set `draft: true`.

## Preview on your computer

```
pip install -r requirements.txt
python build.py --drafts
python -m http.server --directory _site
```

Open http://localhost:8000. `--drafts` also shows placeholders and your "check" notes in blue. The build lists everything still to fill in.

## Put it online (once)

1. On GitHub, create a repository named `GaliluIT.github.io` (your username followed by `.github.io`) for the address `https://galiluit.github.io`. Any other name works too, and the site then lives at `https://galiluit.github.io/<repo-name>/`.
2. Push this folder to it.
3. In the repository go to **Settings → Pages**, and under **Build and deployment** set **Source** to **GitHub Actions**.
4. Wait a minute for the "Publish site" action in the **Actions** tab to finish.

After that, every push republishes the site.

## The domain

The site is served at https://galalucia.com. The domain is set in **Settings → Pages → Custom domain** and in the `CNAME` file. Its DNS (at GoDaddy) points to GitHub: four A records for `@` (185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153) and a CNAME record for `www` pointing to `galiluit.github.io`.

## The 3D object

`assets/fono/fono.glb` is FonoAldo, reduced from the original STL (about 500,000 triangles, 24 MB) to about 76,000 triangles (1 MB) so it loads quickly. `poster.webp` is the still image shown while it loads. To remove the object, delete the `fono:` block in `content/site.yml`.
