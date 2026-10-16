Bewake AI Download Manager – Windows-Prototyp 0.6.0
===================================

START / WEITERGEBEN
Empfohlen: Bewake-AI-Download-Manager-Setup.exe starten. Der Assistent installiert die App
für dein Windows-Konto, erstellt Startmenü- und auf Wunsch Desktop-Verknüpfungen
und richtet einen Eintrag zum Deinstallieren unter Windows-Einstellungen ein.
Python, Laufzeitbibliotheken und Benachrichtigungsmodul sind bereits enthalten.
Beim ersten Start öffnet sich die dunkle Ersteinrichtung: Download-Ordner prüfen,
Comfy Desktop automatisch erkennen oder Datenordner hinzufügen und Ziele prüfen.
Die App und das Setup verwenden Dark Mode. Native Windows-Ordnerdialoge folgen
gegebenenfalls dem Windows-Design.

Alternativ portable verwenden:
Bewake-AI-Download-Manager-Windows.zip entpacken, dann BewakeAIDownloadManager.exe starten.
Der gesamte Ordner muss zusammenbleiben. Python und eine GPU sind nicht nötig.
Windows 10/11 x64. Die EXE ist nicht signiert; Windows kann eine Warnung anzeigen.
HINTERGRUNDBETRIEB / AUTOSTART
Minimieren verschiebt die App in den Systemtray neben der Uhr; die Überwachung
läuft weiter, ohne dauerhaftes Fenster in der Taskleiste. Das Symbol kann unter
dem Pfeil für ausgeblendete Symbole liegen. Doppelklick oder Rechtsklick → Öffnen
zeigt die App wieder. Auch ein erneuter Start über die Verknüpfung öffnet sie.
Standardmäßig läuft die App beim Schließen ebenfalls im Tray weiter.
Vollständig beenden: Rechtsklick auf das Tray-Symbol → Beenden.
Unter Einstellungen ist dieses Verhalten beim Schließen abschaltbar.
„Mit Windows starten (direkt im Systemtray)“ ist im Setup und in Einstellungen
wählbar und anfangs aus. Es gilt für das aktuelle Windows-Konto bei der Anmeldung.
Autostart aktiviert keine Sortierautomatik. Die neue Ablage wird gesondert unter
„Zielordner & Automatik“ gewählt. Alternativ sind eigene automatische Regeln möglich.
Bei fehlendem Tray bleibt das Fenster erreichbar. Kein Windows-Dienst.

ERSTER TEST
1. Einen leeren Testordner anlegen und über „Download-Ordner“ auswählen.
2. Testdateien hineinkopieren, z. B. foto.jpg, mein_lora.safetensors oder einen
   echten ComfyUI-Workflow als JSON. Mindestens 10–15 Sekunden warten.
3. Datei anklicken. Kategorie korrigieren und einen Test-Zielordner wählen.
4. „Vorschau / Details“ zeigt Text oder Modell-Metadaten, ohne Dateien auszuführen.
5. „Verschieben“ bestätigen. Anschließend „Undo“ testen.
6. Erst nach erfolgreichem Test den echten Downloads-Ordner auswählen.

NEUE DOWNLOADS AUTOMATISCH ABLEGEN
Nach der Ersteinrichtung öffnet sich „Zielordner & Automatik“. Dies ist auch
jederzeit über die Hauptansicht erreichbar. Im Reiter „Dateitypen“ Ziele für
Bilder, Videos, Audio, Dokumente, Archive, Programme und Sonstiges festlegen.
Unter „Comfy Desktop“ die gewünschte Installation auswählen und die Ziele für
LoRA, Checkpoint, VAE, ControlNet, Diffusionsmodelle, Textencoder, Upscaler,
Embeddings und Workflows prüfen. Pro Installation bleiben die Pfade anpassbar.
Im Reiter „Automatik“ die Ablage neuer Downloads einschalten und speichern.

Beim Aktivieren wird ein Startzeitpunkt zusammen mit den vorhandenen Dateien
gespeichert. Nur danach neu angelegte Downloads aus diesem Ordner werden
automatisch einsortiert. Alte Dateien, schon laufende Downloads und Dateien
aus anderen Ordnern bleiben ausgenommen. Der Startzeitpunkt bleibt bei Neustarts
erhalten. Aus- und erneutes Einschalten oder Wechseln des Download-Ordners setzt
die Grenze neu. Kopien mit künstlich erhaltenem altem Erstellungsdatum können
vorsichtshalber zur manuellen Prüfung liegen bleiben.
Die bisherige Regelautomatik wird durch diesen Modus ersetzt, solange er aktiv
ist. Ziele kommen aus der Kategorie-Einrichtung, nicht aus alten Regelzielen.
Bei unklarem Modelltyp, fehlendem Ziel, Duplikaten oder Konflikten bleibt die
Datei zur Prüfung liegen. Programme werden nicht gestartet, Archive nicht entpackt.
Undo nimmt die wiederhergestellte Datei von der Automatik aus.

