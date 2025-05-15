from django.views.decorators.cache import cache_page
from django.core.cache import cache

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.utils.decorators import method_decorator

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from datetime import datetime
from time import time
# from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.db.models import Q
from django.db.models import Count
from django.db.models import Sum
from django.core import serializers

from .models import *
from .forms import * 
# from utils.mltools import * 
from utils.generaltools import *
from utils.viewtools import *
from django.views import View
from asgiref.sync import sync_to_async

import json
import os
import pickle


# Table of Contents
	# index
	# about
	# exhibit

## regulate how long pages are cached
cache_timeout = (60 * 60)


# from django.core.cache import cache

# def my_view(request):
#     data = cache.get('my_cached_data')
#     if data is None:
#         # Data is not in the cache, so fetch it
#         data = expensive_operation()
#         cache.set('my_cached_data', data, timeout=60 * 60)  # Cache for 1 hour
#     return render(request, 'my_template.html', {'data': data})

# def clear_my_cache(request):
#     cache.delete('my_cached_data')
#     return HttpResponse("Cache cleared!")



# Create your views here.


from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import get_user_model
# from .forms import CustomUserCreationForm

class SignUpView(generic.CreateView):
	form_class = CustomUserCreationForm
	success_url = reverse_lazy('login') # Redirect to the login page after successful registration
	template_name = 'digisig/signup.html' # Create this template

	def form_valid(self, form):
		user = form.save()
		# You can add additional logic here, such as sending a confirmation email
		Digisiguser.objects.create(
			digisig_user_django=user,
			digisiguser_firstname = form.cleaned_data['first_name'],
			digisiguser_lastname = form.cleaned_data['last_name'],
			digisiguser_interest = form.cleaned_data['interest'],
			digisiguser_academicstatus = form.cleaned_data['academic_status'],
			digisiguser_academicaffiliation = form.cleaned_data['academicaffiliation'],
			digisiguser_email = form.cleaned_data['email'],
		)
		return super().form_valid(form)


class CustomLoginView(LoginView):
	template_name = 'digisig/login.html' 
	redirect_authenticated_user = True # If the user is already logged in redirect them

	def get_success_url(self):
		return reverse('index') 


@cache_page(cache_timeout)
async def index(request):

	pagetitle = 'title'
	template = loader.get_template('digisig/index.html')

	manifestation_total, seal_total, item_total, catalogue_total = await index_info()

	context = {
		'pagetitle': pagetitle,
		'manifestation_total': manifestation_total,
		'seal_total': seal_total,
		'item_total': item_total,
		'catalogue_total': catalogue_total,
		}

	return HttpResponse(template.render(context, request))


#### ABOUT
async def about(request):

	pagetitle = 'title'
	context = {
		'pagetitle': pagetitle,
	}
	template = loader.get_template('digisig/about.html')					
	return HttpResponse(template.render(context, request))


#### Exhibit 

@cache_page(cache_timeout)
async def exhibit(request):
	pagetitle = 'title'

	representation_set = await exhibitgenerate()

	context = {
	'pagetitle': pagetitle,
	'representation_set': representation_set,
	}

	template = loader.get_template('digisig/exhibit.html')

	return HttpResponse(template.render(context, request))


########################### Discover ############################

async def discover(request, discovertype):

	if discovertype == "map":

		pagetitle = 'Map'
		qcollection= 30000287
		qmapchoice = 1
		mapdic = []
		regiondisplayset = []
		region_dict = []
		mapcounties = []
		location_dict = []

		form = CollectionForm_digisig(request.POST or None)
		form = await collectionform_options(form)

		if request.method == 'POST':

			if form.is_valid():
				collectionstr = form.cleaned_data['collection']
				#make sure values are not empty then try and convert to ints
				if len(collectionstr) > 0:
					qcollection = int(collectionstr)

				mapchoicestr = form.cleaned_data['mapchoice']
				if len(mapchoicestr) > 0:
					qmapchoice = int(mapchoicestr)

			#map points
			if (qmapchoice == 1):
				locationset = await map_locationset(qcollection)
				location_dict, center_long, center_lat = await mapgenerator2(locationset)		

			#map counties
			elif (qmapchoice == 2):
				#if collection is set then limit the scope of the dataset
				placeset = await map_placeset(qcollection)
				mapcounties = await map_counties(placeset)

			#map regions
			else:
				regiondisplayset = await map_regionset(qcollection)
				region_dict = await mapgenerator3(regiondisplayset)

		template = loader.get_template('digisig/map.html')
		context = {
			'pagetitle': pagetitle,
			'location_dict': location_dict,
			'counties_dict': mapcounties,
			'region_dict': region_dict,
			'form': form,
			}

		return HttpResponse(template.render(context, request))


