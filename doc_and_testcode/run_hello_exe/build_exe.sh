# note 1: if your os is windows10 please changing build_exe.sh to build_exe.bat
# note 2: this buiild_exe.sh that needs to setup module please as follows
# pip install pyinstaller
# note 3: chmod +x build_exe.sh

pyinstaller -F ./hello.py
cp ./dist/hello ./hello.exe
rm -rf dist
rm -rf __pycache__
rm -rf build
rm *.spec
