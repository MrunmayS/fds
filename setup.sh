#/bin/bash
git clone https://github.com/CyberPoint/libpgm.git


mv libpgm lib
mv lib/build .
mv lib/docs .
mv lib/examples .
mv lib/libpgm .
mv lib/libpgm_examples .
mv lib/runtime-tests .
mv lib/tests .
mv lib/utils .
touch mushroom.json

pip install -r requirements.txt
python main.py