############################ Analyze #############################

async def analyze(request, analysistype):

	if analysistype == "time":

		pagetitle = 'Time'
		qcollection= 30000287
		qmapchoice = 1
		mapdic = []
		regiondisplayset = []
		region_dict = []
		mapcounties = []
		location_dict = []

		form = CollectionForm_digisig(request.POST or None)
		form = await collectionform_options(form)

		if request.method == 'POST':

			if form.is_valid():
				collection_value = form.cleaned_data.get('collection')
				qcollection = None
				if collection_value:
					try:
						qcollection = int(collection_value)
					except ValueError:
						print(f"Error: '{collection_value}' is not a valid integer for collection.")

				mapchoice_value = form.cleaned_data.get('mapchoice')
				qmapchoice = None
				if mapchoice_value:
					try:
						qmapchoice = int(mapchoice_value)
					except ValueError:
						print(f"Error: '{mapchoice_value}' is not a valid integer for map choice.")			

				timechoice_value = form.cleaned_data.get('timechoice')
				qtimechoice = None
				if timechoice_value:
					try:
						qtimechoice = int(timechoice_value)
					except ValueError:
						print(f"Error: '{timechoice_value}' is not a valid integer for time choice.")

				sealtypechoice_value = form.cleaned_data.get('sealtypechoice')
				qsealtypechoice = None
				if sealtypechoice_value:
					try:
						qsealtypechoice = int(sealtypechoice_value)
					except ValueError:
						print(f"Error: '{sealtypechoice_value}' is not a valid integer for seal type choice.")

			#map points
			if (qmapchoice == 1):
				locationset = await map_locationset(qcollection, qtimechoice, qsealtypechoice)
				location_dict, center_long, center_lat = await mapgenerator2(locationset)		

			#map counties
			elif (qmapchoice == 2):
				#if collection is set then limit the scope of the dataset
				placeset = await map_placeset(qcollection, qtimechoice, qsealtypechoice)
				mapcounties = await map_counties(placeset)

			#map regions
			else:
				regiondisplayset = await map_regionset(qcollection, qtimechoice, qsealtypechoice)
				region_dict = await mapgenerator3(regiondisplayset)

		template = loader.get_template('digisig/analysis_time.html')
		context = {
			'pagetitle': pagetitle,
			'location_dict': location_dict,
			'counties_dict': mapcounties,
			'region_dict': region_dict,
			'form': form,
			}

		return HttpResponse(template.render(context, request))


###### Dates ##########
	if analysistype == "dates":

		pagetitle = 'Dates'

		form = DateForm(request.POST or None)
		form = await dateform_options(form)

		#default values
		resulttext = ''
		resultrange= ''
		decisiontreetext = ''
		decisiontreedic = ''
		finalnodevalue = ''
		labels = []
		data1 = []
		representationset = []
		manifestation_set = []

		if request.method == 'POST':

			if form.is_valid(): 
				shape_object, class_object, resultarea = await datesearchfilter(form)

				try:
					# fetch the current model
					url = os.path.join(settings.BASE_DIR, 'staticfiles/ml/ml_tree')
					print ("try")

					with open(url, 'rb') as file:	
						mlmodel = pickle.load(file)

				except:
					# fetch the current model
					url = os.path.join(settings.BASE_DIR, 'digisig\\static\\ml\\ml_tree')
					print ("except")

					with open(url, 'rb') as file:	
						mlmodel = pickle.load(file)

				# pass model and features of seal to function that predicts the date
				result, result1, resulttext, finalnodevalue, df = await mlpredictcase(class_object, shape_object, resultarea, mlmodel)

				# get information about decision path
				decisionpathout, decisiontreedic = await mlshowpath(mlmodel, df)

				seal_set, resultrange, resultset, labels, data1 = await finalnodevalue_set(finalnodevalue, shape_object, class_object)

				seal_set, totalrows, totaldisplay = await defaultpagination(seal_set, 1)

				manifestation_set = await mlmanifestation_set(seal_set)

		context = {
			'pagetitle': pagetitle,
			'form': form,
			'resulttext': resulttext,
			'resultrange': resultrange,
			'labels': labels,
			'data1': data1,
			# 'representationset': representationset,
			'manifestation_set': manifestation_set,
			'decisiontreedic': decisiontreedic,
			'finalnodevalue': finalnodevalue,
			}

		template = loader.get_template('digisig/analysis_date.html')
		return HttpResponse(template.render(context, request))


