from django.urls import path
from subscription.views import index

urlpatterns = [
    path('', index, name='subscription'),
]