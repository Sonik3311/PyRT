@echo off
if not exist "venv" python -m venv ./venv
@echo Virtual environment for python was created. 
goto :runenv

:runenv
cd .\venv\scripts
copy activate.bat activate-auto.bat
echo pip.exe install -r ../../requirements.txt>>activate-auto.bat
echo cd..>>activate-auto.bat
echo cd..>>activate-auto.bat
echo cd Scripts>>activate-auto.bat
echo python main.py>>activate-auto.bat
start activate-auto.bat 