#################### Search #########################
async def search(request, searchtype):

### Actor Search

	if searchtype == "actors":
		
		pagetitle = 'Search Actors'

		form = PeopleForm(request.POST or None)
		form = await peopleform_options(form) 

		qpagination = 1

		individual_object = await individualsearch()

		if request.method == 'POST':

			if form.is_valid():
				qpagination = form.cleaned_data['pagination']
				individual_object = await peoplesearchfilter(individual_object, form)

		individual_object, totalrows, totaldisplay = await defaultpagination(individual_object, qpagination)

		pagecountercurrent = qpagination
		pagecounternext = qpagination + 1
		pagecounternextnext = qpagination +2

		individual_set = await actornamegenerator(individual_object)

		context = {
			'pagetitle': pagetitle,
			'individual_set': individual_set,
			'totalrows': totalrows,
			'totaldisplay': totaldisplay,
			'form': form,
			'pagecountercurrent': pagecountercurrent,
			'pagecounternext': pagecounternext,
			'pagecounternextnext': pagecounternextnext,
			}

		template = loader.get_template('digisig/search_actor.html')
		return HttpResponse(template.render(context, request))


### Search Item

	if searchtype == "items":

		pagetitle = 'Search Items'

		form = ItemForm(request.POST or None)
		form = await itemform_options(form)

		# code prepares the array of series and repositories to pass to the frontend
		series_object= await seriesset()

		qpagination = 1

		item_object = await itemsearch()

		if request.method == 'POST':

			if form.is_valid(): 
				item_object, qpagination = await itemsearchfilter(item_object, form)

		item_pageobject, totalrows, totaldisplay = await defaultpagination(item_object, qpagination)

		pagecountercurrent = qpagination 
		pagecounternext = qpagination + 1
		pagecounternextnext = qpagination +2

		item_displayset = await item_displaysetgenerate(item_pageobject)

		context = {
			'pagetitle': pagetitle,
			'itemset': item_displayset,
			'totalrows': totalrows,
			'totaldisplay': totaldisplay,
			'form': form,
			'series_object': series_object,
			'pagecountercurrent': pagecountercurrent,
			'pagecounternext': pagecounternext,
			'pagecounternextnext': pagecounternextnext,
			}

		template = loader.get_template('digisig/search_item.html')
		return HttpResponse(template.render(context, request))


### Search Seals

	if searchtype == "seals":

		pagetitle = 'Impressions, Matrices and Casts'

		form = ManifestationForm(request.POST or None)
		# form options for manifestation
		form = await manifestationsform_options(form)
		# add the section of form that deals with series and repositories
		form = await itemform_options(form)

		# code prepares the array of series and repositories to pass to the frontend
		series_object= await seriesset()

		qpagination = 1

		manifestation_object = await manifestation_search_all()

		if request.method == 'POST':

			if form.is_valid(): 
				manifestation_object, qpagination = await sealsearchfilter(manifestation_object, form)

		manifestation_pageobject, totalrows, totaldisplay = await defaultpagination(manifestation_object, qpagination)

		pagecountercurrent = qpagination 
		pagecounternext = qpagination + 1
		pagecounternextnext = qpagination +2

		representation_set = await representationsetgenerate(manifestation_pageobject)
		manifestation_set, totalmanifestation_count = await manifestation_searchsetgenerate(manifestation_pageobject)
		manifestation_display_dic, listofseals, listofevents, listofactors = await manifestation_displaysetgenerate(manifestation_set, representation_set)
		description_set = await sealdescription_displaysetgenerate2(listofseals)
		location_set = await location_displaysetgenerate(listofevents)
		manifestation_displayset = await finalassembly_displaysetgenerate(manifestation_display_dic, location_set, description_set)

	# return manifestation_displayset


		context = {
			'pagetitle': pagetitle, 
			'manifestation_set': manifestation_displayset,
			'totalrows': totalrows,
			'totaldisplay': totaldisplay,
			'form': form,
			'pagecountercurrent': pagecountercurrent,
			'pagecounternext': pagecounternext,
			'pagecounternextnext': pagecounternextnext,
			'series_object': series_object,
			}

		template = loader.get_template('digisig/search_seal.html')                    

		return HttpResponse(template.render(context, request))

