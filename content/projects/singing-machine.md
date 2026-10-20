---
title: Singing Machine
years: 2025 – present
summary: A browser-based singing instrument for people who have had a total laryngectomy. An ordinary webcam reads the movements of the mouth and hands, and the machine sings.
order: 1
cover: assets/projects/singing-machine/cover.jpg
cover_alt: A webcam image of a face covered in small blue tracking points, mouth open as if singing, in the Singing Machine.
details:
  Role: Lead researcher
  With: Ivica Ico Bukvic (Indiana University), technical collaborator
  Built with: MediaPipe and WebPd/PD-L2Ork, running in the browser
  Support: CFWPP Future of Work Student Summer Research Grant, Virginia Tech (2025)
  Shown at: ICAT Playdates, Virginia Tech; CMMR 2025, London; DRS2026, Edinburgh
images:
  - src: assets/projects/singing-machine/01.jpg
    alt: "Screenshot of the Singing Machine in use: a webcam image of a face covered in small blue tracking points, mouth open as if singing. Below it, live readings of the mouth's width and height and the vowel it chooses, and three sliders for vowel, loudness and pitch, with buttons for the eight notes of a major scale."
    caption: The mouth chooses the vowel; the sliders show what the machine sings.
  - src: assets/projects/singing-machine/02.jpg
    alt: "Screenshot of the Singing Machine with the face tilted sideways at the edge of the camera frame and the lips rounded; the tracking points follow the face, and the vowel and loudness sliders are at their maximum."
    caption: The tracking follows the face as it moves.
links:
  - label: "Play the Singing Machine in your browser (it needs a webcam; it is online under its earlier name, Song of the Voiceless)"
    url: https://l2ork.bukvic.net:3000/Song-of-the-Voiceless/
  - label: "Paper: Singing without a Larynx (CMMR 2025)"
    url: https://cmmr2025.prism.cnrs.fr/demos/
  - label: "Paper: Re-voicing Identity (DRS2026)"
    url: https://doi.org/10.21606/drs.2026.1993
check: Add a short video of the Singing Machine being played (a screen recording with sound works), on YouTube or Vimeo.
---
After a total laryngectomy, most voice technology aims at one thing: bringing speech back to a functional standard. The Singing Machine starts from a different question. What would it take to sing?

The instrument runs in a web browser, with nothing to install. An ordinary webcam tracks the shape of the mouth and the movements of the hands; the mouth chooses the vowel and the hands shape the sound, which a synthesizer sings in real time. It needs no airflow and no vocal folds, only the gestures of the person playing it.

I treat it as a research product as much as an instrument: a way to ask what a voice is for, and to design for expression and identity rather than only for function. With two undergraduate research assistants, I am now moving it to an independent, documented open-source codebase.
