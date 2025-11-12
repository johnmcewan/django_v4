from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from datetime import datetime
from time import time
# from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.db.models import Q, F
from django.db.models import Count, Sum, Max, Min
# from django.db.models.functions import Concat
# from django.db.models import CharField
from django.core import serializers
from django.db.models import IntegerField, Value
from django.db.models.functions import Concat

from .models import *
from .forms import * 
# from utils.mltools import * 
from utils.generaltools import *
from utils.viewtools import *

import json
import os
import pickle

from asgiref.sync import sync_to_async

# Create your views here.
def index(request):

	pagetitle = 'title'
	template = loader.get_template('witness/index.html')

	#londoners_total = Individual.objects.filter(fk_individual_event__gt=1).distinct('id_individual').count()

	context = {
		'pagetitle': pagetitle,
		#'londoners_total': londoners_total,
		}

	return HttpResponse(template.render(context, request))

def explore(request, exploretype):

	print (request)
	targetphrase = "parish_page"

	return redirect(targetphrase, 50013947)


def information(request, informationtype):

	print (request)
	targetphrase = "parish_page"

	return redirect(targetphrase, 50013947)

def discover(request, discovertype):

	print (request)
	targetphrase = "parish_page"

	return redirect(targetphrase, 50013947)

def analyze(request, analyzetype):

	print (request)
	targetphrase = "parish_page"

	return redirect(targetphrase, 50013947)

def about(request):

	print (request)
	targetphrase = "parish_page"

	return redirect(targetphrase, 50013947)

def exhibit(request):

	print (request)
	targetphrase = "parish_page"

	return redirect(targetphrase, 50013947)


async def search(request, searchtype):

### Parish

	if searchtype == "parish":

		londonparishes_options_choices = await londonparishes_options()

		form = LondonparishForm(request.POST or None)
		form.fields['londonparish'].choices = londonparishes_options_choices

		#adjust values if form submitted
		if request.method == 'POST':
			
			if form.is_valid():
				londonparish = form.cleaned_data['londonparish']
				#make sure values are not empty then try and convert to ints
				if len(londonparish) > 0:
					qlondonparish = int(londonparish)
					targetphrase = "parish_page"
					return redirect(targetphrase, qlondonparish)

		else:
			pass

		template = loader.get_template('witness/search_parish.html')
		context = {
			'form': form,
			}

		return HttpResponse(template.render(context, request))

### Actor (Person)

	if searchtype == "person":

		pagetitle = 'title'

		londonevents = await personsearch_events()

		form = PeopleForm(request.POST or None)

		if request.method == "POST":
			#form = PeopleForm(request.POST)
			if form.is_valid():
				qpagination = form.cleaned_data['pagination']
				qname = form.cleaned_data['name']
				qnamelen = len(qname)
				form = PeopleForm(request.POST)

		else:
			qnamelen = 0
			qname = ""
			qpagination = 1

		individual_object = await individualsearch()

		individual_object = await personsearch_people(qnamelen, qname, qpagination, londonevents, individual_object) 

		individual_object, totalrows, totaldisplay = await defaultpagination(individual_object, qpagination) 

		pagecountercurrent = qpagination
		pagecounternext = qpagination + 1
		pagecounternextnext = qpagination +2  

		individual_set = await personsearch_prepareset(individual_object)

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

		template = loader.get_template('witness/search_person.html')
		return HttpResponse(template.render(context, request))

async def person_page(request, witness_entity_number):

	template = loader.get_template('witness/person.html')

	individual_object = await individualsearch2(witness_entity_number)
	pagetitle= namecompiler(individual_object)

	# list of relationships for each actor
	# relationship_dic, relationshipnumber = await relationship_dataset(witness_entity_number)

	mapparishes, ref_list = await mapparishesdata2(witness_entity_number)

	# print (ref_list)

	# list of references to the actor
	reference_list = await referenceset_references5(witness_entity_number, ref_list)

	context = {
		'pagetitle': pagetitle,
		'individual_object': individual_object,
		#'relationship_dic': relationship_dic,
		#'relationshipnumber' : relationshipnumber,
		'reference_list' : reference_list,
		'parishes_dict': mapparishes,
		#'reference_set': reference_set,
		}

	template = loader.get_template('witness/person.html')
	return HttpResponse(template.render(context, request))

