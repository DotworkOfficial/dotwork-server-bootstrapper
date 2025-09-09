@echo off
echo Building Dotwork Server Bootstraper...
echo.

REM Install PyInstaller if not exists
python -c "import PyInstaller" 2>nul || pip install pyinstaller

REM Build executable
pyinstaller --onefile --windowed --name=DotworkBootstraper --add-data="templates;templates" --hidden-import=PyQt5.sip --hidden-import=jinja2 --hidden-import=yaml main.py

REM Copy templates to dist
if exist dist\templates rmdir /s /q dist\templates
xcopy templates dist\templates /e /i /y

echo.
echo Build completed!
echo Executable: dist\DotworkBootstraper.exe
pause