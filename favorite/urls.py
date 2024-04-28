from django.urls import path
from favorite.views import index

urlpatterns = [
    path('', index, name='favorite'),
]