# this buiild_service_exe.sh that needs to setup module please as follows
# pip install pyinstaller
# note 3: chmod +x build_service_exe.sh

pyinstaller -F ./tracker_service.py
cp -f ./dist/tracker_service ../../../../../Drone_Target/tracker_service.exe
rm -rf dist
rm -rf __pycache__
rm -rf build
rm *.spec
