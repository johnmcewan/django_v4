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
# from django.db.models.functions import Concat
# from django.db.models import CharField
from django.core import serializers

from .models import *
from .forms import * 
# from utils.mltools import * 
from utils.generaltools import *
from utils.viewtools import *

import json
import os
import pickle


# Table of Contents
	# index
	# about
	# exhibit


# Create your views here.
def index(request):
	# return render(request, 'digisig/index.html', {})

	pagetitle = 'title'
	template = loader.get_template('digisig/index.html')

	#### update this to remove databasecall

	manifestation_total = Manifestation.objects.count()
	seal_total = Seal.objects.count()
	#item_total = Support.objects.distinct('fk_part__fk_item').count()
	item_total = 53408
	catalogue_total = Sealdescription.objects.count()

	context = {
		'pagetitle': pagetitle,
		'manifestation_total': manifestation_total,
		'seal_total': seal_total,
		'item_total': item_total,
		'catalogue_total': catalogue_total,
		}

	return HttpResponse(template.render(context, request))


#### ABOUT
def about(request):

	pagetitle = 'title'
	context = {
		'pagetitle': pagetitle,
	}
	template = loader.get_template('digisig/about.html')					
	return HttpResponse(template.render(context, request))


#### Exhibit 

 
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

		form = CollectionForm(request.POST or None)
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

		# #default
		# qcollection= 30000287
		# qmapchoice = 1
		# mapdic = []
		# regiondisplayset = []
		# region_dict = []
		# mapcounties = []
		# location_dict = []

		# #adjust values if form submitted
		# if request.method == 'POST':
		# 	form = CollectionForm(request.POST)
			
		# 	if form.is_valid():
		# 		collectionstr = form.cleaned_data['collection']
		# 		#make sure values are not empty then try and convert to ints
		# 		if len(collectionstr) > 0:
		# 			qcollection = int(collectionstr)

		# 		mapchoicestr = form.cleaned_data['mapchoice']
		# 		if len(mapchoicestr) > 0:
		# 			qmapchoice = int(mapchoicestr)

		# #map points
		# if (qmapchoice == 1):
		# 	if (qcollection == 30000287):
		# 		locationset = Location.objects.filter(
		# 			Q(locationname__locationreference__fk_locationstatus=1)).annotate(count=Count('locationname__locationreference__fk_event__part__fk_part__fk_support'))

		# 	else:
		# 		#data for location map
		# 		locationset = Location.objects.filter(
		# 			Q(locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__sealdescription__fk_collection=qcollection)).annotate(count=Count('locationname__locationreference__fk_event__part__fk_part__fk_support'))

		# 	location_dict, center_long, center_lat = mapgenerator2(locationset)

		# #map counties
		# elif (qmapchoice == 2):
		# 	#if collection is set then limit the scope of the dataset
		# 	if (qcollection == 30000287):
		# 		#data for map counties
		# 		placeset = Region.objects.filter(fk_locationtype=4, 
		# 			location__locationname__locationreference__fk_locationstatus=1
		# 			).annotate(numplaces=Count('location__locationname__locationreference__fk_event__part__fk_part__fk_support')) 

		# 	else:
		# 		#data for map counties
		# 		placeset = Region.objects.filter(fk_locationtype=4, 
		# 			location__locationname__locationreference__fk_locationstatus=1, 
		# 			location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__sealdescription__fk_collection=qcollection
		# 			).annotate(numplaces=Count('location__locationname__locationreference'))

		# 	## data for colorpeth map
		# 	mapcounties1 = get_object_or_404(Jsonstorage, id_jsonfile=1)
		# 	mapcounties = json.loads(mapcounties1.jsonfiletxt)

		# 	for i in mapcounties:
		# 		if i == "features":
		# 			for b in mapcounties[i]:
		# 				j = b["properties"]
		# 				countyvalue = j["HCS_NUMBER"]
		# 				countyname = j["NAME"]
		# 				numberofcases = placeset.filter(fk_his_countylist=countyvalue)
		# 				for i in numberofcases:
		# 					j["cases"] = i.numplaces

		# #map regions
		# else:
		# 	if (qcollection == 30000287):
		# 		regiondisplayset = Regiondisplay.objects.filter(region__location__locationname__locationreference__fk_locationstatus=1
		# 			).annotate(numregions=Count('region__location__locationname__locationreference__fk_event__part__fk_part__fk_support')) 

		# 	else:
		# 		#data for region map 
		# 		regiondisplayset = Regiondisplay.objects.filter( 
		# 			region__location__locationname__locationreference__fk_locationstatus=1, 
		# 			region__location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__sealdescription__fk_collection=qcollection
		# 			).annotate(numregions=Count('region__location__locationname__locationreference'))

		# 	region_dict = mapgenerator3(regiondisplayset)


		# form = CollectionForm(initial={'collection': qcollection, 'mapchoice': qmapchoice})		

		# template = loader.get_template('digisig/map.html')
		# context = {
		# 	'pagetitle': pagetitle,
		# 	'location_dict': location_dict,
		# 	'counties_dict': mapcounties,
		# 	'region_dict': region_dict,
		# 	'form': form,
		# 	}

		# return HttpResponse(template.render(context, request))



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

		form = CollectionForm(request.POST or None)
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

		# print (decisiontreetext)
		# print (type(decisiontreetext))
		# print (decisiontreetext[1])

		# print (manifestation_set)
		#print (labels, data1)

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
			#'sealindividual': sealindividual,
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

		# manifestation_displayset = await manifestation_construction(manifestation_pageobject)

	# async def manifestation_construction(manifestation_pageobject):
	# 	"""
	# 	Function prepares the data for the seal search (manifestation) page
	# 	"""
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



		# placeset = Location.objects.filter(locationname__locationreference__fk_locationstatus=1, longitude__isnull=False, latitude__isnull=False).order_by('location')

		# pagetitle = 'Places'
		# regionselect = False
		# qpagination = 1
		# place_dict = []
		# center_long = 0
		# center_lat = 55

		# if request.method == 'POST':

		# 	form = PlaceForm(request.POST)
		# 	if form.is_valid():
		# 		qregion = form.cleaned_data['region']
		# 		qcounty = form.cleaned_data['county']   
		# 		qpagination = form.cleaned_data['pagination']
		# 		qlocation_name = form.cleaned_data['location_name']

		# 		if qregion.isdigit():
		# 			if int(qregion) > 0:
		# 				placeset = placeset.filter(fk_region__fk_regiondisplay=qregion)
		# 				regionselect = True

		# 		if regionselect == False:
		# 			if qcounty.isdigit():
		# 				if int(qcounty) > 0:
		# 					placeset = placeset.filter(fk_region=qcounty)

		# 		if len(qlocation_name) > 0:
		# 			placeset = placeset.filter(location__icontains=qlocation_name)                  

		# 		form = PlaceForm(request.POST)

		# else:
		# 	form = PlaceForm()
		# 	qpagination = 1

		# placeset = placeset.annotate(count=Count('locationname__locationreference'))

		# placeset, totalrows, totaldisplay, qpagination = defaultpagination(placeset, qpagination) 
		# pagecountercurrent = qpagination
		# pagecounternext = qpagination + 1
		# pagecounternextnext = qpagination +2		

		# if len(placeset) > 0:
		# 	place_dict, center_long, center_lat = mapgenerator2(placeset)

		# context = {
		# 	'pagetitle': pagetitle,
		# 	'placeset': placeset,
		# 	'place_dict': place_dict,
		# 	'center_long': center_long,
		# 	'center_lat': center_lat,
		# 	'totalrows': totalrows,
		# 	'totaldisplay': totaldisplay,
		# 	'form': form,
		# 	'pagecountercurrent': pagecountercurrent,
		# 	'pagecounternext': pagecounternext,
		# 	'pagecounternextnext': pagecounternextnext,
		# 	}

		# template = loader.get_template('digisig/search_place.html')
		# return HttpResponse(template.render(context, request))


