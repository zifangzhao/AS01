@echo off
echo.
echo SelectedFile is %1
cmd /c "C:\\Users\\Frank-G5\\anaconda3\\Scripts\\activate.bat&conda activate phy2&python D:\code\Python\AS01\git\Source\Code\AS01\OpenKwik.py %1"