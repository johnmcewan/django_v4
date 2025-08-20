from django.contrib import admin
from django.shortcuts import get_object_or_404
from digisig.models import *
from datetime import datetime
import math
from django.forms import TextInput, Textarea
from django.db.models import Count
from django.utils.html import format_html
from statistics import mean

#project specific functions
from utils.mltools import *
from utils.generaltools import *


#Change to admin header
admin.site.site_header = "Digisig administration"
admin.site.site_title = "Digisig Admin Portal"
admin.site.index_title = "Welcome to Digisig's administration portal"

#Actions (various)

def event_comparespans(ModelAdmin, request, queryset):

	#testsample = Event.objects.filter(schoyen__gt=0).exclude(startdate__isnull=True)
	testsample = Event.objects.filter(pas_id__gt=0).exclude(startdate__isnull=True)

	resultset= []
	failcase = 0
	Mlttakessub = 0
	Subtakesmlt = 0
	dateset = {}

	for t in testsample:
		v1 = t.repository_startdate.year
		v2 = t.repository_enddate.year

		v3 = t.startdate.year
		v4 = t.enddate.year

		if v3 > 0:
			repvalue = v1
			repset1 = []

			while repvalue < (v2+1):
				repset1.append(repvalue)
				repvalue = repvalue + 1

			repvalue2 = v3
			repset2 = []

			while repvalue2 < (v4+1):
				repset2.append(repvalue2)
				repvalue2 = repvalue2 + 1

			count = 0
			for i in repset1:

				if i in repset2:
					count = count +1

			outvalue = jaccard_set(repset1, repset2)

			if outvalue < 0.000001:
				failcase = failcase + 1
			resultset.append(outvalue)
			# print (t, count, count/(v2-v1+1))
			# print (t, outvalue, count, count/(v2-v1+1))

			if v1 < v3:
				if v2 > v4:
					Subtakesmlt = Subtakesmlt +1

			if v3 < v1:
				if v4 > v2:
					Mlttakessub = Mlttakessub +1

			spanrange = v2-v1

			try:
				valuetemp = dateset.get(spanrange)
				dateset[spanrange] = valuetemp + 1

			except:
				dateset[spanrange] = 1

	matches = (Mlttakessub + Subtakesmlt)/ (len(testsample))
	# print (resultset)
	list_avg = mean(resultset)
	print ("average", list_avg)
	print ("failcase", failcase)
	print ("Mlttales", Mlttakessub, "Subtakes", Subtakesmlt, matches)
	# print (dateset)
	for key, value in dateset.items():
		valuepercent = (round((value/(len(testsample))), 4))

		print (key, "|", value, "|", valuepercent, "\n") 

def jaccard_set(list1, list2):
    """Define Jaccard Similarity function for two sets"""
    intersection = len(list(set(list1).intersection(list2)))
    union = (len(list1) + len(list2)) - intersection
    return float(intersection) / union


