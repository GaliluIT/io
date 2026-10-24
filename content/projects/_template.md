---
# HOW TO ADD A PROJECT
# 1. Copy this file and rename it, e.g. content/projects/my-project.md
#    The file name becomes the page address: projects/my-project.html
# 2. Put its images and short videos in a folder, e.g. assets/projects/my-project/
# 3. Fill in the fields below. Delete any you don't need.
# Files starting with _ (like this one) are not published.

title: Project title
years: 2024 – present
summary: One or two sentences. Shown on the Projects page and at the top of the page.
order: 10            # projects are listed by starting year; order only sorts projects that started the same year
draft: false         # true = hidden on the live site, shown with --drafts
status: ""           # optional label next to the years, e.g. Work in progress

# The picture on the Projects page is the first image below.
# To use a different one, set cover and describe it in cover_alt.
# cover: assets/projects/my-project/cover.jpg
# cover_alt: What the cover shows.

# Optional: a large image at the top of the page.
# hero:
#   src: assets/projects/my-project/hero.jpg
#   alt: What it shows.
#   caption: Optional caption.

# Videos: YouTube or Vimeo links, or a short silent .mp4 in assets/.
# Give each one a title. A file also needs a poster (a still) and a description of what happens in it.
videos:
  - url: https://www.youtube.com/watch?v=XXXXXXXXXXX
    title: What the video is
#  - url: assets/projects/my-project/clip.mp4
#    poster: assets/projects/my-project/clip-poster.jpg
#    title: What the clip is
#    description: What happens in it, for people who can't see it.

# alt: what the picture shows, for people who can't see it (required).
# caption: optional context under the picture: what, where, when, credit.
# wide: true makes a picture take the full width of the page, above the rest.
images:
  - src: assets/projects/my-project/01.jpg
    alt: Two people play a laptop instrument on a dark stage.
    caption: Premiere, Blacksburg, 2025. Photo by Name.
  - src: assets/projects/my-project/02.jpg
    alt: Another description.
    caption: Another caption.

# Short facts shown next to the text. Any labels you like.
details:
  Role: Concept and design
  With: Collaborator names
  Support: Funder or host
  Shown at: Venue, city, year

links:
  - label: Paper
    url: https://doi.org/...
---
Write the project text here in Markdown. Blank lines separate paragraphs.

You can use **bold**, *italics*, [links](https://example.org) and images:

![Description of the image](assets/projects/my-project/03.jpg)
