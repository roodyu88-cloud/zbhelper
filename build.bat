@echo off
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Building executable...
pyinstaller --clean --noconfirm --onedir --windowed --add-data "ui/index.html;ui" --add-data "icon.ico;." --hidden-import=scraper --icon=icon.ico --name "ZBHelper" main.py

echo.
echo To build the installer, please compile installer.iss using Inno Setup (ISCC).
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer.iss
echo.
echo Installer has been generated in Output folder!