## Update the shelfmarks in item AND part --- ### is this code complete? May21/2024
def itemshelfmark_update(modeladmin, request, queryset):

	#queryset = Item.objects.filter(id_item__gt=11395910)

	for i in queryset:
		series = i.fk_series
		partset = Part.objects.filter(fk_item=i.id_item)

		## formulate item #################
		valueadd1 = ""
		valueadd2 = ""
		valueadd3 = ""
		valueadd4 = ""
		valueadd5 = ""
		valueadd6 = ""
		valueadd7 = ""
		valueadd8 = ""
		valueadd9 = ""
		valueadd10 = ""
		valueadd11 = ""
		valueadd12 = ""

		# formulate the item PREFIX 
		if (i.prefix_alpha1 !=None):
			valueadd1 = series.fk_separator_prefix_a1.separator_alternate + i.prefix_alpha1 
	    
		if (i.prefix_number1 !=None):
			valueadd2 = series.fk_separator_prefix_n1.separator_alternate + str(i.prefix_number1) 

		if (i.prefix_alpha2 !=None):
			valueadd3 = series.fk_separator_prefix_a2.separator_alternate +	i.prefix_alpha2 

		if (i.prefix_number2 !=None):
			valuedadd4 = series.fk_separator_prefix_n2.separator_alternate + str(i.prefix_number2) 

		if (i.prefix_alpha3 !=None):
			valueadd5 = series.fk_separator_prefix_a3.separator_alternate + i.prefix_alpha3 

		if (i.prefix_number3 !=None):
			valueadd6 = series.fk_separator_prefix_n3.separator_alternate + i.prefix_number3 

	   # formulate the series
		if (series !=None):
			valueadd7 = series.fk_separator_series.separator_alternate + series.series_abbreviated

	    # formulate item reference

		if (i.classmark_alpha1 !=None):
			valueadd8 = series.fk_separator_a1.separator_alternate + i.classmark_alpha1 

		if (i.classmark_number1 !=None):
			if (series.fk_separator_n1.pk_separator == 4):
				separator = ""
				if len(str(i.classmark_number1)) == 3: separator = "/"
				if len(str(i.classmark_number1)) == 2: separator = "/0"
				if len(str(i.classmark_number1)) == 1: separator = "/00"
				valueadd9 = separator + str(i.classmark_number1)

			elif (series.fk_separator_n1.pk_separator == 17):
				valueadd9 = series.fk_separator_n1.separator_alternate + str(i.classmark_number1) + ")"

			else:
				valueadd9 = series.fk_separator_n1.separator_alternate + str(i.classmark_number1)

		if (i.classmark_alpha2 !=None):
			valueadd10 = series.fk_separator_a2.separator_alternate + i.classmark_alpha2 

		if (i.classmark_number2 !=None):
			valueadd11 = series.fk_separator_n2.separator_alternate + str(i.classmark_number2) 

		if (i.classmark_alpha3 !=None):
			valueadd12 = series.fk_separator_a3.separator_alternate + i.classmark_alpha3 

		if (i.classmark_number3 !=None):
			valueadd13 = series.fk_separator_n3.separator_alternate + str(i.classmark_number3) 
 
		newshelfmark = valueadd1 + valueadd2 + valueadd3 + valueadd4 + valueadd5 + valueadd6
		newshelfmark = newshelfmark + valueadd7 + valueadd8 + valueadd9 + valueadd10 + valueadd11 + valueadd12

		newshelfmark = newshelfmark.replace("??", "")
		newshelfmark = newshelfmark.replace("^", " ")
		print (i.shelfmark, newshelfmark)
		i.shelfmark = newshelfmark
		#i.save()
		#print ("saved")

		# formulate the part reference

		# update objects



