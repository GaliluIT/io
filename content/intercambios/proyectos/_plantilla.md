---
# CÓMO AGREGAR UN PROYECTO A INTERCAMBIOS TRANSORGÁNICOS
# 1. Copiá este archivo y renombralo, por ejemplo: content/intercambios/proyectos/mi-proyecto.md
#    El nombre del archivo es la dirección de la página: intercambios/proyectos/mi-proyecto.html
# 2. Poné las imágenes en una carpeta: assets/intercambios/mi-proyecto/ (JPG de hasta ~1600 px de ancho).
# 3. Completá los campos. Cualquier campo puede tener versión en inglés agregando _en (title_en, summary_en...).
# Los archivos que empiezan con _ (como este) no se publican.

title: Nombre del proyecto
title_en: Project name (solo si cambia en inglés)
years: 2024 – presente
years_en: 2024 – present
order: 10                 # orden en la lista de proyectos (menor = primero)
summary: Una o dos oraciones. Aparece en la lista y arriba de la página.
summary_en: One or two sentences, in English.

video: https://www.youtube.com/watch?v=XXXXXXXXXXX   # YouTube o Vimeo (opcional)

details:                  # datos breves al costado del texto
  - label: Dirección
    label_en: Director
    value: Nombre Apellido

links:
  - label: Nota en un diario
    label_en: Newspaper article
    url: https://...

images:                   # la primera imagen es la portada en la lista
  - src: assets/intercambios/mi-proyecto/01.jpg
    caption: Qué muestra la foto.
    caption_en: What the photo shows.
---
Texto en español. Las líneas en blanco separan párrafos. Se puede usar **negrita**, *itálica* y [enlaces](https://...).

<!-- en -->

English text goes here, after the line above.
