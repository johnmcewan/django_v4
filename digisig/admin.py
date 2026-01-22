from django.contrib import admin
from django.shortcuts import get_object_or_404
from digisig.models import *
from datetime import datetime
import math
from django.forms import TextInput, Textarea
from django.db.models import Count
from django.utils.html import format_html
from statistics import mean
from django import forms

#project specific functions
from utils.mltools import *
from utils.generaltools import *
from utils.adminactions import *

#Change to admin header
admin.site.site_header = "Digisig administration"
admin.site.site_title = "Digisig Admin Portal"
admin.site.index_title = "Welcome to Digisig's administration portal"


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

class SeriesAdmin(admin.ModelAdmin):

	list_display = ('pk_series', 'fk_repository', 'series_name')
	search_fields = ['pk_series', 'series_name']
	
	readonly_fields = ('reference_preview',)

	formfield_overrides = {
		models.TextField: {'widget': forms.TextInput},
	}

	def reference_preview(self, obj):
		if not obj or not obj.pk_series:
			return "Reference will be generated after saving."
		
		# --- PLACEHOLDER LOGIC ---
		# Replace with your actual reference building logic
		parts = []
		if obj.fk_repository: parts.append(obj.fk_repository.repository_fulltitle)
		if obj.fk_separator_series: parts.append(obj.fk_separator_series.separator_alternate)
		if obj.series_abbreviated: parts.append(obj.series_abbreviated)
		if obj.fk_separator_a1: parts.append(obj.fk_separator_a1.separator_alternate)
		if obj.fk_separator_n1: parts.append(obj.fk_separator_n1.separator_alternate)
		if obj.fk_separator_a2: parts.append(obj.fk_separator_a2.separator_alternate)
		if obj.fk_separator_n2: parts.append(obj.fk_separator_n2.separator_alternate)
		if obj.fk_separator_a3: parts.append(obj.fk_separator_a3.separator_alternate)
		if obj.fk_separator_n3: parts.append(obj.fk_separator_n3.separator_alternate)

		# if obj.series_uri: parts.append(f"[{obj.prefixa1.separator_alternate}]")

		
		full_string = "".join(parts)
		
		return format_html(
			'<div style="background-color: #f0f4f8; padding: 10px; border-left: 5px solid #2c3e50;">'
			'<strong style="font-size: 14px; color: #333;">Current Preview:</strong><br>'
			'<span style="font-size: 18px; color: #0056b3;">{}</span>'
			'</div>',
			full_string
		)
	reference_preview.short_description = "Formatted Output"

	# 3. The Helper Function
	def get_fieldsets(self, request, obj=None):
		model_fields = [
			f.name for f in self.model._meta.fields 
			if f.editable and f.name != 'pk_series'
		]

		return (
			(None, {
				'fields': ('reference_preview',) + tuple(model_fields)
			}),
		)



class SupportAdmin(admin.ModelAdmin):

	list_display = ('id_support', 'fk_item', 'fk_part')

	search_fields = ['id_support']
	raw_id_fields= ('fk_part',)


class ChangeAdmin(admin.ModelAdmin):

	list_display = ('pk_change', 'change', 'change_date')
	search_fields = ['change_date']
	

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
admin.site.register(Series, SeriesAdmin)
