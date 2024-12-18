@echo off
if exist output_build rmdir /s /q output_build
py -m pip install -r data/requirements.txt
python compile.py build

echo SourceViewer compiled successfully.
echo Press any key to exit...
pause >nul