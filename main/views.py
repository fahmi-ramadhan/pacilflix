import os
import psycopg2
from django.shortcuts import render

def show_main(request):
    # Get database credentials from environment variables
    db_name = os.environ.get("DB_NAME")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")

    # Establish a connection to the database
    connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )

    # Create a cursor object
    cursor = connection.cursor()

    # Execute your SQL query
    cursor.execute("SELECT judul, sinopsis, asal_negara FROM tayangan")

    # Fetch all the rows
    rows = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Create a list of dictionaries
    data = [{'judul': row[0], 'sinopsis': row[1], 'asal_negara': row[2]} for row in rows]

    context = {
        'title': 'Welcome to Pacilflix',
        'subtitle': 'The best place to watch movies and TV shows!',
        'data': data,
    }

    return render(request, "main.html", context)