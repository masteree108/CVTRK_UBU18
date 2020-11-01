# note 1: if your os is windows10 please changing build_exe.sh to build_exe.bat(it dosen't need if it runs at the cygwin terminal)
# note 2: this buiild_exe.sh that needs to setup module please as follows
# pip install pyinstaller
# note 3: chmod +x build_exe.sh

pyinstaller -F ./vott_tracker.py
cp -f ./dist/vott_tracker ../../VoTT_NTUT/UBU18/NTUT/exe/vott_tracker.exe
cp -f ./dist/vott_tracker ./vott_tracker.exe
rm -rf dist
rm -rf __pycache__
rm -rf build
rm *.spec