COMFY DESKTOP (BEVORZUGT) / COMFYUI
„Comfy Desktop erkennen“ liest installations.json und settings.json unter
%APPDATA%\Comfy Desktop. Abgeschlossene lokale Installationen erscheinen mit Namen.
Cloud-Einträge und laufende/fehlgeschlagene Installationen werden übersprungen.
Als Downloadziele werden die eigenen Modellordner der Installation verwendet,
keine Shared-Bibliothek und keine externen YAML-Modellpfade. Workflows bleiben beim Benutzer-
ordner der gewählten Installation. Adoptierte Datenordner und Startargumente
--user-directory und --base-directory werden ebenfalls berücksichtigt.
Bei zusätzlichen Benutzerprofilen das Workflow-Ziel manuell korrigieren.

Ältere Desktop-Versionen: %APPDATA%\ComfyUI\config.json (basePath) und
extra_models_config.yaml werden ebenfalls gelesen. Der Programmordner ist nicht
automatisch der richtige Modellordner. Desktop-Konfigurationen werden nie verändert.

In der Hauptansicht „Installation / Modellbibliothek“ wählen. Darunter erscheinen
die passenden Ziele. Modelle verwenden models/loras, models/checkpoints usw.
innerhalb der gewählten Dateninstallation. Shared wird nicht benötigt und nicht
angelegt. Vorhandene Shared-Dateien werden nicht verschoben oder gelöscht.
Workflows verwenden user/default/workflows pro Instanz.
Die Ersteinrichtung zeigt erkannte LoRA- und Workflow-Ziele zur Prüfung an.

„Ordner manuell hinzufügen“ akzeptiert ComfyUI-Datenordner und Portable-Elternordner.
„Zielpfad setzen“ speichert einen zusätzlichen Kategoriepfad.
„YAML-Pfade importieren“ liest base_path und Modellpfade als mehrzeiligen Text
oder Liste. Keine vollständige Laufwerkssuche. Modelle werden nicht gescannt.

REGELN / SICHERHEIT
Anfangs ist die Automatik aus. „Regel merken“ speichert ein selbst gewähltes
Dateimuster, Kategorie und Ziel. Automatik erfordert Zustimmung sowohl für die
einzelne Regel als auch unter Einstellungen. Die erste passende Regel gewinnt.
Breite Muster nur nach Prüfung verwenden. „Regeln“ zeigt und löscht Regeln.
Bestehende Downloads werden ebenfalls vorgeschlagen; Überwachung ist nicht rekursiv.
Unvollständige Endungen und zugehörige Teildateien werden übersprungen.
Eine Datei muss 10 Sekunden unverändert sein; unter Windows wird außerdem geprüft,
ob sie exklusiv lesbar ist. Dies ist eine Heuristik, keine Browser-Abschlussmeldung.
Ein pausierter Download ohne erkennbare Teildatei kann wie eine fertige Datei wirken.

Vor dem Entfernen der Quelle wird ins Ziel kopiert und SHA-256 geprüft; Änderungen
während des Kopierens brechen den Vorgang ab. Namenskonflikte überschreiben nichts.
Identische Inhalte unter anderem Namen im gewählten Zielordner werden blockiert.
Kein globaler Duplikatindex. Große Modelle benötigen temporär zusätzlichen Platz.
Undo stellt den letzten verschobenen Inhalt wieder her, sofern dieser unverändert
ist und der ursprüngliche Name frei ist. Wiederholt aufrufbar; kein Redo.
Bei Stromausfall/Abbruch können zwei Kopien verbleiben. prepare/copied/move im
Protokoll helfen bei manueller Prüfung; keine automatische Absturzwiederherstellung.
Vorhandene Dateien werden nie ausgeführt; .ckpt/.pt werden nicht per Pickle geladen.
Vorschau ist derzeit Text/Metadaten, keine Bild-/Video-Vorschau.

