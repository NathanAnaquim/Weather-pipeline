@echo off
REM Roda o pipeline completo: extract -> transform -> load
REM Usado pelo Agendador de Tarefas do Windows para automação diária

cd /d "%~dp0"

echo [%date% %time%] Iniciando pipeline... >> pipeline_log.txt

call venv\Scripts\activate.bat

echo [%date% %time%] Executando extract_weather.py >> pipeline_log.txt
python extract_weather.py >> pipeline_log.txt 2>&1

echo [%date% %time%] Executando transform_weather.py >> pipeline_log.txt
python transform_weather.py >> pipeline_log.txt 2>&1

echo [%date% %time%] Executando load_to_mysql.py >> pipeline_log.txt
python load_to_mysql.py >> pipeline_log.txt 2>&1

echo [%date% %time%] Pipeline finalizado. >> pipeline_log.txt
echo. >> pipeline_log.txt
