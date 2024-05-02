from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now
from utils.db_utils import get_db_connection

@require_http_methods(['GET'])
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

def get_favorites(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT TAYANGAN.judul, TAYANGAN_MEMILIKI_DAFTAR_FAVORIT.timestamp "
        "FROM TAYANGAN_MEMILIKI_DAFTAR_FAVORIT "
        "JOIN TAYANGAN ON TAYANGAN.id = TAYANGAN_MEMILIKI_DAFTAR_FAVORIT.id_tayangan "
        "WHERE TAYANGAN_MEMILIKI_DAFTAR_FAVORIT.username = %s",
        (username,)
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    
    favorites = [{'judul': row[0], 'timestamp': row[1]} for row in rows]
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
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO TAYANGAN_MEMILIKI_DAFTAR_FAVORIT (id_tayangan, username, timestamp) "
        "VALUES (%s, %s, %s)",
        (show_id, username, now())
    )
    connection.commit()
    cursor.close()
    connection.close()

def delete_favorite(username, show_id, timestamp):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM TAYANGAN_MEMILIKI_DAFTAR_FAVORIT "
        "WHERE username = %s AND id_tayangan = %s AND timestamp = %s",
        (username, show_id, timestamp)
    )
    connection.commit()
    cursor.close()
    connection.close()

@require_http_methods(['POST'])
def add_to_favorite_view(request):
    username = request.session.get('username')
    if not username:
        return redirect('authentication:login')

    show_id = request.POST.get('show_id')
    add_to_favorite(username, show_id)
    return redirect('favorite:index')

@require_http_methods(['POST'])
def delete_favorite_view(request):
    username = request.session.get('username')
    if not username:
        return redirect('authentication:login')

    show_id = request.POST.get('show_id')
    timestamp = request.POST.get('timestamp')
    delete_favorite(username, show_id, timestamp)
    return redirect('favorite:index')