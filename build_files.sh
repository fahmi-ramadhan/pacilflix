# build_files.sh
python3.12 -m pip install -r requirements.txt

# make migrations
python3.12 manage.py migrate 
python3.12 manage.py collectstatic