###### Search Seal Descriptions ##########

	if searchtype == "sealdescriptions":

		pagetitle = 'Seal Descriptions'

		form = SealdescriptionForm(request.POST or None)
		form = await sealdescriptionform_options(form)

		qpagination = 1

		sealdescription_object = await sealdescription_search()

		if request.method == 'POST':

			if form.is_valid(): 
				sealdescription_object, qpagination = await sealdescriptionsearchfilter(sealdescription_object, form)

		sealdescription_object, totalrows, totaldisplay = await defaultpagination(sealdescription_object, qpagination) 

		pagecountercurrent = qpagination
		pagecounternext = qpagination + 1
		pagecounternextnext = qpagination +2		

		sealdescription_displayset = await sealdescription_displaysetgenerate(sealdescription_object)

		context = {
			'pagetitle': pagetitle,
			'sealdescription_object': sealdescription_displayset,
			'totalrows': totalrows,
			'totaldisplay': totaldisplay,
			'form': form,
			'pagecountercurrent': pagecountercurrent,
			'pagecounternext': pagecounternext,
			'pagecounternextnext': pagecounternextnext,
			}

		template = loader.get_template('digisig/search_sealdescription.html')
		return HttpResponse(template.render(context, request))


### Search Places 
	
	if searchtype == "places":

		pagetitle = 'Search Places'

		form = PlaceForm(request.POST or None)
		form = await placeform_options(form)

		qpagination = 1

		place_object = await place_search()

		if request.method == 'POST':

			if form.is_valid(): 
				place_object, qpagination = await placesearchfilter(place_object, form)

		place_object = await placeobjectannotate(place_object)

		placepage_object, totalrows, totaldisplay = await defaultpagination(place_object, qpagination) 

		pagecountercurrent = qpagination
		pagecounternext = qpagination + 1
		pagecounternextnext = qpagination +2		

		# place_dict = []
		# center_long = 0
		# center_lat = 55

		place_dict, center_long, center_lat = await mapgenerator2(placepage_object)

		context = {
			'pagetitle': pagetitle,
			'placeset': placepage_object,
			'place_dict': place_dict,
			'center_long': center_long,
			'center_lat': center_lat,
			'totalrows': totalrows,
			'totaldisplay': totaldisplay,
			'form': form,
			'pagecountercurrent': pagecountercurrent,
			'pagecounternext': pagecounternext,
			'pagecounternextnext': pagecounternextnext,
			}

		template = loader.get_template('digisig/search_place.html')
		return HttpResponse(template.render(context, request))

######################### information ################################

async def information(request, infotype):
	if infotype == "changelog":
		pagetitle = 'title'

		cache_key = 'changelog_data'  # Unique key for the cache
		change_object = cache.get(cache_key)

		if change_object is None:
			change_object = await information_changes()
			cache.set(cache_key, change_object, timeout=cache_timeout)

		context = {
			'pagetitle': pagetitle,
			'change_object': change_object,
		}

		template = loader.get_template('digisig/change.html')					
		return HttpResponse(template.render(context, request))


############## Help ###############
	if infotype == "help":
		pagetitle = 'title'

		template = loader.get_template('digisig/help.html')

		class_object, shape_object, nature_object = await information_help()

		context = {
			'pagetitle': pagetitle,
			'class_object': class_object,
			'shape_object': shape_object,
			'nature_object': nature_object,
			}
		return HttpResponse(template.render(context, request))


########################### Contributors #########################
	if infotype == "contributors":

		pagetitle = 'title'
		context = {
			'pagetitle': pagetitle,
		}

		template = loader.get_template('digisig/contributors.html')					
		return HttpResponse(template.render(context, request))



