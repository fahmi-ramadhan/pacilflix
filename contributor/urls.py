from django.urls import path
from contributor.views import index

urlpatterns = [
    path('', index, name='contributor'),
]