from digisig.models import * 
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django.core.paginator import Paginator
from django.core import serializers
from django.db.models import Count, Sum, Max, Min
from django.db.models import Q, F

import statistics
import math
import os
import pandas as pd 
import json

from django.conf import settings

from time import time
from datetime import datetime
from asgiref.sync import sync_to_async

from django.urls import reverse


@sync_to_async
def index_info():

	manifestation_total = Manifestation.objects.count()
	seal_total = Seal.objects.count()
	item_total = Support.objects.distinct('fk_part__fk_item').count()
	# item_total = 53408
	catalogue_total = Sealdescription.objects.count()

	return(manifestation_total, seal_total, item_total, catalogue_total)

@sync_to_async
def registervisit(request, digisig_entity_number):

	## record visit if it is not the admin....
	if request.user.id > 1:
		 Digisigpagevisit.objects.create(
			pagevisit_user = request.user.id,
			pagevisit_entitynumber = digisig_entity_number,
			pagevisit_timestamp = datetime.now(),
			pagevisit_site = 1
			)
	
	return()


#### exhibitions
@sync_to_async
def exhibitgenerate():

	# create the set of RTIs
	representation_set = {}

	# select all representations that are RTIs....
	rti_set = Representation.objects.filter(fk_representation_type=2).values('fk_digisig', 'id_representation')

	rti_set_filter =rti_set.values('fk_digisig')

	rti_set_targets = rti_set.values_list('fk_digisig', 'id_representation', named=True)

	representation_objects = Representation.objects.filter(
		fk_digisig__in=rti_set_filter, primacy=1).select_related(
		'fk_connection').values('fk_connection__thumb', 'representation_thumbnail_hash', 'fk_connection__medium', 'representation_filename_hash', 'fk_digisig')

	for r in representation_objects:
		representation_dic = r

		for l in rti_set_targets:
			if l.fk_digisig == r['fk_digisig']:
				r['id_num'] = l.id_representation
				representation_set[l.id_representation] = representation_dic
				break

	return (representation_set)

### information
@sync_to_async
def information_changes():
	
	return list(Changes.objects.all().order_by('-change_date'))

@sync_to_async
def information_help():
	class_object = list(Terminology.objects.filter(term_deprecated=0).order_by('term_name'))
	shape_object = list(Terminology.objects.filter(digisig_column='shape').order_by('term_name'))
	nature_object = list(Terminology.objects.filter(digisig_column='nature').order_by('term_name'))

	return(class_object, shape_object, nature_object)

@sync_to_async
def information_ML(qcollection, qclassification):

	data1 = []
	data2 = []
	labels = []
	event_seal = []

	seal_set = Seal.objects.filter(fk_sealsealdescription__fk_collection=qcollection).filter(fk_seal_face__fk_class=qclassification)

	if len(seal_set) > 0:
		for s in seal_set:

			### 1/7/2024 -- attempting to put human readable labels -- not working yet -- javascript fails on string with quotes
			sealdescription_entry = Sealdescription.objects.get(Q(fk_collection=qcollection) & Q(fk_seal=s.id_seal))

			event_seal = Event.objects.get(part__fk_part__fk_support__fk_face__fk_seal=s.id_seal)

			try:
				start = event_seal.repository_startdate
				end = event_seal.repository_enddate
				starty = start.year
				endy = end.year

				try:
					start2 = event_seal.startdate
					end2 = event_seal.enddate

					if start2.year > 0 :
						data1.append([starty, endy])
						# data2.append(liney)
						data2.append([start2.year, end2.year])
						#labels.append(event_seal.pk_event)
						labels.append(s.id_seal)

				except:

					print ("fail2", event_seal)

				if starty > 1500:
					print ("fail", event_seal, start, end, starty, endy, start2, end2)

			except:

				print ("fail1", event_seal)

	return (event_seal, labels, data1, data2)


@sync_to_async
def information_terminology():
	
	termexamples_object = Terminologyexample.objects.filter(
		fk_terminology__term_deprecated=0, 
		fk_terminology__level__isnull=False).select_related(
		'fk_representation__fk_connection',
		'fk_terminology').values(
		'fk_terminology__term_sortorder',
		'fk_terminology__id_term',
		'fk_terminology__term_number',
		'fk_terminology__level',
		'fk_terminology__level1',
		'fk_terminology__level2',
		'fk_terminology__level3',
		'fk_terminology__level4',
		'fk_terminology__level5',
		'fk_terminology__level6',
		'fk_terminology__level7',
		'fk_terminology__level8',
		'fk_terminology__level9',
		'fk_terminology__level10',
		'id_terminologyexample',
		'fk_terminology',
		'fk_terminology__term_definition',
		'fk_terminology__term_name',
		'fk_terminology__digisig_column',
		'fk_representation',
		'fk_representation__fk_connection__thumb', 
		'fk_representation__fk_connection__medium', 
		'fk_representation__representation_thumbnail_hash', 
		'fk_representation__representation_filename_hash').order_by('-fk_terminology__level')

	example_set= {}

	for ex in termexamples_object:
		#print (ex['fk_terminology__level'], ex['fk_terminology__term_name'], ex['fk_terminology__term_number'])
		#term_name = ex['fk_terminology__term_name']
		term_number = ex['fk_terminology__term_number']

		# Use setdefault to add the terminology entry if it doesn't exist
		example_set.setdefault(ex['fk_terminology__term_number'], {
			'examples': {},
			'children': {},
			'term_name': ex['fk_terminology__term_name'],
			'id_term': ex['fk_terminology'],
			'term_number':ex['fk_terminology__term_number'],
			'term_group': ex['fk_terminology__digisig_column'],
			'tooltip': ex['fk_terminology__term_definition'],
			'level': ex['fk_terminology__level'],
			'level1': ex['fk_terminology__level1'],
			'level2': ex['fk_terminology__level2'],
			'level3': ex['fk_terminology__level3'],
			'level4': ex['fk_terminology__level4'],
			'level5': ex['fk_terminology__level5'],
			'level6': ex['fk_terminology__level6'],
			'level7': ex['fk_terminology__level7'],
			'level8': ex['fk_terminology__level8'],
			'level9': ex['fk_terminology__level9'],
			'level10': ex['fk_terminology__level10'],
		})

		representation_id = ex['fk_representation']

		# Create the term representation dictionary
		term_representation = {
			representation_id: {  
				"id": representation_id,
				"connection_thumb": ex['fk_representation__fk_connection__thumb'],
				"connection_medium": ex['fk_representation__fk_connection__medium'],
				"address_thumb": ex['fk_representation__representation_thumbnail_hash'],
				"address_medium": ex['fk_representation__representation_filename_hash']
			}
		}

		# Update the examples dictionary for the current term if representation ID is not a key
		if representation_id not in example_set[term_number]['examples']:
			example_set[term_number]['examples'].update(term_representation)

	topset = {}

	for key, value in example_set.items():
		if value['level'] > 1:
			parentlevel = value['level'] - 1
			parent_level_base = "level" + str((value['level'])-1)

			# Construct the key to access the parent term correctly
			parent_level_value = value[parent_level_base]

			# Ensure the parent exists in example_set before trying to add children
			if parent_level_value in example_set:
				example_set[parent_level_value]['children'][value['term_name']] = value
			else:
				print(f"Warning: Parent level '{parent_level_value}' not found for term '{value['term_name']}'")

		elif value['level'] == 1:
			topset[value['term_name']] = value

		else:
			print("error", value)


	generalset = {}
	natureset = {}
	shapeset = {}

	otherterm_object = Terminology.objects.order_by(
		'term_sortorder').values(
		'id_term',
		'term_definition',
		'term_name',
		'digisig_column')

	for o in otherterm_object:
		if o['digisig_column'] == "shape": shapeset[o['id_term']] = o
		if o['digisig_column'] == "general": generalset[o['id_term']] = o
		if o['digisig_column'] == "nature": natureset[o['id_term']] = o 

	#slsls

	return (generalset, natureset, topset, shapeset)  

@sync_to_async
def entity_term(digisig_entity_number):

	statement_set = Skosdata.objects.filter(
		skos_data_subject=digisig_entity_number).values(
		'id_skos_data',
		'skos_data_subject__id_term',
		'skos_data_subject__term_name',
		'skos_data_subject__term_definition',
		'skos_data_predicate__skos_vocabulary_uri', #this is the human label
		'skos_data_predicate__skos_vocabulary_definition',
		'skos_data_object__id_term',
		'skos_data_object__term_name',
		)

	term_object = {}
	if statement_set:
		i = statement_set[0]
		term_object = {
		'id_term': i['skos_data_subject__id_term'], 
		'term_name': i['skos_data_subject__term_name'],
		'term_definition': i['skos_data_subject__term_definition'],
		}

	statement_object = {}
	for s in statement_set:
		statement_object[s['id_skos_data']] = {
		'id_skos_data': s['id_skos_data'],
		'subject__term_name': s['skos_data_subject__term_name'],
		'term_name': s['skos_data_subject__term_name'],
		'predicate__vocabulary_uri': s['skos_data_predicate__skos_vocabulary_uri'], #this is the human label
		'skos_data_object': s['skos_data_object__id_term'],
		'object__term_name': s['skos_data_object__term_name'],
		}

	return (term_object, statement_object)

# @sync_to_async
# def information_terminology():

# 	# code for assembling the classification data
# 	term_object = Terminology.objects.filter(
# 		term_deprecated=0, level__isnull=False).order_by('term_sortorder')

# 	termobject = []
# 	toplevel = term_object.filter(level=1)

# 	fifthset = {}
# 	topset = {}
# 	level5 = {}
# 	level4= {}
# 	level3= {}
# 	level2= {}
# 	level1= {}

# 	#images for display
# 	exampleset1 = {}
# 	exampleset2 = {}
# 	exampleset3 = {}
# 	exampleset4 = {}
# 	exampleset5 = {}

# 	for t in toplevel:
# 		target1 = t.level1
# 		name1 = t.term_name
# 		idterm1 = t.id_term
# 		tooltip1 = t.term_definition
# 		exampleset1= examplefinder(idterm1)

# 		secondlevel = term_object.filter(level=2, level1=target1)
# 		for s in secondlevel:
# 			target2 = s.level2
# 			name2 = s.term_name
# 			idterm2 = s.id_term
# 			tooltip2 = s.term_definition
# 			exampleset2 = examplefinder(idterm2)

# 			thirdlevel = term_object.filter(level=3, level2=target2)
# 			for th in thirdlevel:
# 				target3 = th.level3
# 				name3 = th.term_name
# 				idterm3 = th.id_term
# 				tooltip3 = th.term_definition
# 				exampleset3 = examplefinder(idterm3)

# 				fourthlevel = term_object.filter(level=4, level3=target3)
# 				for fo in fourthlevel:
# 					target4 = fo.level4
# 					name4 = fo.term_name
# 					idterm4 = fo.id_term
# 					tooltip4 = fo.term_definition
# 					exampleset4 = examplefinder(idterm4)

# 					fifthlevel = term_object.filter(level=5, level4=target4)
# 					for fi in fifthlevel:
# 						name5 = fi.term_name
# 						idterm5 = fi.id_term
# 						tooltip5 = fi.term_definition
# 						exampleset5 = examplefinder(idterm5)
# 						fifthset[name5] = {"id_term": idterm5, "examples": exampleset5, "tooltip": tooltip5}
# 						exampleset5 = {}
	
# 					level4[name4] = {"id_term": idterm4, "children": fifthset, "examples": exampleset4, "tooltip": tooltip4}
# 					fifthset = {}
# 					exampleset4 = {}
	
# 				level3[name3] = {"id_term": idterm3, "children": level4, "examples": exampleset3, "tooltip": tooltip3}
# 				level4= {}
# 				exampleset3 = {}

# 			level2[name2] = {"id_term": idterm2, "children":level3, "examples": exampleset2, "tooltip": tooltip2}
# 			level3 = {}
# 			exampleset2 = {}

# 		topset[name1] = {"id_term": idterm1, "children": level2, "examples": exampleset1, "tooltip": tooltip1}
# 		level2 = {}


# 	## code for assembling the shape data
# 	shapeterms = Terminology.objects.filter(digisig_column="shape").order_by("term_name")

# 	shapeset = {}
# 	for s in shapeterms:
# 		nameshape = s.term_name
# 		shapeterm = s.id_term
# 		tooltip = s.term_definition
# 		examplesetshape = examplefinder(shapeterm)
# 		shapeset[nameshape] = {"id_term": shapeterm, "examples":examplesetshape, "tooltip": tooltip}

# 	## code for assembling the nature data
# 	natureterms = Terminology.objects.filter(digisig_column="nature").order_by("term_name")

# 	natureset = {}
# 	for n in natureterms:
# 		namenature = n.term_name
# 		natureterm = n.id_term
# 		tooltip = n.term_definition
# 		examplesetnature = examplefinder(natureterm)
# 		natureset[namenature] = {"id_term": natureterm, "examples":examplesetnature, "tooltip": tooltip}


# 	## code for assembling the general data
# 	generalterms = Terminology.objects.filter(digisig_column="general").order_by("term_name")

# 	generalset = {}
# 	for g in generalterms:
# 		namegeneral = g.term_name
# 		generalterm = g.id_term
# 		tooltip = g.term_definition
# 		examplesetgeneral = examplefinder(generalterm)
# 		generalset[namegeneral] = {"id_term": generalterm, "examples":examplesetgeneral, "tooltip": tooltip}

# 	print(topset)

# 	return (generalset, natureset, topset, shapeset)       

#gets example for classification display
def examplefinder(idterm):
	examplesetouta = ""
	examplesetoutb = ""
	examplesetout = {}

	example1 = Terminologyexample.objects.filter(fk_terminology=idterm)
	for e in example1:
		representationobject= e.fk_representation
		key = representationobject.id_representation
		root = representationobject.fk_connection

		examplesetouta=root.thumb + representationobject.representation_thumbnail_hash
		examplesetoutb=root.medium + representationobject.representation_filename_hash

		examplesetout[key] = {"small": examplesetouta, "medium": examplesetoutb}

	return (examplesetout)

### analysis
# @sync_to_async
# def analyzetime_manifestations(qcollection, qtimechoice=None, qsealtypechoice=None):
#   #map points
#   totalcases = 0

#   #the queries deal with variations in the data differently -- undetermined locations, or ones to regions, 
#   #won't show on all maps
#   #to post correct totals, need to run query separately (which is inefficient)

#   if (qcollection == 30000287):
#       manifestationset = Manifestation.objects.all()
#   else:
#       manifestationset = Manifestation.objects.filter(fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection)

#   totalcollectioncases = manifestationset.count()

#   if (qtimechoice > 0):
#       manifestationset = manifestationset.filter(fk_face__fk_seal__fk_timegroupc=qtimechoice)

#   totalcasesfromperiod = manifestationset.count()

#   if (qsealtypechoice > 0):
#       manifestationset = manifestationset.filter(fk_face__fk_seal__fk_sealtype=qsealtypechoice)

#   totalcases = manifestationset.count()

#   return(totalcases, totalcasesfromperiod, totalcollectioncases)

# from django.db.models import Count
# from asgiref.sync import sync_to_async

@sync_to_async
def analyzetime_manifestations(qcollection, qtimechoice=None, qsealtypechoice=None):
	"""
	Analyzes manifestation data based on collection, time period, and seal type.

	Args:
		qcollection: The collection ID to filter by.
		qtimechoice: Optional time group code to filter by (defaults to None).
		qsealtypechoice: Optional seal type to filter by (defaults to None).

	Returns:
		A tuple containing:
			- totalcases: The total count of manifestations after all filters.
			- totalcasesfromperiod: The total count of manifestations filtered by time period (if provided).
			- totalcollectioncases: The total count of manifestations for the given collection.
	"""
	totalcases = 0
	totalcasesfromperiod = 0

	if qcollection == 30000287:
		manifestationset = Manifestation.objects.all()
	else:
		manifestationset = Manifestation.objects.filter(
			fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection
		)

	totalcollectioncases = manifestationset.count()

	# Filter by time choice only if it's not None and greater than 0
	if qtimechoice is not None and qtimechoice > 0:
		manifestationset = manifestationset.filter(fk_face__fk_seal__fk_timegroupc=qtimechoice)
		totalcasesfromperiod = manifestationset.count()  # Calculate after time filter
	else:
		totalcasesfromperiod = totalcollectioncases # If no time filter, it's the same as collection total

	# Filter by seal type choice only if it's not None and greater than 0
	if qsealtypechoice is not None and qsealtypechoice > 0:
		manifestationset = manifestationset.filter(fk_face__fk_seal__fk_sealtype=qsealtypechoice)

	totalcases = manifestationset.count()

	return totalcases, totalcasesfromperiod, totalcollectioncases


### discovery
@sync_to_async
def collectionform_options(form):
	#Form for collections, map and time analysis

	collections_options = [('30000287', 'All Collections')]
	graphchoices = [('1', 'Seal Descriptions'), ('2', 'Seal Impressions, Matrices and Casts')]
	mapchoices = [('1', 'Places'), ('2', 'Counties'), ('3', 'Regions')]
	sealtype_options = [('', 'None')]
	period_options = [('', 'None')]
	timegroup_options2 = [('', 'None')]

	for e in Collection.objects.order_by('collection_shorttitle'):
		collections_options.append((e.id_collection, e.collection_shorttitle))

	for e in Sealtype.objects.order_by('sealtype_name'):
		sealtype_options.append((e.id_sealtype, e.sealtype_name))

	for e in TimegroupC.objects.order_by('pk_timegroup_c'):
		timegroup_options2.append((e.pk_timegroup_c, e.timegroup_c_range))

	form.fields['collection'].choices = collections_options
	form.fields['mapchoice'].choices = mapchoices
	form.fields['timechoice'].choices = timegroup_options2
	form.fields['sealtypechoice'].choices = sealtype_options

	# collection = forms.ChoiceField(choices=collections_options, required=False)
	# #graphchoice = forms.ChoiceField(choices=graphchoices, required=False)
	# mapchoice = forms.ChoiceField(choices=mapchoices, required=False)
	# timechoice = forms.ChoiceField(choices=timegroup_options2, required=False)
	# # classname = forms.ChoiceField(label='Digisig Class', choices=classname_options, required=False)
	# sealtypechoice = forms.ChoiceField(choices=sealtype_options, required=False)

	return(form)

#####collection options

@sync_to_async
def digisigcollection_options(form):

	collection_options = [(30000287, 'All Collections')]

	for e in Collection.objects.order_by('collection_shorttitle').annotate(numdescriptions=Count('sealdescription')):

		if (e.numdescriptions > 0):
			collection_options.append((e.id_collection, e.collection_shorttitle))

	form.fields['collection'].choices = collection_options

	return(form)

#####parish search

#forms support
@sync_to_async
def londonparishes_options():

	londonparishes_options = []

	for e in Location.objects.filter(fk_locationtype=1, fk_region=87).order_by('location'):
		londonparishes_options.append((e.id_location, e.location))

	return(londonparishes_options)

#####person search

