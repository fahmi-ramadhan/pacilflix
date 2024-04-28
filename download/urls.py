from django.urls import path
from download.views import index

urlpatterns = [
    path('', index, name='download'),
]