##Update the Names in Individual
def individualname_update(modeladmin, request, queryset):

	# enable if you want to bulk redo names.....
	#queryset = Individual.objects.all()

	#note a similar function in views -- DEF namecompiler
	nameout= ''
	for actor in queryset:
		namevariable1 = ''
		namevariable2 = ''
		groupstatus = 0

		if (actor.fk_group !=None):
			targetgroup = actor.fk_group
			namevariable1 = targetgroup.group_name
			namevariable2 = targetgroup.group_name
			groupstatus = 1

		if (groupstatus == 0):
			if (actor.fk_descriptor_title !=None):
				namevariable1, namevariable2 = individualname_descriptor(namevariable1, namevariable2, actor.fk_descriptor_title) 

			if (actor.fk_descriptor_name !=None):
				namevariable1, namevariable2 = individualname_descriptor(namevariable1, namevariable2, actor.fk_descriptor_name) 

			if (actor.fk_separator_name !=None):
			 	namevariable1, namevariable2 = individualname_separator(namevariable1, namevariable2, actor.fk_separator_name) 

			if (actor.fk_descriptor_prefix1 !=None):
			 	namevariable1, namevariable2 = individualname_prefix(namevariable1, namevariable2, actor.fk_descriptor_prefix1) 

			if (actor.fk_descriptor_descriptor1 !=None):
				namevariable1, namevariable2 = individualname_descriptor(namevariable1, namevariable2, actor.fk_descriptor_descriptor1) 

			if (actor.fk_separator_1 !=None):
				namevariable1, namevariable2 = individualname_separator(namevariable1, namevariable2, actor.fk_separator_1) 

			if (actor.fk_descriptor_prefix2 !=None):
			 	namevariable1, namevariable2 = individualname_prefix(namevariable1, namevariable2, actor.fk_descriptor_prefix2) 

			if (actor.fk_descriptor_descriptor2 !=None):
				namevariable1, namevariable2 = individualname_descriptor(namevariable1, namevariable2, actor.fk_descriptor_descriptor2) 

			if (actor.fk_separator_2 !=None):
			 	namevariable1, namevariable2 = individualname_separator(namevariable1, namevariable2, actor.fk_separator_2) 

			if (actor.fk_descriptor_prefix3 !=None):
			 	namevariable1, namevariable2 = individualname_prefix(namevariable1, namevariable2, actor.fk_descriptor_prefix3) 

			if (actor.fk_descriptor_descriptor3 !=None):
				namevariable1, namevariable2 = individualname_descriptor(namevariable1, namevariable2, actor.fk_descriptor_descriptor3) 

		nameout1 = namevariable1.strip()
		nameout2 = namevariable2.strip()

		actor.fullname_modern = nameout1
		actor.fullname_original = nameout2
		actor.save()
		print ("saved")

	return(nameout1)

def individualname_descriptor(name1, name2, descriptor):
	namevariable1 = name1 + " " + descriptor.descriptor_original
	namevariable2 = name2 + " " + descriptor.descriptor_modern
	return(namevariable1, namevariable2)

def individualname_prefix(name1, name2, prefix):
	namevariable1 = name1 + " " + prefix.prefix_english
	namevariable2 = name2 + " " + prefix.prefix
	return(namevariable1, namevariable2)

def individualname_separator(name1, name2, separator):
	namevariable1 = (name1 + separator.separator_alternate).replace("^", "")
	namevariable2 = (name2 + separator.separator_alternate).replace("^", "")
	return(namevariable1, namevariable2)

def sealml_trainmodel(modeladmin, request, queryset):
	print ("ML model training initiated")

	mlmodel = mltrainmodel()

	return()


def sealml_documentmodel(modeladmin, request, queryset):
	print ("document model")

	mlmodel_document = mlmodel_document()

	return ()


## update events using ML -- only for seals with PAS at moment
def eventml_predictmatrices(modeladmin, request, queryset):
	print ("prediction process initiated")

	#if you just want to run the PAS...
	# queryset = Seal.objects.filter(
	# 	sealdescription__fk_collection=30000047)

	#if you just want to run the Schoyen...
	queryset = Seal.objects.filter(
		sealdescription__fk_collection=30000337)


	# fetch node information set
	nodeinfoset = sealml_timegroups(modeladmin, request, queryset)

	# fetch the current model
	mlmodel = mlmodelget()

	for seal in queryset:

		face_object = get_object_or_404(Face, fk_seal=seal, fk_faceterm=1)
		class_object = face_object.fk_class
		shape_object = face_object.fk_shape
		face_area = faceupdater(shape_object.pk_shape, face_object.face_vertical, face_object.face_horizontal)

		if face_area > 1:
			# pass model and features of seal to function that predicts the date
			result, result1, resulttext, finalnodevalue, df = mlpredictcase(class_object, shape_object, face_area, mlmodel)

			try:
				event_object = get_object_or_404(Event, part__fk_part__fk_support__fk_face=face_object)

			except:
				print (face_object)
				exit()

			#test to ensure the object is actually medieval....
			datestart = event_object.repository_startdate
			dateend = event_object.repository_enddate

			if datestart.year < 1500:
				if dateend.year > 1099:

					year1 = int(nodeinfoset[finalnodevalue]["quantiles"][0])
					year2 = int(nodeinfoset[finalnodevalue]["quantiles"][4])

					# event_object.startdate =  str(resulttext) + "-01-01"
					event_object.startdate =  str(year1) + "-01-01"
					event_object.enddate =  str(year2) + "-12-31"
					event_object.save()
					print (event_object, "saved", event_object.repository_startdate, event_object.repository_enddate, event_object.startdate,year1, year2)

	return()

