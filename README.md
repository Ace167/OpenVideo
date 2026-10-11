# OpenVideo Downloader

[![CI](https://github.com/Ace167/OpenVideo/actions/workflows/ci.yml/badge.svg)](https://github.com/Ace167/OpenVideo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows 10/11](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://github.com/Ace167/OpenVideo)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

Een moderne, betrouwbare en privacyvriendelijke desktopapplicatie voor Windows om video's en audio te downloaden van ondersteunde webplatforms. Gebouwd met Python, PySide6 (Qt 6), yt-dlp en SQLite.

> **Disclaimer:** OpenVideo Downloader is een onafhankelijk open-source project en is niet gelieerd aan, gesponsord door of officieel verbonden met YouTube, Google of enig ander mediaplatform. Gebruikers zijn zelf verantwoordelijk voor naleving van de toepasselijke wetgeving, auteursrechten en de gebruiksvoorwaarden van de bezochte platforms. OpenVideo omzeilt expliciet géén DRM of toegangsbeveiligingen.

---

## 🌟 Belangrijkste functionaliteiten

- **Windows 11 Fluent interface:** Moderne navigatiekolom, vloeiende animaties en dynamische ondersteuning voor lichte en donkere thema's.
- **Uitgebreide downloadengine:** Aangedreven door `yt-dlp` met asynchrone achtergrondworkers (`QThread`) zodat de gebruikersinterface altijd responsief blijft.
- **Multitasking wachtrijbeheer:** Configureerbare gelijktijdige downloads, live voortgangsbalken, downloadsnelheid (MB/s), ETA en veilige taakannulering.
- **SQLite-downloadgeschiedenis:** Volledige lokale persistentie met automatische schemamigraties, live zoeken (op titel, URL of bestandsnaam), filteren op status en sorteren op datum.
- **Robuust bij crashes en herstart:** Onderbroken actieve downloads worden bij herstart automatisch gemarkeerd en veilig hersteld.
- **Slimme FFmpeg-integratie:** Automatische detectie van FFmpeg op het systeem of in lokale mappen (`bin/`). Beschikt over een automatische terugval naar progressieve streams (video en audio gecombineerd) wanneer FFmpeg niet aanwezig is.
- **Privacy & Lokale opslag:** Geen telemetry, geen cloudservers en automatische redactie van gevoelige gegevens (tokens, cookies, gebruikersnamen) in diagnostische logs.

---

## 💻 Download & Installatie (Windows)

OpenVideo Downloader is beschikbaar als **Windows Installer** of als **Portable ZIP**:

### Optie 1: Windows Installer (Aanbevolen)
1. Ga naar [Releases](https://github.com/Ace167/OpenVideo/releases) en download de nieuwste `OpenVideoDownloader-Setup-v0.1.0.exe`.
2. Start het installatieprogramma en volg de stappen in de Nederlandstalige installatiewizard.
3. Start de applicatie eenvoudig vanuit het Startmenu.
4. *Deïnstalleren:* Verwijderen kan te allen tijde via Windows *Instellingen > Geïnstalleerde apps*. Jouw gedownloade bestanden en instellingen blijven daarbij veilig behouden.

### Optie 2: Portable Versie (Geen installatie nodig)
1. Download `OpenVideoDownloader-portable-v0.1.0.zip` via de [Releases](https://github.com/Ace167/OpenVideo/releases)-pagina.
2. Pak het zip-bestand uit in een map naar keuze.
3. Start `OpenVideoDownloader.exe`.

> [!NOTE]
> **Windows SmartScreen melding:** Omdat dit een open-source project is zonder commercieel Authenticode-certificaat, kan Windows SmartScreen bij de eerste start een waarschuwing tonen (*"Windows heeft uw pc beschermd"*). Klik op **Meer informatie** en vervolgens op **Toch uitvoeren**.

---

## 🎬 FFmpeg & Hoge Kwaliteit (1080p / 4K)

### Hoe werkt het?
- **Zonder FFmpeg:** OpenVideo Downloader werkt direct uit de doos! Wanneer FFmpeg ontbreekt, downloadt de applicatie automatisch de hoogste beschikbare progressieve stream (waarin beeld en geluid al door het platform zijn samengevoegd, veelal tot 720p).
- **Met FFmpeg:** Platforms zoals YouTube splitsen resoluties van 1080p, 1440p en 4K in losse video- en audiostreams. Met FFmpeg voegt OpenVideo deze na het downloaden automatisch samen tot één hoogwaardig videobestand.

### Optioneel FFmpeg installeren:
Wil je 1080p of 4K downloaden? Installeer FFmpeg via één van de volgende methoden:
- **Via Windows Package Manager (winget):**
  ```powershell
  winget install Gyan.FFmpeg
  ```
- **Portable in applicatiemap:**
  Plaats `ffmpeg.exe` en `ffprobe.exe` simpelweg in de installatiemap of in een submap genaamd `bin\`. OpenVideo detecteert dit automatisch.

---

## 🛠️ Ontwikkeling & Lokale Setup

### Vereisten
- Windows 10 / 11 (64-bit)
- Python 3.10 of nieuwer (aanbevolen: Python 3.12)
- Git

### Installatiestappen
1. **Clone de repository:**
   ```powershell
   git clone https://github.com/Ace167/OpenVideo.git
   cd OpenVideo
   ```

2. **Maak een virtuele omgeving en activeer deze:**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Installeer development-dependencies en het package:**
   ```powershell
   pip install -e ".[dev]"
   ```

4. **Start de applicatie vanuit de broncode:**
   ```powershell
   open-video-downloader
   # of via het Python-modulecommando:
   python -m open_video_downloader
   ```

---

## 🧪 Kwaliteitscontroles & Tests

Het project hanteert strikte kwaliteitsstandaarden voor alle commits en pull requests:

```powershell
# Voer de volledige testsuite uit (unit- en UI-tests met pytest-qt):
pytest

# Voer de linter uit:
ruff check .

# Controleer codeformattering:
ruff format --check .

# Controleer statische type-definities:
mypy src
```

---

## 📦 Zelf een Windows-build maken

Een standalone distributie en installer bouwen kan lokaal met de meegeleverde scripts:

```powershell
# 1. Bouw de standalone executable met PyInstaller:
python scripts/build_windows.py

# 2. Voer de headless smoke-test uit op de gebouwde binary:
python scripts/smoke_test_binary.py

# 3. Compileer de Inno Setup installer (vereist Inno Setup 6):
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\open_video_downloader.iss
```

Het resultaat is te vinden in:
- Executable: `dist\OpenVideoDownloader\OpenVideoDownloader.exe`
- Installer: `dist\installer\OpenVideoDownloader-Setup-v0.1.0.exe`

---

## 🔒 Privacy & Veiligheid

- **100% Offline & Lokaal:** Er worden geen telemetriegegevens, foutrapporten of gebruikersstatistieken verzameld of verzonden.
- **Logboekredactie:** Foutopsporingslogs worden lokaal bewaard in `%LOCALAPPDATA%\OpenVideoDownloader\logs\app.log`. Gevoelige URL-tokens, gebruikersnamen en sessiecookies worden automatisch gemaskeerd.
- **Bestandsbeveiliging:** Downloadbestanden worden niet stilzwijgend overschreven of verwijderd.

---

## ⚠️ Bekende beperkingen

1. **DRM-beschermde media:** Content beschermd met DRM (zoals Netflix, Spotify, Disney+) wordt niet ondersteund en kan niet worden gedownload.
2. **Platformwijzigingen:** Videoplatforms veranderen regelmatig hun interne API's. Wanneer een extractie faalt, kan een update van `yt-dlp` (`pip install --upgrade yt-dlp`) nodig zijn.
3. **FFmpeg vereist voor gescheiden DASH-streams:** Losse videostreams (1080p/4K) vereisen FFmpeg om samengevoegd te worden met audio.

---

## 🤝 Bijdragen & Problemen melden

Bijdragen zijn van harte welkom! Lees onze [CONTRIBUTING.md](CONTRIBUTING.md) voor richtlijnen en ontwikkelafspraken.

- **Fout gevonden?** [Meld een bug](https://github.com/Ace167/OpenVideo/issues/new?template=bug_report.md)
- **Idee voor een functie?** [Dien een functieverzoek in](https://github.com/Ace167/OpenVideo/issues/new?template=feature_request.md)
- **Beveiligingslek?** Zie ons beveiligingsbeleid in [SECURITY.md](SECURITY.md).

---

## 📄 Licentie

OpenVideo Downloader is gelicenseerd onder de [MIT License](LICENSE).  
Overzicht van gebruikte externe bibliotheken en componenten: zie [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
