
# Uitleg van `pisgstats.py`

Dit bestand bevat de volledige cog-implementatie. Belangrijke onderdelen:

- **Imports & regex**: regex om woorden, emoji’s, links en mentions te herkennen.
- **STOPWORDS**: lijst van woorden die genegeerd worden bij woord-statistieken.
- **Helper-functies**:
  - `tokenize`: zet tekst om in woorden.
  - `extract_emojis`: haalt emoji’s uit een tekst.
  - `svg_bar_chart` en `svg_bar_chart_vertical`: maken simpele SVG-grafieken voor HTML.

- **Class `PisgStats`**:
  - **config**: gebruikt Redbot Config om alles per guild (server) op te slaan.
  - **_update_stats_for_message**: verwerkt een bericht en update statistieken (woorden, emoji, links, gebruikersinfo).
  - **Listeners**:
    - `on_message`: vangt elk bericht.
    - `on_member_join` en `on_member_remove`: tellen joins/leaves.
  - **Commands** (`pstats`):
    - `pstats html`: genereert een HTML-rapport met grafieken, topwoorden, emoji’s en gebruikersinfo.

- **Gebruikersdata**:
  - Per gebruiker worden naam, aantal berichten, woorden, karakters, links, emoji’s, mentions opgeslagen.
  - Elke dag kan er een willekeurige quote worden bewaard.
  - Per gebruiker wordt ook een histogram van activiteit per uur bijgehouden (voor "actiefste uur").

- **HTML Output**:
  - Genereert een nette HTML-pagina met CSS-styling en SVG-grafieken.
  - Informatie per gebruiker (naam, berichten, actiefste uur, quote).
  - Secties voor topwoorden, emoji’s en globale statistieken.