######################### information ################################


async def information(request, infotype):

	if infotype == "changelog":
		pagetitle = 'title'

		change_object = await information_changes() 

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

		form = CollectionForm(request.POST or None)
		form = await digisigcollection_options(form)

		#adjust values if form submitted
		if request.method == 'POST':

			if form.is_valid():
				collectionstr = form.cleaned_data['collection']

				print ("here is clean ", form.cleaned_data['collection'])

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

def entity(request, digisig_entity_number):

	print(digisig_entity_number)

	#create flag that this is a view operation....
	operation = 1
	application = 1

	#item = 0, seal=1, manifestation=2, sealdescription=3, etc...
	targetphrase = redirectgenerator(digisig_entity_number, operation, application)

	print ("targetphrase", targetphrase)

	return redirect(targetphrase)


def entity_fail(request, entity_phrase):
	pagetitle = 'title'

	print(entity_phrase)
	return HttpResponse("%s is not an entity I know about." % entity_phrase)


############################## Actor #############################

async def actor_page(request, digisig_entity_number):

	template = loader.get_template('digisig/actor.html')

	individual_object = await individualsearch(digisig_entity_number)
	pagetitle= namecompiler(individual_object)

	manifestation_set = await manifestation_search()
	manifestation_object = await sealsearch_actor(manifestation_set, digisig_entity_number)

	# #hack to deal with cases where there are too many seals for the form to handle
	qpagination = 1
	manifestation_pageobject, totalrows, totaldisplay = await defaultpagination(manifestation_object, qpagination)

	representation_set = await representationsetgenerate(manifestation_pageobject)
	manifestation_set, totalmanifestation_count = await manifestation_searchsetgenerate(manifestation_pageobject)
	manifestation_display_dic, description_set, listofseals, listofevents = await manifestation_displaysetgenerate(manifestation_set, representation_set)
	description_set = await sealdescription_displaysetgenerate2(listofseals)
	location_set = await location_displaysetgenerate(listofevents)
	manifestation_set = await finalassembly_displaysetgenerate(manifestation_display_dic, location_set, description_set)

	relationship_object, relationshipnumber = await relationship_dataset(digisig_entity_number)

	# list of references to the actor
	reference_set = await referenceset_references(digisig_entity_number)

	context = {
		'pagetitle': pagetitle,
		'individual_object': individual_object,
		'relationship_object': relationship_object,
		'relationshipnumber' : relationshipnumber,
		'manifestation_set': manifestation_set,
		'totalrows': totalrows,
		'totaldisplay': totaldisplay,
		'reference_set': reference_set,
		}

	return HttpResponse(template.render(context, request))