async def person_ajax(request, witness_entity_number):

	#list of references to the actor
	reference_list = await referenceset_references3(witness_entity_number)

	datareferences = json.dumps(reference_list)

	return (JsonResponse(datareferences, safe=False))

async def personrelationships_ajax(request, witness_entity_number):

	# list of relationships for each actor
	relationship_dic, relationshipnumber = await relationship_dataset(witness_entity_number)

	datareferences = json.dumps(relationship_dic)

	return (JsonResponse(datareferences, safe=False))



async def parishpersonajax(request, witness_entity_number):

	individual_object = await parish_fetch(witness_entity_number)
	individual_list = await parish_individuallistfetch(individual_object)

	datareferences = json.dumps(individual_list)

	return(JsonResponse(datareferences, safe=False)) 


def parishnetwork_page(request, witness_entity_number):

	#default
	qlondonparish= 50013947

	qlondonparish = witness_entity_number

	parishevents = Location.objects.filter(id_location=qlondonparish).values('locationname__locationreference__fk_event')

	exclusionset = Digisigrelationshipview.objects.filter(Q(person2=10140149)|Q(person2=10140449)|Q(person2=10139569)).values('fk_individual')

	reference_set = Referenceindividual.objects.filter(
		fk_referencerole=1).exclude(
		fk_individual=10000019).exclude(
		fk_individual__in=exclusionset).filter(
		fk_event__in=parishevents)

	reference_set = referencecollectindividual(reference_set)

	reference_set = reference_set.values(
		'fk_individual', 
		'fk_event', 
		'fk_individual__fullname_original',
		'fk_individual__fk_descriptor_name__descriptor_modern',
		'fk_individual__fk_descriptor_prefix1__prefix_english',
		'fk_individual__fk_descriptor_descriptor1__descriptor_modern',
		'fk_individual__fk_descriptor_prefix2__prefix_english',
		'fk_individual__fk_descriptor_descriptor2__descriptor_modern',
		'fk_individual__fk_descriptor_prefix3__prefix_english').order_by('pk_referenceindividual')

	linkslist, nodelist = networkgenerator(reference_set)

	template = loader.get_template('witness/parish_graph.html')
	context = {
		'nodelist': nodelist,
		'linkslist': linkslist,
		}

	return HttpResponse(template.render(context, request))


###### Entities


def entity(request, witness_entity_number):

	#create flag that this is a view operation....
	operation = 1
	application = 2

	#item = 0, seal=1, manifestation=2, sealdescription=3, etc...
	targetphrase = redirectgenerator(witness_entity_number, operation, application)

	return redirect(targetphrase)



async def parish_page(request, witness_entity_number):
 
	parish = await parishvalue(witness_entity_number)

	individual_object = await individualsearch()
	individual_object = await parish_fetch(individual_object, witness_entity_number)
	individual_list = await parish_individuallistfetch(individual_object)
	#case_value, totalcases = await parishcases_fetch(individual_object)

	mapparishes = await parish_map(witness_entity_number, parish)

	template = loader.get_template('witness/parish.html')
	context = {
		'parish': parish,
		'individual_list': individual_list,
		'parishes_dict': mapparishes,
		}

	return HttpResponse(template.render(context, request))