@sync_to_async
def londonpeople_options_choices():

	name = forms.CharField(label='id_name', max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Example: John'}))

@sync_to_async
def personsearch_events():

	londonevents = Location.objects.filter(fk_region=87).values('locationname__locationreference__fk_event')

	return (londonevents)

@sync_to_async
def personsearch_people(qnamelen, qname, qpagination, londonevents, individual_object):
	
	# individual_set1 = individual_object.filter(
	#   fk_individual_event__in=londonevents)

	individual_object = individual_object.filter(
		fk_individual_event__in=londonevents).distinct('id_individual').order_by('id_individual')

	if qnamelen > 0:
		individual_object = individual_object.filter(
			Q(
				fullname_modern__icontains=qname) | Q(
				fullname_original__icontains=qname) | Q(
				fk_descriptor_title__descriptor_original__icontains=qname)| Q(
				fk_descriptor_name__descriptor_original__icontains=qname)| Q(
				fk_descriptor_prefix1__prefix__icontains=qname)| Q(
				fk_descriptor_descriptor1__descriptor_original__icontains=qname)| Q(
				fk_descriptor_prefix2__prefix__icontains=qname)| Q(
				fk_descriptor_descriptor2__descriptor_original__icontains=qname)| Q(
				fk_descriptor_prefix3__prefix__icontains=qname)| Q(
				fk_descriptor_descriptor3__descriptor_original__icontains=qname)) 

	return (individual_object)

@sync_to_async
def personsearch_prepareset(individual_object):

	individual_set = {}

	for i in individual_object:
		individual_info = {}
		individual_info['actor_name'] = namecompiler(i)
		individual_info['id_individual'] = i.id_individual
		individual_set[i.id_individual] = individual_info

	return(individual_set)

## a function to apply this complex filter to actor searches


@sync_to_async
def peoplesearchfilter(individual_object, form):

	qname = form.cleaned_data['name']   

	qgroup = form.cleaned_data['group']
	qclass = form.cleaned_data['personclass']
	qorder = form.cleaned_data['personorder']

	if qgroup.isdigit():
		qgroup = int(qgroup)
		if int(qgroup) == 2: individual_object = individual_object.filter(corporateentity=True)
		if int(qgroup) == 1: individual_object = individual_object.filter(corporateentity=False)

	if len(qname) > 0:
		individual_object = individual_object.filter(
			Q(
				fullname_modern__icontains=qname) | Q(
				fullname_original__icontains=qname) | Q(
				fk_descriptor_title__descriptor_original__icontains=qname)| Q(
				fk_descriptor_name__descriptor_original__icontains=qname)| Q(
				fk_descriptor_prefix1__prefix__icontains=qname)| Q(
				fk_descriptor_descriptor1__descriptor_original__icontains=qname)| Q(
				fk_descriptor_prefix2__prefix__icontains=qname)| Q(
				fk_descriptor_descriptor2__descriptor_original__icontains=qname)| Q(
				fk_descriptor_prefix3__prefix__icontains=qname)| Q(
				fk_descriptor_descriptor3__descriptor_original__icontains=qname)) 

	if qclass.isdigit():
		if int(qclass) > 0:
			qclass = int(qclass)
			individual_object = individual_object.filter(fk_group_class=qclass)

	if qorder.isdigit():
		if int(qorder) > 0:
			qorder = int(qorder)
			individual_object = individual_object.filter(fk_group_order=qorder)

	return (individual_object)




@sync_to_async
def parishvalue(witness_entity_number):
	parish = Location.objects.get(id_location=witness_entity_number)

	return(parish)

@sync_to_async
def parish_map(witness_entity_number, parish):

	totalcases = Referenceindividual.objects.filter(fk_event__fk_event_locationreference__fk_locationname__fk_location=witness_entity_number).count()

	mapparishes = []

	## data for colorpeth map
	mapparishes1 = get_object_or_404(Jsonstorage, id_jsonfile=2)
	mapparishes = json.loads(mapparishes1.jsonfiletxt)

	for i in mapparishes:
		if i == "features":
			for b in mapparishes[i]:
				t = b["properties"]
				if t["fk_locatio"] == parish.pk_location:
					t["cases"] = totalcases
					t["parishname"] = parish.location

	return(mapparishes)


@sync_to_async
def parish_fetch(individual_object, witness_entity_number):

	individual_object = individual_object.filter(
		fk_individual_event__fk_event__fk_event_locationreference__fk_locationname__fk_location=witness_entity_number).annotate(
		occurences=
		Count('fk_individual_event')).annotate(
		witnessref=Count('fk_individual_event', filter=Q(fk_individual_event__fk_referencerole=1))).annotate(
		earlydate=Min('fk_individual_event__fk_event__startdate')).annotate(
		latedate=Max('fk_individual_event__fk_event__enddate'))

	return(individual_object)

@sync_to_async
def parish_individuallistfetch(individual_object):

	individual_list = []

	for i in individual_object:
		individual_info = {}
		individual_info['actor_name'] = namecompiler(i)
		individual_info['id_individual'] = i.id_individual
		individual_info['occurences'] = i.occurences
		individual_info['witnessref'] = i.witnessref
		try:
			individual_info['mindate'] = i.earlydate.year
		except:
			individual_info['mindate'] = 2000
		try:
			individual_info['maxdate'] = i.latedate.year
		except:
			pass
		individual_list.append(individual_info)

	individual_list = sorted (individual_list, key=lambda x: x["mindate"])

	return(individual_list)


#### My original code for the maps function
# @sync_to_async
# def mapparishesdata2(witness_entity_number):

#   reference_set = Referenceindividual.objects.filter(
#       fk_individual=witness_entity_number).values(
#   'fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location',
#   'fk_event__fk_event_locationreference__fk_locationname__fk_location__location',
#   'pk_referenceindividual')

#   parishstats = {}
#   parishnamevalues = {}
#   ref_list = []

#   for r in reference_set:
#       parisholdid = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location']
#       parishname = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__location']
#       if parisholdid in parishstats:
#           parishstats[parisholdid] += 1
#       else:
#           parishstats[parisholdid] = 1
#           parishnamevalues[parisholdid] = parishname
#       ref_list.append({r['pk_referenceindividual']: parishname})

#   mapparishes = []
#   mapparishes1 = get_object_or_404(Jsonstorage, id_jsonfile=2)
#   mapparishes = json.loads(mapparishes1.jsonfiletxt)

#   for i in mapparishes:
#       if i == "features":
#           for b in mapparishes[i]:
#               j = b["properties"]

#               parishvalue = j["fk_locatio"]
#               try:
#                   j["cases"] = parishstats[parishvalue]
#                   j["parishname"] = parishnamevalues[parishvalue]
#               except:
#                   pass

#   return(mapparishes, ref_list)

#chatgpt refinement
@sync_to_async
def mapparishesdata2(witness_entity_number):

	reference_set = Referenceindividual.objects.filter(
		fk_individual=witness_entity_number).values(
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__location',
	'pk_referenceindividual')

	parishstats = {}
	parishnamevalues = {}
	ref_list = {}

	for r in reference_set:
		parisholdid = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location']
		parishname = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__location']
		if parisholdid in parishstats:
			parishstats[parisholdid] += 1
		else:
			parishstats[parisholdid] = 1
			parishnamevalues[parisholdid] = parishname
		ref_list[r['pk_referenceindividual']] = parishname

	# Step 3: Fetch and load the map JSON file from storage
	mapparishes1 = get_object_or_404(Jsonstorage, id_jsonfile=2)
	mapparishes = json.loads(mapparishes1.jsonfiletxt)

	# Step 4: Update the mapparishes data with the parish statistics
	for feature in mapparishes.get("features", []):
		properties = feature.get("properties", {})
		parish_value = properties.get("fk_locatio")

		if parish_value in parishstats and parish_value in parishnamevalues:
			properties["cases"] = parishstats[parish_value]
			properties["parishname"] = parishnamevalues[parish_value]

	# Return the updated map data and the reference list
	return mapparishes, ref_list



@sync_to_async
def mapparishesdata3(witness_entity_number):
	# Prefetch only necessary related data
	reference_set = Referenceindividual.objects.filter(fk_individual=witness_entity_number).select_related(
		'fk_referencerole', 'fk_event', 'fk_event__part__fk_item', 'fk_event__fk_event_locationreference__fk_locationname__fk_location'
	).values(
		'fk_event', 'fk_individual', 'pk_referenceindividual',
		'fk_event__startdate', 'fk_event__enddate', 
		'fk_event__repository_startdate', 'fk_event__repository_enddate',
		'fk_referencerole__referencerole', 'fk_event__part__fk_item__shelfmark',
		'fk_event__part__fk_item__id_item', 'fk_event__part__id_part',
		'fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region',
		'fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location',
		'fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location',
		'fk_event__fk_event_locationreference__fk_locationname__fk_location__location'
	)

	parishstats = {}
	parishnamevalues = {}
	reference_list = []

	# Prepare reference list and statistics for parishes
	for r in reference_set:
		parish_id = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location']
		parish_name = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__location']

		# Track parish statistics
		parishstats[parish_id] = parishstats.get(parish_id, 0) + 1
		parishnamevalues[parish_id] = parish_name

		# Build reference row
		reference_row = {
			"role": r['fk_referencerole__referencerole'],
			"item_shelfmark": r['fk_event__part__fk_item__shelfmark'],
			"item_id": r['fk_event__part__fk_item__id_item'],
			"part_id": r['fk_event__part__id_part'],
			"region": r['fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region'],
			"location_id": r['fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location'],
			"location": r['fk_event__fk_event_locationreference__fk_locationname__fk_location__location'],
			"location_pk": r['fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location'],
			"part_url": reverse('entity', kwargs={'witness_entity_number': r['fk_event__part__id_part']}),
		}

		# Handle date formatting
		start_date = r.get('fk_event__startdate') or r.get('fk_event__repository_startdate')
		end_date = r.get('fk_event__enddate') or r.get('fk_event__repository_enddate')

		if start_date and end_date:
			start_year = int(str(start_date)[:4])
			end_year = int(str(end_date)[:4])
			reference_row['date'] = f"{start_year} - {end_year}" if end_year > start_year else str(start_year)
		else:
			reference_row['date'] = "20000"

		reference_list.append(reference_row)

	# Sort reference list by date (assuming the 'date' field is properly formatted)
	reference_list.sort(key=lambda x: x["date"])

	# Fetch mapparishes from JSON storage
	mapparishes_obj = get_object_or_404(Jsonstorage, id_jsonfile=2)
	mapparishes = json.loads(mapparishes_obj.jsonfiletxt)

	# Update mapparishes features with parish stats
	for feature in mapparishes.get("features", []):
		parish_value = feature["properties"].get("fk_location")
		
		if parish_value:
			feature["properties"]["cases"] = parishstats.get(parish_value, 0)
			feature["properties"]["parishname"] = parishnamevalues.get(parish_value, '')

	return mapparishes, reference_list

@sync_to_async
def mapparishesdata(reference_set):

	parishstats = {}
	parishnamevalues = {}
	ref_list = []

	for r in reference_set.values():
		parisholdid = r['location_pk']
		parishname = r['location']
		if parisholdid in parishstats:
			parishstats[parisholdid] += 1
		else:
			parishstats[parisholdid] = 1
			parishnamevalues[parisholdid] = parishname

		ref_list.append(r)
	
	reference_list = sorted (ref_list, key=lambda x: x["date"])

	mapparishes = []
	mapparishes1 = get_object_or_404(Jsonstorage, id_jsonfile=2)
	mapparishes = json.loads(mapparishes1.jsonfiletxt)

	for i in mapparishes:
		if i == "features":
			for b in mapparishes[i]:
				j = b["properties"]

				parishvalue = j["fk_locatio"]
				try:
					j["cases"] = parishstats[parishvalue]
					j["parishname"] = parishnamevalues[parishvalue]
					#print ("found", parishvalue)
				except:
					pass
					#print ("can't find", parishvalue)

	return(reference_list, mapparishes)


@sync_to_async
def individualsearch2(witness_entity_number):

	individual_object = Individual.objects.select_related(
	'fk_group').select_related(
	'fk_descriptor_title').select_related(
	'fk_descriptor_name').select_related(
	'fk_descriptor_prefix1').select_related(
	'fk_descriptor_descriptor1').select_related(
	'fk_separator_1').select_related(
	'fk_descriptor_prefix2').select_related(
	'fk_descriptor_descriptor2').select_related(
	'fk_descriptor_prefix3').select_related(
	'fk_descriptor_descriptor3').select_related(
	'fk_group__fk_group_order').select_related(
	'fk_group__fk_group_class')

	individual_object = individual_object.get(id_individual=witness_entity_number)

	return(individual_object)

@sync_to_async
def relationship_dataset(witness_entity_number):
		 
	relationship_object = Digisigrelationshipview.objects.filter(
		fk_individual = witness_entity_number).select_related(
		'person2__fk_group').select_related(
		'person2__fk_descriptor_title').select_related(
		'person2__fk_descriptor_name').select_related(
		'person2__fk_descriptor_prefix1').select_related(
		'person2__fk_descriptor_descriptor1').select_related(
		'person2__fk_descriptor_prefix2').select_related(
		'person2__fk_descriptor_descriptor2').select_related(
		'person2__fk_descriptor_prefix3').select_related(
		'person2__fk_descriptor_descriptor3').values(
		'relationship_role',
		'person2__id_individual',
		'person2__fk_group__group_name',
		'person2__fk_descriptor_name__descriptor_modern',
		'person2__fk_descriptor_prefix1__prefix_english',
		'person2__fk_descriptor_descriptor1__descriptor_modern',
		'person2__fk_descriptor_prefix2__prefix_english',
		'person2__fk_descriptor_descriptor2__descriptor_modern',
		'person2__fk_descriptor_prefix3__prefix_english').order_by('person2')

	relationship_dic = {}
	relationshipnumber = 0

	for r in relationship_object:

		relationshipnumber += 1

		relationshipvalues = {}

		nameoriginal = ""
		if r['person2__fk_group__group_name'] != None:
			nameoriginal =  r['person2__fk_group__group_name']
		if r['person2__fk_descriptor_name__descriptor_modern'] != None:
			nameoriginal =  r['person2__fk_descriptor_name__descriptor_modern']
		if r['person2__fk_descriptor_prefix1__prefix_english'] != None:
			nameoriginal = nameoriginal + " " + r['person2__fk_descriptor_prefix1__prefix_english']
		if r['person2__fk_descriptor_descriptor1__descriptor_modern'] != None:
			nameoriginal = nameoriginal + " " + r['person2__fk_descriptor_descriptor1__descriptor_modern']
		if r['person2__fk_descriptor_prefix2__prefix_english'] != None:
			nameoriginal = nameoriginal + " " + r['person2__fk_descriptor_prefix2__prefix_english']
		if r['person2__fk_descriptor_descriptor2__descriptor_modern'] != None:
			nameoriginal = nameoriginal + " " + r['person2__fk_descriptor_descriptor2__descriptor_modern']
		if r['person2__fk_descriptor_prefix3__prefix_english'] != None:
			nameoriginal = nameoriginal + " " + r['person2__fk_descriptor_prefix3__prefix_english']

		relationshipvalues['name'] = nameoriginal
		relationshipvalues['role'] = r['relationship_role']
		relationshipvalues['id_individual'] = r['person2__id_individual']

		relationship_dic[r['person2__id_individual']] = relationshipvalues

	return(relationship_dic, relationshipnumber)    


def referencenamegenerator(r):

	nameoriginal = ""

	if r['fk_individual__fk_descriptor_name__descriptor_modern'] != None:
		nameoriginal =  r['fk_individual__fk_descriptor_name__descriptor_modern']
	if r['fk_individual__fk_descriptor_prefix1__prefix_english'] != None:
		nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_prefix1__prefix_english']
	if r['fk_individual__fk_descriptor_descriptor1__descriptor_modern'] != None:
		nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_descriptor1__descriptor_modern']
	if r['fk_individual__fk_descriptor_prefix2__prefix_english'] != None:
		nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_prefix2__prefix_english']
	if r['fk_individual__fk_descriptor_descriptor2__descriptor_modern'] != None:
		nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_descriptor2__descriptor_modern']
	if r['fk_individual__fk_descriptor_prefix3__prefix_english'] != None:
		nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_prefix3__prefix_english']

	return (nameoriginal)

### network diagrams
def networkgenerator(reference_set):

	linkslist = []
	nodelist = []

	reference_dic = {}
	person_dic = {}
	personlist = []  

	for r in reference_set:

		if r['fk_event'] in reference_dic:
			eventid = r['fk_event']
			reference_dic[eventid].append(r['fk_individual'])
		else:
			eventid = r['fk_event']
			reference_dic[eventid] = [r['fk_individual']]

		nameoriginal = referencenamegenerator(r)

		# nameoriginal = ""

		# if r['fk_individual__fk_descriptor_name__descriptor_modern'] != None:
		#   nameoriginal =  r['fk_individual__fk_descriptor_name__descriptor_modern']
		# if r['fk_individual__fk_descriptor_prefix1__prefix_english'] != None:
		#   nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_prefix1__prefix_english']
		# if r['fk_individual__fk_descriptor_descriptor1__descriptor_modern'] != None:
		#   nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_descriptor1__descriptor_modern']
		# if r['fk_individual__fk_descriptor_prefix2__prefix_english'] != None:
		#   nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_prefix2__prefix_english']
		# if r['fk_individual__fk_descriptor_descriptor2__descriptor_modern'] != None:
		#   nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_descriptor2__descriptor_modern']
		# if r['fk_individual__fk_descriptor_prefix3__prefix_english'] != None:
		#   nameoriginal = nameoriginal + " " + r['fk_individual__fk_descriptor_prefix3__prefix_english']

		valuetarget = 1
		person = r['fk_individual']

		if person in personlist:
			x=personlist.index(person)
			case = nodelist[x]
			currentvalue = case['val'] + 1
			if currentvalue > 1: colour = '#4d4db3'
			if currentvalue > 3: colour = '#409fbf'
			if currentvalue > 5: colour = '#c6a339'
			if currentvalue > 7: colour = '#c68039'
			if currentvalue > 10: colour = '#d95326'
			if currentvalue > 15: colour = '#ff0000'
			nodelist.pop(x)
			nodelist.insert(x, {'id':person, 'name': nameoriginal, 'val': currentvalue, 'color': colour})
			# nodelist.insert(x, {'id':person})

		else:
			personlist.append(person)
			nodelist.append({'id':person, 'name': nameoriginal, 'val': 1, 'color':'#806c93'})
			# nodelist.append({'id':person})

	for r in reference_dic:
		targetset = reference_dic[r]
		numberofpeople = len(reference_dic[r])

		for x in range(numberofpeople):
			for y in range(x+1, numberofpeople):
				person1 = targetset[x]
				person2 = targetset[y]
				linkslist.append({'source': person1, 'target': person2})

	return (linkslist, nodelist)


#### creates redirect links from generic URLs 
def redirectgenerator(digisig_entity_number, operation, application):

	entitynumber = int(digisig_entity_number)

	if (operation == 1): root = "/page/"
	if (operation == 2): root = "/edit/"
	if (operation == 3): 
		root = "/discover/exhibit/"
		targetphrase = root + str(digisig_entity_number)
		return (targetphrase)       

	finalcharacter = (str(digisig_entity_number))[7:] 

	if finalcharacter == '0': stem = "item/"
	if finalcharacter == '1': stem = "seal/"
	if finalcharacter == '2': stem = "manifestation/"
	if finalcharacter == '3': stem = "sealdescription/"
	if finalcharacter == '4': stem = "representation/"
	if finalcharacter == '5': stem = "support/"
	if finalcharacter == '6': stem = "face/"

	#term=7 (10000007-29999997) collection=7(30000007-49999997) and place=7(higher than 49999997...)    
	if finalcharacter == '7':
		if (entitynumber < 29999997): stem = "term/"
		elif (entitynumber < 49999997): stem = "collection/"
		else: 
			stem = "place/" 
			if application == 2:
				stem = "parish/" 

	#temp workaround -- parts to redirect to item page
	if finalcharacter == '8': 
		stem = "part/"
		if application == 1: 
			part_object = get_object_or_404(Part, id_part=digisig_entity_number)
			digisig_entity_number = part_object.fk_item.id_item

	if finalcharacter == '9':
		stem = "actor/" 
		if application == 2:
			stem = "person/"

	targetphrase = root + stem + str(digisig_entity_number)
	
	return (targetphrase)


def temporaldistribution(timegroupcases):
	#prepare the temporal groups of seals for graph
	timegroupset = TimegroupC.objects.filter(pk_timegroup_c__lt=15).order_by('pk_timegroup_c')
	timecount = {}

	# set the number in each group to 0
	for t in timegroupset:
		timecount.update({t.timegroup_c_range: 0})

	# how many seals belong in each temporal group?
	for case in timegroupcases:

		if case['date_origin'] < 1500 and case['date_origin'] > 999:
			if case['fk_timegroupc'] < 15:
				#number of cases for each time period
				timegroupupdate = case['fk_timegroupc__timegroup_c_range']
				timecount[timegroupupdate] += 1

	labels = []
	data = []

	# determine how many seals should go in each temporal group
	for key, value in timecount.items():
		labels.append(key)
		data.append(value)

	return (labels, data)


def getquantiles(timegroupcases):

	timelist = []
	for t in timegroupcases:

		try:
			timelist.append(int(t['date_origin']))

		except:
			print ("exception", t)

	quantileset = statistics.quantiles(timelist, n=6)

	# print ("timelist", timelist)
	# print ("quantileset", quantileset)

	resultrange = "c." + str(int(quantileset[0])) + "-" + str(int(quantileset[4]))

	return (resultrange, timelist)


@sync_to_async
def mlpredictcase (class_object, shape_object, case_area, mlmodel):

	data = mldatacase(class_object, shape_object, case_area)
	df = pd.DataFrame(data)

	result = mlmodel.predict(df)
	leaf_id = mlmodel.apply(df)
	finalnode = (list(leaf_id))
	finalnodevalue = finalnode[0]
	result1 = result.item(0)
	resulttext = int(result.item(0))

	return (result, result1, resulttext, finalnodevalue, df)


def mldatacase(class_object, shape_object, resultarea):

	data = { 
		'Round': [shape_object.round],
		'pointedoval': [shape_object.pointedoval],
		'roundedoval': [shape_object.roundedoval],
		'scutiform': [shape_object.scutiform],
		'trianglepointingup': [shape_object.trianglepointingup],
		'unknown': [shape_object.unknown],
		'square': [shape_object.square],
		'lozenge': [shape_object.lozenge],
		'drop': [shape_object.drop],
		'trianglepointingdown': [shape_object.trianglepointingdown],
		'rectangular': [shape_object.rectangular],
		'hexagonal': [shape_object.hexagonal],
		'octagonal': [shape_object.octagonal],
		'abnormal': [shape_object.abnormal],
		'kite': [shape_object.kite],
		'quatrefoil': [shape_object.quatrefoil],
		'size_area': [resultarea],
		'animal': [class_object.animal],
		'human': [class_object.human],
		'objects': [class_object.object_class],
		'device': [class_object.device],
		'beast': [class_object.beast],
		'bird': [class_object.bird],
		'fish': [class_object.fish],
		'insect': [class_object.insect],
		'bust': [class_object.bust],
		'hand': [class_object.hand],
		'boat': [class_object.boat],
		'building': [class_object.building],
		'container': [class_object.container],
		'equipment': [class_object.equipment],
		'naturalproduct': [class_object.naturalproduct],
		'irregular': [class_object.irregular],
		'radial': [class_object.radial],
		'lattice': [class_object.lattice],
		'fulllength': [class_object.fulllength],
		'symbol': [class_object.symbol],
		'hawkhunting': [class_object.hawkhunting],
		'pelicaninpiety': [class_object.pelicaninpiety],
		'headondish': [class_object.headondish],
		'twoheads': [class_object.twoheads],
		'crossedhands': [class_object.crossedhands],
		'handholdingitem': [class_object.handholdingitem],
		'seated': [class_object.seated],
		'standing': [class_object.standing],
		'riding': [class_object.riding],
		'crucified': [class_object.crucified],
		'apparel': [class_object.apparel],
		'crenellation': [class_object.crenellation],
		'tool': [class_object.tool],
		'weapon': [class_object.weapon],
		'Shell': [class_object.shell],
		'wheatsheaf': [class_object.wheatsheaf],
		'stylizedlily': [class_object.stylizedlily],
		'crosses': [class_object.crosses],
		'heart': [class_object.heart],
		'merchantmark': [class_object.merchantmark],
		'texts': [class_object.texts],
		'handholdingbird': [class_object.handholdingbird],
		'halflength': [class_object.halflength],
		'crescent': [class_object.crescent],
		'beastbody': [class_object.beastbody],
		'beasthead': [class_object.beasthead],
		'doubleheadedeagle': [class_object.doubleheadedeagle],
		'horseshoe': [class_object.horseshoe],
		'twobirdsdrinking': [class_object.twobirdsdrinking],
		'animalequipment': [class_object.animalequipment],
		'transport': [class_object.transport],
		'halflengthwomanholdingchild': [class_object.halflengthwomanholdingchild],
		'halflengthwoman': [class_object.halflengthwoman],
		'halflengthman': [class_object.halflengthman],
		'swine': [class_object.swine],
		'boarhead': [class_object.boarhead],
		'centaur': [class_object.centaur],
		'dragon': [class_object.dragon],
		'hare': [class_object.hare],
		'lion': [class_object.lion],
		'lionhead': [class_object.lionhead],
		'mermaid': [class_object.mermaid],
		'squirrel': [class_object.squirrel],
		'stag': [class_object.stag],
		'staghead': [class_object.staghead],
		'unicorn': [class_object.unicorn],
		'unicornhead': [class_object.unicornhead],
		'wolf': [class_object.wolf],
		'wolfhead': [class_object.wolfhead],
		'standingwoman': [class_object.standingwoman],
		'standingman': [class_object.standingman],
		'armouredmanequestrian': [class_object.armouredmanequestrian],
		'seatedwomanholdingchild': [class_object.seatedwomanholdingchild],
		'axe': [class_object.axe],
		'shears': [class_object.shears],
		'arrow': [class_object.arrow],
		'spear': [class_object.spear],
		'sword': [class_object.sword],
		'banner': [class_object.banner],
		'shield': [class_object.shield],
		'christogram': [class_object.christogram],
		'lionfighting': [class_object.lionfighting],
		'sheep': [class_object.sheep],
		'griffin': [class_object.griffin],
		'hammer': [class_object.hammer],
		'standingwomanholdingchild': [class_object.standingwomanholdingchild],
		'hareonhound': [class_object.hareonhound],
		'lambandstaff': [class_object.lambandstaff],
		'lionsleeping': [class_object.lionsleeping],
		'standingliturgicalapparel': [class_object.standingliturgicalapparel],
		'manfightinganimal': [class_object.manfightinganimal],
		'bowandarrow': [class_object.bowandarrow],
		'spearandpennon': [class_object.spearandpennon],
		'seatedman': [class_object.seatedman],
		}

	return (data)


# def mlmodelget():
#   #url = os.path.join(settings.STATIC_ROOT, 'ml/2023_feb20_ml_tree')
#   #url = os.path.join(settings.STATIC_ROOT, 'ml/ml_tree')


#   url = os.path.join(settings.STATIC_ROOT, 'ml/ml_faceobjectset')
#   url = os.path.join(settings.STATIC_URL, 'ml/ml_tree')

#   print (url)
#   print (os.listdir(settings.STATIC_URL))

#   with open(url, 'rb') as file:   
#       mlmodel = pickle.load(file)

#   return(mlmodel)

@sync_to_async
def finalnodevalue_set(finalnodevalue, shape_object, class_object):
	#find other seals assigned to this decision tree group
	timegroupcases = Seal.objects.filter(
		date_prediction_node=finalnodevalue).order_by(
		"date_origin").select_related(
		'fk_timegroupc').values(
		'date_origin', 'id_seal', 'fk_timegroupc', 'fk_timegroupc__timegroup_c_range', 'fk_seal_face__fk_shape', 'fk_seal_face__fk_class')

	resultrange, resultset = getquantiles(timegroupcases)
	labels, data1 = temporaldistribution(timegroupcases)
	sealtargets = timegroupcases.values_list('id_seal', flat='True')

	# #identify a subset of seal to display as suggestions
	seal_set = Representation.objects.filter(
		primacy=1).filter(
		fk_manifestation__fk_face__fk_seal__in=sealtargets).filter(
		fk_manifestation__fk_face__fk_shape=shape_object).filter(
		fk_manifestation__fk_face__fk_class=class_object).select_related(
		'fk_connection').select_related(
		'fk_manifestation__fk_face__fk_seal').select_related(
		'fk_manifestation__fk_support__fk_part__fk_item__fk_repository').select_related(
		'fk_manifestation__fk_support__fk_number_currentposition').select_related(
		'fk_manifestation__fk_support__fk_attachment').select_related(
		'fk_manifestation__fk_support__fk_supportstatus').select_related(
		'fk_manifestation__fk_support__fk_nature').select_related(
		'fk_manifestation__fk_imagestate').select_related(
		'fk_manifestation__fk_position').select_related(
		'fk_manifestation__fk_support__fk_part__fk_event').order_by(
		'fk_manifestation')

	return(seal_set, resultrange, resultset, labels, data1)

@sync_to_async
def mlmanifestation_set(seal_set):
	manifestation_set = {}
	
	for s in seal_set:
		manifestation_dic = {}
		connection = s.fk_connection
		manifestation_dic["thumb"] = connection.thumb
		manifestation_dic["medium"] = connection.medium
		manifestation_dic["representation_thumbnail_hash"] = s.representation_thumbnail_hash
		manifestation_dic["representation_filename_hash"] = s.representation_filename_hash 
		manifestation_dic["id_representation"] = s.id_representation    
		manifestation_dic["id_item"] = s.fk_manifestation.fk_support.fk_part.fk_item.id_item
		manifestation_dic["id_manifestation"] = s.fk_manifestation.id_manifestation
		manifestation_dic["id_seal"] = s.fk_manifestation.fk_face.fk_seal.id_seal
		manifestation_dic["repository_fulltitle"] = s.fk_manifestation.fk_support.fk_part.fk_item.fk_repository.repository_fulltitle
		manifestation_dic["number"] = s.fk_manifestation.fk_support.fk_number_currentposition.number
		manifestation_dic["imagestate_term"] = s.fk_manifestation.fk_imagestate
		manifestation_dic["shelfmark"] = s.fk_manifestation.fk_support.fk_part.fk_item.shelfmark
		manifestation_dic["label_manifestation_repository"] = s.fk_manifestation.label_manifestation_repository

		manifestation_set[s.fk_manifestation.id_manifestation] = manifestation_dic

	return(manifestation_set)


@sync_to_async
def mlshowpath (mlmodel, df):
	node_indicator = mlmodel.decision_path(df)
	leaf_id = mlmodel.apply(df)
	feature = mlmodel.tree_.feature
	threshold = mlmodel.tree_.threshold
	n_nodes = mlmodel.tree_.node_count

	sample_id = 0
	# obtain ids of the nodes `sample_id` goes through, i.e., row `sample_id`
	node_index = node_indicator.indices[
		node_indicator.indptr[sample_id] : node_indicator.indptr[sample_id + 1]
	]

	#print ("node_index", node_index)

	# feature names
	i = -1
	featurenames = []
	for col in df.columns:
		i = i + 1
		#print (i, col)

		if col == "size_area":
			col = "size"
		featurenames.append(col)

	decisiontreetext= []
	decisiontreedic= {}
	for node_id in node_index:
		
		# continue to the next node if it is a leaf node
		if leaf_id[sample_id] == node_id:
			continue 

		value = df.iat[0,feature[node_id]]
		
		if value <= threshold[node_id]:
			threshold_sign = "<="
		else:
			threshold_sign = ">"

		decisiontreetext.append(
			"decision node {node} : {featurename}({value}) "
			"{inequality} {threshold}".format(
				node=node_id,
				sample=sample_id,
				feature=feature[node_id],
				featurename=featurenames[feature[node_id]],
				value = df.iat[0,feature[node_id]],
				#value=X2[sample_id, feature[node_id]],
				inequality=threshold_sign,
				threshold=threshold[node_id],
			)
		)

		decisiontreedic[node_id] = {
			"node": node_id,
			"inequality": threshold_sign,
			"feature": feature[node_id],
			"featurename": featurenames[feature[node_id]],
			"value": df.iat[0,feature[node_id]],
			"inequality":threshold_sign,
			"threshold": round(threshold[node_id], 2)
		}

	return (node_index, decisiontreedic)




def faceupdater(shapecode, height, width):

	print (shapecode, height, width)
	returnarea = 0

	if height == None:
		return(returnarea)

	if width == None:
		return(returnarea)

	if height > 0:
		if width > 0:
			#round
			if shapecode == 1:
				radius1 = height/2
				returnarea = math.pi * (radius1 **2)

			# Pointed Oval
			if shapecode == 2:
				radius1 = ((height * 1.06)/ 2)
				width1 = width/2
				returnarea = (((radius1**2) * (math.acos((radius1-width1) / radius1)))-((radius1-width1) * (math.sqrt((2*radius1*width1)-(width1**2))))) *2

			# Rounded Oval
			if shapecode == 3:
				returnarea = roundedoval(height, width)

			# Scutiform
			if shapecode == 4:
				returnarea = ((height/2) * width) + ((height/2) * (width/2))

			# Unknown
			if shapecode == 5:
				returnarea = roundedoval(height, width)

			# Triangle pointing up
			if shapecode == 6:
				returnarea = (height * (width/2))

			# Square
			if shapecode == 7:
				returnarea = (height * width)

			# Lozenge-shaped
			if shapecode == 8:
				returnarea = (height * width)/2

			# Quatrofoil
			if shapecode == 9:
				heightvalue = height/2
				returnarea = ((heightvalue**2) + 2 * ((math.pi * (heightvalue**2) /4)))

			# Drop-shaped
			if shapecode == 10:
				returnarea = roundedoval(height, width)

			# Undetermined
			if shapecode == 11:
				returnarea = 0

			# Triangle pointing down
			if shapecode == 12:
				returnarea = (height * (width/2))

			# Rectangular
			if shapecode == 13:
				returnarea = (height * width)

			# Hexagonal
			if shapecode == 14:
				## note that hexagons might measured from either the angle or a flat side
				## run calculation with the smallest dimension -- not the angles. https://www.math.net/area-of-a-hexagon
				testdimension = width
				if height < width:
					testdimension = height
				returnarea = (math.sqrt(3)/2) * (testdimension**2)

			# Octagonal
			if shapecode == 15:
				returnarea = 2*((height/(1+math.sqrt(2)))**2)*(1+math.sqrt(2))

			# Abnormal shape
			if shapecode == 16:
				returnarea = roundedoval(height, width)

			# Kite-shaped
			if shapecode == 17:
				returnarea = roundedoval(height, width)

	returnarea = round(returnarea,2)
	
	return(returnarea)

def roundedoval(height, width):
	radius1 = height/2
	width1 = width/2
	returnarea = math.pi * radius1 * width1 

	return(returnarea)

@sync_to_async
def collection_details(qcollection):

	collection = Collection.objects.get(id_collection=qcollection)

	collection_dic = {}
	collection_dic["id_collection"] = int(qcollection)
	collection_dic["collection_thumbnail"] = collection.collection_thumbnail
	collection_dic["collection_publicationdata"] = collection.collection_publicationdata
	collection_dic["collection_fulltitle"] = collection.collection_fulltitle
	collection_dic["notes"] = collection.notes

	sealdescription_set = Sealdescription.objects.filter(fk_seal__gt=1).select_related('fk_seal')

	#if collection is set then limit the scope of the dataset
	if (qcollection == 30000287):
		collection_dic["collection_title"] = 'All Collections'
		pagetitle = 'All Collections'
		collection_dic["totalsealdescriptions"] = sealdescription_set.count()
		collection_dic["totalseals"] = sealdescription_set.distinct('fk_seal').count()

	else:
		collection_dic["collection_title"] = collection.collection_title
		pagetitle = collection.collection_title
		sealdescription_set = sealdescription_set.filter(fk_collection=qcollection)
		collection_dic["totalsealdescriptions"] = sealdescription_set.distinct(
			'sealdescription_identifier').count()
		collection_dic["totalseals"] = sealdescription_set.distinct(
			'fk_seal').count()

	return(collection, collection_dic, sealdescription_set)

@sync_to_async
def collection_counts(sealdescription_set):
	actorscount = sealdescription_set.filter(fk_seal__fk_individual_realizer__gt=10000019).count()

	datecount =sealdescription_set.filter(fk_seal__date_origin__gt=1).count()

	classcount = sealdescription_set.filter(
		fk_seal__fk_seal_face__fk_class__isnull=False).exclude(
		fk_seal__fk_seal_face__fk_class=10000367).exclude(
		fk_seal__fk_seal_face__fk_class=10001007).count()

	facecount = sealdescription_set.filter(fk_seal__fk_seal_face__fk_faceterm=1).distinct('fk_seal__fk_seal_face').count() 

	return(actorscount, datecount, classcount, facecount)

@sync_to_async
def collection_chart2():

	result = Terminology.objects.filter(
		term_type=1).order_by(
		'term_sortorder').annotate(
		num_cases=Count("fk_term_interchange__fk_class__fk_class_face"))

	totalcases = sum([r.num_cases for r in result]) 

	data2 = []
	labels2 = []

	for r in result:
		percentageresult = (r.num_cases / totalcases) * 100 

		if percentageresult > 1:
			data2.append((r.num_cases / totalcases) * 100)
			labels2.append(r.term_name)

	return(data2, labels2)


@sync_to_async
# def map_locationset(qcollection):
#   if (qcollection == 30000287):
#       locationset = Location.objects.filter(
#           Q(locationname__locationreference__fk_locationstatus=1)).annotate(
#           count=Count('locationname__locationreference__fk_event__part__fk_part__fk_support'))

#   else:
#       #data for location map
#       locationset = Location.objects.filter(
#           Q(locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection)).annotate(
#           count=Count('locationname__locationreference__fk_event__part__fk_part__fk_support'))
def map_locationset(qcollection, qtimechoice=None, qsealtypechoice=None):
	"""
	Retrieves a queryset of Location objects based on the provided criteria.

	Args:
		qcollection: The collection ID to filter by.
		qtimechoice: Optional time group code to filter by.
		qsealtypechoice: Optional seal type to filter by.

	Returns:
		A queryset of Location objects with an annotation for 'count'.
	"""
	base_filters = Q(locationname__locationreference__fk_locationstatus=1)

	if qcollection == 30000287:
		pass ## This is a notional rather than actual collection, so do not try and filter on this value!
	else:
		base_filters &= Q(locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection)

	if qtimechoice is not None:
		base_filters &= Q(locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_timegroupc=qtimechoice)

	if qsealtypechoice is not None:
		base_filters &= Q(locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealtype=qsealtypechoice)

	locationset = Location.objects.filter(base_filters).annotate(
		count=Count('locationname__locationreference__fk_event__part__fk_part__fk_support')
	)

	return(locationset)

# @sync_to_async
# def map_placeset(qcollection):
#   if (qcollection == 30000287):
#       #data for map counties
#       placeset = Region.objects.filter(fk_locationtype=4, 
#           location__locationname__locationreference__fk_locationstatus=1
#           ).annotate(numplaces=Count('location__locationname__locationreference__fk_event__part__fk_part__fk_support')).values(
#           'numplaces', 
#           'fk_his_countylist') 
#   else:
#       #data for map counties
#       placeset = Region.objects.filter(fk_locationtype=4, 
#           location__locationname__locationreference__fk_locationstatus=1, 
#           location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection
#           ).annotate(numplaces=Count('location__locationname__locationreference')).values(
#           'numplaces', 
#           'fk_his_countylist')

#   return(placeset)

@sync_to_async
def map_placeset(qcollection, qtimechoice=None, qsealtypechoice=None):
	"""
	Retrieves data for mapping counties based on the provided collection ID
	and optional time and seal type filters.

	Args:
		qcollection: The collection ID to filter by.
		qtimechoice: Optional time group code to filter by (defaults to None).
		qsealtypechoice: Optional seal type to filter by (defaults to None).

	Returns:
		A queryset of Region objects with annotations for 'number_cases'
		and selected 'fk_his_countylist' values.
	"""
	base_filters = {
		'fk_locationtype': 4,
		'location__locationname__locationreference__fk_locationstatus': 1,
	}

	if qtimechoice is not None:
		base_filters['location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_timegroupc'] = qtimechoice

	if qsealtypechoice is not None:
		base_filters['location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealtype'] = qsealtypechoice

	if qcollection == 30000287:
		# Data for map counties (specific condition)
		queryset = Region.objects.filter(**base_filters).annotate(
			number_cases=Count('location__locationname__locationreference__fk_event__part__fk_part__fk_support')
		)
	else:
		# Data for map counties (general condition)
		queryset = Region.objects.filter(
			**base_filters,
			location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection
		).annotate(
			number_cases=Count('location__locationname__locationreference')
		)

	placeset = queryset.values('number_cases', 'fk_his_countylist')

	return (placeset)

@sync_to_async
def map_placecases(placeset):
	
	placecases = 0

	for p in placeset:
		placecases = placecases + p['number_cases']

	return(placecases)


@sync_to_async
def map_counties(placeset):

	## data for colorpeth map
	mapcounties1 = get_object_or_404(Jsonstorage, id_jsonfile=1)
	mapcounties = json.loads(mapcounties1.jsonfiletxt)

	# for i in mapcounties:
	#   if i == "features":
	#       for b in mapcounties[i]:
	#           j = b["properties"]
	#           countyvalue = j["HCS_NUMBER"]
	#           countyname = j["NAME"]
	#           numberofcases = placeset.filter(fk_his_countylist=countyvalue)
	#           for t in numberofcases:
	#               j["cases"] = t['numplaces']

	# return(mapcounties)

	# Create a dictionary to quickly access numplaces by county ID
	county_places = {}
	for place in placeset:
		county_id = place['fk_his_countylist']
		num_places = place['number_cases']
		if county_id not in county_places:
			county_places[county_id] = 0
		county_places[county_id] += num_places  # Accumulate if multiple places per county

	# Iterate through the features in mapcounties and update 'cases'
	if "features" in mapcounties:
		for feature in mapcounties["features"]:
			properties = feature.get("properties")
			if properties:
				county_value = properties.get("HCS_NUMBER")
				if county_value in county_places:
					properties["cases"] = county_places[county_value]
				else:
					properties["cases"] = 0  # Or some other default value if no places

	return mapcounties


# @sync_to_async
# def map_regionset(qcollection):
#   if (qcollection == 30000287):
#       regiondisplayset = Regiondisplay.objects.filter(region__location__locationname__locationreference__fk_locationstatus=1
#           ).annotate(numregions=Count('region__location__locationname__locationreference__fk_event__part__fk_part__fk_support')) 

#   else:
#       #data for region map 
#       regiondisplayset = Regiondisplay.objects.filter( 
#           region__location__locationname__locationreference__fk_locationstatus=1, 
#           region__location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection
#           ).annotate(numregions=Count('region__location__locationname__locationreference'))

#   return(regiondisplayset)

@sync_to_async
def map_regionset(qcollection, qtimechoice=None, qsealtypechoice=None):
	"""
	Retrieves a queryset of Regiondisplay objects for mapping regions,
	filtered by the provided collection ID and optional time and seal type filters.

	Args:
		qcollection: The collection ID to filter by.
		qtimechoice: Optional time group code to filter by (defaults to None).
		qsealtypechoice: Optional seal type to filter by (defaults to None).

	Returns:
		A queryset of Regiondisplay objects with an annotation for 'number_cases'.
	"""
	base_filters = {
		'region__location__locationname__locationreference__fk_locationstatus': 1,
	}

	if qtimechoice is not None:
		base_filters['region__location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_timegroupc'] = qtimechoice

	if qsealtypechoice is not None:
		base_filters['region__location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealtype'] = qsealtypechoice

	if qcollection == 30000287:
		# Data for region map (specific collection)
		queryset = Regiondisplay.objects.filter(**base_filters).annotate(
			number_cases=Count('region__location__locationname__locationreference__fk_event__part__fk_part__fk_support')
		)
	else:
		# Data for region map (other collections)
		queryset = Regiondisplay.objects.filter(
			**base_filters,
			region__location__locationname__locationreference__fk_event__part__fk_part__fk_support__fk_face__fk_seal__fk_sealsealdescription__fk_collection=qcollection
		).annotate(
			number_cases=Count('region__location__locationname__locationreference')
		)

	regionset = queryset.values('number_cases', 'id_regiondisplay', 'regiondisplay_label', 'regiondisplay_long', 'regiondisplay_lat')

	return regionset

@sync_to_async
def mapgenerator(location_object, count_in=0):
	#Establishing the Map data

	mapdic = {"type": "FeatureCollection"}
	properties = {}
	geometry = {}
	location = {}
	placelist = []

	longitude=""
	latitude=""
	# location=""
	location_dict = ""
	additionalformat = ""

	value1 = location_object.id_location
	value2 = location_object.location
	value3 = count_in
	value4 = location_object.longitude
	value5 = location_object.latitude

	popupcontent = '<a href="entity/' + str(value1) + '">' + str(value2) + '</a>'

	if count_in > 0:
		popupcontent = popupcontent + ' ' + str(value3)

	properties = {"id_location": value1, "location": value2, "count": value3, "popupContent": popupcontent}
	geometry = {"type": "Point", "coordinates": [value4, value5]}
	location = {"type": "Feature", "properties": properties, "geometry": geometry}
	placelist.append(location)

	mapdic["features"] = placelist

	return(mapdic)

@sync_to_async
def mapgenerator2(location_object):

	center_lat = []
	center_long = []

	mapdic = {"type": "FeatureCollection"}
	properties = {}
	geometry = {}
	location = {}
	placelist = []
	lat_values = []
	long_values = []

	for loc in location_object:
		value1 = loc.id_location
		value2 = loc.location
		value3 = loc.count
		value4 = loc.longitude
		value5 = loc.latitude

		if type(loc.longitude) == int or type(loc.longitude) == float:
			lat_values.append(loc.latitude)
		if type(loc.latitude) == int or type(loc.latitude) == float:
			long_values.append(loc.longitude)

		popupcontent = '<a href="entity/' + str(value1) + '">' + str(value2) + '</a>'

		if value3 > 0:
			popupcontent = popupcontent + ' ' + str(value3)

		properties = {"id_location": value1, "location": value2, "count": value3, "popupContent": popupcontent}
		geometry = {"type": "Point", "coordinates": [value4, value5]}
		location = {"type": "Feature", "properties": properties, "geometry": geometry}
		placelist.append(location)

	mapdic["features"] = placelist

	center_long = statistics.median(long_values)
	center_lat = statistics.median(lat_values)

	return(mapdic, center_long, center_lat)


@sync_to_async
def collection_loadmaplayer(selectedlayer):
	maplayer1 = get_object_or_404(Jsonstorage, id_jsonfile=selectedlayer)
	maplayer = json.loads(maplayer1.jsonfiletxt)

	return(maplayer)

@sync_to_async
def seriesset():
	series_object = serializers.serialize('json', Series.objects.all(), fields=('pk_series','fk_repository'))

	return (series_object)


@sync_to_async
def collection_printgroup(qcollection, collection_dic):
	#for print group totals (legacy)
	if (qcollection == 30000287):
		printgroupset = Printgroup.objects.annotate(numcases=Count('fk_printgroup', filter=Q(fk_printgroup__fk_sealsealdescription__fk_collection__gte=0))).order_by('printgroup_order')

	else: printgroupset = Printgroup.objects.annotate(numcases=Count('fk_printgroup', filter=Q(fk_printgroup__fk_sealsealdescription__fk_collection=qcollection))).order_by('printgroup_order')

	#for modern group system
	if (qcollection == 30000287):
		groupset = Groupclass.objects.annotate(numcases=Count('id_groupclass', filter=Q(fk_group_class__fk_group__fk_actor_group__fk_sealsealdescription__fk_collection__gte=0))).order_by('id_groupclass')

	else:
		groupset = Groupclass.objects.annotate(numcases=Count('id_groupclass', filter=Q(fk_group_class__fk_group__fk_actor_group__fk_sealsealdescription__fk_collection=qcollection))).order_by('id_groupclass')

	data5 = []
	labels5 = []
	for g in groupset:
		if (g.numcases > 0):
			percentagedata = (g.numcases/collection_dic["totalseals"])*100 
			# if percentagedata > 1:
			data5.append(percentagedata)
			labels5.append(g.groupclass)

	return(data5, labels5)

@sync_to_async
def mapgenerator3(regiondisplayset):

	## data for region map
	# make circles data -- defaults -- note that this code is very similar to the function mapdata2
	mapdic = {"type": "FeatureCollection"}
	properties = {}
	geometry = {}
	location = {}
	regionlist = []

	count = 0

	#for circles
	for r in regiondisplayset:
		if (r['number_cases'] > 0):
			value1 = r['id_regiondisplay']
			value2 = r['regiondisplay_label']
			value3 = r['number_cases']
			value4 = r['regiondisplay_long']
			value5 = r['regiondisplay_lat']

			popupcontent = str(value2)
			if value3 > 0:
				popupcontent = popupcontent + ' ' + str(value3)

			properties = {"id_location": value1, "location": value2, "count": value3, "popupContent": popupcontent}
			geometry = {"type": "Point", "coordinates": [value4, value5]}
			location = {"type": "Feature", "properties": properties, "geometry": geometry}
			regionlist.append(location)

	mapdic["features"] = regionlist

	return(mapdic)


### generate the collection info data for chart-- 'Percentage of seals by class',
@sync_to_async
def datedistribution(qcollection):
	sealset = Seal.objects.values('date_origin')

	if (qcollection == 30000287):
		print ("whole collection")

	else:
		sealset = sealset.filter(fk_sealsealdescription__fk_collection=qcollection)

	eleventhc = 0
	twelfthc = 0
	thirteenthc = 0
	fourteenthc = 0
	fifteenthc = 0
	sixteenthc = 0
	seventeenthc = 0
	eighteenthc = 0
	nineteenthc = 0
	twentiethc = 0

	for s in sealset:
		for date_origin in s.values():
			if date_origin >= 1000 and date_origin <= 1099 : 
				eleventhc = eleventhc + 1
			elif date_origin >= 1100 and date_origin <= 1199 : 
				twelfthc = twelfthc + 1
			elif date_origin >= 1200 and date_origin <= 1299 : 
				thirteenthc = thirteenthc + 1
			elif date_origin >= 1300 and date_origin <= 1399 : 
				fourteenthc = fourteenthc + 1
			elif date_origin >= 1400 and date_origin <= 1499 : 
				fifteenthc = fifteenthc + 1
			elif date_origin >= 1500 and date_origin <= 1599 : 
				sixteenthc = sixteenthc + 1
			elif date_origin >= 1600 and date_origin <= 1699 : 
				seventeenthc = seventeenthc + 1
			elif date_origin >= 1700 and date_origin <= 1799 : 
				eighteenthc = eighteenthc + 1
			elif date_origin >= 1800 and date_origin <= 1899 : 
				nineteenthc = nineteenthc + 1
			elif date_origin >= 1900 and date_origin <= 1999 : 
				twentiethc = twentiethc + 1

		else:
			pass

	data3 = [eleventhc, twelfthc, thirteenthc, fourteenthc, fifteenthc, sixteenthc, seventeenthc, eighteenthc, nineteenthc, twentiethc]
	labels3 = ["11th", "12th", "13th", "14th", "15th", "16th", "17th", "18th", "19th", "20th"]

	return(data3, labels3)




def collection_basemetricsqueries():

	#total number cases that have NOT been assigned to a location (yet) --- 7042 = not assigned --- location status =2 is a secondary location
	casecount = Locationname.objects.exclude(
		pk_locationname=7042).exclude(
		locationreference__fk_locationstatus=2).filter(
		locationreference__fk_event__part__fk_part__fk_support__gt=1)

	place_set = sealdescription_set.exclude(fk_seal__fk_seal_face__manifestation__fk_support__fk_part__fk_event__fk_event_locationreference__fk_locationstatus__isnull=True).exclude(
			fk_seal__fk_seal_face__manifestation__fk_support__fk_part__fk_event__fk_event_locationreference__fk_locationname__fk_location=7042)

	#data for map counties
	placeset = Region.objects.filter(fk_locationtype=4, 
		location__locationname__locationreference__fk_locationstatus=1)

	#data for map regions
	regiondisplayset = Regiondisplay.objects.filter(region__location__locationname__locationreference__fk_locationstatus=1) 

	#faceset = Face.objects.filter(fk_faceterm=1)
	face_set = sealdescription_set.filter(fk_seal__fk_seal_face__fk_faceterm=1).distinct('fk_seal__fk_seal_face') 

	return(sealdescription_set, casecount, place_set, placeset, regiondisplayset, face_set)


def collectiondata(collectionid, sealcount):
	collectiondatapackage = []
	if collectionid == 30000287:
		totalsealdescriptions = Sealdescription.objects.all().count()
	else:
		totalsealdescriptions = Sealdescription.objects.filter(fk_collection=collectionid).values().distinct('sealdescription_identifier').count()

	collectiondatapackage.extend([totalsealdescriptions, sealcount])

	return(collectiondatapackage)


@sync_to_async
def individualsearch(digisig_entity_number=None):
	base_queryset = Individual.objects.select_related(
		'fk_group',
		'fk_descriptor_title',
		'fk_descriptor_name',
		'fk_descriptor_prefix1',
		'fk_descriptor_descriptor1',
		'fk_separator_1',
		'fk_descriptor_prefix2',
		'fk_descriptor_descriptor2',
		'fk_descriptor_prefix3',
		'fk_descriptor_descriptor3',
		'fk_group__fk_group_order',
		'fk_group__fk_group_class'
	).order_by('fk_group__group_name', 'fk_descriptor_name')

	if digisig_entity_number is not None:
		return get_object_or_404(base_queryset, id_individual=digisig_entity_number)
	else:
		return base_queryset.exclude(id_individual=10000019)



def referencecollectindividual(reference_set):
	reference_set = reference_set.select_related(
		'fk_individual__fk_descriptor_title').select_related(
		'fk_individual__fk_descriptor_name').select_related(
		'fk_individual__fk_descriptor_prefix1').select_related(
		'fk_individual__fk_descriptor_descriptor1').select_related(
		'fk_individual__fk_descriptor_prefix2').select_related(
		'fk_individual__fk_descriptor_descriptor2').select_related(
		'fk_individual__fk_descriptor_prefix3').select_related(
		'fk_individual__fk_descriptor_descriptor3').values(
		'fk_individual', 
		'fk_event', 
		'fk_individual__fullname_original',
		'fk_individual__fk_descriptor_name__descriptor_modern',
		'fk_individual__fk_descriptor_prefix1__prefix_english',
		'fk_individual__fk_descriptor_descriptor1__descriptor_modern',
		'fk_individual__fk_descriptor_prefix2__prefix_english',
		'fk_individual__fk_descriptor_descriptor2__descriptor_modern',
		'fk_individual__fk_descriptor_prefix3__prefix_english').order_by('pk_referenceindividual')

	return(reference_set)

## function to collect all the possible information you would need to present a representation
@sync_to_async
def representationmetadata(representation_case):

	representation_dic = {}

	#defaults to stop some forms from breaking
	representation_dic["main_title"] = "Title"
	representation_dic["representation_object"] = representation_case
	representation_dic["id_representation"] = representation_case.id_representation

	#what type of entity is depicted? (Manifestation, Document....)
	digisigentity = representation_case.fk_digisig

	if digisigentity is None:
		digisigentity = representation_case.fk_manifestation.id_manifestation
	if digisigentity is None:
		digisigentity = representation_case.fk_part.id_part
	if digisigentity is None:
		digisigentity = representation_case.fk_sealdescription.id_sealdescription

	digisigentity = str(digisigentity)

	representation_dic["entity_type"] = int(digisigentity[7:])
	
	if int(digisigentity[7:]) == 2: 
		representation_dic["entity_link"] = representation_case.fk_manifestation.id_manifestation
	if int(digisigentity[7:]) == 8:
		representation_dic["entity_link"] = representation_case.fk_part.id_part
	if int(digisigentity[7:]) == 3:
		representation_dic["entity_link"] = representation_case.fk_sealdescription.id_sealdescription

	#what type of image? (Photograph, RTI....)
	representation_dic["representation_type"] = representation_case.fk_representation_type.representation_type

	#where is the image stored?
	connection = representation_case.fk_connection

	if representation_case.fk_representation_type.pk_representation_type == 2:
		print ("found RTI:", representation_case.id_representation)
		representation_dic["rti"] = connection.rti
		representation_dic["representation_folder"] = representation_case.representation_folder
		try:
			thumbnailRTI_object = get_object_or_404(Representation, fk_digisig=representation_case.fk_digisig, primacy=1)
			representation_case = thumbnailRTI_object
		except:
			print ("An exception occurred in fetching representation case for the thumbnail of the RTI", representation_dic)

	#basic info for displaying image
	representation_dic = representation_fetchinfo(representation_dic, representation_case)

	#image dimensions
	representation_dic["width"] = representation_case.width
	representation_dic["height"] = representation_case.height

	#who made it?
	creator_object = representation_case.fk_contributor_creator
	try:
		creator_phrase = creator_object.name_first + " " + creator_object.name_middle + " " + creator_object.name_last
	except:
		try:
			creator_phrase = creator_object.name_first + " " + creator_object.name_last
		except:
			try:
				creator_phrase = creator_object.name_last
			except:
				creator_phrase = "N/A"
	representation_dic["contributorcreator_name"] = creator_phrase.strip()

	#when was it made?
	representation_dic["datecreated"] = representation_case.representation_datecreated

	#where does it come from?
	try:
		representation_dic["collection_fulltitle"] = representation_case.fk_collection.collection_fulltitle
	except:
		print ("no collection")

	#what rights?
	try:
		representation_dic["rightsholder"] = representation_case.fk_rightsholder.rightsholder
	except:
		print ("no rights")

	#what other representations are there of the targetobject?
	representation_objectset = Representation.objects.filter(
		fk_digisig=representation_case.fk_digisig).exclude(
		id_representation=representation_case.id_representation)

	if representation_objectset.count() > 0:
		representation_dic["totalrows"] = representation_objectset.count()
		representation_dic["representation_objectset"] = {} # Initialize the dictionary
		for r_extra in representation_objectset:
			extra_dic = {}
			extra_dic = representation_fetchinfo(extra_dic, r_extra)
			representation_dic["representation_objectset"][r_extra.id_representation] = extra_dic

	return (representation_dic)


@sync_to_async
def representationmetadata_manifestation(manifestation_case, representation_dic):

	manifestation= manifestation_case[0]

	representation_dic["id_seal"] = manifestation['fk_face__fk_seal']
	representation_dic["date_origin"] = manifestation['fk_face__fk_seal__date_origin']
	representation_dic['repository_fulltitle'] = manifestation['fk_support__fk_part__fk_item__fk_repository__repository_fulltitle']
	representation_dic["id_individual"] = manifestation['fk_face__fk_seal__fk_individual_realizer']

	# sealdescription_objectset = Sealdescription.objects.select_related('fk_collection').filter(fk_seal = seal.id_seal)
	# representation_dic["sealdescription_objectset"] = sealdescription_objectset

	return(representation_dic)

@sync_to_async
def representationmetadata_partquery(searchvalue, representation_dic):

	part_case = Part.objects.values(
		'fk_item',
		'fk_item__fk_repository__repository_fulltitle',
		'fk_item__shelfmark',
		'id_part',
		'fk_event',
		'fk_event__repository_startdate',
		'fk_event__repository_enddate',
		'fk_event__startdate',
		'fk_event__enddate',
		'fk_event__fk_dateapprox_repository_start__approximation_temporal',
		'fk_event__fk_dateapprox_repository_end__approximation_temporal'
		).get(id_part=searchvalue)

	representation_dic["id_item"] = part_case['fk_item']
	representation_dic["main_title"] =  part_case['fk_item__fk_repository__repository_fulltitle'] + " " + str(part_case['fk_item__shelfmark'])
	representation_dic["repository_fulltitle"] = part_case['fk_item__fk_repository__repository_fulltitle']
	representation_dic["shelfmark"] = part_case['fk_item__shelfmark']

	representation_dic["object_startdate"] = part_case['fk_event__startdate'] if part_case['fk_event__startdate'] else None
	representation_dic["object_enddate"] = part_case['fk_event__enddate'] if part_case['fk_event__enddate'] else None
	representation_dic["object_startdate_repository"] = part_case['fk_event__repository_startdate'] if part_case['fk_event__repository_startdate'] else None
	representation_dic["object_enddate_repository"] = part_case['fk_event__repository_enddate'] if part_case['fk_event__repository_enddate'] else None

	representation_dic["object_startdate_repository_approx"] = part_case['fk_event__fk_dateapprox_repository_start__approximation_temporal']
	representation_dic["object_enddate_repository_approx"] = part_case['fk_event__fk_dateapprox_repository_end__approximation_temporal']

	event = int(part_case['fk_event'])

	region_objectset = Region.objects.filter( 
		location__locationname__locationreference__fk_locationstatus=1, 
		location__locationname__locationreference__fk_event=event).values('region_label').first()
	representation_dic["region_label"] = region_objectset['region_label']

	return(representation_dic)


@sync_to_async
def representationmetadata_part(manifestation_case, representation_dic):

	manifestation_case = manifestation_case[0]

	representation_dic["id_item"] = manifestation_case['fk_support__fk_part__fk_item']
	representation_dic["main_title"] =  manifestation_case['fk_support__fk_part__fk_item__fk_repository__repository_fulltitle'] + " " + str(manifestation_case['fk_support__fk_part__fk_item__shelfmark'])
	representation_dic["repository_fulltitle"] = manifestation_case['fk_support__fk_part__fk_item__fk_repository__repository_fulltitle']
	representation_dic["shelfmark"] = manifestation_case['fk_support__fk_part__fk_item__shelfmark']

	representation_dic["object_startdate"] = manifestation_case['fk_support__fk_part__fk_event__startdate'] if manifestation_case['fk_support__fk_part__fk_event__startdate'] else None
	representation_dic["object_enddate"] = manifestation_case['fk_support__fk_part__fk_event__enddate'] if manifestation_case['fk_support__fk_part__fk_event__enddate'] else None
	representation_dic["object_startdate_repository"] = manifestation_case['fk_support__fk_part__fk_event__repository_startdate'] if manifestation_case['fk_support__fk_part__fk_event__repository_startdate'] else None
	representation_dic["object_enddate_repository"] = manifestation_case['fk_support__fk_part__fk_event__repository_enddate'] if manifestation_case['fk_support__fk_part__fk_event__repository_enddate'] else None

	representation_dic["object_startdate_repository_approx"] = manifestation_case['fk_support__fk_part__fk_event__fk_dateapprox_repository_start__approximation_temporal']
	representation_dic["object_enddate_repository_approx"] = manifestation_case['fk_support__fk_part__fk_event__fk_dateapprox_repository_end__approximation_temporal']

	event = int(manifestation_case['fk_support__fk_part__fk_event'])

	region_objectset = Region.objects.filter( 
		location__locationname__locationreference__fk_locationstatus=1, 
		location__locationname__locationreference__fk_event=event).values('region_label').first()
	if region_objectset is not None:
		representation_dic["region_label"] = region_objectset['region_label']
	else:
		# Handle the case where region_objectset is None
		representation_dic["region_label"] = None  # Or some other default value
		print("Warning: region_objectset is None, setting region_label to None.")


	# representation_dic["region_label"] = region_objectset['region_label']

	return(representation_dic)

@sync_to_async
def representationmetadata_sealdescription(representation_case, representation_dic):

	#Seal Description
	if representation_dic["entity_type"] == 3:
		representation_dic["main_title"] = "Seal Description"

	return(representation_dic)


@sync_to_async
def itemform_options(form):

	series_all_options = [('', 'None')]
	repositories_all_options = [('', 'None')]

	series_set = Series.objects.exclude(
		series_name__istartswith="z").order_by(
		'fk_repository').select_related('fk_repository_id').values(
		'pk_series', 
		'series_name', 
		'fk_repository', 
		'fk_repository_id__repository_fulltitle',
		'fk_repository_id__repository')

	for s in series_set:
		appendvalue = s['fk_repository_id__repository'] + " : " + s['series_name']
		series_all_options.append((s['pk_series'], appendvalue))
		entry = (s['fk_repository'], s['fk_repository_id__repository_fulltitle'])
		if entry not in repositories_all_options:
			repositories_all_options.append(entry)  
				
	form.fields['series'].choices = series_all_options
	form.fields['repository'].choices = repositories_all_options

	return (form)

@sync_to_async
def itemsearch():

	item_object = Item.objects.all().order_by(
	"fk_repository", "fk_series", "classmark_number3", "classmark_number2", "classmark_number1").select_related(
	'fk_repository')

	return (item_object)

@sync_to_async
def itemsearchfilter(item_object, form):

	try:
		qrepository = int(form.cleaned_data['repository'])
		if qrepository > 0:
			item_object = item_object.filter(fk_repository=qrepository)
	except: 
		pass
	
	try:        
		qseries = int(form.cleaned_data['series'])
		if qseries > 0:
			item_object = item_object.filter(fk_series=qseries)
	except: 
		pass
	
	try:
		qshelfmark = form.cleaned_data['shelfmark']
		if len(qshelfmark) > 0:
			item_object = item_object.filter(shelfmark__icontains=qshelfmark)
	except: 
		pass

	try:
		qsearchphrase = form.cleaned_data['searchphrase']
		if len(searchphrase) > 0:
			item_object = item_object.filter(part_description__icontains=searchphrase)
	except: 
		pass

	try:
		qpagination = int(form.cleaned_data['pagination'])
	except: 
		qpagination = 1

	return (item_object, qpagination)


@sync_to_async
def item_displaysetgenerate(item_pageobject):

	# Items can have multiple parts and each part can have a photograph
	
	listofitems = [] # for finding related records
	item_set = {}

	for i in item_pageobject:
		item_dic = {}
		item_dic["id_item"] = i.id_item
		item_dic["shelfmark"] = i.shelfmark
		item_dic["repository"] = i.fk_repository.repository_fulltitle
		item_dic["part"] = {}

		item_set.update({i.id_item: item_dic})
		listofitems.append(i.id_item)

	part_object = Part.objects.filter(fk_item__in=listofitems).select_related('fk_item')

	for p in part_object:
		part_dic = {}
		part_dic['id_part'] = p.id_part

		item_set[p.fk_item.id_item]["part"].update({p.id_part: part_dic})

	representation_part = Representation.objects.filter(
		fk_part__fk_item__in=listofitems).select_related(
		'fk_connection').values(
		'representation_thumbnail_hash',
		'id_representation',
		'representation_filename',
		'fk_connection__thumb',
		'fk_part',
		'fk_part__fk_item',
		'id_representation')

	for r in representation_part:
		representation_dic = {}
		targetpart = r['fk_part']
		targetitem = r['fk_part__fk_item']

		representation_dic["connection"] = r['fk_connection__thumb']
		representation_dic["medium"] = r['representation_filename']
		representation_dic["thumb"] = r['representation_thumbnail_hash']
		representation_dic["id_representation"] = r['id_representation'] 
		item_set[targetitem]["part"][targetpart].update({"representation": representation_dic})


	return(item_set)

@sync_to_async
def placeform_options(form):

	county_options = [('0', 'None')]
	region_options = [('0', 'None')]

	for e in Region.objects.filter(location__isnull=False).filter(fk_locationtype=4).order_by('region_label').distinct('region_label'):
		county_options.append((e.pk_region, e.region_label))

	for e in Regiondisplay.objects.filter(region__location__isnull=False).order_by('regiondisplay_label').distinct('regiondisplay_label'):
		region_options.append((e.id_regiondisplay, e.regiondisplay_label))

	form.fields['county'].choices = county_options
	form.fields['region'].choices = region_options

	return(form)

@sync_to_async
def place_search():
## many places
	place_object = Location.objects.filter(
		locationname__locationreference__fk_locationstatus=1, longitude__isnull=False, latitude__isnull=False).order_by(
		'location').annotate(count=Count('locationname__locationreference'))

	return (place_object)

## Information about one place
@sync_to_async
def place_information(entity):

	place_object = get_object_or_404(Location, id_location=entity)

	place_name = str(place_object.location)

	return (place_object, place_name)


@sync_to_async
def placesearchfilter(placeset):

	qregion = form.cleaned_data['region']
	qcounty = form.cleaned_data['county']   
	qpagination = form.cleaned_data['pagination']
	qlocation_name = form.cleaned_data['location_name']

	if qregion.isdigit():
		if int(qregion) > 0:
			placeset = placeset.filter(fk_region__fk_regiondisplay=qregion)
			regionselect = True

	if regionselect == False:
		if qcounty.isdigit():
			if int(qcounty) > 0:
				placeset = placeset.filter(fk_region=qcounty)

	if len(qlocation_name) > 0:
		placeset = placeset.filter(location__icontains=qlocation_name)

	if qpagination < 1: qapgination =1 

	return (placeset, qpagination)

@sync_to_async
def placeobjectannotate(place_object):

	place_object.annotate(count=Count('locationname__locationreference'))

	totalcount = 1
	for p in place_object:
		if totalcount < 10:
			print (p, p.count)
			totalcount = totalcount + 1 

	return (place_object)

@sync_to_async
def dateform_options(form):

	shape_options = [('', 'None')]
	classname_options = [('', 'None')]

	for e in Shape.objects.order_by('shape').distinct('shape'):
			shape_options.append((e.pk_shape, e.shape))

	for e in Terminology.objects.filter(term_type=1).order_by('term_name').distinct('term_name'):
		classname_options.append((e.id_term, e.term_name))

	form.fields['shape'].choices = shape_options
	form.fields['classname'].choices = classname_options

	return (form)

@sync_to_async
def datesearchfilter(form):

	qclass = form.cleaned_data['classname']
	qshape = form.cleaned_data['shape'] 
	qvertical = form.cleaned_data['face_vertical']
	qhorizontal = form.cleaned_data['face_horizontal']

	if qclass.isdigit():
		if int(qclass) > 0:
			qclass = int(qclass)
			class_object = get_object_or_404(Classification, id_class=qclass)

	if qshape.isdigit():
		qshape = int(qshape)
		if int(qshape) > 0:
			qshape = int(qshape)
			shape_object = get_object_or_404(Shape, pk_shape=qshape)

	if qvertical > 0:
		if qhorizontal > 0:
			resultarea = faceupdater(qshape, qvertical, qhorizontal)

	return(shape_object, class_object, resultarea)


@sync_to_async
def manifestationsform_options(form):

	#repositories_options = [('','None')]
	#series_options = [('', 'None')]
	location_options = [('', 'None')]
	nature_options = [('', 'None')]
	representation_options = [('', 'None')]
	timegroup_options = [('', 'None')]
	shape_options = [('', 'None')]
	classname_options = [('', 'None')]
	group_options = [('', 'None')]

	# for e in Repository.objects.order_by('repository_fulltitle'):
	# 	repositories_options.append((e.fk_repository, e.repository_fulltitle))

	# for e in Series.objects.select_related('fk_repository').order_by('series_name').distinct('series_name'):
	# 	appendvalue = str(e.fk_repository) + " : " + e.series_name
	# 	series_options.append((e.pk_series, appendvalue))

	for e in Region.objects.order_by('region_label').distinct('region_label'):
		location_options.append((e.pk_region, e.region_label))

	for e in Nature.objects.order_by('nature_name').distinct('nature_name'):
		nature_options.append((e.pk_nature, e.nature_name))

	for e in RepresentationType.objects.order_by('representation_type').distinct('representation_type').exclude(pk_representation_type=5):
		representation_options.append((e.pk_representation_type, e.representation_type))
		
	for e in TimegroupC.objects.order_by('pk_timegroup_c'):
		timegroup_options.append((e.timegroup_c, e.timegroup_c_range))

	for e in Shape.objects.order_by('shape').distinct('shape'):
		shape_options.append((e.pk_shape, e.shape))

	for e in Terminology.objects.filter(term_type=1).order_by('term_name').distinct('term_name'):
		classname_options.append((e.id_term, e.term_name))

	for e in Printgroup.objects.order_by('printgroup_order'):
		group_options.append((e.pk_printgroup, e.printgroup))

	# form.fields['repository'].choices = repositories_options
	# form.fields['series'].choices = series_options  
	form.fields['location'].choices = location_options
	form.fields['nature'].choices = nature_options
	form.fields['representation'].choices = representation_options
	form.fields['timegroup'].choices = timegroup_options
	form.fields['shape'].choices = shape_options
	form.fields['classname'].choices = classname_options
	form.fields['group'].choices = group_options 

	return (form)

@sync_to_async
def peopleform_options(form):

	#Form for Actor search

	Choices = [('0', 'None'), ('1', 'Individual'), ('2', 'Corporate')]
	personclass_options = []
	personorder_options = []

	for e in Groupclass.objects.order_by('groupclass'):
		personclass_options.append((e.fk_group_class, e.groupclass))

	for e in Grouporder.objects.order_by('grouporder'):
		personorder_options.append((e.fk_group_order, e.grouporder))

	form.fields['group'].choices = Choices
	form.fields['personclass'].choices = personclass_options
	form.fields['personorder'].choices = personorder_options 

	return(form)


@sync_to_async
def sealdescriptionform_options(form):

	collections_options = [('30000287', 'All Collections')]

	for e in Collection.objects.order_by('collection_shorttitle').annotate(numdescriptions=Count('sealdescription')):
		if (e.numdescriptions > 0):
			collections_options.append((e.id_collection, e.collection_shorttitle))

	form.fields['collection'].choices = collections_options

	return(form)

@sync_to_async
def sealdescription_search():
	sealdescription_objects = Sealdescription.objects.all().select_related(
		'fk_collection').select_related('fk_seal__fk_individual_realizer').select_related(
		'fk_seal').order_by(
		'id_sealdescription')

	return(sealdescription_objects)

@sync_to_async
def sealdescriptionsearchfilter(sealdescription_object, form):

	qcollection = form.cleaned_data['collection']   
	qcataloguecode = form.cleaned_data['cataloguecode']
	qcataloguemotif = form.cleaned_data['cataloguemotif']
	qcataloguename = form.cleaned_data['cataloguename']
	qpagination = form.cleaned_data['pagination']

	if qcollection.isdigit():
		if int(qcollection) > 0:
			if int(qcollection) == 30000287:
				print("all collections")
			else: sealdescription_object = sealdescription_object.filter(fk_collection=qcollection)
			
	if len(qcataloguecode) > 0:
		sealdescription_object = sealdescription_object.filter(sealdescription_identifier__icontains=qcataloguecode)

	if len(qcataloguemotif) > 0:
		sealdescription_object = sealdescription_object.filter(
			Q(motif_obverse__contains=qcataloguemotif) | Q(motif_reverse__icontains=qcataloguemotif)
			)

	if len(qcataloguename) > 0:
		sealdescription_object = sealdescription_object.filter(sealdescription_title__icontains=qcataloguename)

	if qpagination < 1: qapgination =1 

	return(sealdescription_object, qpagination)

@sync_to_async
def sealdescription_displaysetgenerate(sealdescription_object):

	sealdescription_displayset = {}
	for sd in sealdescription_object:
		sealdes_temp = {}
		sealdes_temp['id_sealdescription'] = sd.id_sealdescription
		sealdes_temp['fk_seal'] = sd.fk_seal.id_seal
		sealdes_temp['sealdescription_title'] = sd.sealdescription_title
		sealdes_temp['collection_shorttitle'] = sd.fk_collection.collection_shorttitle
		sealdes_temp['sealdescription_identifier'] = sd.sealdescription_identifier
		sealdes_temp['catalogue_pagenumber'] = sd.catalogue_pagenumber
		sealdes_temp['motif_reverse'] = sd.motif_reverse
		sealdes_temp['motif_obverse'] = sd.motif_obverse
		sealdes_temp['legend_obverse'] = sd.legend_obverse
		sealdes_temp['legend_reverse'] = sd.legend_reverse
		sealdes_temp['realizer'] = sd.fk_seal.fk_individual_realizer
		#sealdes_temp['collection_thumbnail'] = sd.collection_thumbnail
		#sealdes_temp['collection_fulltitle'] = sd.collection_fulltitle
		sealdes_temp['fk_collection'] = sd.fk_collection

		sealdescription_displayset[sd.id_sealdescription] = sealdes_temp

	return (sealdescription_displayset)


# @sync_to_async
# def manifestation_search():
#   manifestation_object = Manifestation.objects.all().select_related(
#   'fk_face__fk_seal').select_related(
#   'fk_support__fk_part__fk_item__fk_repository').select_related(
#   'fk_support__fk_number_currentposition').select_related(
#   'fk_support__fk_attachment').select_related(
#   'fk_support__fk_supportstatus').select_related(
#   'fk_support__fk_nature').select_related(
#   'fk_imagestate').select_related(
#   'fk_position').select_related(
#   'fk_support__fk_part__fk_event').order_by(
#   'id_manifestation').prefetch_related(
#   Prefetch('fk_manifestation', queryset=Representation.objects.filter(primacy=1)))

#   return(manifestation_object)


## find seal manifestations and optionally limit to those associated with a particular place
@sync_to_async
def manifestation_search(digisig_entity_number=None, placecall=False):
	manifestation_object = Manifestation.objects.all().select_related(
		'fk_face__fk_seal',
		'fk_support__fk_part__fk_item__fk_repository',
		'fk_support__fk_number_currentposition',
		'fk_support__fk_attachment',
		'fk_support__fk_supportstatus',
		'fk_support__fk_nature',
		'fk_imagestate',
		'fk_position',
		'fk_support__fk_part__fk_event'
	).order_by('id_manifestation').prefetch_related(
		Prefetch('fk_manifestation', queryset=Representation.objects.filter(primacy=1))
	)

	if placecall is True:
		manifestation_object = manifestation_object.filter(
			fk_support__fk_part__fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location=digisig_entity_number
		).distinct()

	return (manifestation_object)




@sync_to_async
def manifestation_search_all():
	manifestation_object = Manifestation.objects.all().values('id_manifestation').order_by('id_manifestation')

	return(manifestation_object)

@sync_to_async
def sealsearch3(sealentity):
	manifestation_object = Manifestation.objects.filter(fk_face__fk_seal=sealentity).values('id_manifestation').order_by('id_manifestation')

	return(manifestation_object)

@sync_to_async
def sealsearch_actor(seal_object, digisig_entity_number):
	#assumes you will have run manifestation_search() first and now want to further limit based on the actor in question

	manifestation_set = seal_object.filter(
		Q(fk_face__fk_seal__fk_individual_realizer=digisig_entity_number) | Q(fk_face__fk_seal__fk_actor_group=digisig_entity_number)
	). order_by('fk_face__fk_seal__fk_individual_realizer')

	return(manifestation_set)

@sync_to_async
def representation_queryformulate(digisig_entity_number):

	representation_object = Representation.objects.select_related(
		'fk_manifestation').select_related(
		'fk_representation_type').select_related(
		'fk_connection').select_related(
		'fk_contributor_creator').select_related(
		'fk_manifestation__fk_support__fk_part__fk_item__fk_repository').select_related(
		'fk_manifestation__fk_support__fk_part__fk_event').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_group').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_descriptor_title').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_descriptor_name').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_descriptor_prefix1').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_descriptor_descriptor1').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_separator_1').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_descriptor_prefix2').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_descriptor_descriptor2').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_descriptor_prefix3').select_related(
		'fk_manifestation__fk_face__fk_seal__fk_individual_realizer__fk_descriptor_descriptor3').get(
		id_representation=digisig_entity_number)

	return (representation_object)