LOKALE KI (OPTIONAL)
Ohne KI funktioniert alles auf CPU. In „Einrichtung“ oder „Einstellungen“ kann
„KI automatisch einrichten“ gewählt werden. Nach Bestätigung installiert die App
bei Bedarf Ollama über den Windows-App-Installer (winget) und lädt qwen3:4b.
Internet und mindestens 8 GB freier Speicher empfohlen; Modell ca. 2,5 GB.
Die Erstinstallation kann mehrere Minuten dauern. Das KI-Setup-Protokoll steht
unter %LOCALAPPDATA%\BewakeAI\ki-setup.log. Bei Downloadfehler erneut starten.
Ollama bleibt ein separat installiertes Programm und kann über Windows entfernt
werden. Bewake-AI-Deinstallation entfernt keine Ollama-Modelle.
Bestehende lokale Modelle werden in der Ersteinrichtung angeboten; ein anderer
Modellname kann auch manuell unter Einstellungen eingetragen werden.
„Lokale KI fragen“ sendet ausschließlich Dateiname und
Größe an http://127.0.0.1:11434. Modelldownload nur über den bestätigten KI-Setup-Knopf.
Die KI wählt nur eine Kategorie und erhält keinen Zugriff auf Dateipfade oder Tools.
KI-Antworten lösen keine automatische Verschiebung oder Regelerstellung aus.
GPU-Nutzung übernimmt Ollama. RTX 4080 Super / 5070 sind keine Voraussetzung;
die konkrete GPU-/Treiber-Unterstützung wurde auf diesen Geräten nicht getestet.

BENACHRICHTIGUNGEN / DATEN
Windows-Toasts bei neuen Vorschlägen; Verfügbarkeit hängt von Windows-Einstellungen
ab. Fehler landen im Protokoll; die GUI funktioniert trotzdem weiter.
Einstellungen und journal.jsonl liegen unter %LOCALAPPDATA%\BewakeAI.
Beim ersten Start werden vorhandene Daten aus %LOCALAPPDATA%\DownloadPilot
kopiert. Das Original bleibt erhalten. Das Setup behält die frühere Kennung,
damit die bestehende DownloadPilot-Installation aktualisiert werden kann.
Das Protokoll enthält lokale Dateinamen, Pfade und Prüfsummen. Beim Weitergeben
des Programmordners werden diese persönlichen Einstellungen nicht mitgeliefert.

QUELLCODE / BUILD
app.py: GUI und Überwachung. core.py: Klassifikation, Pfade und Dateivorgänge.
Python 3.14 x64: py -m pip install -r requirements.txt
Start: py app.py
Isolierter Test: py app.py --data-dir C:\Temp\BewakeAI-Test
Tests: py -m unittest -v
Build: powershell -ExecutionPolicy Bypass -File build.ps1
54 automatisierte Tests für Klassifikation, Stabilität, Desktop-Pfade, Regeln,
Duplikate, Konflikte, Undo und Ersteinrichtung. KI-Setup-Tests verwenden simulierte
Antworten; ein echter Ollama-Download wurde bei diesem Build nicht durchgeführt.
GUI-Start sowie Installation und Deinstallation werden zusätzlich geprüft.
installer.iss erzeugt mit Inno Setup 6.6+ die Setup-Datei. build.ps1 baut das Setup,
wenn ISCC.exe im PATH verfügbar ist. Dark Mode ist fest als Standard eingestellt.
GITHUB-UPDATES
Repository: ruyaekin/BewakeAI. Es muss öffentlich erreichbar sein.
Unter Einstellungen > GitHub-Updates kann die Versionsprüfung beim Start und
alle zwei Stunden ein- oder ausgeschaltet werden. Automatische Installation ist
separat wählbar und zunächst aus. Sonst gibt es einen Hinweis und den Updates-Knopf.
Updates werden ausschließlich aus diesem Repository geladen und vor dem Start
per SHA-256 geprüft. Laufende Dateioperationen werden abgewartet. Die App startet
nach der Installation im Tray neu. Einstellungen bleiben erhalten.
Die GitHub-Einrichtung steht in GITHUB-ANLEITUNG.txt. Der Workflow unter
.github/workflows/release.yml baut beim Veröffentlichen eines neuen Releases
Setup, portable ZIP und Prüfsummen und hängt sie automatisch an den Release.
GitHub-Build und echter Update-Durchlauf sind erst nach Veröffentlichung testbar.
Prototyp: unsignierter Installer. Kein Zugriff auf private GitHub-Repositories.

REFERENZEN
ComfyUI-Pfade: https://github.com/Comfy-Org/ComfyUI/blob/master/extra_model_paths.yaml.example
Ollama: https://ollama.com/blog/structured-outputs
Windows-Installation: https://docs.ollama.com/windows
Modell: https://ollama.com/library/qwen3:4b
Setup-Compiler: https://jrsoftware.org/isdl.php
Desktop-Modellpfade: https://github.com/Comfy-Org/Comfy-Desktop/blob/main/src/main/lib/models.ts
Desktop-Installationen: https://github.com/Comfy-Org/Comfy-Desktop/blob/main/src/main/installations.ts

