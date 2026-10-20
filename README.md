# Gala Lucia Gonzalez Barrios: website

A small static site for GitHub Pages. All the text lives in `content/`, the images and files in `assets/`. GitHub rebuilds and publishes the site every time you push.

## Where things are

| To change | Edit |
|---|---|
| Name, tagline, profile links (LinkedIn, Instagram…), the 3D object | `content/site.yml` |
| About text | `content/about.en.md` and `content/about.es.md` (the home page shows the first paragraph, the About page all of it) |
| Your photo on the About page | `assets/about/portrait.jpg`, and its description `portrait_alt` in `content/site.yml` |
| Publications (home page and CV) | `content/publications.yml` (`lang: en` or `lang: es` picks the column) |
| CV | `content/cv.yml` (the PDF is made from it, see below) |
| Projects | one file per project in `content/projects/` |
| Colors and fonts | `assets/style.css` (the variables at the top; fonts are in `assets/fonts/`) |

## Accessibility

- Every page has a **Display** bar at the top: Light, Dark or High contrast. Until a visitor picks one, the site follows their device settings (dark mode, more contrast). The choice is remembered.
- Every image needs an `alt`: a sentence describing what it shows, for people who can't see it. The build lists any image without one. Describe what is in the picture; the caption can add the context.
- Videos need a `title`. A video file (not YouTube or Vimeo) also needs a `description` of what happens in it.
- The 3D object turns slowly, with a button to stop it; it stays still for visitors who ask their device for reduced motion, and it can be turned with the arrow keys.
- Links to PDFs say "(PDF)".

## The CV PDF

The "Download the CV (PDF)" button gives a PDF printed from the CV page, so it always matches `content/cv.yml`. GitHub makes it each time it publishes. To make it yourself (you need Chrome):

```
python build.py
python make_cv_pdf.py --save
```

`--save` updates the copy kept in `assets/cv/`. The PDF shows your name, website and LinkedIn at the top, and never a phone number or email.

## Intercambios Transorgánicos page (Spanish and English)

galalucia.com/intercambios is one page that introduces the program and sends visitors to its own website, intercambiostransorganicos.org. Its content lives in `content/intercambios/`:

| To change | Edit |
|---|---|
| Introduction, students, recognition, the website address | `content/intercambios/programa.md` |
| Projects (a picture, a line, and a link or video) | `content/intercambios/proyectos.yml` |
| Team | `content/intercambios/equipo.yml` |
| Long texts | `content/intercambios/textos/` |

Every text field can have an English version with the same name plus `_en` (`title` / `title_en`). In Markdown files, the Spanish text comes first, then a line `<!-- en -->`, then the English text. If there is no English version, the Spanish text shows in both languages. Visitors switch language with the Español / English buttons; the page opens in Spanish.

Before adding photos, check they don't show children's faces, and resize them to about 1600 px wide. Photos from a phone carry the place they were taken; resizing them with the method in the next section removes it.

## Add a project

1. Copy `content/projects/_template.md` to `content/projects/your-project.md`.
2. Make a folder `assets/projects/your-project/` and put the images there.
3. Fill in the fields at the top of the file and write the text underneath. The first image is the picture on the Projects page, unless you set `cover`.
4. Commit and push. The page appears at `projects/your-project.html`.

Videos: a YouTube or Vimeo link is best. Short, silent `.mp4` clips can go in `assets/` (keep them under a few MB).

To make photos web-ready (smaller, upright, and without the camera's location data):

```
python -c "from PIL import Image, ImageOps; im = ImageOps.exif_transpose(Image.open('photo.jpg')).convert('RGB'); im.thumbnail((1600, 1600)); im.save('01.jpg', quality=82)"
```

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

`assets/fono/fono.glb` is Fonocosa Aldo, reduced from the original STL (about 500,000 triangles, 24 MB) to about 76,000 triangles (1 MB) so it loads quickly. `poster.webp` is the still image shown while it loads. Its color changes with the display: graphite on light backgrounds, pale on dark ones (`assets/site.js`). To remove the object, delete the `fono:` block in `content/site.yml`.