@sync_to_async
def representationsetgenerate(manifestation_pageobject):

	representation_set = Representation.objects.filter(
		fk_manifestation__in=manifestation_pageobject.object_list).filter(
		primacy=1).values('representation_thumbnail_hash', 
		'representation_filename_hash', 
		'id_representation',
		'fk_manifestation',
		'fk_connection__thumb',
		'fk_connection__medium') 

	return(representation_set)


### this works without running through paginator
@sync_to_async
def representationsetgenerate2(manifestation_object, primacy=False):

	listofmanifestations = []
	for m in manifestation_object:
		listofmanifestations.append(m['id_manifestation'])

	representation_values = [
		'representation_thumbnail_hash',
		'representation_filename_hash',
		'id_representation',
		'fk_digisig',
		'fk_manifestation',
		'fk_part',
		'fk_sealdescription',
		'fk_connection__thumb',
		'fk_connection__medium',
		'fk_representation_type'
	]

	# Build the base queryset
	representation_queryset = Representation.objects.filter(
		fk_manifestation__in=listofmanifestations
	).values(*representation_values)

	# Add the primacy filter if needed
	if primacy:
		representation_set = representation_queryset.filter(primacy=1)
	else:
		representation_set = representation_queryset

	# Fallback if the queryset is empty
	if not representation_set.exists():
		return Representation.objects.none() # Returns an empty queryset

	return representation_set