###revise this code
async def part_page(request, witness_entity_number):

	externallinkset = await externallinkgenerator(witness_entity_number)

	place_object, pagetitle, item_object, event_dic = await place_object_creator(witness_entity_number)

	mapdic = await mapgenerator(place_object, 0)

	#for part images (code to show images not implemented yet)
	representationset = {}

	######REVISE THIS CODE AND DO NOT DELETE
	# try: 
	# 	representation_part = Representation.objects.filter(fk_digisig=part_object.id_part).select_related('fk_connection')

	# 	for t in representation_part:
	# 		#Holder for representation info
	# 		representation_dic = {}

	# 		#for all images
	# 		connection = t.fk_connection
	# 		representation_dic["connection"] = t.fk_connection
	# 		representation_dic["connection_thumb"] = t.fk_connection.thumb
	# 		representation_dic["connection_medium"] = t.fk_connection.medium
	# 		representation_dic["representation_filename"] = t.representation_filename_hash
	# 		representation_dic["representation_thumbnail"] = t.representation_thumbnail_hash
	# 		representation_dic["id_representation"] = t.id_representation 
	# 		representation_dic["fk_digisig"] = t.fk_digisig
	# 		representation_dic["repository_fulltitle"] = item_object.fk_repository.repository_fulltitle
	# 		representation_dic["shelfmark"] = item_object.shelfmark
	# 		representation_dic["fk_item"] = item_object.id_item
	# 		representationset[t.id_representation] = representation_dic

	# except:
	# 	print ('no image of document available')

	template = loader.get_template('witness/item.html')
	context = {
		'pagetitle': pagetitle,
		'item_object': item_object,
		'event_dic': event_dic,
		'mapdic': mapdic,
		'representationset': representationset,
		'externallink_object': externallinkset,
		}

	return HttpResponse(template.render(context, request))


async def item_page(request, witness_entity_number):

	part_dic = await partobjectforitem_define(witness_entity_number)

	if len(part_dic) == 1:

		for key, part_info in part_dic.items():
			template = loader.get_template('witness/item.html')
			context = {
				'pagetitle': part_info['pagetitle'],
				'part_object': part_info,
				'mapdic': part_info['mapdic'],
				}
	else:
		template = loader.get_template('witness/item.html')
		for key, part_info in part_dic.items():
			template = loader.get_template('witness/item.html')
			context = {
				'pagetitle': part_info['pagetitle'],
				'part_object': part_info,
				'mapdic': part_info['mapdic'],
				}

	return HttpResponse(template.render(context, request))


def seal_page(request, witness_entity_number):

	targetphrase = "parish_page"

	return redirect(targetphrase, 50013947)

def personnetwork_page(request, witness_entity_number):

	#default
	qpersonnetwork = witness_entity_number
 
	reference_set1 = Referenceindividual.objects.filter(fk_individual=qpersonnetwork).distinct('fk_event')

	witnessevents = Referenceindividual.objects.filter(
		fk_referencerole=1).filter(
		fk_individual=qpersonnetwork).values('fk_event')

	reference_set = Referenceindividual.objects.filter(
		fk_referencerole=1).exclude(fk_individual=10000019).filter(
		fk_event__in=witnessevents)


### extra view

def searchletterbook(request):

	pagetitle = 'title'

	form = DescriptorForm(request.POST or None)

	if request.method == "POST":
		if form.is_valid():
			qpagination = form.cleaned_data['pagination']
			qname = form.cleaned_data['name']
			qnamelen = len(qname)
			form = DescriptorForm(request.POST)

	else:
		qnamelen = 0
		qname = ""
		qpagination = 1


	individual_object = IndividualMontreal.objects.all().order_by('namephrase')

	if qnamelen > 0:
		individual_object = individual_object.filter(
			Q(
				namephrase__icontains=qname) | Q(
				fk_descriptor_firstname__descriptor_original__icontains=qname)| Q(
				fk_descriptor_secondname__descriptor_original__icontains=qname)| Q(
				fk_descriptor_thirdname__descriptor_original__icontains=qname)) 

	individual_object = Paginator(individual_object, 10).page(qpagination)
	totalrows = individual_object.paginator.count
	totaldisplay = str(individual_object.start_index()) + "-" + str(individual_object.end_index())

	pagecountercurrent = qpagination
	pagecounternext = qpagination + 1
	pagecounternextnext = qpagination +2  

	individual_set = {}

	for i in individual_object:
		individual_info = {}
		individual_info['actor_name'] = i.namephrase
		individual_info['id_indpropose'] = i.id_indpropose
		individual_set[i.id_indpropose] = individual_info


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

	template = loader.get_template('witness/search_letterbook.html')
	return HttpResponse(template.render(context, request))