########################### Collections #########################
	if infotype == "collections":

		#default
		digisig_entity_number= 30000287

		form = CollectionForm_digisig(request.POST or None)
		form = await digisigcollection_options(form)

		#adjust values if form submitted
		if request.method == 'POST':

			if form.is_valid():
				collectionstr = form.cleaned_data['collection']

				#make sure values are not empty then try and convert to ints
				if len(collectionstr) > 0:
					digisig_entity_number = int(collectionstr)

			else:
				print ("not valid")

		targetphrase = "/page/collection/" + str(digisig_entity_number)

		return redirect(targetphrase)


############ Terminology ###############
	if infotype =="terminology":
		pagetitle = 'Terminology'

		generalset, natureset, topset, shapeset = await information_terminology()

		context = {
			'generalobject': generalset,
			'natureobject': natureset,
			'classterms': topset,
			'shapeobject': shapeset,
			'pagetitle': pagetitle,
			}
		template = loader.get_template('digisig/terminology.html')                    
		return HttpResponse(template.render(context, request))


################################ ML ######################################

	#### 4/23/2025 -- removed hyper link to this page
	if infotype == "machinelearning":

		pagetitle = 'ML'

		form = MLpredictionForm(initial={'classification': 10000487})
		qcollection = 30000047
		qclassification = 10000487

		#adjust values if form submitted
		if request.method == 'POST':
			form = MLpredictionForm(request.POST)

			if form.is_valid():
				qclassification = int(form.cleaned_data['classification'])
				qcollection = int(form.cleaned_data['collection2'])

		event_seal, labels, data1, data2 = await information_ML(qcollection, qclassification)

		# data1 = []
		# data2 = []
		# labels = []
		# event_seal = []

		# seal_set = Seal.objects.filter(fk_sealsealdescription__fk_collection=qcollection).filter(fk_seal_face__fk_class=qclassification)

		# if len(seal_set) > 0:
		# 	for s in seal_set:

		# 		### 1/7/2024 -- attempting to put human readable labels -- not working yet -- javascript fails on string with quotes
		# 		sealdescription_entry = Sealdescription.objects.get(Q(fk_collection=qcollection) & Q(fk_seal=s.id_seal))

		# 		event_seal = Event.objects.get(part__fk_part__fk_support__fk_face__fk_seal=s.id_seal)

		# 		try:
		# 			start = event_seal.repository_startdate
		# 			end = event_seal.repository_enddate
		# 			starty = start.year
		# 			endy = end.year

		# 			try:
		# 				start2 = event_seal.startdate
		# 				end2 = event_seal.enddate

		# 				if start2.year > 0 :
		# 					data1.append([starty, endy])
		# 					# data2.append(liney)
		# 					data2.append([start2.year, end2.year])
		# 					#labels.append(event_seal.pk_event)
		# 					labels.append(s.id_seal)

		# 			except:

		# 				print ("fail2", event_seal)

		# 			if starty > 1500:
		# 				print ("fail", event_seal, start, end, starty, endy, start2, end2)

		# 		except:

		# 			print ("fail1", event_seal)

		template = loader.get_template('digisig/machinelearning.html')

		context = {
			'pagetitle': pagetitle,
			'event_object': event_seal,
			'labels': labels,
			'data1': data1,
			'data2': data2,
			'form': form,
			}

		return HttpResponse(template.render(context, request))





############################## ENTITY #########################

@login_required(login_url='/login/')
async def entity(request, digisig_entity_number):

	#create flag that this is a view operation....
	operation = 1
	application = 1

	#item = 0, seal=1, manifestation=2, sealdescription=3, etc...
	targetphrase = redirectgenerator(digisig_entity_number, operation, application)

	return redirect(targetphrase)


async def entity_fail(request, entity_phrase):
	pagetitle = 'title'

	print(entity_phrase)

	return HttpResponse("%s is not an entity I know about." % entity_phrase)


############################## Actor #############################

#@method_decorator(login_required(login_url='/login/'), name='dispatch')
#@method_decorator(sync_to_async(login_required(login_url='/login/')), name='dispatch')


