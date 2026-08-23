@echo off

setlocal

set AUDIO=%1
set SALIDA=%2
set MODELO=%3
set IDIOMA=%4

call C:\Whisper\venv\Scripts\activate.bat

whisper "%AUDIO%" ^
--model %MODELO% ^
--language %IDIOMA% ^
--device cuda ^
--output_dir "%SALIDA%"