def personletterbooknetwork_page(request, page_number):

	# default
	qpersonnetwork = int(page_number) # This is the id_report of the person being centered on.

	# Get letterbook entry IDs (not objects) where person appears
	reference_set1 = LetterBooksNerData.objects.filter(
		fk_individual_id=qpersonnetwork
	).values_list('fk_letterbookentry', flat=True).distinct()

	# Filtering by a list of integer IDs
	reference_set = LetterBooksNerData.objects.filter(
		fk_letterbookentry__in=reference_set1
	).filter(
	fk_individual_id__fk_descriptor_secondname__isnull=False).values(
		'fk_letterbookentry',
		'fk_individual_id', 
		'fk_individual_id__namephrase', 
		'fk_individual_id__eventcount'
	)

	linkslist = []
	nodelist = []

	# Maps event ID to a SET of canonical Report IDs (fk_report) in that event
	reference_dic = {} 
	# Caches person data (namephrase, eventcount) keyed by Report ID (fk_report)
	person_data_cache = {} 
	
	# --- Step 1: Process Events, Cache Report Data, and Map Co-occurrences by Report ID ---
	for r in reference_set:

		eventid = r['fk_letterbookentry']
		report_id = r['fk_individual_id']
		
		# 1a. Build the event dictionary using the CANONICAL REPORT ID
		if eventid in reference_dic:
			# Use add() on a set to prevent duplicates if a person has multiple distinct_names in the same event
			reference_dic[eventid].add(report_id) 
		else:
			reference_dic[eventid] = {report_id}

		# 1b. Cache the data from the report table, keyed by the canonical Report ID (fk_report)
		if report_id not in person_data_cache:
			person_data_cache[report_id] = {
				'namephrase': r['fk_individual_id__namephrase'] or str(report_id),
				'eventcount': r['fk_individual_id__eventcount'] or 1
			}


	# --- Step 2: Build the Final Nodelist ---
	
	# Iterate through the cached report IDs to build the final nodelist once.
	for report_id, data in person_data_cache.items():
			
		node_id = report_id 
		label = data['namephrase']
		value = data['eventcount']

		# Define color logic based on the *canonical* person's total eventcount
		colour = '#806c93' # Default
		if node_id == qpersonnetwork:
			 colour = '#259E6A' # Highlight the central person (new addition)
		elif value > 15: colour = '#ff0000'
		elif value > 10: colour = '#d95326'
		elif value > 7: colour = '#c68039'
		elif value > 5: colour = '#c6a339'
		elif value > 3: colour = '#409fbf'
		elif value > 1: colour = '#4d4db3'


		# Build the node dictionary
		nodelist.append({
			'id': node_id, 
			'name': label, 
			'val': value, 
			'color': colour
		})
		

	# --- Step 3: Generate Links (Co-occurrence) ---
	
	# Iterate through events. reference_dic already contains canonical Report IDs.
	for canonical_report_ids_set in reference_dic.values():
		
		# Convert the set of canonical Report IDs to a list for indexed iteration
		canonical_report_ids = list(canonical_report_ids_set)
		numberofpeople = len(canonical_report_ids)

		# Skip events involving only one person
		if numberofpeople < 2:
			continue

		# Create links for every unique pair of canonical Report IDs in this event
		for x in range(numberofpeople):
			for y in range(x + 1, numberofpeople):
				person1 = canonical_report_ids[x]
				person2 = canonical_report_ids[y]
				
				# Links are already between canonical Report IDs
				linkslist.append({'source': person1, 'target': person2})


	print(f"Central person ID: {qpersonnetwork}")
	print(f"Central person in cache: {qpersonnetwork in person_data_cache}")
	print(f"Total events found: {len(reference_dic)}")
	print(f"Total unique people: {len(person_data_cache)}")


	# --- Step 4: Render ---

	template = loader.get_template('witness/person_graph_letterbook.html')
	context = {
		'nodelist': nodelist,
		'linkslist': linkslist,
		# Add the central person's ID (qpersonnetwork) to context if needed for highlighting
		'central_person_id': qpersonnetwork
	}

	return HttpResponse(template.render(context, request))