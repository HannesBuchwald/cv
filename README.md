# Hannes Buchwald · CV & Portfolio

Die Inhalte liegen als Markdown mit OKF-Metadaten vor. `build_site.py` erstellt daraus die einfache, responsive HTML-Webseite in `site/`.

## Webseite aktualisieren

1. Markdown-Dateien und Bilder im Repository bearbeiten.
2. `python3 build_site.py` ausführen (keine zusätzlichen Pakete notwendig).
3. `site/index.html` direkt im Browser öffnen oder `python3 -m http.server 8765 --directory site` starten.

Die fertigen Dateien in `site/` lassen sich auf einem beliebigen statischen Webserver bereitstellen. Die private Sites-Vorschau wird separat aktualisiert; ein GitHub-Push allein veröffentlicht sie nicht automatisch.

## Inhalt

- `cv.md`: Lebenslauf und Qualifikationen.
- `Projekte/`: einzelne Projekte.
- `publications.md`: Awards, Papers, Konferenzen, Ausstellungen und Presse.
- `portraetfotografie.md`: fotografisches Portfolio; die Bildauswahl folgt.
- `assets/`: lokal gespeicherte Projektbilder.

Die Webseite erzeugt Projektseiten aus den Markdown-Dateien, erhält interne Links und bildet die vorhandenen einfachen Markdown-Strukturen ab. Sie enthält Projekt- und Publications-Filter, Smartphone-Layouts und eine Druckansicht. Offene biografische Angaben bleiben als solche gekennzeichnet.