# note this does not require the synctoasync
async def manifestation_dataassemble(manifestation_pageobject):

	manifestation_set = await manifestation_searchsetgenerate(manifestation_pageobject)
	representation_set = await representationsetgenerate(manifestation_pageobject)
	manifestation_display_dic, description_set, listofseals, listofevents = await manifestation_displaysetgenerate(manifestation_set, representation_set)
	description_set = await sealdescription_displaysetgenerate2(listofseals, description_set)
	location_set = await location_displaysetgenerate(listofevents)
	manifestation_displayset = await finalassembly_displaysetgenerate(manifestation_display_dic, location_set, description_set)

	return (manifestation_displayset)


@sync_to_async
def seal_displaysetgenerate(manifestation_display_dic, description_set, digisig_entity_number, name_set):

	seal_info = {}
	seal_info['sealdescription'] = description_set

	obverse = {}
	reverse = {}

	face_set = Face.objects.filter(
		fk_seal=digisig_entity_number).select_related(
		'fk_class',
		'fk_seal',
		'fk_faceterm').values(
		'fk_seal__date_origin',
		'fk_faceterm__faceterm',
		'fk_seal__date_origin',
		'fk_seal__fk_individual_realizer',
		'fk_class')

	for f in face_set:
		if f['fk_faceterm__faceterm'] == "Obverse":         
			obverse['faceterm'] = f['fk_faceterm__faceterm']
			obverse['fk_class'] = f['fk_class']
		if f['fk_faceterm__faceterm'] == "Reverse":         
			reverse['faceterm'] = f['fk_faceterm__faceterm']
			reverse['fk_class'] = f['fk_class']

		seal_info['date_origin'] = f['fk_seal__date_origin']
		seal_info['id_individual'] = f['fk_seal__fk_individual_realizer']
		seal_info['actorname'] = name_set[f['fk_seal__fk_individual_realizer']]

	seal_info['manifestation_set'] = manifestation_display_dic
	seal_info['obverse'] = obverse
	seal_info['reverse'] = reverse
	
	return (seal_info)