class EntityView(View):
	
	@method_decorator(login_required(login_url='/login/'))
	async def dispatch(self, request, *args, **kwargs):
		return await super().dispatch(request, *args, **kwargs)

	async def get(self, request, entity_type, digisig_entity_number):
		if entity_type == 'actor':
			return await self.actor_page(request, digisig_entity_number)
		elif entity_type == 'collection':

			return await self.collection_page(request, digisig_entity_number)
		elif entity_type == 'item':
			return await self.item_page(request, digisig_entity_number)
		elif entity_type == 'manifestation':
			return await self.manifestation_page(request, digisig_entity_number)
		elif entity_type == 'place':
			return await self.place_page(request, digisig_entity_number)
		elif entity_type == 'representation':
			return await self.representation_page(request, digisig_entity_number)
		elif entity_type == 'seal':
			return await self.seal_page(request, digisig_entity_number)
		elif entity_type == 'sealdescription':
			return await self.sealdescription_page(request, digisig_entity_number)
		elif entity_type == 'term':
			return await self.term_page(request, digisig_entity_number)
		else:
			raise Http404("Invalid entity type")


################################ Actor ######################################

	async def actor_page(self, request, digisig_entity_number):


		# establishing the base queries
		individual_object = await individualsearch(digisig_entity_number)
		manifestation_set = await manifestation_search()

		# limits manifestation set to cases connected with actor in question
		manifestation_object = await sealsearch_actor(manifestation_set, digisig_entity_number)

		# #hack to deal with cases where there are too many seals for the form to handle
		qpagination = 1
		manifestation_pageobject, totalrows, totaldisplay = await defaultpagination(manifestation_object, qpagination)

		############ compile information for Actor
		# get representation information
		representation_set = await representationsetgenerate(manifestation_pageobject)
		manifestation_set, totalmanifestation_count = await manifestation_searchsetgenerate(manifestation_pageobject)
		manifestation_display_dic, listofseals, listofevents, listofactors = await manifestation_displaysetgenerate(manifestation_set, representation_set)
		description_set = await sealdescription_displaysetgenerate2(listofseals)
		location_set = await location_displaysetgenerate(listofevents)
		manifestation_object = await finalassembly_displaysetgenerate(manifestation_display_dic, location_set, description_set)

		relationship_object, relationshipnumber = await relationship_dataset(digisig_entity_number)

		# list of references to the actor
		reference_set = await referenceset_references(digisig_entity_number)

		pagetitle= namecompiler(individual_object)

		context = {
			'pagetitle': pagetitle,
			'individual_object': individual_object,
			'relationship_object': relationship_object,
			'relationshipnumber' : relationshipnumber,
			'manifestation_set': manifestation_object,
			'totalrows': totalrows,
			'totaldisplay': totaldisplay,
			'reference_set': reference_set,
			}

		# template = loader.get_template('digisig/actor.html')

		return render(request, 'digisig/actor.html', context)


################################ Collection ######################################

#https://allwin-raju-12.medium.com/reverse-relationship-in-django-f016d34e2c68

	async def collection_page(self, request, digisig_entity_number):
		pagetitle = 'Collection'

		#defaults
		qcollection = int(digisig_entity_number)
		
		### This code prepares collection info box and the data for charts on the collection page

		form = CollectionForm_digisig(request.POST or None)
		collection_choices = await digisigcollection_options(form)

		collection, collection_dic, sealdescription_set = await collection_details(qcollection)

		contributor_dic = await sealdescription_contributorgenerate(collection, collection_dic)

		### generate the collection info data for chart 1
		actorscount, datecount, classcount, facecount = await collection_counts(sealdescription_set)

		actors = await calpercent(collection_dic["totalseals"], actorscount)
		date = await calpercent(collection_dic["totalseals"], datecount)
		fclass = await calpercent(facecount, classcount)
	 
		data1 = [actors, date, fclass]
		labels1 = ["actor", "date", "class"]

		### generate the collection info data for chart 2 -- 'Percentage of seals per class',

		data2, labels2 = await collection_chart2()

		### generate the collection info data for chart 3  -- 'Percentage of seals by period',

		data3, labels3 = await datedistribution(qcollection)

		maplayer = await collection_loadmaplayer(1)

		regiondisplayset = await map_regionset(qcollection)

		region_dict = await mapgenerator3(regiondisplayset)

		# ### generate the collection info data for chart 5 --  'Percentage of actors per class',

		data5, labels5 = await collection_printgroup(qcollection, collection_dic)


		context = {
			'pagetitle': pagetitle,
			'collection': collection,
			'collection_dic': collection_dic,
			'contributor_dic': contributor_dic,
			'labels1': labels1,
			'data1': data1,
			'labels2': labels2,
			'data2': data2,
			'labels3': labels3,
			'data3': data3,
			'region_dict': region_dict,
			'maplayer': maplayer,
			'labels5': labels5,
			'data5': data5,
			'form': form,
		}
			
		# template = loader.get_template('digisig/collection.html') 
					 
		return render(request, 'digisig/collection.html', context)


