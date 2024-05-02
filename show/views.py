import datetime
from django.shortcuts import render
from django.http import JsonResponse
import json
from utils.db_utils import get_db_connection
from django.views.decorators.http import require_http_methods
from django.core.serializers.json import DjangoJSONEncoder

def execute_sql_query(execute_sql_query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(execute_sql_query, params or [])
            return cursor.fetchall()

def index(request):
    return render(request, 'show/index.html')

def trailers(request):
    username = request.session.get('username', None)
    user_country = 'Global'  # Default to global if not logged in or no country is set

    # Check if the user has selected to view local content
    view_type = request.GET.get('type', 'global')  # Default to global

    if username:
        user_country_query = """
            SELECT negara_asal FROM PENGGUNA WHERE username = %s
        """
        user_country_result = execute_sql_query(user_country_query, [username])
        if user_country_result:
            user_country = user_country_result[0][0]

    base_query = """
        SELECT 
            t.judul,
            t.sinopsis_trailer, 
            t.url_video_trailer, 
            to_char(t.release_date_trailer, 'DD-MM-YYYY') as release_date_trailer,
            COALESCE(rv.total_views, 0) as total_views
        FROM 
            TAYANGAN as t
        LEFT JOIN (
            SELECT 
                id_tayangan, 
                COUNT(*) AS total_views
            FROM 
                riwayat_nonton
            GROUP BY 
                id_tayangan
        ) AS rv ON t.id = rv.id_tayangan
    """

    query_params = []
    if view_type == 'local' and username:
        base_query += """
        WHERE 
            EXISTS (
                SELECT 1 FROM PENGGUNA p WHERE p.id_tayangan = t.id AND p.negara_asal = %s
            )
        """
        query_params = [user_country]

    base_query += """
        ORDER BY 
            total_views DESC,
            t.release_date_trailer DESC
        LIMIT 10;
    """
    top_trailers = execute_sql_query(base_query, query_params)

    film_query = """
        SELECT 
            judul,
            sinopsis_trailer, 
            url_video_trailer, 
            to_char(release_date_trailer, 'DD-MM-YYYY') as release_date_trailer
        FROM 
            TAYANGAN
        JOIN 
            FILM ON FILM.id_tayangan = TAYANGAN.id
        ORDER BY 
            release_date_trailer DESC;
    """
    films = execute_sql_query(film_query)

    series_query = """
        SELECT 
            judul,
            sinopsis_trailer, 
            url_video_trailer, 
            to_char(release_date_trailer, 'DD-MM-YYYY') as release_date_trailer
        FROM 
            TAYANGAN
        JOIN 
            SERIES ON SERIES.id_tayangan = TAYANGAN.id
        ORDER BY 
            release_date_trailer DESC;
    """
    series = execute_sql_query(series_query)

    context = {
        'top_trailers': top_trailers,
        'films': films,
        'series': series,
    }
    
    return render(request, "show/trailer.html", context)


def show_tayangan(request):
    context = {
        "is_logged_in": False
    }
    if "username" in request.session:
        context["is_logged_in"] = True
        context["username"] = request.session["username"]
        
    tayangan = execute_sql_query("""
        SELECT 
            judul,
            sinopsis_trailer, 
            url_video_trailer, 
            to_char(release_date_trailer, 'DD-MM-YYYY') as release_date_trailer
        FROM
            TAYANGAN
        """)
    
    top_ten = execute_sql_query("""
        SELECT 
            TAYANGAN.judul,
            TAYANGAN.sinopsis_trailer,
            TAYANGAN.url_video_trailer,
            to_char(TAYANGAN.release_date_trailer, 'DD-MM-YYYY') as release_date_trailer,
            COALESCE(total_view_all_time.total_view_all_time, 0) AS total_view_all_time,
            COALESCE(total_view_7_days.total_view_7_days, 0) AS total_view_7_days
        FROM 
            TAYANGAN
        LEFT JOIN (
            SELECT 
                id_tayangan, 
                COUNT(*) AS total_view_7_days
            FROM 
                riwayat_nonton
            WHERE 
                end_date_time >= NOW() - INTERVAL '7 days'
            GROUP BY 
                id_tayangan
        ) AS total_view_7_days ON TAYANGAN.id = total_view_7_days.id_tayangan
        LEFT JOIN (
            SELECT 
                id_tayangan, 
                COUNT(*) AS total_view_all_time
            FROM 
                riwayat_nonton
            GROUP BY 
                id_tayangan
        ) AS total_view_all_time ON TAYANGAN.id = total_view_all_time.id_tayangan
        ORDER BY 
            total_view_all_time DESC,
            TAYANGAN.release_date_trailer DESC
        LIMIT 10;
    """)
    
    film = execute_sql_query("""
        SELECT 
            judul,
            sinopsis_trailer, 
            url_video_trailer, 
            to_char(release_date_trailer, 'DD-MM-YYYY') as release_date_trailer
        FROM 
            TAYANGAN
        JOIN 
            FILM f ON f.id_tayangan = TAYANGAN.id
        GROUP BY 
            TAYANGAN.id
        ORDER BY
            TAYANGAN.judul ASC;
        """)
    
    series = execute_sql_query("""
        SELECT 
            judul,
            sinopsis_trailer, 
            url_video_trailer, 
            to_char(release_date_trailer, 'DD-MM-YYYY') as release_date_trailer
        FROM 
            TAYANGAN
        JOIN 
            SERIES s ON s.id_tayangan = TAYANGAN.id
        GROUP BY 
            TAYANGAN.id
        ORDER BY
            TAYANGAN.judul ASC;
        """)

    pengguna = execute_sql_query("""
        SELECT
            username,
            to_char(end_date_time, 'DD-MM-YYYY') as end_date_time
        FROM
            TRANSACTION
        WHERE end_date_time > NOW()
        ORDER BY
            username ASC;
        """)
    
    context.update({'tayangan': tayangan, 'trailers': top_ten, 'film': film, 'series': series, 'pengguna': pengguna})
    return render(request, "show/tayangan.html", context)

def detil(request):
    return render(request, 'show/detail_film.html')
def series(request):
    return render(request, 'show/series.html')
def episodes(request):
    return render(request, 'show/episodes.html')
def review(request):
    return render(request, 'show/review.html')

