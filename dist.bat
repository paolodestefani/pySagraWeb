REM creazione pacchetto per pySagraWeb

REM utilizzo di un virtual enviroment
CALL C:\PyWare\.venv\pysagraweb\Scripts\Activate.bat

REM mi sposto sulla cartella dell'applicazione Flask
CD C:\PyWare\PysagraWeb

REM eseguo pyInstaller
pyinstaller --clean ^
--onedir ^
--icon=pySagra.ico ^
--add-data "templates;templates" ^
--add-data "static;static" ^
pysagra_web.py
	
REM copia il file di configurazione
copy config.cfg dist\pysagra_web\

REM disattivo il virtual enviroment
CALL deactivate.bat

pause


