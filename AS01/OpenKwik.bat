@echo off
echo.
echo SelectedFile is %1
cmd /c "C:\%HOMEPATH%\\anaconda3\\Scripts\\activate.bat&conda activate phy2&python "%PROGRAMFILES(X86)%\AS01 Sorting Suite\OpenKwik.py" %1"