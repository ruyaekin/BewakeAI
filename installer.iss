#ifndef AppIdValue
  #define AppIdValue "DownloadPilot.Desktop"
#endif
#ifndef AppLabel
  #define AppLabel "Bewake AI Download Manager"
#endif
#ifndef SetupName
  #define SetupName "Bewake-AI-Download-Manager-Setup"
#endif
#ifndef StartupValueName
  #define StartupValueName "BewakeAI"
#endif
#ifndef BuildVersion
  #define BuildVersion "0.6.0"
#endif
[Setup]
AppId={#AppIdValue}
AppName={#AppLabel}
AppVersion={#BuildVersion}
AppPublisher=Bewake AI
DefaultDirName={localappdata}\Programs\{#AppLabel}
DefaultGroupName={#AppLabel}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern dark
DisableProgramGroupPage=yes
DisableWelcomePage=no
OutputDir=..
OutputBaseFilename={#SetupName}
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\BewakeAIDownloadManager.exe
AppMutex=Local\DownloadPilotPrototype
CloseApplications=no
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Verknüpfungen:"
Name: "startup"; Description: "Mit Windows starten (direkt im Systemtray)"; GroupDescription: "Hintergrundbetrieb:"; Flags: unchecked

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#StartupValueName}"; ValueData: """{app}\BewakeAIDownloadManager.exe"" --tray"; Tasks: startup; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "{#StartupValueName}"; Flags: dontcreatekey uninsdeletevalue

[Files]
Source: "release\BewakeAIDownloadManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

#if AppIdValue == "DownloadPilot.Desktop"
[InstallDelete]
Type: files; Name: "{userprograms}\DownloadPilot.lnk"
Type: files; Name: "{userdesktop}\DownloadPilot.lnk"
Type: files; Name: "{app}\DownloadPilot.exe"
#endif

[Icons]
Name: "{userprograms}\{#AppLabel}"; Filename: "{app}\BewakeAIDownloadManager.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\{#AppLabel}"; Filename: "{app}\BewakeAIDownloadManager.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\BewakeAIDownloadManager.exe"; Description: "Bewake AI Download Manager starten und Ordner einrichten"; Flags: nowait postinstall skipifsilent

[Messages]
german.WelcomeLabel2=Dieses Setup installiert Bewake AI Download Manager mit allen benötigten Programmdateien.%n%nBeim ersten Start werden Downloads und Comfy-Desktop-Ziele eingerichtet. Die lokale KI kann anschließend optional automatisch installiert werden.%n%nPython und eine GPU sind für die Grundfunktionen nicht erforderlich.