@sync_to_async
def manifestation_searchsetgenerate(searchvalue, searchtype=None):
	# a single manifestation
	if searchtype == "manifestation":
		manifestation_set = Manifestation.objects.filter(id_manifestation=searchvalue)

	# a group of seal manifestations (either based on seal or manifestation set)
	elif searchtype == "seal":
		manifestation_set = Manifestation.objects.filter(fk_face__fk_seal=searchvalue)      
	
	# a set of seal manifestations taken from the paginator function
	else:
		manifestation_set = Manifestation.objects.filter(id_manifestation__in=searchvalue.object_list)

	manifestation_out = manifestation_set.select_related(
		'fk_support__fk_part__fk_item__fk_repository',
		'fk_support__fk_number_currentposition',
		'fk_support__fk_attachment',
		'fk_support__fk_supportstatus',
		'fk_support__fk_nature',
		'fk_imagestate',
		'fk_position',
		'fk_support__fk_part__fk_event',
		'fk_support__fk_part__fk_event__fk_dateapprox_repository_start',
		'fk_support__fk_part__fk_event__fk_dateapprox_repository_end',
		'fk_face__fk_seal'
	).order_by('id_manifestation').values(
		'id_manifestation',
		'fk_support',
		'fk_position',
		'fk_face',
		'fk_face__fk_seal',
		'fk_face__fk_seal__date_origin',
		'fk_face__fk_seal__fk_individual_realizer',
		'fk_support__fk_part__fk_item',
		'fk_support__fk_part__fk_item__fk_repository__repository_fulltitle',
		'fk_support__fk_part__fk_item__shelfmark',
		'fk_support__fk_supportstatus',
		'fk_support__fk_attachment',
		'fk_support__fk_attachment__attachment',
		'fk_support__fk_number_currentposition',
		'fk_support__fk_number_currentposition__number',
		'fk_support__fk_nature',
		'label_manifestation_repository',
		'fk_imagestate',
		'fk_support__fk_part',
		'fk_support__fk_part__fk_event',
		'fk_support__fk_part__fk_event__repository_startdate',
		'fk_support__fk_part__fk_event__repository_enddate',
		'fk_support__fk_part__fk_event__startdate',
		'fk_support__fk_part__fk_event__enddate',
		'fk_support__fk_part__fk_event__fk_dateapprox_repository_start__approximation_temporal',
		'fk_support__fk_part__fk_event__fk_dateapprox_repository_end__approximation_temporal'
	)

	totalmanifestation_count = manifestation_set.count()

	return (manifestation_out, totalmanifestation_count)