################################ Collection ######################################

#https://allwin-raju-12.medium.com/reverse-relationship-in-django-f016d34e2c68

async def collection_page(request, digisig_entity_number):
	pagetitle = 'Collection'

	#defaults
	qcollection = int(digisig_entity_number)
	
	### This code prepares collection info box and the data for charts on the collection page

	form = CollectionForm(request.POST or None)
	collection_choices = await digisigcollection_options(form)

	# #adjust values if form submitted
	# if request.method == 'POST':
		
	# 	if form.is_valid():

	# 		collection = form.cleaned_data['collection']

	# 		#make sure values are not empty then try and convert to ints
	# 		if len(collection) > 0:
	# 			qcollection = int(collection)

	# else:
	# 	pass




	collection, collection_dic, sealdescription_set = await collection_details(qcollection)

	contributor_dic = await sealdescription_contributorgenerate(collection, collection_dic)

	# collection = Collection.objects.get(id_collection=qcollection)

	# collection_dic = {}
	# collection_dic["id_collection"] = int(qcollection)
	# collection_dic["collection_thumbnail"] = collection.collection_thumbnail
	# collection_dic["collection_publicationdata"] = collection.collection_publicationdata
	# collection_dic["collection_fulltitle"] = collection.collection_fulltitle
	# collection_dic["notes"] = collection.notes
	# contributor_dic = sealdescription_contributorgenerate(collection, collection_dic)

	# sealdescription_set = Sealdescription.objects.filter(fk_seal__gt=1).select_related('fk_seal')

	# #if collection is set then limit the scope of the dataset
	# if (qcollection == 30000287):
	# 	collection_dic["collection_title"] = 'All Collections'
	# 	pagetitle = 'All Collections'
	# 	collection_dic["totalsealdescriptions"] = sealdescription_set.count()
	# 	collection_dic["totalseals"] = sealdescription_set.distinct('fk_seal').count()

	# else:
	# 	collection_dic["collection_title"] = collection.collection_title
	# 	pagetitle = collection.collection_title
	# 	sealdescription_set = sealdescription_set.filter(fk_collection=qcollection)
	# 	collection_dic["totalsealdescriptions"] = sealdescription_set.distinct(
	# 		'sealdescription_identifier').count()
	# 	collection_dic["totalseals"] = sealdescription_set.distinct(
	# 		'fk_seal').count()


	### generate the collection info data for chart 1
	actorscount, datecount, classcount, facecount = await collection_counts(sealdescription_set)

	# actorscount = sealdescription_set.filter(fk_seal__fk_individual_realizer__gt=10000019).count()

	# datecount =sealdescription_set.filter(fk_seal__date_origin__gt=1).count()

	# classcount = sealdescription_set.filter(
	# 	fk_seal__fk_seal_face__fk_class__isnull=False).exclude(
	# 	fk_seal__fk_seal_face__fk_class=10000367).exclude(
	# 	fk_seal__fk_seal_face__fk_class=10001007).count()

	# facecount = sealdescription_set.filter(fk_seal__fk_seal_face__fk_faceterm=1).distinct('fk_seal__fk_seal_face').count() 

	actors = await calpercent(collection_dic["totalseals"], actorscount)
	date = await calpercent(collection_dic["totalseals"], datecount)
	fclass = await calpercent(facecount, classcount)
 
	data1 = [actors, date, fclass]
	labels1 = ["actor", "date", "class"]

	### generate the collection info data for chart 2 -- 'Percentage of seals per class',

	data2, labels2 = await collection_chart2()

	# result = Terminology.objects.filter(
	# 	term_type=1).order_by(
	# 	'term_sortorder').annotate(
	# 	num_cases=Count("fk_term_interchange__fk_class__fk_class_face"))

	# totalcases = sum([r.num_cases for r in result])	

	# data2 = []
	# labels2 = []

	# for r in result:

	# 	percentageresult = (r.num_cases / totalcases) * 100 

	# 	if percentageresult > 1:
	# 		data2.append((r.num_cases / totalcases) * 100)
	# 		labels2.append(r.term_name)


	### generate the collection info data for chart 3  -- 'Percentage of seals by period',

	data3, labels3 = await datedistribution(qcollection)

	# ### generate the collection info data for chart 4 -- seals per region,

	## data for colorpeth map
	# maplayer1 = get_object_or_404(Jsonstorage, id_jsonfile=1)
	# maplayer = json.loads(maplayer1.jsonfiletxt)

	maplayer = await collection_loadmaplayer(1)


	## data for region map
	# make circles data -- defaults -- note that this code is very similar to the function mapdata2
	#data for region map 

	# if (qcollection == 30000287):
	# 	regiondisplayset = Regiondisplay.objects.filter(
	# 		region__location__locationname__locationreference__fk_locationstatus=1).annotate(
	# 		numregions=Count(
	# 			'region__location__locationname__locationreference__fk_event__part__fk_part__fk_support')).values(
	# 	'id_regiondisplay', 'id_regiondisplay', 'regiondisplay_label', 'numregions', 'regiondisplay_long', 'regiondisplay_lat') 
	# else:
	# 	regiondisplayset = Regiondisplay.objects.filter( 
	# 		region__location__locationname__locationreference__fk_locationstatus=1, 
	# 		region__location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection
	# 		).annotate(
	# 		numregions=Count(
	# 			'region__location__locationname__locationreference__fk_event__part__fk_part__fk_support')).values(
	# 	'id_regiondisplay', 'id_regiondisplay', 'regiondisplay_label', 'numregions', 'regiondisplay_long', 'regiondisplay_lat')

	regiondisplayset = await map_regionset(qcollection)

	region_dict = await mapgenerator3(regiondisplayset)

	# ### generate the collection info data for chart 5 --  'Percentage of actors per class',

	data5, labels5 = await collection_printgroup(qcollection, collection_dic)

	# #for print group totals (legacy)
	# if (qcollection == 30000287):
	# 	printgroupset = Printgroup.objects.annotate(numcases=Count('fk_printgroup', filter=Q(fk_printgroup__fk_sealsealdescription__fk_collection__gte=0))).order_by('printgroup_order')

	# else: printgroupset = Printgroup.objects.annotate(numcases=Count('fk_printgroup', filter=Q(fk_printgroup__fk_sealsealdescription__fk_collection=qcollection))).order_by('printgroup_order')

	# #for modern group system
	# if (qcollection == 30000287):
	# 	groupset = Groupclass.objects.annotate(numcases=Count('id_groupclass', filter=Q(fk_group_class__fk_group__fk_actor_group__fk_sealsealdescription__fk_collection__gte=0))).order_by('id_groupclass')

	# else:
	# 	groupset = Groupclass.objects.annotate(numcases=Count('id_groupclass', filter=Q(fk_group_class__fk_group__fk_actor_group__fk_sealsealdescription__fk_collection=qcollection))).order_by('id_groupclass')

	# data5 = []
	# labels5 = []
	# for g in groupset:
	# 	if (g.numcases > 0):
	# 		percentagedata = (g.numcases/collection_dic["totalseals"])*100 
	# 		# if percentagedata > 1:
	# 		data5.append(percentagedata)
	# 		labels5.append(g.groupclass)

	
	context = {
		'pagetitle': pagetitle,
		#'collectioninfo': collectioninfo,
		'collection': collection,
		'collection_dic': collection_dic,
		'contributor_dic': contributor_dic,
		'labels1': labels1,
		'data1': data1,
		'labels2': labels2,
		'data2': data2,
		'labels3': labels3,
		'data3': data3,
		# 'labels4': labels4,
		# 'data4': data4,await 
		'region_dict': region_dict,
		'maplayer': maplayer,
		'labels5': labels5,
		'data5': data5,
		'form': form,
	}
		
	template = loader.get_template('digisig/collection.html') 
				 
	return HttpResponse(template.render(context, request))