##Display data for Seal ML nodes
def sealml_timegroups(modeladmin, request, queryset):

	nodedata = sealml_timegroups_main()

	return (nodedata)

##Update the Seal dates
def sealdate_update(modeladmin, request, queryset):

	# Try and find the earliest and most precisely dated example of a seal

	#if you just want to run the PAS...
	#queryset = Seal.objects.filter(sealdescription__fk_collection=30000047)

	for seal in queryset:
		targetseal = seal.id_seal
		manifestation_object = Manifestation.objects.filter(fk_face__fk_seal=targetseal)
		timegroupset = TimegroupC.objects.all()
		timegroup = 0
		# finaldate = 0
		# finalprecision = 0
		count = 0
		datespan = ""
		selecteddate = 0
		selectedprecision = 10000

		for manifestation1 in manifestation_object:
			indate = 0
			inprecision = 0
			count = count + 1
			print ("Target manifestation:", manifestation1)

			targetsupport = manifestation1.fk_support
			targetpart = targetsupport.fk_part
			targetevent = targetpart.fk_event

			print ("Part and Event:", targetpart, targetevent)

			#Nb: repository_startdate is a date field so have to pull the year...				
			if(targetevent.repository_startdate is not None):
				indate, inprecision = datetester(targetevent.repository_startdate, targetevent.repository_enddate)

			print ("repository", indate, inprecision)
			
			#Nb: startdate is a date field so have to pull the year...
			if(targetevent.startdate is not None):
				indate, inprecision = datetester(targetevent.startdate, targetevent.enddate)

			print ("simpleyear", indate, inprecision)

			if(targetevent.event_yearstart is not None):
				indate, inprecision = datetester(targetevent.event_yearstart, targetevent.event_yearend)

			print ("preciseyear", indate, inprecision)

			## This loop sorts the various manifestations of the seal to find the best date

			if (indate > 0):
				score1 = (indate + (inprecision * 2))
				score2 = (selecteddate + (selectedprecision * 2))

				print ("score1", score1, indate, inprecision)
				print ("score2", score2, selecteddate, selectedprecision)

				if score1 < score2:
					print("lower")
					# additionalnumber = math.trunc((inprecision/2))
					selecteddate = indate 
					selectedprecision = inprecision

				print ("selected", selecteddate, selectedprecision)

		if (2099 >= selecteddate >= 1):
			for t in timegroupset:
				if (t.timegroup_c_finaldate >= selecteddate >= t.timegroup_c_startdate):
					#timegroup = t.pk_timegroup_c
					seal.fk_timegroupc = t

		# seal.date_origin = selecteddate + (math.trunc(selectedprecision /2))
		seal.date_origin = selecteddate

		print (seal.date_origin)

		if selectedprecision < 9999:
			seal.date_precision = selectedprecision
		seal.save()
		print (seal, "saved")

# handle range dates -- if range, then determine midpoint and precision
def datetester(date1, date2):
	returndate = 0
	returnprecision = 0
	#this is a hack -- must be a better way to test if value is datetime.

	print (date1, date2)
	if str(type(date1)) == "<class 'datetime.date'>":
		date1 = date1.year
	if date1 > 0:
		returndate = date1
		returnprecision = 0
		if(date2 is not None):
			if str(type(date2)) == "<class 'datetime.date'>":
				date2 = date2.year
			if date2 > date1:
				returndate = int((date1 + date2)/2)
				returnprecision = int((date2-date1)/2)

	return(returndate, returnprecision)