@sync_to_async
def manifestation_displaysetgenerate(manifestation_set, representation_set):
### maindata for manifestations

	manifestation_display_dic = {}
	listofseals = []
	listofevents = []
	listofactors = []
	description_set = {}

	#the default fallback
	r_set = Representation.objects.values('fk_connection__thumb',
		'fk_connection__medium',
		'representation_thumbnail_hash',
		'representation_filename_hash',
		'id_representation').get(id_representation=12204474)

	for e in manifestation_set:
		manifestation_dic = {}
		manifestation_dic["id_manifestation"] = e['id_manifestation']
		manifestation_dic["fk_support"] = e['fk_support']
		manifestation_dic["fk_position"] = e['fk_position']
		manifestation_dic["id_seal"] = e['fk_face__fk_seal']
		manifestation_dic['id_individual'] = e['fk_face__fk_seal__fk_individual_realizer']
		#manifestation_dic['outname'] = namecompiler(e['fk_face__fk_seal__fk_individual_realizer'])
		manifestation_dic["id_item"] = e['fk_support__fk_part__fk_item']
		manifestation_dic["fk_event"] = e['fk_support__fk_part__fk_event']
		manifestation_dic["repository_fulltitle"] = e['fk_support__fk_part__fk_item__fk_repository__repository_fulltitle']
		manifestation_dic["shelfmark"] = e['fk_support__fk_part__fk_item__shelfmark']
		manifestation_dic["fk_supportstatus"] = e['fk_support__fk_supportstatus']
		manifestation_dic["fk_attachment"] = e['fk_support__fk_attachment']
		manifestation_dic["attachment"] = e['fk_support__fk_attachment__attachment'] 
		manifestation_dic["number"] = e['fk_support__fk_number_currentposition__number']
		manifestation_dic["support_type"] = e['fk_support__fk_nature']
		manifestation_dic["label_manifestation_repository"] = e['label_manifestation_repository']
		
		#Adding these values through logic seems to dramatically decrease the query run time as compared to DBS query
		if e['fk_imagestate'] == 2:
			manifestation_dic["imagestate_term"] = "Seal matrix"
		else:   
			manifestation_dic["imagestate_term"] = "Seal impression"

		manifestation_dic["partvalue"] = e['fk_support__fk_part']
		manifestation_dic["repository_startdate"] = e['fk_support__fk_part__fk_event__repository_startdate']
		manifestation_dic["repository_enddate"] = e['fk_support__fk_part__fk_event__repository_startdate']
		manifestation_dic["startdate"] = e['fk_support__fk_part__fk_event__startdate']
		manifestation_dic["enddate"] = e['fk_support__fk_part__fk_event__enddate']

		## installing default image details
		manifestation_dic["thumb"] = r_set['fk_connection__thumb']
		manifestation_dic["medium"] = r_set['fk_connection__medium']
		manifestation_dic["representation_thumbnail_hash"] = r_set['representation_thumbnail_hash']
		manifestation_dic["representation_filename_hash"] = r_set['representation_filename_hash']
		manifestation_dic["id_representation"] = r_set['id_representation']

		#test to see if a better image available
		for r in representation_set:
			if r['fk_manifestation'] == manifestation_dic["id_manifestation"]:
				manifestation_dic["thumb"] = r['fk_connection__thumb']
				manifestation_dic["medium"] = r['fk_connection__medium']
				manifestation_dic["representation_thumbnail_hash"] = r['representation_thumbnail_hash']
				manifestation_dic["representation_filename_hash"] = r['representation_filename_hash']
				manifestation_dic["id_representation"] = r['id_representation']
					
		manifestation_display_dic[e['id_manifestation']] = manifestation_dic
		listofseals.append(e['fk_face__fk_seal'])
		listofevents.append(e['fk_support__fk_part__fk_event'])
		listofactors.append(e['fk_face__fk_seal__fk_individual_realizer'])

	return(manifestation_display_dic, listofseals, listofevents, listofactors)


@sync_to_async
def sealdescription_displaysetgenerate2(listofseals):

## gather the sealdescription references
	sealdescription_set = Sealdescription.objects.filter(
		fk_seal__in=listofseals).values(
		'id_sealdescription',
		'fk_collection__collection_shorttitle',
		'sealdescription_identifier',
		'fk_seal')

	seal_set = {}

	for l in listofseals:
		seal_set[l] = {}

	for s in sealdescription_set:
		description = {}
		description["sealdescription_id"] = s['id_sealdescription']
		description["collection"] = s['fk_collection__collection_shorttitle']
		description["identifier"] = s['sealdescription_identifier']
		sealvalue = s['fk_seal']
		description["fk_seal"] = sealvalue

		seal_set[sealvalue][s['id_sealdescription']] = description

	return(seal_set)

@sync_to_async
def location_displaysetgenerate(listofevents):

##gather the location references
	locationreference_set = Locationreference.objects.filter(
		fk_event__in=listofevents,fk_locationstatus=1).values(
		'fk_locationname', 
		'fk_locationname__fk_location', 
		'fk_locationname__fk_location__location',
		'fk_locationname__fk_location__id_location',
		'fk_event')

	location_set = {}

	for l in locationreference_set:
		location = {}
		location["locationname"] = l['fk_locationname']
		location["location"] = l['fk_locationname__fk_location']
		location["repository_location"] = l['fk_locationname__fk_location__location']
		location["id_location"] = l['fk_locationname__fk_location__id_location']

		location_set[l['fk_event']] = location

	return(location_set)

@sync_to_async
def finalassembly_displaysetgenerate(manifestation_display_dic, location_set, description_set):
### final assembly

	for key, m in manifestation_display_dic.items():
		m["sealdescription"] = description_set[m["id_seal"]]
		m["locationname"] = location_set[m['fk_event']]["locationname"]
		m["location"] = location_set[m['fk_event']]['location']
		m["repository_location"] = location_set[m['fk_event']]['repository_location']
		m["id_location"] = location_set[m['fk_event']]['id_location']

	return(manifestation_display_dic)


async def manifestation_construction(manifestation_pageobject):
	"""
	Function prepares the data for the seal search (manifestation) page
	"""
	representation_set = await representationsetgenerate(manifestation_pageobject)
	manifestation_set, totalmanifestation_count = await manifestation_searchsetgenerate(manifestation_pageobject)
	manifestation_display_dic, listofseals, listofevents, listofactors = await manifestation_displaysetgenerate(manifestation_set, representation_set)
	description_set = await sealdescription_displaysetgenerate2(listofseals)
	location_set = await location_displaysetgenerate(listofevents)
	manifestation_displayset = await finalassembly_displaysetgenerate(manifestation_display_dic, location_set, description_set)

	return manifestation_displayset


@sync_to_async
def sealsearchfilter(manifestation_object, form):
	qrepository = form.cleaned_data['repository']   
	qseries = form.cleaned_data['series']
	qrepresentation_type = form.cleaned_data['representation']
	qnature = form.cleaned_data['nature']
	qlocation = form.cleaned_data['location']
	qtimegroup = form.cleaned_data['timegroup']
	qshape = form.cleaned_data['shape']
	qshelfmark = form.cleaned_data['name']
	qclassname = form.cleaned_data['classname']
	qpagination = form.cleaned_data['pagination']
	qgroup = form.cleaned_data['group']

	if qrepository.isdigit():
		if int(qrepository) > 0:
			manifestation_object = manifestation_object.filter(
				fk_support__fk_part__fk_item__fk_repository=qrepository)

	if qseries.isdigit():
		if int(qseries) > 0:
			manifestation_object = manifestation_object.filter(
				fk_support__fk_part__fk_item__fk_series=qseries)

	if qrepresentation_type.isdigit():
		if int(qrepresentation_type) > 0:
			manifestation_object = manifestation_object.filter(
				fk_manifestation__fk_representation_type=qrepresentation_type)

	if qnature.isdigit():
		if int(qnature) > 0:
			manifestation_object = manifestation_object.filter(
				fk_support__fk_nature=qnature)

	if qlocation.isdigit():
		if int(qlocation) > 0:
			manifestation_object = manifestation_object.filter(
				fk_support__fk_part__fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region=qlocation)

	if qtimegroup.isdigit():
		if int(qtimegroup) > 0:
			qtimegroup_int = int(qtimegroup)
			temporalperiod_target = (TimegroupC.objects.get(timegroup_c = qtimegroup_int))   
			yearstart = (temporalperiod_target.timegroup_c_startdate)
			yearend = (temporalperiod_target.timegroup_c_finaldate)
			# manifestation_object = manifestation_object.filter(
			# 	fk_support__fk_part__fk_event__repository_startdate__lt=datetime.strptime(str(yearstart), "%Y")).filter(
			# 	fk_support__fk_part__fk_event__repository_enddate__gt=datetime.strptime(str(yearstart+50), "%Y"))
			manifestation_object = manifestation_object.filter(
				fk_support__fk_part__fk_event__startdate__lt=datetime.strptime(str(yearend), "%Y")).filter(
				fk_support__fk_part__fk_event__enddate__gt=datetime.strptime(str(yearstart), "%Y"))




	if qshape.isdigit():
		if int(qshape) > 0:
			manifestation_object = manifestation_object.filter(
				fk_face__fk_shape=qshape)

	if qgroup.isdigit():
		if int(qgroup) > 0:
			manifestation_object = manifestation_object.filter(
				fk_face__fk_seal__fk_printgroup=qgroup)

	if qclassname.isdigit():
		if int(qclassname) > 0:
			searchclassification =  Classification.objects.get(id_class = qclassname)
			manifestation_object = manifestation_object.filter(
				fk_face__fk_class__level1=searchclassification.level1)

			if searchclassification.level2 > 0:
				manifestation_object = manifestation_object.filter(
				fk_face__fk_class__level2=searchclassification.level2)

				if searchclassification.level3 > 0:
					manifestation_object = manifestation_object.filter(
					fk_face__fk_class__level3=searchclassification.level3)

					if searchclassification.level4 > 0:
						manifestation_object = manifestation_object.filter(
						fk_face__fk_class__level4=searchclassification.level4)

						if searchclassification.level5 > 0:
							manifestation_object = manifestation_object.filter(
							fk_face__fk_class__level5=searchclassification.level5)

							if searchclassification.level6 > 0:
								manifestation_object = manifestation_object.filter(
								fk_face__fk_class__level6=searchclassification.level6)

								if searchclassification.level7 > 0:
									manifestation_object = manifestation_object.filter(
									fk_face__fk_class__level7=searchclassification.level7)

	if len(qshelfmark) > 0:
		manifestation_object = manifestation_object.filter(
		fk_support__fk_part__fk_item__shelfmark__icontains=qshelfmark)

	if qpagination < 1: qapgination =1 

	return(manifestation_object, qpagination)

@sync_to_async
def defaultpagination(pagination_object, qpagination):

	pagination_object = Paginator(pagination_object, 10).page(qpagination)
	totalrows = pagination_object.paginator.count
	totaldisplay = str(pagination_object.start_index()) + "-" + str(pagination_object.end_index())

	return(pagination_object, totalrows, totaldisplay)

@sync_to_async
def sealdescription_fetchobject(digisig_entity_number):
	sealdescription_object = Sealdescription.objects.select_related(
		'fk_collection').select_related(
		'fk_seal').get(
		id_sealdescription=digisig_entity_number)

	return (sealdescription_object)

#assembles the list of people credited with a work
@sync_to_async
def sealdescription_contributorgenerate(collection, contributor_dic):

	collectioncontributions = Collectioncontributor.objects.filter(
		fk_collection=collection).select_related(
		'fk_contributor').select_related(
		'fk_collectioncontribution')

	contribution_set = {}

	for c in collectioncontributions:
		contribution = {}
		contribution['contribution'] = c.fk_collectioncontribution.collectioncontribution 
		
		namevalue = ""
		if c.fk_contributor.name_first:
			namevalue = namevalue + c.fk_contributor.name_first
		if c.fk_contributor.name_middle:
			namevalue = namevalue + " " + c.fk_contributor.name_middle
		if c.fk_contributor.name_last:
			namevalue = namevalue + " " + c.fk_contributor.name_last

		contribution['name'] = namevalue
		contribution['uricontributor'] = c.fk_contributor.uricontributor
		
		contribution_set[c.fk_contributor] = contribution

	contributor_dic["contributors"] = contribution_set

	return(contributor_dic)

@sync_to_async
def sealdescription_fetchrepresentation(sealdescription_object):

	description_dic = {}

	try:
		representation_set = Representation.objects.select_related(
			'fk_connection').get(
			fk_sealdescription=sealdescription_object.id_sealdescription, primacy=1)

	except:
		print ("no image available for:", sealdescription_object)
		representation_set = Representation.objects.select_related('fk_connection').get(id_representation=12204474)

	sealdescription_dic = representation_fetchinfo(description_dic, representation_set)

	return(sealdescription_dic)

def representation_fetchinfo(description_dic, representation_set):

	description_dic["thumb"] = representation_set.fk_connection.thumb
	description_dic["medium"] = representation_set.fk_connection.medium
	description_dic["representation_thumbnail_hash"] = representation_set.representation_thumbnail_hash
	description_dic["representation_filename_hash"] = representation_set.representation_filename_hash 
	description_dic["id_representation"] = representation_set.id_representation

	return(description_dic)


@sync_to_async
def manifestation_fetchrepresentations(e, manifestation_dic):

	try:
		representation_set = Representation.objects.select_related('fk_connection').get(fk_manifestation=e.id_manifestation, primacy=1)

	except:
		print ("no image available for:", e.id_manifestation)
		representation_set = Representation.objects.select_related('fk_connection').get(id_representation=12204474)


	manifestation_dic["thumb"] = representation_set.fk_connection.thumb
	manifestation_dic["medium"] = representation_set.fk_connection.medium
	manifestation_dic["representation_thumbnail_hash"] = representation_set.representation_thumbnail_hash
	manifestation_dic["representation_filename_hash"] = representation_set.representation_filename_hash 
	manifestation_dic["id_representation"] = representation_set.id_representation

	return(manifestation_dic)

@sync_to_async
def manifestation_fetchsealdescriptions(e, manifestation_dic):
	sealdescription_set = Sealdescription.objects.filter(fk_seal=e.fk_face.fk_seal).select_related('fk_collection')

	description_set = {}

	for s in sealdescription_set:
		description = {}
		description["sealdescription_id"] = s.id_sealdescription
		description["collection"] = s.fk_collection
		description["identifier"] = s.sealdescription_identifier

		description_set[s.id_sealdescription] = description

	manifestation_dic["sealdescriptions"] = description_set
	
	return(manifestation_dic)

@sync_to_async
def manifestation_fetchlocations(e, manifestation_dic):
	locationreference = Locationreference.objects.select_related(
		'fk_locationname__fk_location').get(
		fk_event=e.fk_support.fk_part.fk_event,fk_locationstatus=1)
	locationname= locationreference.fk_locationname
	location = locationreference.fk_locationname.fk_location
	manifestation_dic["repository_location"] = locationreference.fk_locationname.fk_location.location
	manifestation_dic["id_location"] = locationreference.fk_locationname.fk_location.id_location

	return (manifestation_dic)

@sync_to_async
def manifestation_fetchstandardvalues (e, manifestation_dic):
	facevalue = e.fk_face
	sealvalue = facevalue.fk_seal
	supportvalue = e.fk_support
	numbervalue = supportvalue.fk_number_currentposition
	partvalue = supportvalue.fk_part
	eventvalue = partvalue.fk_event
	itemvalue = partvalue.fk_item
	repositoryvalue = itemvalue.fk_repository
	manifestation_dic["manifestation"] = e
	manifestation_dic["id_manifestation"] = e.id_manifestation
	manifestation_dic["fk_position"] = e.fk_position

	manifestation_dic["id_seal"] = sealvalue.id_seal
	manifestation_dic["id_item"] = itemvalue.id_item
	manifestation_dic["repository_fulltitle"] = repositoryvalue.repository_fulltitle
	manifestation_dic["shelfmark"] = itemvalue.shelfmark
	manifestation_dic["fk_supportstatus"] = supportvalue.fk_supportstatus
	manifestation_dic["fk_attachment"] = supportvalue.fk_attachment     
	manifestation_dic["number"] = numbervalue.number
	manifestation_dic["support_type"] = supportvalue.fk_nature
	manifestation_dic["label_manifestation_repository"] = e.label_manifestation_repository
	manifestation_dic["imagestate_term"] = e.fk_imagestate
	manifestation_dic["partvalue"] = partvalue.id_part

	#take the repository submitted date in preference to the Digisig date
	if eventvalue.repository_startdate:
		manifestation_dic["repository_startdate"] = eventvalue.repository_startdate
	else:
		manifestation_dic["repository_startdate"] = eventvalue.startdate 

	if eventvalue.repository_enddate:
		manifestation_dic["repository_enddate"] = eventvalue.repository_enddate
	else:
		manifestation_dic["repository_enddate"] = eventvalue.enddate

	return (manifestation_dic)


