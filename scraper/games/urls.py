from django.urls import path
from . import views

urlpatterns = [
    path('', views.GamesListView.as_view(), name='games_list'),
]
