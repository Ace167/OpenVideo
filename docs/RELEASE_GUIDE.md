# OpenVideo Downloader — Release- en Distributiehandleiding

Deze handleiding beschrijft het volledige releaseproces voor OpenVideo Downloader, van versiebeheer tot het bouwen van de Windows-installer en publicatie op GitHub.

---

## 1. Versiebeheer en voorbereiding

OpenVideo Downloader volgt [SemVer (Semantic Versioning)](https://semver.org/).

### Stappen voor een nieuwe release:

1. **Versienummer bijwerken:**
   Werk het versienummer bij in de volgende bestanden:
   - `pyproject.toml` (`version = "x.y.z"`)
   - `src/open_video_downloader/__init__.py` (`__version__ = "x.y.z"`)
   - `installer/open_video_downloader.iss` (`#define MyAppVersion "x.y.z"`)

2. **Changelog bijwerken (`CHANGELOG.md`):**
   - Verplaats de items onder `## [Unreleased]` naar een nieuwe sectie: `## [x.y.z] - YYYY-MM-DD`.
   - Groepeer wijzigingen onder `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

3. **Kwaliteitscontroles uitvoeren:**
   ```powershell
   pytest
   ruff check .
   ruff format --check .
   mypy src
   ```

---

## 2. Lokale Windows-build maken

### Stap 1: Bouw de standalone Windows-executable
Voer het automatische buildscript uit:
```powershell
python scripts/build_windows.py
```
Dit script:
- Verifieert de aanwezigheid van `open_video_downloader.spec` en het applicatie-icoon (`assets/app_icon.ico`).
- Voert PyInstaller uit in one-folder modus (`--onedir`, windowed zonder console).
- Plaatst het resultaat in `dist\OpenVideoDownloader\`.

### Stap 2: Voer de smoke test uit op de executable
```powershell
python scripts/smoke_test_binary.py
```
Dit controleert headless (`QT_QPA_PLATFORM=offscreen`) of de gebouwde `OpenVideoDownloader.exe` correct start zonder ontbrekende DLL's of initialisatiefouten.

### Stap 3: Bouw de Windows Setup Installer (Inno Setup)
Indien Inno Setup 6 geïnstalleerd is:
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\open_video_downloader.iss
```
Het installatieprogramma wordt gegenereerd in `dist\installer\OpenVideoDownloader-Setup-vx.y.z.exe`.

### Stap 4: Maak een portable ZIP-bestand
```powershell
Compress-Archive -Path dist\OpenVideoDownloader\* -DestinationPath dist\OpenVideoDownloader-portable-vx.y.z.zip -Force
```

---

## 3. SHA256-controlesommen genereren

Voor verificatie en integriteit door gebruikers:
```powershell
$files = Get-ChildItem -Path dist\installer\*.exe, dist\*.zip
$lines = foreach ($f in $files) {
    $hash = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash
    "$hash  $($f.Name)"
}
$lines | Out-File -Encoding utf8 dist\SHA256SUMS.txt
Get-Content dist\SHA256SUMS.txt
```

---

## 4. Testen van de installer & uninstaller

Voer vóór publicatie de volgende verificaties uit op een Windows 10/11-machine:

1. **Schone installatie:**
   - Start `OpenVideoDownloader-Setup-v0.1.0.exe`.
   - Controleer of de wizard in het Nederlands opent.
   - Installeer naar de standaardlocatie (`%LOCALAPPDATA%\Programs\OpenVideo Downloader` of `Program Files`).
   - Controleer of de applicatie start na afloop van de setup.

2. **Startmenu en snelkoppelingen:**
   - Controleer of de snelkoppeling "OpenVideo Downloader" in het Startmenu aanwezig is met het correcte blauwe icoon.

3. **Gegevensopslag:**
   - Controleer of de database `openvideo.db` en logbestanden netjes in `%LOCALAPPDATA%\OpenVideoDownloader\` worden bewaard en **niet** in de programma-installatiemap.

4. **Deïnstallatie (Uninstall):**
   - Verwijder de app via Windows Instellingen > Geïnstalleerde apps.
   - Controleer of de installatiemap netjes wordt opgeruimd.
   - **Cruciaal:** Controleer dat de downloads van de gebruiker (in de downloadmap) en instellingen/database **niet** verloren gaan.

---

## 5. Publicatie via GitHub Actions & GitHub Releases

### Automatisch via Git-tags:
1. Commit en push alle release-aanpassingen naar de `main`-branch:
   ```powershell
   git add pyproject.toml src/open_video_downloader/__init__.py CHANGELOG.md installer/open_video_downloader.iss
   git commit -m "chore: release v0.1.0"
   git push origin main
   ```
2. Maak een release-tag aan en push deze:
   ```powershell
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. De GitHub Actions-workflow `.github/workflows/release.yml` start automatisch:
   - Voert de PyInstaller-build uit op een `windows-latest` runner.
   - Compileert de Inno Setup-installer.
   - Pakt de portable zip in.
   - Berekent SHA256-checksums.
   - Maakt een officiële GitHub Release aan met de assets.

---

## 6. Belangrijke opmerking over Code Signing (SmartScreen)

Op dit moment is er geen commercieel Windows Authenticode-certificaat (EV/OV) gekoppeld aan het project. Hierdoor kan Windows SmartScreen bij de eerste download waarschuwen met: *"Windows heeft uw pc beschermd (Onbekende uitgever)"*.

Gebruikers kunnen klikken op **"Meer informatie"** > **"Toch uitvoeren"**. Dit is normaal voor open-source projecten zonder betaald code-signing certificaat en dient duidelijk in de documentatie vermeld te worden.