#information for presenting a seal
def sealmetadata(digisig_entity_number):
	seal_info = {}

	face_set = Face.objects.filter(fk_seal=digisig_entity_number).select_related(
		'fk_seal__fk_individual_realizer__fk_group').select_related(
		'fk_seal__fk_individual_realizer__fk_descriptor_title').select_related(
		'fk_seal__fk_individual_realizer__fk_descriptor_name').select_related(
		'fk_seal__fk_individual_realizer__fk_descriptor_prefix1').select_related(
		'fk_seal__fk_individual_realizer__fk_descriptor_descriptor1').select_related(
		'fk_seal__fk_individual_realizer__fk_separator_1').select_related(
		'fk_seal__fk_individual_realizer__fk_descriptor_prefix2').select_related(
		'fk_seal__fk_individual_realizer__fk_descriptor_descriptor2').select_related(
		'fk_seal__fk_individual_realizer__fk_descriptor_prefix3').select_related(
		'fk_seal__fk_individual_realizer__fk_descriptor_descriptor3').select_related(
		'fk_class')

	face_obverse = face_set.get(fk_faceterm=1)

	seal_info["seal"] = face_obverse.fk_seal
	seal_info["sealdescription_set"]= Sealdescription.objects.filter(fk_seal=digisig_entity_number).select_related('fk_collection')
	seal_info["actor"] = face_obverse.fk_seal.fk_individual_realizer

	return (seal_info, face_set, face_obverse)

#information for class value
@sync_to_async
def sealinfo_classvalue (face_case):
	
	classvalue = {}

	try:
		classvalue["level1"] = Classification.objects.get(class_number=face_case.fk_class.level1)
	except: 
		print("level1 unassigned")

	try:
		if face_case.fk_class.level2 > 0:
			faceclass2 = Classification.objects.get(class_number=face_case.fk_class.level2)
			classvalue["level2"] = faceclass2           
	except: 
		print("level2 unassigned")

	try:
		if face_case.fk_class.level3 > 0:
			faceclass3 = Classification.objects.get(class_number=face_case.fk_class.level3)
			classvalue["level3"] = faceclass3           
	except: 
		print("level3 unassigned")

	try:
		if face_case.fk_class.level4 > 0:
			faceclass4 = Classification.objects.get(class_number=face_case.fk_class.level4)
			classvalue["level4"] = faceclass4
	except: 
		print("level4 unassigned")

	try:
		if face_case.fk_class.level5 > 0:
			faceclass5 = Classification.objects.get(class_number=face_case.fk_class.level5)
			classvalue["level5"] = faceclass5           
	except: 
		print("level5 unassigned")          

	return(classvalue)

###### Actor name generators #####

@sync_to_async
def actorfinder(manifestation_set):

	manifestation = manifestation_set[0]
	actortarget = Seal.objects.get(id_seal=int(manifestation['fk_face__fk_seal']))

	nameout = namecompiler(actortarget.fk_individual_realizer)

	return(nameout, actortarget.fk_individual_realizer) 


@sync_to_async
def actornamegenerator(individual_object):

	individual_set = {}

	for i in individual_object:
		individual_info = {}
		individual_info['actor_name'] = namecompiler(i)
		individual_info['id_individual'] = i.id_individual
		individual_set[i.id_individual] = individual_info

	return(individual_set)


def namecompiler(individual_target):

	if not isinstance(individual_target, Individual):
		print(f"Warning: Expected Individual object, but received: {type(individual_target)}")
		individual_object = Individual.objects.get(id_individual=individual_target)

	else:
		individual_object= individual_target

	namevariable = ''

	if hasattr(individual_object, 'fk_group') and individual_object.fk_group is not None: namevariable = individual_object.fk_group.group_name
	if hasattr(individual_object, 'fk_descriptor_title') and individual_object.fk_descriptor_title is not None: namevariable = namevariable + " " + individual_object.fk_descriptor_title.descriptor_modern
	if hasattr(individual_object, 'fk_descriptor_name') and individual_object.fk_descriptor_name is not None: namevariable = namevariable + " " + individual_object.fk_descriptor_name.descriptor_modern
	if hasattr(individual_object, 'fk_descriptor_prefix1') and individual_object.fk_descriptor_prefix1: namevariable = namevariable + " " + individual_object.fk_descriptor_prefix1.prefix_english
	if hasattr(individual_object, 'fk_descriptor_descriptor1') and individual_object.fk_descriptor_descriptor1 is not None: namevariable = namevariable + " " + individual_object.fk_descriptor_descriptor1.descriptor_modern
	if hasattr(individual_object, 'fk_descriptor_prefix2')  and individual_object.fk_descriptor_prefix2: namevariable = namevariable + " " + individual_object.fk_descriptor_prefix2.prefix_english
	if hasattr(individual_object, 'fk_descriptor_descriptor2') and individual_object.fk_descriptor_descriptor2 is not None: namevariable = namevariable + " " + individual_object.fk_descriptor_descriptor2.descriptor_modern
	if hasattr(individual_object, 'fk_descriptor_prefix3') and individual_object.fk_descriptor_prefix3: namevariable = namevariable + " " + individual_object.fk_descriptor_prefix3.prefix_english
	if hasattr(individual_object, 'fk_descriptor_descriptor3') and individual_object.fk_descriptor_descriptor3 is not None: namevariable = namevariable + " " + individual_object.fk_descriptor_descriptor3.descriptor_modern

	nameout = namevariable.strip()

	return(nameout)

@sync_to_async
def namecompiler_group(listofactors):

	#create the list of people whose names need to be formulated
	individual_set = Individual.objects.filter(id_individual__in=listofactors).values(
		'id_individual',
		'fk_descriptor_title',
		'fk_descriptor_name',
		'fk_descriptor_prefix1',
		'fk_descriptor_descriptor1',
		'fk_separator_1',
		'fk_descriptor_prefix2',
		'fk_descriptor_descriptor2',
		'fk_descriptor_prefix3',
		'fk_descriptor_descriptor3',
		'fk_group',
		)

	#gather the information needed to make the names
	descriptor_list =[]
	prefix_list= []
	group_list= []

	for d in individual_set:
		descriptor_list.append(d['fk_descriptor_title'])
		descriptor_list.append(d['fk_descriptor_name'])
		descriptor_list.append(d['fk_descriptor_descriptor1'])
		descriptor_list.append(d['fk_descriptor_descriptor2'])
		descriptor_list.append(d['fk_descriptor_descriptor3'])

	for p in individual_set:
		prefix_list.append(p['fk_descriptor_prefix1'])
		prefix_list.append(p['fk_descriptor_prefix2'])
		prefix_list.append(p['fk_descriptor_prefix3'])

	for g in individual_set:
		group_list.append(g['fk_group'])

	descriptor_set = Descriptor.objects.filter(
		pk_descriptor__in=descriptor_list).values_list(
		'pk_descriptor',
		'descriptor_modern')

	prefix_set = Prefix.objects.filter(
		pk_prefix__in=prefix_list).values_list(
		'pk_prefix',
		'prefix_english')

	group_set = Groupname.objects.filter(
		id_group__in=group_list).values_list(
		'id_group',
		'group_name')

	descriptor_modern_map = dict(descriptor_set)
	prefix_english_map = dict(prefix_set)
	group_name_map = dict(group_set)

	# loop each person and construct the name
	name_set = {}

	for i in individual_set:
		name_temp = ""
		name_temp += group_name_map.get(i.get('i.fk_group'), "") + " " if group_name_map else ""
		name_temp += descriptor_modern_map.get(i.get('fk_descriptor_title'), "") + " "
		name_temp += descriptor_modern_map.get(i.get('fk_descriptor_name'), "") + " "
		name_temp += prefix_english_map.get(i.get('fk_descriptor_prefix1'), "") + " "
		name_temp += descriptor_modern_map.get(i.get('fk_descriptor_descriptor1'), "") + " "
		name_temp += prefix_english_map.get(i.get('fk_descriptor_prefix2'), "") + " "
		name_temp += descriptor_modern_map.get(i.get('fk_descriptor_descriptor2'), "") + " "
		name_temp += prefix_english_map.get(i.get('fk_descriptor_prefix3'), "") + " "
		name_temp += descriptor_modern_map.get(i.get('fk_descriptor_descriptor3'), "")
		name_set[i['id_individual']] = name_temp.strip()

	return(name_set)


#gets event set
def eventset_datedata(event_object, event_dic):

	if event_object.repository_startdate is not None: 
		yeartemp = event_object.repository_startdate
		event_dic["year1"] = yeartemp.year
		if event_object.repository_enddate is not None: 
			yeartemp = event_object.repository_enddate
			event_dic["year2"] = yeartemp.year

	if event_object.startdate is not None:
		yeartemp = event_object.startdate
		event_dic["year3"] = yeartemp.year
		if event_object.enddate is not None: 
			yeartemp = event_object.enddate
			event_dic["year4"] = yeartemp.year

	return (event_dic)

def eventset_locationdata(event_object, event_dic):
	if event_object is not None:
		targetlocation = event_object.pk_event
		
		location_object = Location.objects.filter(locationname__locationreference__fk_event=targetlocation, locationname__locationreference__location_reference_primary = False).first()

		location_name = location_object.location
		location_id = location_object.id_location
		location_longitude = str(location_object.longitude)
		location_latitude = str(location_object.latitude)

		location= {"type": "Point", "coordinates":[location_longitude, location_latitude]}
		location_dict = {'location': location_name, 'latitude': location_latitude, 'longitude': location_longitude} 

		event_dic["repository_location"] = event_object.repository_location 
		event_dic["location"] = location_object
		event_dic["location_name"] = location_name 
		event_dic["location_id"] = location_id 
		event_dic["location_latitude"] = location_longitude 
		event_dic["location_latitude"] = location_latitude 

	return (event_dic)

def eventset_references(event_object, event_dic):
	reference_dict = {}
	referenceset = Referenceindividual.objects.filter(
		fk_event=event_object).order_by(
		"fk_referencerole__role_order", "pk_referenceindividual").select_related(
		'fk_individual').select_related(
		'fk_referencerole')

	event_dic["referenceset"] = referenceset

	return(event_dic)

