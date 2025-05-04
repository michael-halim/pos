run:
	@echo "Running Development POS"
	python main.py

build-install:
	@echo "Building POS and Its Installer"
	if exist "dist\data" rd /s /q "dist\data"
	mkdir "dist\data"
	copy "data\pos.db" "dist\data\pos.db"
	pyinstaller build.spec
	"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss