from django.urls import path
from show.views import index

urlpatterns = [
    path('', index, name='show'),
]