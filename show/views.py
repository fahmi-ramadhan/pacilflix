import datetime
from django.shortcuts import redirect, render
from django.http import JsonResponse
import json
from utils.db_utils import get_db_connection
from django.views.decorators.http import require_http_methods
from django.core.serializers.json import DjangoJSONEncoder

def execute_sql_query(sql_query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_query, params or [])
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
                SELECT 1 FROM PENGGUNA p WHERE p.id_tayangan = t.id AND p.asal_negara= %s
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
    is_Lokal = request.GET.get('lokal') == 'true'
    context = {
        "is_logged_in": False
    }
    username = request.session.get("username")

    if username:
        context["is_logged_in"] = True
        context["username"] = username
        
    tayangan = execute_sql_query("""
        SELECT 
            judul,
            sinopsis_trailer, 
            url_video_trailer, 
            to_char(release_date_trailer, 'DD-MM-YYYY') as release_date_trailer
        FROM TAYANGAN
    """)
    
    top_ten = execute_sql_query("""
    SELECT 
    t.id,
    t.judul,
    t.sinopsis_trailer,
    t.url_video_trailer,
    to_char(t.release_date_trailer, 'DD-MM-YYYY') as release_date_trailer,
    COALESCE(tv_all_time.total_view_all_time, 0) AS total_view_all_time,
    COALESCE(tv_7_days.total_view_7_days, 0) AS total_view_7_days
FROM 
    TAYANGAN t
LEFT JOIN 
    (
        SELECT 
            rn.id_tayangan, 
            COUNT(*) AS total_view_7_days
        FROM 
            riwayat_nonton rn
        INNER JOIN 
            TAYANGAN t ON rn.id_tayangan = t.id
        INNER JOIN
            FILM f ON f.id_tayangan = t.id
        WHERE 
            rn.end_date_time >= NOW() - INTERVAL '7 days'
            AND EXTRACT(EPOCH FROM (rn.end_date_time - rn.start_date_time)) >= 0.7 * f.durasi_film
        GROUP BY rn.id_tayangan
    ) as tv_7_days ON t.id = tv_7_days.id_tayangan
LEFT JOIN 
    (
        SELECT 
            rn.id_tayangan, 
            COUNT(*) AS total_view_all_time
        FROM 
            riwayat_nonton rn
        INNER JOIN 
            TAYANGAN t ON rn.id_tayangan = t.id
        INNER JOIN
            FILM f ON f.id_tayangan = t.id
        WHERE 
            EXTRACT(EPOCH FROM (rn.end_date_time - rn.start_date_time)) >= 0.7 * f.durasi_film
        GROUP BY rn.id_tayangan
    ) as tv_all_time ON t.id = tv_all_time.id_tayangan
ORDER BY 
    tv_7_days.total_view_7_days DESC,
    tv_all_time.total_view_all_time DESC,
    t.release_date_trailer DESC
LIMIT 10;


    """)

    film = execute_sql_query("""
        SELECT 
            id,                 
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
            id,                   
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

    if username:
        top_lokal = execute_sql_query("""
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
                GROUP BY id_tayangan
            ) AS total_view_7_days ON TAYANGAN.id = total_view_7_days.id_tayangan
            LEFT JOIN (
                SELECT 
                    id_tayangan, 
                    COUNT(*) AS total_view_all_time
                FROM 
                    riwayat_nonton
                GROUP BY id_tayangan
            ) AS total_view_all_time ON TAYANGAN.id = total_view_all_time.id_tayangan
            WHERE
                TAYANGAN.asal_negara = (SELECT negara_asal FROM PENGGUNA WHERE username = %s)
            ORDER BY 
                total_view_all_time DESC,
                TAYANGAN.release_date_trailer DESC
            LIMIT 10;
        """, [username])
        context['top_lokal'] = top_lokal
    else:
        context['top_lokal'] = []
    context.update({'tayangan': tayangan, 'top_ten': top_ten if not is_Lokal else top_lokal, 'films': film, 'series': series})
    return render(request, "show/tayangan.html", context)


def detil_tayangan(request, id_tayangan):
    context = {
        "is_logged_in": request.session.get("username", False)
    }

    if context["is_logged_in"]:
        context["username"] = request.session["username"]
    
    # Fetching main tayangan details
    tayangan = execute_sql_query("""
    SELECT 
        t.id,
        t.judul,
        t.sinopsis, 
        t.asal_negara, 
        COALESCE(total_view_all_time.total_view_all_time, 0) AS total_view_all_time,
        STRING_AGG(DISTINCT gt.genre, ', ') AS genre,
        ROUND(COALESCE(AVG(u.rating),0), 1) AS rating_rata_rata
    FROM
        TAYANGAN AS t
    LEFT JOIN (
        SELECT 
            id_tayangan, 
            COUNT(*) AS total_view_all_time
        FROM 
            riwayat_nonton
        GROUP BY 
            id_tayangan
    ) AS total_view_all_time ON t.id = total_view_all_time.id_tayangan
    LEFT JOIN genre_tayangan AS gt ON t.id = gt.id_tayangan
    LEFT JOIN ULASAN AS u ON t.id = u.id_tayangan
    WHERE
        t.id = %s
    GROUP BY
        t.id, t.judul, t.sinopsis, t.asal_negara, total_view_all_time.total_view_all_time
    """, [id_tayangan])

    # Fetching film specific details
    film_data = execute_sql_query("""
        SELECT
            durasi_film,
            release_date_film,
            url_video_film
        FROM 
            FILM
        WHERE
            id_tayangan = %s
    """, [id_tayangan])

    # Check if film_data is fetched correctly and update the context
    if film_data:
        context.update({
            'film': film_data[0]
        })
    
    pemain = execute_sql_query("""
    SELECT
        nama
    FROM 
        CONTRIBUTORS
    LEFT JOIN memainkan_tayangan mt ON mt.id_pemain = CONTRIBUTORS.id
    LEFT JOIN tayangan t ON t.id = mt.id_tayangan
    WHERE
        t.id = %s
    GROUP BY
        nama;
    """, [id_tayangan])

    penulis = execute_sql_query("""
    SELECT
        nama
    FROM 
        CONTRIBUTORS
    LEFT JOIN menulis_skenario_tayangan ms ON ms.id_penulis_skenario = CONTRIBUTORS.id
    LEFT JOIN tayangan t ON t.id = ms.id_tayangan
    WHERE
        t.id = %s
    GROUP BY
        nama;
    """, [id_tayangan])

    sutradara = execute_sql_query("""
    SELECT
        nama
    FROM 
        CONTRIBUTORS
    LEFT JOIN tayangan t ON t.id_sutradara = CONTRIBUTORS.id
    WHERE
        t.id = %s
    GROUP BY
        nama;
    """, [id_tayangan])
    
    ulasan = execute_sql_query(f"SELECT * FROM ULASAN WHERE id_tayangan = '{id_tayangan}'")
    
    episode = None
    
    if request.GET.get('type') == "series":
        episode = execute_sql_query(f"SELECT * FROM EPISODE WHERE id_series = '{id_tayangan}';")
    else:
        episode: None

    print(ulasan)

    context.update({
        'tayangan': tayangan,
        'pemain': pemain,
        'penulis': penulis,
        'sutradara': sutradara,
        'ulasan': ulasan,
        'episode': episode
    })
    

    # Check if the tayangan is a film or a series and choose the appropriate template
    template_name = 'show/detail_film.html' if film_data else 'show/series.html'

    return render(request, template_name, context)


def episode_detail(request, judul, sub_judul):
    context = {
        "is_logged_in": False
    }
    if "username" in request.session:
        context["is_logged_in"] = True
        context["username"] = request.session["username"]
        
    episode_khusus = execute_sql_query("""
        SELECT
            e.sub_judul,
            t.judul,
            e.sinopsis,
            e.durasi,
            e.url_video,
            e.release_date
        FROM episode e
        LEFT JOIN tayangan t ON t.id= e.id_series
        WHERE
            t.judul = %s AND
            e.sub_judul = %s
        ORDER BY
            e.sub_judul ASC;
        """, (judul, sub_judul))
    
    episode = execute_sql_query("""
        SELECT
            e.sub_judul,
            t.judul
        FROM episode e
        LEFT JOIN tayangan t ON t.id= e.id_series
        WHERE
            t.judul = %s
        ORDER BY
            e.sub_judul ASC;
        """, (judul,))
    
    release_episode = execute_sql_query("""
        SELECT
            sub_judul,release_date
        FROM EPISODE e
        LEFT JOIN SERIES s ON s.id_tayangan = e.id_series
        WHERE 
            e.release_date <= CURRENT_DATE;
        """)
    print(episode_khusus)
    context.update({'episode':episode,'episode_khusus':episode_khusus,'release_episode': release_episode, 'judul': judul, 'subjudul': sub_judul})
    return render(request, 'show/detail_episodes.html', context)


def save_review(request):
    if request.method == 'POST':
        username = request.session['username']
        review = request.POST['review']
        rating = request.POST['rating']
        print(rating)
        id_tayangan = request.GET.get('id_tayangan')
        
        # Lakukan penyisipan data ke dalam basis data
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"INSERT INTO ULASAN VALUES ('{id_tayangan}', '{username}', CURRENT_TIMESTAMP, {rating}, '{review}');")
        connection.commit()
        print("berhasil")
        cursor.close()
        connection.close()
        return redirect('show:tayangan')
    else:
        return JsonResponse({"status": "error", "message": "Method not allowed."}, status=405)

def update_review(request, judul):
    ulasan = execute_sql_query("""
        SELECT username, deskripsi, rating
        FROM ULASAN
        LEFT JOIN tayangan t ON t.id = ULASAN.id_tayangan
        WHERE t.judul = %s
        ORDER BY ulasan.timestamp DESC;
    """, (judul,))
    
    return JsonResponse({'ulasan': ulasan}, content_type='application/json')

def add_to(request):
    username = request.session['username']
    judul = request.GET.get('judul')
    id_tayangan = request.GET.get('id')
    connection = get_db_connection()
    cursor = connection.cursor()
    if request.GET.get('addto') == "favorit":
        cursor.execute(f"INSERT INTO DAFTAR_FAVORIT VALUES (CURRENT_TIMESTAMP, '{username}', '{judul}')")
        connection.commit()
    elif request.GET.get('addto') == "download":
        cursor.execute(f"INSERT INTO TAYANGAN_TERUNDUH VALUES ('{id_tayangan}', '{username}', CURRENT_TIMESTAMP)")
        connection.commit()
    cursor.close()
    connection.close()

    return redirect('show:tayangan')

def add_tontonan(request):
    username = request.session['username']
    judul = request.GET.get('judul')
    id_tayangan = request.GET.get('id')
    connection = get_db_connection()
    cursor = connection.cursor()
    if request.GET.get('addto') == "favorit":
        cursor.execute(f"INSERT INTO DAFTAR_FAVORIT VALUES (CURRENT_TIMESTAMP, '{username}', '{judul}')")
        connection.commit()
    elif request.GET.get('addto') == "download":
        cursor.execute(f"INSERT INTO TAYANGAN_TERUNDUH VALUES ('{id_tayangan}', '{username}', CURRENT_TIMESTAMP)")
        connection.commit()
    cursor.close()
    connection.close()

    return redirect('show:tayangan')