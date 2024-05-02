from django.urls import path
from . import views

app_name = 'download'

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_download_view, name='add_download'),
    path('delete/', views.delete_show, name='delete_show'),
]