############################## Face #############################


############################## Item #############################

	async def item_page(self, request, digisig_entity_number):

		part_dic = await partobjectforitem_define(digisig_entity_number)

		if len(part_dic) == 1:

			for key, part_info in part_dic.items():
				# template = loader.get_template('digisig/item.html')
				context = {
					'pagetitle': part_info['pagetitle'],
					'part_object': part_info,
					'mapdic': part_info['mapdic'],
					}
		
		## this seems to be a hack to deal with cases with multiple parts #14/5/2025
		else:
			# template = loader.get_template('digisig/item.html')
			for key, part_info in part_dic.items():
				template = loader.get_template('digisig/item.html')
				context = {
					'pagetitle': part_info['pagetitle'],
					'part_object': part_info,
					'mapdic': part_info['mapdic'],
					}

		return render(request, 'digisig/item.html', context)

############################ Manifestation #####################

	async def manifestation_page(self, request, digisig_entity_number): 
		####manifestation_dic = await manifestation_createdic(manifestation_object)
		pagetitle = 'title'

		# manifestation_object = await manifestationobject_define(digisig_entity_number)

		manifestation_set, totalmanifestation_count = await manifestation_searchsetgenerate(digisig_entity_number, searchtype="manifestation")
		representation_set = await representationsetgenerate2(manifestation_set, primacy=True)
		manifestation_display_dic, listofseals, listofevents, listofactors = await manifestation_displaysetgenerate(manifestation_set, representation_set)
		description_set = await sealdescription_displaysetgenerate2(listofseals)
		name_set = await namecompiler_group(listofactors)
		manifestation_info = await seal_displaysetgenerate(manifestation_display_dic, description_set, digisig_entity_number, name_set)
		outname, actor_id = await actorfinder(manifestation_set)

		first_item = next(iter(manifestation_display_dic.items()))
		first_key, manifestation_dic = first_item

		#template = loader.get_template('digisig/manifestation.html')
		context = {
				'pagetitle': pagetitle,
				'manifestation_info': manifestation_info,
				'manifestation_dic': manifestation_dic,
				'outname': outname,
		}

		return render(request, 'digisig/manifestation.html', context)



############################## Part #############################



############################## Place #############################

	async def place_page(self, request, digisig_entity_number):


		# displaystatus = 1

		qpagination = 1

		if request.method == 'POST':
			form = PageCycleForm(request.POST)

			if form.is_valid():
				qpagination = form.cleaned_data['pagination']
				form = PageCycleForm(request.POST)
				# displaystatus = 0		

		else:
			form = PageCycleForm()

		place_object, pagetitle = await place_information(digisig_entity_number)

		mapdic = await mapgenerator(place_object)

		placecall = True
		manifestation_object = await manifestation_search(digisig_entity_number, placecall)

		# #note that is should pick up cases where manifestations are associated with secondary places?
		# manifestation_object = manifestation_object.filter(
		# 		fk_support__fk_part__fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location=digisig_entity_number).distinct()

		## these pagecounters are going to break on pages that are small lists
		manifestation_pageobject, totalrows, totaldisplay = await defaultpagination(manifestation_object, qpagination)
		pagecountercurrent = qpagination 
		pagecounternext = qpagination + 1
		pagecounternextnext = qpagination +2

		representation_set = await representationsetgenerate(manifestation_pageobject)
		manifestation_set, totalmanifestation_count = await manifestation_searchsetgenerate(manifestation_pageobject)
		manifestation_display_dic, listofseals, listofevents, listofactors = await manifestation_displaysetgenerate(manifestation_set, representation_set)
		description_set = await sealdescription_displaysetgenerate2(listofseals)
		location_set = await location_displaysetgenerate(listofevents)
		manifestation_output = await finalassembly_displaysetgenerate(manifestation_display_dic, location_set, description_set)

		context = {
			'pagetitle': pagetitle,
			'place_object': place_object,
			'mapdic': mapdic, 
			'manifestation_set': manifestation_output,
			'totalrows': totalrows,
			'totaldisplay': totaldisplay,
			'form': form,
			'pagecountercurrent': pagecountercurrent,
			'pagecounternext': pagecounternext,
			'pagecounternextnext': pagecounternextnext,
			}

		# template = loader.get_template('digisig/place.html')  

		return render(request, 'digisig/place.html', context)


