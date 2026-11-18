@echo off
rem Gera dist\Instalar-DateEverything-PTBR.exe (requer Python 3.12 no PATH e a pasta dados\)
if not exist dados\manifesto.json (echo Falta a pasta dados\. & goto :erro)
python -m venv .venv || goto :erro
.venv\Scripts\python -m pip install -r requirements.txt pyinstaller || goto :erro
.venv\Scripts\pyinstaller --noconfirm --clean --onefile --console --name Instalar-DateEverything-PTBR ^
  --add-data "dados;dados" --paths . ^
  --collect-all UnityPy --collect-all fmod_toolkit --collect-all texture2ddecoder ^
  --collect-all astc_encoder --collect-all archspec instalar.py || goto :erro
echo.
echo Pronto: dist\Instalar-DateEverything-PTBR.exe
exit /b 0
:erro
echo Falhou.
exit /b 1
