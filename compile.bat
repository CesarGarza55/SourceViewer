pip install -r data/requirements.txt
pyinstaller --clean --workpath ./temp --noconfirm --onefile --windowed --specpath ./ --distpath ./ --icon "data\icon.ico" --add-data "data;." --name "SourceViewer" --hidden-import "comtypes.stream" "data\main.py"
del SourceViewer.spec
rmdir /s /q temp