############################## Face #############################


############################## Item #############################

async def item_page(request, digisig_entity_number):

	part_dic = await partobjectforitem_define(digisig_entity_number)

	if len(part_dic) == 1:

		for key, part_info in part_dic.items():
			template = loader.get_template('digisig/item.html')
			context = {
				'pagetitle': part_info['pagetitle'],
				'part_object': part_info,
				'mapdic': part_info['mapdic'],
				}
	else:
		template = loader.get_template('digisig/item.html')
		for key, part_info in part_dic.items():
			template = loader.get_template('digisig/item.html')
			context = {
				'pagetitle': part_info['pagetitle'],
				'part_object': part_info,
				'mapdic': part_info['mapdic'],
				}

	return HttpResponse(template.render(context, request))

############################ Manifestation #####################

async def manifestation_page(request, digisig_entity_number): 
	####manifestation_dic = await manifestation_createdic(manifestation_object)
	pagetitle = 'title'

	# manifestation_object = await manifestationobject_define(digisig_entity_number)

	manifestation_set = await manifestation_searchsetgenerate(digisig_entity_number, searchtype="manifestation")
	representation_set = await representationsetgenerate2(manifestation_set, primacy=True)
	manifestation_display_dic, listofseals, listofevents = await manifestation_displaysetgenerate(manifestation_set, representation_set)
	description_set = await sealdescription_displaysetgenerate2(listofseals)

	manifestation_info = await seal_displaysetgenerate(manifestation_display_dic, description_set, digisig_entity_number)

	outname, actor_id = await actorfinder(manifestation_set)

	# actornamegenerator(individual_object)

	first_item = next(iter(manifestation_display_dic.items()))
	first_key, manifestation_dic = first_item

	# manifestation_object = get_object_or_404(Manifestation, id_manifestation=digisig_entity_number)
	# face_object = manifestation_object.fk_face
	# seal_object = face_object.fk_seal
	# sealdescription_set = Sealdescription.objects.filter(fk_seal=seal_object)

	# location_reference_object = Locationreference.objects.get(fk_event=manifestation_object.fk_support.fk_part.fk_event, fk_locationstatus=1)
	
	# try:
	# 	region = location_reference_object.fk_locationname.fk_location.fk_region.region_label
	# except:
	# 	region = "Undetermined"
		
	# try:
	# 	representation_object = Representation.objects.get(fk_digisig=digisig_entity_number, primacy=1)
	# except:
	# 	#add graphic of generic seal 
	# 	representation_object = Representation.objects.get(id_representation=12132404)

	# externallink_object = Digisiglinkview.objects.filter(fk_digisigentity=digisig_entity_number)

	# individualtarget = seal_object.fk_individual_realizer
	# outname = namecompiler(individualtarget)

	template = loader.get_template('digisig/manifestation.html')
	context = {
			#'authenticationstatus': authenticationstatus,
			'pagetitle': pagetitle,
			'manifestation_info': manifestation_info,
			'manifestation_dic': manifestation_dic,
			# 'manifestation_object': manifestation_object,
			# 'representation_object': representation_object,
			# 'region': region,
			# 'seal_object': seal_object,
			# 'individualtarget': individualtarget.id_individual,
			# 'sealdescription_object': sealdescription_set,
			# 'externallink_object': externallink_object,
			'outname': outname,
			# 'rdftext': rdftext,
	}

	return HttpResponse(template.render(context, request))



############################## Part #############################



############################## Place #############################

async def place_page(request, digisig_entity_number):

	template = loader.get_template('digisig/place.html')  
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
	manifestation_display_dic, description_set, listofseals, listofevents = await manifestation_displaysetgenerate(manifestation_set, representation_set)
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

	return HttpResponse(template.render(context, request))


############################## Representation #############################


async def representation_page(request, digisig_entity_number):

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

	return HttpResponse(template.render(context, request))


############################## Seal #############################


async def seal_page(request, digisig_entity_number):
	pagetitle = 'title'
	template = loader.get_template('digisig/seal.html')

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

	return HttpResponse(template.render(context, request))


############################## Seal description #############################


async def sealdescription_page(request, digisig_entity_number):

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

	return HttpResponse(template.render(context, request))


############################## Support #############################


################################ TERM ######################################


async def term_page(request, digisig_entity_number):
	pagetitle = 'Term'

	term_object, statement_object = await entity_term(digisig_entity_number)

	#print (statement_object)

	template = loader.get_template('digisig/term.html')
	context = {
		'pagetitle': pagetitle,
		'term_object': term_object,
		'statement_object': statement_object,
		}

	return HttpResponse(template.render(context, request))



