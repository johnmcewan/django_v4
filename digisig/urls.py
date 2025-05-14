from django.urls import path, re_path
from debug_toolbar.toolbar import debug_toolbar_urls

from .views import CustomLoginView, LogoutView, EntityView

from . import views


urlpatterns = [
	path('', views.index, name='index'),
	path('login/', CustomLoginView.as_view(), name='login'),
	path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
	path('search/<str:searchtype>', views.search, name='search'),
	path('information/<str:infotype>', views.information, name='information'),
	path('discover/<str:discovertype>', views.discover, name='discover'),
	path('analyze/<str:analysistype>', views.analyze, name='analyze'),
	path('about', views.about, name='about'),
	path('exhibit', views.exhibit, name='exhibit'),

	re_path(r'page/(?P<entity_type>item)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='item_page'),
    re_path(r'page/(?P<entity_type>term)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='term_page'),
    re_path(r'page/(?P<entity_type>seal)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='seal_page'),
    re_path(r'page/(?P<entity_type>manifestation)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='manifestation_page'),
    re_path(r'page/(?P<entity_type>sealdescription)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='sealdescription_page'),
    re_path(r'page/(?P<entity_type>representation)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='representation_page'),
    re_path(r'page/(?P<entity_type>actor)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='actor_page'),
    re_path(r'page/(?P<entity_type>place)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='place_page'),
    re_path(r'page/(?P<entity_type>collection)/(?P<digisig_entity_number>[0-9]{8})', views.EntityView.as_view(), name='collection_page'),

	# re_path(r'page/item/(?P<digisig_entity_number>[0-9]{8})', views.item_page, name='item_page'),
	# re_path(r'page/term/(?P<digisig_entity_number>[0-9]{8})', views.term_page, name='term_page'),
	# re_path(r'page/seal/(?P<digisig_entity_number>[0-9]{8})', views.seal_page, name='seal_page'),
	# re_path(r'page/manifestation/(?P<digisig_entity_number>[0-9]{8})', views.manifestation_page, name='manifestation_page'),
	# re_path(r'page/sealdescription/(?P<digisig_entity_number>[0-9]{8})', views.sealdescription_page, name='sealdescription_page'),
	# re_path(r'page/representation/(?P<digisig_entity_number>[0-9]{8})', views.representation_page, name='representation_page'),
	# re_path(r'page/actor/(?P<digisig_entity_number>[0-9]{8})', views.actor_page, name='actor_page'),
	# re_path(r'page/place/(?P<digisig_entity_number>[0-9]{8})', views.place_page, name='place_page'),
	# re_path(r'page/collection/(?P<digisig_entity_number>[0-9]{8})', views.collection_page, name='collection_page'),

	re_path(r'entity/(?P<digisig_entity_number>[0-9]{8})', views.entity, name='entity'),

] #+ debug_toolbar_urls()
