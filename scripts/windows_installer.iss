#define AppVer "1.0.0"

[Setup]
AppId={{A31A35F0-7C09-46D0-87CD-B8EE6DD9D1D6}
AppName=LOL 大乱斗海克斯助手
AppVersion={#AppVer}
AppPublisher=Nyx0ra
DefaultDirName={autopf}\LOL-ARAM-Mayhem-Hextech-Helper
DefaultGroupName=LOL 大乱斗海克斯助手
UninstallDisplayIcon={app}\大乱斗海克斯助手.exe
OutputDir=..\dist_installer
OutputBaseFilename=LOL-ARAM-Mayhem-Hextech-Helper-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务"; Flags: unchecked

[Files]
Source: "..\dist\大乱斗海克斯助手\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\LOL 大乱斗海克斯助手"; Filename: "{app}\大乱斗海克斯助手.exe"
Name: "{autodesktop}\LOL 大乱斗海克斯助手"; Filename: "{app}\大乱斗海克斯助手.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\大乱斗海克斯助手.exe"; Description: "立即启动 LOL 大乱斗海克斯助手"; Flags: nowait postinstall skipifsilent
