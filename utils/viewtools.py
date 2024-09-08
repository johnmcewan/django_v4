from digisig.models import * 
from django.shortcuts import get_object_or_404

from time import time

def sealsearch(ManifestationForm):
	manifestation_object = Manifestation.objects.all().order_by('id_manifestation')

	form = ManifestationForm(request.POST)

	if form.is_valid():

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

		rows = manifestation_object.count()

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
					fk_support__fk_part__fk_event__locationreference__fk_locationname__fk_location__fk_region=qlocation)

		if qtimegroup.isdigit():
			if int(qtimegroup) > 0:
				temporalperiod_target = (TimegroupA.objects.get(pk_timegroup_a = qtimegroup))   
				yearstart = (temporalperiod_target.timegroup_a_startdate)
				manifestation_object = manifestation_object.filter(
					fk_support__fk_part__fk_event__repository_startdate__lt=datetime.strptime(str(yearstart), "%Y")).filter(
					fk_support__fk_part__fk_event__repository_enddate__gt=datetime.strptime(str(yearstart+50), "%Y"))

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


		form = ManifestationForm(request.POST)


	return(manifestation_object, form)



	# information for presenting a seal manifestation
def sealsearchmanifestationmetadata(manifestation_object):

	manifestation_set = {}

	manifestation_object2 = manifestation_object.prefetch_related('fk_manifestation').all()

	for e in manifestation_object2:
		starttime = time()
		manifestation_dic = {}
		manifestation_dic["manifestation"] = e
		manifestation_dic["id_manifestation"] = e.id_manifestation
		manifestation_dic["fk_position"] = e.fk_position
		manifestation_dic["label_manifestation_repository"] = e.label_manifestation_repository
		manifestation_dic["imagestate_term"] = e.fk_imagestate

		facevalue = e.fk_face
		sealvalue = facevalue.fk_seal
		supportvalue = e.fk_support
		numbervalue = supportvalue.fk_number_currentposition
		partvalue = supportvalue.fk_part
		eventvalue = partvalue.fk_event
		itemvalue = partvalue.fk_item
		repositoryvalue = itemvalue.fk_repository
		representation_set = Representation.objects.filter(fk_manifestation=e.id_manifestation).filter(primacy=1)[:1]

		if representation_set.count() == 0:
			print ("no image available for:", e.id_manifestation)
			representation_set = Representation.objects.filter(id_representation=12204474)

		sealdescription_set = Sealdescription.objects.filter(fk_seal=facevalue.fk_seal)
		locationreference_set = Locationreference.objects.filter(fk_event=eventvalue.pk_event).filter(fk_locationstatus=1)[:1]

		manifestation_dic["id_seal"] = sealvalue.id_seal
		manifestation_dic["id_item"] = itemvalue.id_item

		manifestation_dic["repository_fulltitle"] = repositoryvalue.repository_fulltitle
		manifestation_dic["shelfmark"] = itemvalue.shelfmark
		# manifestation_dic["fk_supportstatus"] = supportvalue.fk_supportstatus
		# manifestation_dic["fk_attachment"] = supportvalue.fk_attachment		
		manifestation_dic["number"] = numbervalue.number
		# manifestation_dic["support_type"] = supportvalue.fk_nature

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

		for l in locationreference_set:
			locationname= l.fk_locationname
			location = locationname.fk_location
			manifestation_dic["repository_location"] = location.location
			manifestation_dic["id_location"] = location.id_location

		for r in representation_set:
			connection = r.fk_connection
			manifestation_dic["thumb"] = connection.thumb
			manifestation_dic["medium"] = connection.medium
			manifestation_dic["representation_thumbnail_hash"] = r.representation_thumbnail_hash
			manifestation_dic["representation_filename_hash"] = r.representation_filename_hash 
			# manifestation_dic["representation_thumbnail"] = r.representation_thumbnail
			# manifestation_dic["representation_filename"] = r.representation_filename
			manifestation_dic["id_representation"] = r.id_representation

		manifestation_dic["sealdescriptions"] = sealdescription_set

		manifestation_set[e.id_manifestation] = manifestation_dic
		print("Compute Time:", time()-starttime)
	return (manifestation_set)