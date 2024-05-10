from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now
from utils.db_utils import get_db_connection
from django.http import HttpResponseBadRequest
import datetime
from django.utils import timezone

def index(request):
    username = request.session.get('username')
    if not username:
        return redirect('authentication:login')

    favorites = get_favorites(username)
    available_shows = get_available_shows(username)
    context = {
        'favorites': favorites,
        'available_shows': available_shows
    }
    return render(request, 'favorite/index.html', context)

def parse_timestamp(input_timestamp):
    input_timestamp = input_timestamp.strip().replace(' a.m.', ' AM').replace(' p.m.', ' PM')
    formats = [
        "%B %d, %Y, %I:%M %p",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(input_timestamp, fmt)
            aware_dt = timezone.make_aware(dt, timezone.get_current_timezone())
            return aware_dt
        except ValueError:
            continue
    raise ValueError("Timestamp format not recognized.")

def get_favorites(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT TAYANGAN.id, TAYANGAN.judul, TAYANGAN_MEMILIKI_DAFTAR_FAVORIT.timestamp "
        "FROM TAYANGAN_MEMILIKI_DAFTAR_FAVORIT "
        "JOIN TAYANGAN ON TAYANGAN.id = TAYANGAN_MEMILIKI_DAFTAR_FAVORIT.id_tayangan "
        "WHERE TAYANGAN_MEMILIKI_DAFTAR_FAVORIT.username = %s",
        (username,)
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    
    favorites = [{'show_id': row[0], 'judul': row[1], 'timestamp': row[2]} for row in rows]
    return favorites

def get_available_shows(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT TAYANGAN.id, TAYANGAN.judul "
        "FROM TAYANGAN "
        "WHERE TAYANGAN.id NOT IN (SELECT id_tayangan FROM TAYANGAN_MEMILIKI_DAFTAR_FAVORIT WHERE username = %s)",
        (username,)
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    shows = [{'id': row[0], 'judul': row[1]} for row in rows]
    return shows

def add_to_favorite(username, show_id):
    timestamp = add_to_daftar_favorit(username)
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO TAYANGAN_MEMILIKI_DAFTAR_FAVORIT (id_tayangan, username, timestamp) "
        "VALUES (%s, %s, %s)",
        (show_id, username, timestamp)
    )
    connection.commit()
    cursor.close()
    connection.close()

def delete_favorite(username, show_id, input_timestamp):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        aware_timestamp = parse_timestamp(input_timestamp)
        
        timestamp_lower = (aware_timestamp - datetime.timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
        timestamp_upper = (aware_timestamp + datetime.timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')

        sql_query = """
        DELETE FROM tayangan_memiliki_daftar_favorit
        WHERE username = %s AND id_tayangan = %s AND timestamp BETWEEN %s AND %s
        """
        cursor.execute(sql_query, (username, show_id, timestamp_lower, timestamp_upper))
        result = cursor.rowcount
        connection.commit()

        return result

    finally:
        cursor.close()
        connection.close()

def add_to_daftar_favorit(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    timestamp = now().replace(microsecond=0).isoformat()
    cursor.execute(
        "INSERT INTO DAFTAR_FAVORIT (timestamp, username, judul) VALUES (%s, %s, %s)",
        (timestamp, username, 'My Favorite Shows')
    )
    connection.commit()
    cursor.close()
    connection.close()
    return timestamp

@require_http_methods(['POST'])
def add_to_favorite_view(request):
    username = request.session.get('username')
    if not username:
        return redirect('authentication:login')

    show_id = request.POST.get('show_id')
    add_to_favorite(username, show_id)
    return redirect('favorite:index')

def delete_favorite_view(request):
    try:
        username = request.session.get('username')
        if not username:
            return redirect('login')

        show_id = request.POST.get('show_id')
        raw_timestamp = request.POST.get('timestamp')

        try:
            deletion_result = delete_favorite(username, show_id, raw_timestamp)
            return redirect('favorite:index')
        except Exception as e:
            return HttpResponseBadRequest("Invalid request: could not delete favorite.")

    except Exception as e:
        return HttpResponseBadRequest("Invalid request: could not delete favorite.")