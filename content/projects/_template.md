---
# HOW TO ADD A PROJECT
# 1. Copy this file and rename it, e.g. content/projects/my-project.md
#    The file name becomes the page address: projects/my-project.html
# 2. Put its images and short videos in a folder, e.g. assets/projects/my-project/
# 3. Fill in the fields below. Delete any you don't need.
# Files starting with _ (like this one) are not published.

title: Project title
years: 2024 – present
summary: One or two sentences. Shown on the projects list and at the top of the page.
order: 10            # lower numbers come first on the projects list
draft: false         # true = hidden on the live site, shown with --drafts

cover: assets/projects/my-project/cover.jpg   # image for the projects list (optional)

# A YouTube or Vimeo link, or a short .mp4 in assets/ (GitHub rejects files over 100 MB).
video: https://www.youtube.com/watch?v=XXXXXXXXXXX
# For several videos, use a list instead:
# videos:
#   - https://vimeo.com/123456789
#   - assets/projects/my-project/clip.mp4

images:
  - src: assets/projects/my-project/01.jpg
    caption: What the picture shows, and credit if needed.
  - src: assets/projects/my-project/02.jpg
    caption: Another one.

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
