from django.urls import path
from show import views

urlpatterns = [
    path('trailer/', views.trailers, name='show'),
    path('tayangan/', views.show_tayangan, name='tayangan'),
    path('detail_film/', views.detil , name='detil_film'),
    path('series/', views.series, name='series'),
    path('episodes/', views.episodes, name='episode_series'),
    path('review/', views.review, name='review'),

 ]