##Size Measuring
def facesize_update (modeladmin, request, queryset):

	#enables this code to run for whole dataset
	queryset = Face.objects.all()

	for face in queryset:
		targetface = face.id_face
		height = face.face_vertical
		width = face.face_horizontal
		shape = face.fk_shape

		if shape != None:
			shapecode = shape.pk_shape
			output = faceupdater(shapecode, height, width)
			print(output)

			face.size_area = output
			face.save()
			print ("saved")
		else:
			print("skipped")


def sealdescription_order(modeladmin, request, queryset):

	## a function that reorders seals in a particular collection -- mostly used for Birch
	queryset = Sealdescription.objects.filter(fk_collection=9).order_by('catalogue_orderingnumber', 'id_sealdescription')

	counter = 0
	for q in queryset:
		counter += 1
		print (counter, q.catalogue_orderingnumber)

		####Deactivate for time being --- 
		# q.catalogue_orderingnumber = counter
		# q.save()
		# print ("saved")

########### Permissions ###############

class Adminpermissions(admin.ModelAdmin):

	def has_add_permission(self, request):
		return True



#########################################################################

#Model

# ModelInline
class CollectioncontributorInline(admin.TabularInline):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}
	model = Collectioncontributor
	# raw_id_fields= ('fk_contributor',)
	fields = [('fk_contributor', 'fk_collection', 'fk_collectioncontribution')]

class FaceInline(admin.TabularInline):
	model = Face
	fields = [('fk_faceterm', 'fk_class', 'fk_shape', 'face_vertical', 'face_horizontal')]
	extra = 0


class IndividualInline(admin.TabularInline):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}

	model = Individual
	fields = [('corporateentity', 'fk_group'), ('fullname_original', 'fullname_modern')]
	extra = 0
	readonly_fields = ('fullname_original', 'fullname_modern')


class ReferenceindividualInline(admin.TabularInline):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}
	model = Referenceindividual
	fields = [('referenceindividual', 'fk_individualoffice', 'fk_referencerole', 'fk_event')]
	readonly_fields = ('referenceindividual', 'fk_event', 'fk_individualoffice', 'fk_referencerole')
	extra = 0
	classes = ['collapse']

class Referenceindividual2Inline(admin.TabularInline):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}
	model = Referenceindividual
	fields = [('referenceindividual', 'fk_referencerole', 'fk_individualoffice', 'fk_individual')]
	raw_id_fields= ('fk_individual',)
	extra = 0
	classes = ['collapse']


class RelationshipBranchInline(admin.TabularInline):
	model = RelationshipBranch
	fields = [('fk_individual', 'fk_relationshiprole')]
	raw_id_fields= ('fk_individual',)
	#readonly_fields = ('fk_individual',)
	extra = 0


class SealInline(admin.TabularInline):
	model = Seal
	fields = [('fk_individual_realizer'), ('date_origin', 'date_precision'), ('fk_sealtype')]
	raw_id_fields= ('fk_individual_realizer',)
	readonly_fields = ('date_origin', 'date_precision')

class SealdescriptionInline(admin.TabularInline):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}
	model = Sealdescription
	fields = [('fk_collection', 'sealdescription_title'), ('motif_obverse',  'legend_obverse'), ('motif_reverse','legend_reverse')]
	extra = 0


# ModelAdmin Class
class ChangesAdmin(admin.ModelAdmin):
    list_display = ('pk_change', 'change_date')
    search_fields = ['change']
    fields = [('change_date', 'change')]

class CollectionsAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}
	list_display = ('id_collection', 'collection_shorttitle')
	fieldsets = (
		('Title', {
    		'fields': (('collection_shorttitle', 'collection_fulltitle', 'collection_title'),
    		)}),
		('Publication', {
    		'fields': (('collection_publicationdata', 'collection_url'),
    		)}),
		('Other', {
    		# 'classes': ('collapse',),
     		'fields':(('fk_unit', 'collection_thumbnail', 'fk_contributor'), 
     		)}),
    	)

	inlines = [CollectioncontributorInline]

class ContributorAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}
	list_display = ('name_last', 'name_first', 'name_middle', 'uricontributor')
	ordering = ('name_last', 'name_first')

class DescriptorAdmin(admin.ModelAdmin):
	list_display = ('descriptor_original', 'descriptor_modern')
	search_fields = ['descriptor_original']
	fields = [('descriptor_original', 'descriptor_modern', 'fk_descriptor'), ('descriptor_comment')]

class EventAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}

	actions = [eventml_predictmatrices, event_comparespans]
	list_display = ('pk_event', 'fk_locationreference', 'startdate', 'enddate')
	search_fields = ['pk_event', 'fk_locationreference']
	fieldsets = (
		('Details', {
    		'fields': (('startdate', 'enddate'),
    		)}),
		('Time', {
    		'classes': ('collapse',),
     		'fields':(('fk_dateapprox_event_start', 'event_daystart', 'fk_month_event_start', 'event_yearstart'), 
     			('event_comment_start'), 
     			('fk_dateapprox_event_end', 'event_dayend', 'fk_month_event_end', 'event_yearend'),
     			('event_comment_end'),  
     		)}),
    	('Place', {
    		'classes': ('collapse',),
    		'fields':(('fk_locationreference'), ('event_comment_location'), 
    		)}),
   	   	('Time and Place: Repository', {
    		'classes': ('collapse',),
    		'fields':(('repository_startdate', 'repository_enddate', 'repository_location'), 
    		)}),
    	)
	ordering = ('pk_event',)
	raw_id_fields= ('fk_locationreference',)

	inlines = [Referenceindividual2Inline]

class FaceAdmin(admin.ModelAdmin):
	list_display = ('id_face', 'fk_seal', 'fk_shape', 'face_vertical', 'face_horizontal', 'size_area')
	search_fields = ['id_face']
	actions = [facesize_update]
	fields = [('fk_seal', 'fk_shape', 'face_vertical', 'face_horizontal')]


class GroupnameAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}
	list_display = ('group_name', 'id_group', 'fk_group_class', 'fk_group_order')
	search_fields = ['group_name']
	ordering = ('group_name',)
	inlines = [IndividualInline]
	fields = [('group_name', 'fk_group_class', 'fk_group_order')]
	list_filter = ('fk_group_order', 'fk_group_class')


class IndividualAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}

	list_display = ('id_individual', 'fullname_original', 'corporateentity')
	#list_filter = ('fk_descriptor_name', 'fk_group')
	search_fields = ['id_individual', 'fullname_original']
	ordering = ('fullname_original',)
	actions = [individualname_update]
	fieldsets = (
		('Formatted Name', {

    		'fields': (('fullname_original', 'fullname_modern'),
    		)}),
    	('Name Elements', {
    		'classes': ('collapse',),
    		'fields':(('corporateentity', 'fk_group'), 
    		('fk_descriptor_title', 'fk_descriptor_name', 'fk_separator_name'),
    		('fk_descriptor_prefix1', 'fk_descriptor_descriptor1', 'fk_separator_1'), 
    		('fk_descriptor_prefix2', 'fk_descriptor_descriptor2', 'fk_separator_2'), 
    		('fk_descriptor_prefix3', 'fk_descriptor_descriptor3')
    		)}),
    	)
	readonly_fields = ('fullname_original','fullname_modern')

	inlines = [ReferenceindividualInline]

class ItemAdmin(admin.ModelAdmin):
	list_display = ('id_item', 'shelfmark')
	search_fields = ['id_item', 'shelfmark']
	actions = [itemshelfmark_update]
	fields = [('shelfmark', 'fk_repository', 'fk_series')]


class LogAdmin(admin.ModelAdmin):
    list_display = ('fk_userdigisig', 'action_time')
    search_fields = ['fk_userdigisig']
    fields = [('fk_userdigisig', 'action_time', 'action_entityedit', 'action_editrequest')]


class ReferenceindividualAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}

	list_display = ('referenceindividual', 'fk_individual')
	search_fields = ['referenceindividual']
	ordering = ('pk_referenceindividual',)
	fields = [('referenceindividual','fk_individual'), ('fk_referencerole', 'fk_event')]
	raw_id_fields= ('fk_individual', 'fk_event')
	readonly_fields = ('fk_event',)


class RelationshipnodeAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}

	list_display = ('fk_event', "participants_count", "participants_names")
	search_fields = ['fk_event']
	fields = [('fk_event', 'comment')]
	inlines = [RelationshipBranchInline]
	raw_id_fields= ('fk_event',)
	readonly_fields = ('fk_event',)

	#https://docs.djangoproject.com/en/4.0/ref/contrib/admin/
	#https://www.dothedev.com/blog/2019/10/12/django-admin-show-custom-field-list_display/
	#https://medium.com/@singhgautam7/django-annotations-steroids-to-your-querysets-766231f0823a


	def participants_names(self, obj):
		displaystring = ""
		print(obj.pk_relationship_node)
		relationship_object = RelationshipBranch.objects.filter(fk_relationshipnode=obj.pk_relationship_node)
		for i in relationship_object:
			print(i.fk_individual)
			displaystring= displaystring + str(i.fk_individual)

		return format_html(displaystring)

		#### these two functions are modelled on -- https://www.dothedev.com/blog/2019/10/12/django-admin-show-custom-field-list_display/
	def participants_count(self, obj):
		return obj._participants_count

	def get_queryset(self, request):
		queryset = super().get_queryset(request)
		queryset = queryset.annotate(
			_participants_count=Count("relationshipbranch", distinct=True),
			)
		return queryset

class RepresentationAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}
	
	list_display = ('id_representation', 'fk_collection', 'image_thumb')
	search_fields = ['id_representation']
	fields = [
		('fk_contributor_creator', 'fk_representation_type', 'fk_collection'),
		('dimensions', 'width', 'height', 'representation_datecreated', 'image_thumb'),
    	('representation_filename', 'original_representation_filename'),
    	('fk_contributor', 'representation_date'),
    	('fk_digisig', 'fk_manifestation',  'fk_collection_old'), 
    	('fk_access', 'fk_rightsholder'),
    	('fk_connection', 'primacy')
    ]

	raw_id_fields= ('fk_manifestation',)
	readonly_fields = ('image_thumb',)
	
	#https://stackoverflow.com/questions/2443752/django-display-image-in-admin-interface
	def image_thumb(self, obj):
		if obj.representation_thumbnail:
			targetvalue = "https://f000.backblazeb2.com/file/repository-digisig/" + obj.representation_thumbnail
			obj.image_thumb = mark_safe('<img src="%s" style="width: 45px; height:45px;" />' % targetvalue)
			
		else:
			obj.image_thumb = 'No Image found'
		 
		return obj.image_thumb


class SealAdmin(admin.ModelAdmin):
	list_display = ('id_seal', 'date_origin', 'date_precision', 'fk_timegroupc')
	search_fields = ['id_seal']
	actions = [sealdate_update, sealml_trainmodel, sealml_documentmodel, sealml_timegroups]
	inlines = [FaceInline, SealdescriptionInline]
	fields = [('fk_individual_realizer'), ('date_origin', 'date_precision'), ('biface_seal','ancientgem', 'fk_sealtype')]
	raw_id_fields= ('fk_individual_realizer',)
	readonly_fields = ('date_origin', 'date_precision')


class SealdescriptionAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':1, 'cols':40})}
	}

	list_display = ('id_sealdescription', 'fk_collection', 'sealdescription_identifier', 'sealdescription_title')
	search_fields = ['sealdescription_identifier']
	actions = [sealdescription_order]
	# fields = [('fk_seal', 'fk_collection'), ('motif_obverse',  'legend_obverse'), ('motif_reverse','legend_reverse')]
	list_filter = ('fk_collection',)


	fieldsets = (
		('Details', {
    		'fields': (('fk_collection', 'sealdescription_identifier'), ('sealdescription_title'), ('fk_seal'),
    		)}),
		('Description', {
     		'fields':(('sealdescription'), 
     		)}),
    	('Motif Obverse', {
    		'classes': ('collapse',),
    		'fields':(('motif_obverse', 'legend_obverse'), 
    		)}),
   	   	('Motif Reverse', {
    		'classes': ('collapse',),
    		'fields':(('motif_reverse', 'legend_reverse'), 
    		)}),
    	('Dimensions', {
    		'classes': ('collapse',),
    		'fields':(('shape', 'sealsize_vertical', 'sealsize_horizontal'), 
    		)}),
    	)

	raw_id_fields= ('fk_seal',)


class SealdescriptionAdmin2(admin.ModelAdmin):
	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':10, 'cols':100})}
	}

	list_display = ('id_sealdescription', 'fk_collection', 'sealdescription_identifier', 'sealdescription_title')
	search_fields = ['sealdescription_identifier']
	actions = [sealdescription_order]
	# fields = [('fk_seal', 'fk_collection'), ('motif_obverse',  'legend_obverse'), ('motif_reverse','legend_reverse')]
	list_filter = ('fk_collection',)


	fieldsets = (
		('Details', {
    		'fields': (('fk_collection', 'sealdescription_identifier'), ('sealdescription_title'), ('fk_seal'),
    		)}),
		('Description', {
     		'fields':(('sealdescription'), 
     		)}),
     	('Dimensions', {
    		'fields':(('shape', 'sealsize_vertical', 'sealsize_horizontal'), 
    		)}),
    	)

	raw_id_fields= ('fk_seal',)

class SealtypeAdmin(admin.ModelAdmin):

	formfield_overrides = {
		models.CharField: {'widget': TextInput(attrs={'size':'20'})},
		models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})}
	}

	list_display = ('id_sealtype', 'sealtype_name')
	search_fields = ['sealtype_name']
	inlines = [SealInline]


	fieldsets = (
		('Seal Type', {
			'fields': ('sealtype_name','sealtype_example', 'sealtype_time', 'sealtype_place', 'sealtype_history', 'sealtype_bibliography', 'sealtype_description')
			}),
		)

	# class meta:
	# 	default_permissions = ('add', 'change', 'delete', 'view')

	# def has_add_permission(self, request):
	# 	return True

class SupportAdmin(admin.ModelAdmin):

	list_display = ('id_support', 'fk_item', 'fk_part')

	search_fields = ['id_support']
	raw_id_fields= ('fk_part',)


class ChangeAdmin(admin.ModelAdmin):

	list_display = ('pk_change', 'change', 'change_date')
	search_fields = ['change_date']
	#raw_id_fields= ('fk_part',)	

#######################################################################################


# Register your models here.
admin.site.register(Seal, SealAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Manifestation,)
admin.site.register(Individual, IndividualAdmin)
admin.site.register(Face, FaceAdmin)
admin.site.register(Sealdescription, SealdescriptionAdmin2)
admin.site.register(Changes, ChangesAdmin)
admin.site.register(Descriptor, DescriptorAdmin)
admin.site.register(Groupname, GroupnameAdmin)
admin.site.register(Referenceindividual, ReferenceindividualAdmin)
admin.site.register(RelationshipNode, RelationshipnodeAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Collection, CollectionsAdmin)
admin.site.register(Collectioncontributor,)
admin.site.register(Contributor, ContributorAdmin)
admin.site.register(Collectioncontribution,)
admin.site.register(Representation, RepresentationAdmin)
#admin.site.register(Logdigisigedit, LogAdmin)
admin.site.register(Support, SupportAdmin)
admin.site.register(Sealtype, SealtypeAdmin)