############################## Representation #############################

	async def representation_page(self, request, digisig_entity_number):

		pagetitle = 'Representation'
		template = loader.get_template('digisig/representation.html')

		representation_object = await representation_queryformulate(digisig_entity_number)

		representation_dic = await representationmetadata(representation_object)

		# Entity type is determined by the final digit in the DIGISIG ID number (manifestation=2, sealdescription=3, part=8)
		entitytype = representation_dic["entity_type"]
		searchvalue = representation_dic['entity_link']

		if entitytype == 2:
			manifestation_case, totalmanifestation_count = await manifestation_searchsetgenerate(searchvalue, searchtype="manifestation")
			representation_dic = await representationmetadata_manifestation(manifestation_case, representation_dic)
			representation_dic = await representationmetadata_part(manifestation_case, representation_dic)
			representation_dic['outname'], actor_id = await actorfinder(manifestation_case)

			# representation_dic = await representationmetadata_part(representation_object, representation_dic)
			#representation_dic = await representationmetadata_manifestation(representation_object, representation_dic)

		if entitytype == 3:
			representation_dic = await representationmetadata_sealdescription(representation_object, representation_dic)

		if entitytype == 8:
			representation_dic = await representationmetadata_partquery(searchvalue, representation_dic)
			
			#representation_dic = await representationmetadata_part(representation_object, representation_dic)

		context = {
			'pagetitle': pagetitle,
			'representation_dic': representation_dic,
			}

		#template = loader.get_template('digisig/representation.html')
		return render(request, 'digisig/representation.html', context)


############################## Seal #############################

	async def seal_page(self, request, digisig_entity_number):
		pagetitle = 'title'

		manifestation_set, totalmanifestation_count = await manifestation_searchsetgenerate(digisig_entity_number, searchtype="seal")
		representation_set = await representationsetgenerate2(manifestation_set)
		manifestation_display_dic, listofseals, listofevents, listofactors = await manifestation_displaysetgenerate(manifestation_set, representation_set)
		description_set = await sealdescription_displaysetgenerate2(listofseals)
		name_set = await namecompiler_group(listofactors)
		# location_set = await location_displaysetgenerate(listofevents)

		seal_info = await seal_displaysetgenerate(manifestation_display_dic, description_set, digisig_entity_number, name_set)

		context = {
			'pagetitle': pagetitle,
			'seal_info': seal_info,
			}

		#template = loader.get_template('digisig/seal.html')

		return render(request, 'digisig/seal.html', context)


############################## Seal description #############################

	async def sealdescription_page(self, request, digisig_entity_number):

		template = loader.get_template('digisig/sealdescription.html')

		sealdescription_object = await sealdescription_fetchobject(digisig_entity_number)
		
		pagetitle = sealdescription_object.fk_collection.collection_title

		sealdescription_dic= await sealdescription_fetchrepresentation(sealdescription_object)
		sealdescription_dic = await sealdescription_contributorgenerate(sealdescription_object.fk_collection, sealdescription_dic)
		externallinkset = await externallinkgenerator(digisig_entity_number)

		context = {
			'pagetitle': pagetitle,
			'sealdescription_object': sealdescription_object,
			'sealdescription_dic': sealdescription_dic,
			'externallinkset': externallinkset, 
			}

		#template = loader.get_template('digisig/sealdescription.html')

		return render(request, 'digisig/sealdescription.html', context)


############################## Support #############################


################################ TERM ######################################

	async def term_page(self, request, digisig_entity_number):
		pagetitle = 'Term'

		term_object, statement_object = await entity_term(digisig_entity_number)

		template = loader.get_template('digisig/term.html')
		context = {
			'pagetitle': pagetitle,
			'term_object': term_object,
			'statement_object': statement_object,
			}

		return render(request, 'digisig/term.html', context)