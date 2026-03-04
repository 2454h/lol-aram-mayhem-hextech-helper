param(
    [string]$Version = "1.0.0",
    [string]$InnoSetupCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (Test-Path "$ProjectRoot\build") { Remove-Item "$ProjectRoot\build" -Recurse -Force }
if (Test-Path "$ProjectRoot\dist") { Remove-Item "$ProjectRoot\dist" -Recurse -Force }
if (Test-Path "$ProjectRoot\dist_installer") { Remove-Item "$ProjectRoot\dist_installer" -Recurse -Force }

python -m pip install -r requirements.txt
python -m pip install pyinstaller pytest
python -m pytest -q
pyinstaller build_windows.spec --noconfirm --clean

$builtExe = Get-ChildItem "$ProjectRoot\dist" -Recurse -Filter "*.exe" |
    Where-Object { $_.FullName -notlike "*dist_installer*" } |
    Select-Object -First 1
if ($null -eq $builtExe) { throw "封装失败，未生成可执行文件" }

$installerScript = "$ProjectRoot\scripts\windows_installer.iss"

if (!(Test-Path $InnoSetupCompiler)) { throw "未找到 Inno Setup 编译器: $InnoSetupCompiler" }
& $InnoSetupCompiler "/DAppVer=$Version" $installerScript

Write-Host "发布完成:"
Write-Host "目录版: $ProjectRoot\dist\大乱斗海克斯助手"
Write-Host "安装包: $ProjectRoot\dist_installer\LOL-ARAM-Mayhem-Hextech-Helper-Setup.exe"
