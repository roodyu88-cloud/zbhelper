[Setup]
AppName=ZBHelper
AppVersion=1.0
DefaultDirName={pf}\ZBHelper
DefaultGroupName=ZBHelper
OutputDir=.\Output
OutputBaseFilename=ZBHelper_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\ZBHelper.exe

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\ZBHelper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ZBHelper"; Filename: "{app}\ZBHelper.exe"; IconFilename: "{app}\_internal\icon.ico"
Name: "{commondesktop}\ZBHelper"; Filename: "{app}\ZBHelper.exe"; IconFilename: "{app}\_internal\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\ZBHelper.exe"; Description: "{cm:LaunchProgram,ZBHelper}"; Flags: nowait postinstall skipifsilent
