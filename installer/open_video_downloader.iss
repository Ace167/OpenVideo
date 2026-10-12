; Inno Setup script for OpenVideo Downloader
; Compatible with Inno Setup 6.0+

#define MyAppName "OpenVideo Downloader"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "OpenVideo Downloader Contributors"
#define MyAppURL "https://github.com/Ace167/OpenVideo"
#define MyAppExeName "OpenVideoDownloader.exe"

[Setup]
AppId={{E680E7A2-1C3D-4A8E-8FE4-2B474A53DE6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=..\dist\installer
OutputBaseFilename=OpenVideoDownloader-Setup-v{#MyAppVersion}
SetupIconFile=..\assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
MinVersion=10.0
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no

; Windows Explorer Version Info
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher}

[Languages]
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
dutch.LaunchProgram=Start OpenVideo Downloader
english.LaunchProgram=Launch OpenVideo Downloader
dutch.AppRunningPrompt=OpenVideo Downloader is momenteel actief. Sluit de applicatie voordat u doorgaat.
english.AppRunningPrompt=OpenVideo Downloader is currently running. Please close the application before continuing.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application binaries and dependencies built by PyInstaller
Source: "..\dist\OpenVideoDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
; Register application in Windows App Paths (allows Win+R > OpenVideoDownloader)
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--lang {language}"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Cleanup install directory artifacts (never touch user database, settings or download folders)
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.tmp"
Type: filesandordirs; Name: "{app}\__pycache__"
