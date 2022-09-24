python -m venv _setup_/standalone/.venv
call _setup_/standalone/.venv/Scripts/Activate
pip install -r _setup_/standalone/requirements.txt
pip install -e .
:: end print
echo .venv file created at _setup_/standalone/.venv
echo Please run start_standalone.bat to start the tool



