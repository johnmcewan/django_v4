from django.urls import path, re_path
# from debug_toolbar.toolbar import debug_toolbar_urls

#https://www.valentinog.com/blog/django-vhosts/

from .views import index

# from . import views

urlpatterns = [
	#path("witness/", index, name="index")
	path('', index, name='index'),
    path('graph', views.graph, name='graph'),
# ] + debug_toolbar_urls()
]
