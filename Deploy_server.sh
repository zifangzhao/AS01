#!/bin/bash
cp "./KlustaKwik" "/bin"
chmod 777 /bin/KlustaKwik

mkdir -p "/usr/local/bin/cereloop"

cp "./data.prm" "/usr/local/bin/cereloop"
chmod 777 /usr/local/bin/cereloop/data.prm

cp "./AS01_start.sh" "/usr/local/bin/cereloop"
chmod 777 /usr/local/bin/cereloop/AS01_start.sh

cp "./AS01-Sorting-Server-GUI.desktop" "/usr/share/applications/"
#chmod +x /usr/share/applications/AS01-Sorting-Server-GUI.desktop

mkdir -p "/usr/local/bin/cereloop/map"
cd "./map"
this_path=*
for f in $this_path
do
	cp "./$f" "//usr/local/bin/cereloop/map/$f"
done
cd ..

cd "./NeuroSuite/dist"
this_path=*
for f in $this_path
do
	echo "Copying $f file..."
	cp "./$f" "/usr/local/bin/cereloop/$f"
done


cd "./pytransform"
mkdir -p "/usr/local/bin/cereloop/pytransform"
chmod 777 -R "/usr/local/bin/cereloop/pytransform/"
this_path=*
for f in $this_path
do
	echo "Copying $f file..."
	cp "./$f" "/usr/local/bin/cereloop/pytransform/$f"
done
cd ../../..

cd "./AS01/dist"
this_path=*
for f in $this_path
do
	echo "Copying $f file..."
	cp "./$f" "/usr/local/bin/cereloop/AS01/$f"
done


cd "./pytransform"
mkdir -p "/usr/local/bin/cereloop/AS01/pytransform"
chmod 777 -R "/usr/local/bin/cereloop/AS01/pytransform/"
this_path=*
for f in $this_path
do
	echo "Copying $f file..."
	cp "./$f" "/usr/local/bin/cereloop/AS01/pytransform/$f"
done
cd ../../..

cp "./run_resample.py" "/usr/local/bin/cereloop/"
cp "./nsx2dat" "/usr/local/bin/cereloop/"
chmod 777 -R "/usr/local/bin/cereloop"

