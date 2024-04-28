# build_files.sh
python3.9 -m pip install -r requirements.txt

# make migrations
python3.9 manage.py migrate 
python3.9 manage.py collectstatic