@sync_to_async
def referenceset_references(witness_entity_number):

	eventset= Event.objects.filter(
			fk_event_event__fk_individual=witness_entity_number).values('pk_event')

	reference_dic = Referenceindividual.objects.filter(
		fk_event__in=eventset).select_related(
	'fk_referencerole').select_related(
	'fk_event').select_related(
	'fk_individual').order_by(
	'pk_referenceindividual').values(
	'fk_event',
	'fk_individual',
	'pk_referenceindividual',
	'fk_event__startdate',
	'fk_event__enddate',
	'fk_event__repository_startdate',
	'fk_event__repository_enddate',
	'fk_referencerole__referencerole',
	'fk_event__part__fk_item__shelfmark',
	'fk_event__part__fk_item__id_item',
	'fk_event__part__id_part',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__location')

	position_dic = {}

	# determines where a person is located in the witness list
	for r in reference_dic:

		if r['fk_referencerole__referencerole'] == 'Witness':

			eventvalue = r['fk_event']
			position_dic.setdefault(eventvalue, {'total':0, 'position': 0, 'startdate':r['fk_event__startdate'], 'dateend':r['fk_event__enddate']})

			position_dic[eventvalue]['total'] += 1

			if str(r['fk_individual']) == witness_entity_number:
				position_dic[eventvalue]['position'] += position_dic[eventvalue]['total']


	reference_set = {}

	# assembles the references to the person
	for r in reference_dic:

		if str(r['fk_individual']) == witness_entity_number:

			reference_row = {}

			#date
			if r['fk_event__startdate'] != None:
				startyear = int(str(r['fk_event__startdate'])[:4])
				endyear = int(str(r['fk_event__enddate'])[:4])

				if endyear > startyear:
					reference_row['date'] = str(startyear) + " - " + str(endyear)
				else:
					reference_row['date'] = str(startyear)
			elif r['fk_event__repository_startdate'] != None:
				startyear = int(str(r['fk_event__repository_startdate'])[:4])
				endyear = int(str(r['fk_event__repository_enddate'])[:4])

				if endyear > startyear:
					reference_row['date'] = str(startyear) + " - " + str(endyear)
				else:
					reference_row['date'] = str(startyear)
			else:
				reference_row['date'] = "20000"
			#role
			reference_row["role"] = r['fk_referencerole__referencerole']

			if r['fk_referencerole__referencerole'] == "Witness":
				eventvalue = r['fk_event']
				reference_row["position"] = position_dic[eventvalue]['position']
				reference_row["total"] = position_dic[eventvalue]['total']

			#item
			reference_row["item_shelfmark"] = r['fk_event__part__fk_item__shelfmark']
			reference_row["item_id"] = r['fk_event__part__fk_item__id_item']
			reference_row["part_id"] = r['fk_event__part__id_part']
			reference_row["region"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region']
			reference_row["location_id"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location']
			reference_row["location"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__location']
			reference_row["location_pk"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location']
			reference_set[r['pk_referenceindividual']] = reference_row

	return(reference_set)

@sync_to_async
def referenceset_references2(witness_entity_number):

	eventset= Event.objects.filter(
			fk_event_event__fk_individual=witness_entity_number).values('pk_event')

	reference_dic = Referenceindividual.objects.filter(
		fk_event__in=eventset).select_related(
	'fk_referencerole').select_related(
	'fk_event').select_related(
	'fk_individual').order_by(
	'pk_referenceindividual').values(
	'fk_event',
	'fk_individual',
	'pk_referenceindividual',
	'fk_event__startdate',
	'fk_event__enddate',
	'fk_event__repository_startdate',
	'fk_event__repository_enddate',
	'fk_referencerole__referencerole',
	'fk_event__part__fk_item__shelfmark',
	'fk_event__part__fk_item__id_item',
	'fk_event__part__id_part',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location',
	'fk_event__fk_event_locationreference__fk_locationname__fk_location__location')

	position_dic = {}

	# determines where a person is located in the witness list
	for r in reference_dic:

		if r['fk_referencerole__referencerole'] == 'Witness':

			eventvalue = r['fk_event']
			position_dic.setdefault(eventvalue, {'total':0, 'position': 0, 'startdate':r['fk_event__startdate'], 'dateend':r['fk_event__enddate']})

			position_dic[eventvalue]['total'] += 1

			if str(r['fk_individual']) == witness_entity_number:
				position_dic[eventvalue]['position'] += position_dic[eventvalue]['total']


	reference_list = []

	# assembles the references to the person
	for r in reference_dic:

		if str(r['fk_individual']) == witness_entity_number:

			reference_row = {}

			#date
			if r['fk_event__startdate'] != None:
				#reference_row['startyear'] = r['fk_event__startdate']
				#reference_row['endyear'] = r['fk_event__enddate']

				startyear = int(str(r['fk_event__startdate'])[:4])
				endyear = int(str(r['fk_event__enddate'])[:4])

				if endyear > startyear:
					reference_row['date'] = str(startyear) + " - " + str(endyear)
				else:
					reference_row['date'] = str(startyear)
			elif r['fk_event__repository_startdate'] != None:
				#reference_row['startyear'] = r['fk_event__repository_startdate']
				#reference_row['endyear'] = r['fk_event__repository_enddate']

				startyear = int(str(r['fk_event__repository_startdate'])[:4])
				endyear = int(str(r['fk_event__repository_enddate'])[:4])

				if endyear > startyear:
					reference_row['date'] = str(startyear) + " - " + str(endyear)
				else:
					reference_row['date'] = str(startyear)
			else:
				reference_row['date'] = "20000"
			#role
			reference_row["role"] = r['fk_referencerole__referencerole']

			if r['fk_referencerole__referencerole'] == "Witness":
				eventvalue = r['fk_event']
				reference_row["position"] = position_dic[eventvalue]['position']
				reference_row["total"] = position_dic[eventvalue]['total']

			#item
			# part_object = Part.objects.select_related('fk_item').get(fk_event=r.fk_event)
			reference_row["item_shelfmark"] = r['fk_event__part__fk_item__shelfmark']
			reference_row["item_id"] = r['fk_event__part__fk_item__id_item']
			reference_row["part_id"] = r['fk_event__part__id_part']
			reference_row["region"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region']
			reference_row["location_id"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location']
			reference_row["location"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__location']
			reference_row["location_pk"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location']
			reference_row["part_url"] = reverse('entity', kwargs={'witness_entity_number': r['fk_event__part__id_part']}),
			reference_list.append(reference_row)
	
	reference_list = sorted (reference_list, key=lambda x: x["date"])

	return(reference_list)

@sync_to_async
def referenceset_references3(witness_entity_number):
	# Use a single query to get all relevant events
	eventset = Event.objects.filter(
		fk_event_event__fk_individual=witness_entity_number).values('pk_event')
	
	# Query references with the necessary fields and related data all at once
	reference_dic = Referenceindividual.objects.filter(
		fk_event__in=eventset
	).select_related(
		'fk_referencerole', 'fk_event', 'fk_individual',
		'fk_event__part__fk_item', 'fk_event__fk_event_locationreference__fk_locationname__fk_location'
	).values(
		'fk_event', 'fk_individual', 'pk_referenceindividual',
		'fk_event__startdate', 'fk_event__enddate', 
		'fk_event__repository_startdate', 'fk_event__repository_enddate',
		'fk_referencerole__referencerole', 'fk_event__part__fk_item__shelfmark',
		'fk_event__part__fk_item__id_item', 'fk_event__part__id_part',
		'fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region',
		'fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location',
		'fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location',
		'fk_event__fk_event_locationreference__fk_locationname__fk_location__location'
	)

	position_dic = {}

	# Combining position calculation and role assignment in a single loop
	for r in reference_dic:
		if r['fk_referencerole__referencerole'] == 'Witness':
			eventvalue = r['fk_event']
			position_dic.setdefault(eventvalue, {'total': 0, 'position': 0, 'startdate': r['fk_event__startdate'], 'dateend': r['fk_event__enddate']})

			# Update position and total for the event
			position_dic[eventvalue]['total'] += 1
			if str(r['fk_individual']) == witness_entity_number:
				position_dic[eventvalue]['position'] += position_dic[eventvalue]['total']

	# Prepare reference list
	reference_list = []
	#base_url = reverse('entity')  # Precompute the base URL outside the loop
	
	for r in reference_dic:
		if str(r['fk_individual']) == witness_entity_number:
			reference_row = {}

			# Handle date formatting
			if r['fk_event__startdate']:
				startyear = int(str(r['fk_event__startdate'])[:4])
				endyear = int(str(r['fk_event__enddate'])[:4])
				reference_row['date'] = f"{startyear} - {endyear}" if endyear > startyear else str(startyear)
			elif r['fk_event__repository_startdate']:
				startyear = int(str(r['fk_event__repository_startdate'])[:4])
				endyear = int(str(r['fk_event__repository_enddate'])[:4])
				reference_row['date'] = f"{startyear} - {endyear}" if endyear > startyear else str(startyear)
			else:
				reference_row['date'] = "20000"

			# Role
			reference_row["role"] = r['fk_referencerole__referencerole']
			if r['fk_referencerole__referencerole'] == "Witness":
				eventvalue = r['fk_event']
				reference_row["position"] = position_dic[eventvalue]['position']
				reference_row["total"] = position_dic[eventvalue]['total']

			# Item info
			reference_row["item_shelfmark"] = r['fk_event__part__fk_item__shelfmark']
			reference_row["item_id"] = r['fk_event__part__fk_item__id_item']
			reference_row["part_id"] = r['fk_event__part__id_part']
			reference_row["region"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__fk_region']
			reference_row["location_id"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__id_location']
			reference_row["location"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__location']
			reference_row["location_pk"] = r['fk_event__fk_event_locationreference__fk_locationname__fk_location__pk_location']
			reference_row["part_url"] = reverse('entity', kwargs={'witness_entity_number': r['fk_event__part__id_part']})
			# Precompute the URL once
			#reference_row["part_url"] = f"{base_url}?witness_entity_number={r['fk_event__part__id_part']}"

			reference_list.append(reference_row)

	# Sort the reference list by date
	reference_list = sorted(reference_list, key=lambda x: x["date"])

	return reference_list


@sync_to_async
def referenceset_references4(witness_entity_number, ref_dic_locations):
	# Use a single query to get all relevant events
	eventset = Event.objects.filter(
		fk_event_event__fk_individual=witness_entity_number).values('pk_event')
	
	# Query references with the necessary fields and related data all at once
	reference_dic = Referenceindividual.objects.filter(
		fk_event__in=eventset
	).select_related(
		'fk_referencerole', 'fk_event'
	).values(
		'fk_event', 'fk_individual', 
		'pk_referenceindividual',
		'fk_event__startdate', 'fk_event__enddate', 
		'fk_event__repository_startdate', 'fk_event__repository_enddate',
		'fk_referencerole__referencerole', 'fk_event__part__fk_item__shelfmark',
		'fk_event__part__fk_item__id_item', 'fk_event__part__id_part'
	)

	position_dic = {}

	# Combining position calculation and role assignment in a single loop
	for r in reference_dic:
		if r['fk_referencerole__referencerole'] == 'Witness':
			eventvalue = r['fk_event']
			position_dic.setdefault(eventvalue, {'total': 0, 'position': 0, 'startdate': r['fk_event__startdate'], 'dateend': r['fk_event__enddate']})

			# Update position and total for the event
			position_dic[eventvalue]['total'] += 1
			if str(r['fk_individual']) == witness_entity_number:
				position_dic[eventvalue]['position'] += position_dic[eventvalue]['total']

	# Prepare reference list
	reference_list = []
	#base_url = reverse('entity')  # Precompute the base URL outside the loop
	
	for r in reference_dic:
		if str(r['fk_individual']) == witness_entity_number:
			reference_row = {}

			# Handle date formatting
			if r['fk_event__startdate']:
				startyear = int(str(r['fk_event__startdate'])[:4])
				endyear = int(str(r['fk_event__enddate'])[:4])
				reference_row['date'] = f"{startyear} - {endyear}" if endyear > startyear else str(startyear)
			elif r['fk_event__repository_startdate']:
				startyear = int(str(r['fk_event__repository_startdate'])[:4])
				endyear = int(str(r['fk_event__repository_enddate'])[:4])
				reference_row['date'] = f"{startyear} - {endyear}" if endyear > startyear else str(startyear)
			else:
				reference_row['date'] = "20000"

			# Role
			reference_row["role"] = r['fk_referencerole__referencerole']
			if r['fk_referencerole__referencerole'] == "Witness":
				eventvalue = r['fk_event']
				reference_row["position"] = position_dic[eventvalue]['position']
				reference_row["total"] = position_dic[eventvalue]['total']

			# Item info
			reference_row["item_shelfmark"] = r['fk_event__part__fk_item__shelfmark']
			reference_row["item_id"] = r['fk_event__part__fk_item__id_item']
			reference_row["part_id"] = r['fk_event__part__id_part']
			reference_row["part_url"] = reverse('entity', kwargs={'witness_entity_number': r['fk_event__part__id_part']})

			reference_row["location"] = ref_dic_locations[r['pk_referenceindividual']]

			reference_list.append(reference_row)

	# Sort the reference list by date
	reference_list = sorted(reference_list, key=lambda x: x["date"])

	return reference_list


@sync_to_async
def referenceset_references5(witness_entity_number, ref_dic_locations):

	eventset= Event.objects.filter(
			fk_event_event__fk_individual=witness_entity_number).values('pk_event')

	reference_dic = Referenceindividual.objects.filter(
		fk_event__in=eventset).select_related(
	'fk_referencerole').select_related(
	'fk_event').order_by(
	'pk_referenceindividual').values(
	'fk_event',
	'fk_individual',
	'pk_referenceindividual',
	'fk_event__startdate',
	'fk_event__enddate',
	'fk_event__repository_startdate',
	'fk_event__repository_enddate',
	'fk_referencerole__referencerole',
	'fk_event__part__fk_item__shelfmark',
	'fk_event__part__fk_item__id_item',
	'fk_event__part__id_part')

	position_dic = {}

	# determines where a person is located in the witness list
	for r in reference_dic:

		if r['fk_referencerole__referencerole'] == 'Witness':

			eventvalue = r['fk_event']
			position_dic.setdefault(eventvalue, {'total':0, 'position': 0, 'startdate':r['fk_event__startdate'], 'dateend':r['fk_event__enddate']})

			position_dic[eventvalue]['total'] += 1

			if str(r['fk_individual']) == witness_entity_number:
				position_dic[eventvalue]['position'] += position_dic[eventvalue]['total']


	reference_list = []

	# assembles the references to the person
	for r in reference_dic:

		if str(r['fk_individual']) == witness_entity_number:

			reference_row = {}

			#date
			if r['fk_event__startdate'] != None:
				#reference_row['startyear'] = r['fk_event__startdate']
				#reference_row['endyear'] = r['fk_event__enddate']

				startyear = int(str(r['fk_event__startdate'])[:4])
				endyear = int(str(r['fk_event__enddate'])[:4])

				if endyear > startyear:
					reference_row['date'] = str(startyear) + " - " + str(endyear)
				else:
					reference_row['date'] = str(startyear)
			elif r['fk_event__repository_startdate'] != None:
				#reference_row['startyear'] = r['fk_event__repository_startdate']
				#reference_row['endyear'] = r['fk_event__repository_enddate']

				startyear = int(str(r['fk_event__repository_startdate'])[:4])
				endyear = int(str(r['fk_event__repository_enddate'])[:4])

				if endyear > startyear:
					reference_row['date'] = str(startyear) + " - " + str(endyear)
				else:
					reference_row['date'] = str(startyear)
			else:
				reference_row['date'] = "20000"
			#role
			reference_row["role"] = r['fk_referencerole__referencerole']

			if r['fk_referencerole__referencerole'] == "Witness":
				eventvalue = r['fk_event']
				reference_row["position"] = position_dic[eventvalue]['position']
				reference_row["total"] = position_dic[eventvalue]['total']

			#item
			# part_object = Part.objects.select_related('fk_item').get(fk_event=r.fk_event)
			reference_row["item_shelfmark"] = r['fk_event__part__fk_item__shelfmark']
			reference_row["item_id"] = r['fk_event__part__fk_item__id_item']
			reference_row["part_id"] = r['fk_event__part__id_part']
			reference_row["part_url"] = reverse('entity', kwargs={'witness_entity_number': r['fk_event__part__id_part']})
			reference_row["location"] = ref_dic_locations[r['pk_referenceindividual']]
			reference_list.append(reference_row)
	
	reference_list = sorted (reference_list, key=lambda x: x["date"])

	return(reference_list)


#externallinks for object
@sync_to_async
def externallinkgenerator(entity_number):
	externallinkset = Externallink.objects.filter(internal_entity=entity_number).values('external_link')
	return (externallinkset)    

@sync_to_async
def partobjectforitem_define(entity_number):

	#### prepare parts
	part_object = Part.objects.filter(
		fk_item=entity_number).values(
		'id_part',
		'part_description',
		'fk_item',
		'fk_item__shelfmark',
		'fk_item__fk_repository__repository_fulltitle',
		'fk_event',
		'fk_event__repository_startdate',
		'fk_event__repository_enddate',
		'fk_event__startdate',
		'fk_event__enddate',
		'fk_event__repository_location')

	part_dic= {}
	reference_dic= {}
	manifestationpart = {}
	listofparts = []
	listofitems = []
	listofevents = []

	for p in part_object:
		part_temp_dic = {}
		part_temp_dic['fk_item'] = p['fk_item']
		part_temp_dic['id_part'] = p['id_part']
		part_temp_dic['part_description'] = p['part_description']
		part_temp_dic['fk_event'] = p['fk_event']
		part_temp_dic['pagetitle'] = p['fk_item__fk_repository__repository_fulltitle'] + " " + p['fk_item__shelfmark']
		part_temp_dic['fk_repository'] = p['fk_item__fk_repository__repository_fulltitle']
		part_temp_dic['shelfmark'] = p['fk_item__shelfmark']
		part_temp_dic['year1'] = p['fk_event__repository_startdate']
		part_temp_dic['year2'] = p['fk_event__repository_enddate']
		part_temp_dic['year3'] = p['fk_event__startdate']
		part_temp_dic['year4'] = p['fk_event__enddate']
		part_temp_dic["repository_location"] = p['fk_event__repository_location']

		listofparts.append(p['id_part'])
		listofitems.append(p['fk_item'])
		listofevents.append(p['fk_event'])

		part_dic[p['id_part']] = part_temp_dic

		reference_dic.update({p['fk_event']: {} })
		manifestationpart.update({p['id_part']: {} })

	### prepare representations of part
	representation_part = Representation.objects.filter(fk_digisig__in=listofparts).select_related('fk_connection')

	try:
		for t in representation_part:
			#for all images
			connection = t.fk_connection
			part_dic[t.fk_digisig]["connection"] = t.fk_connection
			part_dic[t.fk_digisig]["connection_thumb"] = t.fk_connection.thumb
			part_dic[t.fk_digisig]["connection_medium"] = t.fk_connection.medium
			part_dic[t.fk_digisig]["representation_filename"] = t.representation_filename_hash
			part_dic[t.fk_digisig]["representation_thumbnail"] = t.representation_thumbnail_hash
			part_dic[t.fk_digisig]["id_representation"] = t.id_representation 

	except:
		print ('no image of PART available')

	### prepare references
	referenceset = Referenceindividual.objects.filter(
		fk_event__in=listofevents).order_by(
		"fk_referencerole__role_order", "pk_referenceindividual").values(
		'pk_referenceindividual',
		'fk_individual',
		'fk_individual__fullname_original',
		'referenceindividual',
		'fk_referencerole__referencerole',
		'fk_individualoffice',
		'fk_event',
		)
	
	for referencecase in referenceset:

		reference_dic_temp = {}
		reference_dic_temp['pk_referenceindividual']= referencecase['pk_referenceindividual']
		reference_dic_temp['fk_individual']= referencecase['fk_individual']
		reference_dic_temp['fullname_original']= referencecase['fk_individual__fullname_original']
		reference_dic_temp['referenceindividual']= referencecase['referenceindividual']
		reference_dic_temp['fk_referencerole']= referencecase['fk_referencerole__referencerole']
		reference_dic_temp['fk_individualoffice']= referencecase['fk_individualoffice']
		reference_dic_temp['fk_event'] = referencecase['fk_event']


		reference_dic[referencecase['fk_event']].update ({referencecase['pk_referenceindividual']: reference_dic_temp})

	for partneedingreference in part_dic.values():
		searchvalue = partneedingreference['fk_event'] 
		partneedingreference['reference_set'] = reference_dic[searchvalue]

	# try:
	#   externallinkset = Externallink.objects.filter(internal_entity_in=listofitems)

	#   links_dic = {}
	#   for e in externallinkset:
	#       links_dic[e.internal_entity].update({e.id_external_link}:{external_link})

	#   for l in links_dic:
	#       part_dic[l.]

	location_object = Location.objects.filter(
		locationname__locationreference__fk_event__in=listofevents, locationname__locationreference__location_reference_primary = False).values(
		'locationname__locationreference__fk_event',
		'location',
		'id_location',
		'longitude',
		'latitude').first()

	l = location_object

	searchvalue = int(location_object['locationname__locationreference__fk_event'])

	for key, part_info in part_dic.items():
		 
		if searchvalue == part_info['fk_event']:

			mapdic = {"type": "FeatureCollection"}
			properties = {}
			geometry = {}
			location = {}
			placelist = []

			location= {"type": "Point", "coordinates":[ location_object['longitude'], location_object['latitude'] ]}
			location_dict = {'location': location_object['location'], 'latitude': location_object['latitude'], 'longitude': location_object['longitude']} 

			properties = {"id_location": location_object['id_location'], "location": location}
			geometry = {"type": "Point", "coordinates": [location_object['longitude'] , location_object['latitude']]}
			location = {"type": "Feature", "properties": properties, "geometry": geometry}
			placelist.append(location)

			mapdic["features"] = placelist

			part_info["location"] = location
			part_info["location_name"] = location_object['location'] 
			part_info["location_id"] = location_object['id_location'] 
			part_info["location_latitude"] = location_object['longitude'] 
			part_info["location_latitude"] = location_object['latitude']
			part_info['location_dict'] = location_dict
			part_info['mapdic'] = mapdic

		### to avoid forms breaking where location info is not present 6/5/2025
		else:
			part_info['mapdic'] = {} 

	## find seals associated with the parts
	manifestation_set = Manifestation.objects.filter(
		fk_support__fk_part__in=listofparts).values(
		'label_manifestation_repository',
		'id_manifestation',
		'fk_position__position',
		'fk_face__fk_seal',
		'fk_imagestate__imagestate_term',
		'fk_support__fk_supportstatus__supportstatus',
		'fk_support__fk_part',
		'fk_support__fk_attachment__attachment',
		'fk_support__fk_number_currentposition__number',
		)

	for manifestationcase in manifestation_set:
		manifestation_dic = {}
		manifestation_dic['fk_seal'] = manifestationcase['fk_face__fk_seal']
		manifestation_dic['id_manifestation'] = manifestationcase['id_manifestation']
		manifestation_dic['imagestate_term'] = manifestationcase['fk_imagestate__imagestate_term']
		manifestation_dic['fk_supportstatus'] = manifestationcase['fk_support__fk_supportstatus__supportstatus']
		manifestation_dic['label_manifestation_repository'] = manifestationcase['label_manifestation_repository']
		manifestation_dic['fk_attachment'] = manifestationcase['fk_support__fk_attachment__attachment']
		manifestation_dic['number'] = manifestationcase['fk_support__fk_number_currentposition__number']
		manifestation_dic['fk_position'] = manifestationcase['fk_position__position']

		manifestationpart[manifestationcase['fk_support__fk_part']].update ({manifestationcase['id_manifestation']: manifestation_dic})

	for partneedingmanifestation in part_dic.values():
		searchvalue = partneedingmanifestation['id_part'] 
		partneedingmanifestation['manifestation_set'] = manifestationpart[searchvalue]

	return (part_dic)

@sync_to_async
def manifestationobject_define(digisig_entity_number):

	manifestation_case = Manifestation.objects.get(id_manifestation=digisig_entity_number).select_related(
	'fk_face__fk_seal').select_related(
	'fk_support__fk_part__fk_item__fk_repository').select_related(
	'fk_support__fk_number_currentposition').select_related(
	'fk_support__fk_attachment').select_related(
	'fk_support__fk_supportstatus').select_related(
	'fk_support__fk_nature').select_related(
	'fk_imagestate').select_related(
	'fk_position').select_related(
	'fk_support__fk_part__fk_event')

	return(manifestation_case)  


#### this is not functional
@sync_to_async
def manifestation_createdic(manifestationcase):

	manifestation_dic = {}

	manifestation_dic['id_manifestation'] = manifestationcase['id_manifestation']
	manifestation_dic['ui_manifestation_repository'] = ['ui_manifestation_repository']
	manifestation_dic['label_manifestation_repository'] = manifestationcase['label_manifestation_repository']

	manifestation_dic['position'] = manifestationcase['fk_position__position']

	manifestation_dic['imagestate_term'] = manifestationcase['fk_imagestate__imagestate_term']
	manifestation_dic['supportstatus'] = manifestationcase['fk_support__fk_supportstatus__supportstatus']
	manifestation_dic['fk_supportstatus'] = manifestationcase['fk_support__fk_supportstatus']   
	manifestation_dic['fk_attachment'] = manifestationcase['fk_support__fk_attachment']
	manifestation_dic['attachment'] = manifestationcase['fk_support__fk_attachment__attachment']
	manifestation_dic['number'] = manifestationcase['fk_support__fk_number_currentposition__number']
	manifestation_dic['fk_number_currentposition'] = manifestationcase['fk_support__fk_number_currentposition'] 
	manifestation_dic['fk_nature'] = manifestationcase['fk_support__fk_nature']
	manifestation_dic['nature_name'] = manifestationcase['fk_support__fk_nature__nature_name']
	manifestation_dic['fk_material'] = manifestationcase['fk_support__fk_material']

	manifestation_dic['id_item'] = manifestationcase['fk_support__fk_part__fk_item']
	manifestation_dic['shelfmark'] = manifestationcase['fk_support__fk_part__fk_item__shelfmark']
	manifestation_dic['repository_fulltitle'] = manifestationcase['fk_support__fk_part__fk_item__fk_repository__repository_fulltitle']

	manifestation_dic['startdate'] = manifestationcase['fk_support__fk_part__fk_event__startdate']
	manifestation_dic['enddate'] = manifestationcase['fk_support__fk_part__fk_event__enddate']

	manifestation_dic['fk_seal'] = manifestationcase['fk_face__fk_seal']
	manifestation_dic['date_origin'] = manifestationcase['fk_face__fk_seal__date_origin']

		
	try:
		#representation_case = Representation.objects.get(fk_digisig=manifestationcase['id_manifestation'], primacy=1)
		representation_case = Representation.objects.get(fk_digisig=manifestationcase['id_manifestation'])
	except:
		#add graphic of generic seal 
		representation_case = Representation.objects.get(id_representation=12132404)

	for r in representation_case:



		manifestation_dic['connection'] = representation_case.fk_connection.connection
		manifestation_dic['fk_representation_type'] = representation_case.fk_representation_type
		manifestation_dic['thumb'] = representation_case.fk_connection.thumb
		manifestation_dic['representation_thumbnail_hash'] = representation_case.representation_thumbnail_hash
		manifestation_dic['id_representation'] = representation_case.id_representation
		manifestation_dic['medium'] = representation_case.fk_connection.medium
		manifestation_dic['representation_filename'] = representation_case.representation_filename
		manifestation_dic['id_representation'] = representation_case.id_representation
		manifestation_dic['count'] = representation_case.count
		manifestation_dic['representation_filename'] = representation_case.representation_thumbnail
		manifestation_dic['id_representation'] = representation_case.id_representation
		manifestation_dic['medium'] = representation_case.medium
		manifestation_dic['representation_type'] = representation_case.representation_type
		manifestation_dic['representation_filename'] = representation_case.represenation_datecreated
		manifestation_dic['thumb'] = representation_case.thumb
		manifestation_dic['name_first'] = representation_case.name_first 
		manifestation_dic['name_middle'] = representation_case.name_middle 
		manifestation_dic['name_last'] = representation_case.name_last
		#manifestation_dic['totalrows'] = {{totalrows}}


	sealdescription_set = Sealdescription.objects.filter(fk_seal=manifestationcase['id_manifestation'])


	manifestation_dic['collection_shorttitle'] = {{description.fk_collection.collection_shorttitle}}
	manifestation_dic['sealdescription_identifier'] = {{description.sealdescription_identifier}}
	manifestation_dic['region'] = {{region}}



	manifestation_dic['outname'] = {{outname}}

	location_reference_object = Locationreference.objects.get(fk_event=manifestation_object.fk_support.fk_part.fk_event, fk_locationstatus=1)
	
	try:
		region = location_reference_object.fk_locationname.fk_location.fk_region.region_label
	except:
		region = "Undetermined"

	externallink_object = Digisiglinkview.objects.filter(fk_digisigentity=digisig_entity_number)

	individualtarget = seal_object.fk_individual_realizer
	outname = namecompiler(individualtarget)




	return(manifestation_dic)



#info for collections page
def classdistribution(classset, facecount):

	data2 = []
	labels2 = []
	resultdic = {}

	allclasses = Classification.objects.all()

	for case in allclasses:
		casecount = 0
		if (case.level == 4):
			limitset = classset.filter(level4=case.class_number)
			for l in limitset: 
				casecount = casecount + l.numcases
		if (case.level == 3):
			limitset = classset.filter(level3=case.class_number)
			for l in limitset:
				casecount = casecount + l.numcases
				#print ("++", l.class_name, l.level, l.numcases, case.numcases)
		if (case.level == 2):
			limitset = classset.filter(level2=case.class_number)
			for l in limitset:
				casecount = casecount + l.numcases
				#print ("++", l.class_name, l.level, l.numcases, case.numcases)
		if (case.level == 1):
			limitset = classset.filter(level1=case.class_number)
			for l in limitset:
				casecount = casecount + l.numcases
				# print ("++", l.class_name, l.level, l.numcases, case.numcases)

		percentagedata = (casecount/facecount)*100
		if percentagedata > 1:
			resultdic.update({case.class_name: percentagedata})

	allclasses = allclasses.order_by('class_sortorder')
	for case in allclasses:
		if case.class_name in resultdic:
			classpercentage = resultdic.get(case.class_name)
			if classpercentage > 1:
				data2.append(classpercentage)
				labels2.append(case.class_name)

	return(data2, labels2)