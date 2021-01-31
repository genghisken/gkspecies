# Create your views here.

from django.conf.urls.defaults import *
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import Avg, Max, Min, Count
from django.db import IntegrityError
from inchidb.db.models import *
from inchidb.db.dbviews import *
import django_tables as tables
from math import log
import datetime


from inchidb.db.utils import getInChIAndInChIKeyFromSMILES, getInChIAndInChIKeyFromCML, getInChIAndInChIKeyFromMOL, jsMultilineString

from django.db.models import Q    # Need Q objects for OR query

# Allow Django to save files
from django.core.files import File
 
# Required for pagination
from django.template import RequestContext

# 2012-05-07 KWS Newly created Python API to InChI API.  Used to generate
#                the inchikey from an inchi.
import inchiapi

from inchidb.db.common import *

# Need to refer to MEDIA_ROOT until I find the correct way of configuring this
from django.conf import settings

def homepage(request):
    inchi = None
    inchikey = None
    if request.method == 'POST':
        form = CMLandSMILESForm(request.POST)
        if form.is_valid(): # All validation rules pass

            inchikey_field = str(form.cleaned_data['inchikey']).strip()
            cml = str(form.cleaned_data['cml'])
            mol = str(form.cleaned_data['mol'])
            smiles = str(form.cleaned_data['smiles']).strip()
            doNotAddH = form.cleaned_data['doNotAddH']
            reconnectMetal = form.cleaned_data['reconnectMetal']
            if len(inchikey_field) > 0:
                inchikey = inchikey_field
            elif len(mol) > 0:
                inchi, inchikey = getInChIAndInChIKeyFromMOL(mol, doNotAddH = doNotAddH, reconnectMetal = reconnectMetal)
            elif len(cml) > 0:
                # If there's any CML use it in preference to SMILES
                inchi, inchikey = getInChIAndInChIKeyFromCML(cml, doNotAddH = doNotAddH, reconnectMetal = reconnectMetal)
            elif len(smiles) > 0:
                inchi, inchikey = getInChIAndInChIKeyFromSMILES(smiles, doNotAddH = doNotAddH, reconnectMetal = reconnectMetal)
            else:
                pass

            # OK - we now have an inchikey.  Does it exist?  If not redirect to form
            # to add it to the database.

            if inchikey:
                # look it up.  If it's not there redirect.
                # Otherwise give option to add aliases (prepopulated)
                molecule_queryset = VamdcSpecies.objects.filter(inchikey = inchikey)

                # 2012-09-09 KWS Send the CML also to the aliases form on the species page. Note max cookie length = 4096
                if cml and len(cml) > 0: #and len(cml) < 4096:
                    # Need to create a javascript variable with newlines, etc
                    request.session['cml'] = cml

                if smiles and len(smiles) > 0:
                    request.session['smiles'] = smiles

                if mol and len(mol) > 0:
                    request.session['mol'] = mol

                if molecule_queryset.count() > 0:
                    if molecule_queryset.count() > 1:
                        # There are more than one molecule with this inchikey - probably a conformer
                        # so which one do we want to modify?
                        # Display a list of the molecules so the user can choose
                        common_inchikey = molecule_queryset[0].inchikey
                        redirect_to = './duplicates/%s/' % common_inchikey
                    else:
                        # There's only one molecule
                        # Redirect to the single molecule page.
                        # The page should allow users to add more aliases.
                        species_id = molecule_queryset[0].id
                        redirect_to = './species/%s/' % species_id

                    return HttpResponseRedirect(redirect_to)
                else:
                    # No molecule in the database. Do we want to add it?
                    # PROBLEM here - I need to send the inchi and inchikey to the add
                    # molecule page.  Perhaps will need to redesign the index page.
                    # A possible solution is to add a parameter to the web page to hide
                    # the extra parameters form.
                    # What about redirecting to add form page with inchikey and inchi as hidden fields?

                    redirect_to = './add/'


                    # OK - what we need is a form wizard. This maintains state by storing hashed data in
                    # hidden fields.


                    # Better still - just use Django Sessions.  We can pass the data via a cookie to the add page
                    if inchi:
                        request.session['inchi'] = inchi
                    request.session['inchikey'] = inchikey

                    # 2012-04-04 KWS Send the CML also to the add page. Note max cookie length = 4096
                    if cml and len(cml) > 0: #and len(cml) < 4096:
                        # Need to create a javascript variable with newlines, etc
                        request.session['cml'] = cml

                    if smiles and len(smiles) > 0:
                        request.session['smiles'] = smiles

                    if mol and len(mol) > 0:
                        request.session['mol'] = mol

                return HttpResponseRedirect(redirect_to)

    else:
        form = CMLandSMILESForm()


    return render_to_response('db/index.html', {'form' : form, 'inchi': inchi, 'inchikey': inchikey})



def molecule(request, species_id):
    species = get_object_or_404(VamdcSpecies, pk=species_id)
    # Need form to allow addition of more aliases
    # Need link to allow addition of "duplicates" - i.e. conformers or nuclear spin isomers

    # Collect all the data for the species
    relatedSpecies = VamdcSpecies.objects.filter(inchikey=species.inchikey).exclude(id=species.id)
    speciesNames = VamdcSpeciesNames.objects.filter(species=species).order_by('search_priority', 'name')
    speciesStructuralFormulae = VamdcSpeciesStructFormulae.objects.filter(species=species).order_by('search_priority', 'formula')
    memberDatabaseIds = VamdcMemberDatabaseIdentifiers.objects.filter(species=species).order_by('member_database', 'database_species_id')
    conformers = VamdcConformers.objects.filter(species=species).order_by('id')
    exceptions = VamdcInchikeyExceptions.objects.filter(species=species).order_by('id')
    resourceURLs = VamdcSpeciesResources.objects.filter(species=species).order_by('id')

    currentDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == 'POST':
        form = AddAliasesForm(request.POST)
        if form.is_valid(): # All validation rules pass
            names_field = unicode(form.cleaned_data['names']).strip()
            structural_formulae_field = str(form.cleaned_data['structural_formulae']).strip()

            database_source = int(form.cleaned_data['database_source'])
            source_database_identifiers_field = str(form.cleaned_data['source_database_identifiers']).strip()
            resource_urls_field = str(form.cleaned_data['resource_urls']).strip()
            resource_urls = resource_urls_field.split('|')

            cml = str(form.cleaned_data['cml'])
            mol = str(form.cleaned_data['mol'])
            smiles = str(form.cleaned_data['smiles']).strip()

            conformer_name_field = str(form.cleaned_data['conformer_name']).strip()
            conformer_names = conformer_name_field.split('|')

            # Now split the aliases by semicolon
            names = names_field.split('|')
            structural_formulae = structural_formulae_field.split('|')

            markup_type = int(form.cleaned_data['markup_type'])

            markupType = VamdcMarkupTypes.objects.get(pk=markup_type)

            # Add the names - one at a time, checking for unique constraint violations.

            for name in names:
                name = name.strip()
                if name != '':
                    # Add the name

                    # Get the max search priority id.
                    maxSearchPriority = VamdcSpeciesNames.objects.filter(species = species, markup_type = markupType).aggregate(Max('search_priority'))['search_priority__max']
                    if maxSearchPriority is None:
                        maxSearchPriority = 0

                    try:
                        dbName = VamdcSpeciesNames(species = species,
                                                      name = name,
                                           search_priority = maxSearchPriority + 1,
                                               markup_type = markupType,
                                                   created = currentDate)

                        dbName.save()

                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form

            for formula in structural_formulae:
                formula = formula.strip()
                if formula != '':
                    # Add the formula

                    # Get the max search priority id.
                    maxSearchPriority = VamdcSpeciesStructFormulae.objects.filter(species = species, markup_type = markupType).aggregate(Max('search_priority'))['search_priority__max']
                    if maxSearchPriority is None:
                        maxSearchPriority = 0

                    try:
                        dbFormula = VamdcSpeciesStructFormulae(species = species,
                                                               formula = formula,
                                                       search_priority = maxSearchPriority + 1,
                                                           markup_type = markupType,
                                                               created = currentDate)

                        dbFormula.save()

                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form

            # Add the source databases aliases if any

            if database_source > 0:
                source_database_identifiers = source_database_identifiers_field.split('|')
                databaseSource = VamdcMemberDatabases.objects.get(pk=database_source)

                for database_species_id in source_database_identifiers:
                    database_species_id = database_species_id.strip()
                    if database_species_id != '':
                        # Add the member database identifier

                        try:
                            memberDatabaseId = VamdcMemberDatabaseIdentifiers(species = species,
                                                                  database_species_id = database_species_id,
                                                                      member_database = databaseSource)

                            memberDatabaseId.save()

                        except IntegrityError, e:
                            if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                                pass # Do nothing - will eventually raise some errors on the form


            # Add the external URL references, if given
            for resourceURL in resource_urls:
                resourceURL = resourceURL.strip()
                if resourceURL != '':

                    # Get the max search priority id.
                    maxSearchPriority = VamdcSpeciesResources.objects.filter(species = species, markup_type = markupType).aggregate(Max('search_priority'))['search_priority__max']
                    if maxSearchPriority is None:
                        maxSearchPriority = 0

                    try:
                        # NOTE: URL description left unset for the time being.
                        speciesResource = VamdcSpeciesResources(species = species,
                                                                    url = resourceURL,
                                                        search_priority = maxSearchPriority + 1,
                                                                created = currentDate)

                        speciesResource.save()

                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form

            # Add the conformer_names
            for conformer_name in conformer_names:
                conformer_name = conformer_name.strip()
                if conformer_name != '':
                    # Add the conformer_names

                    try:
                        conformer = VamdcConformers(species = species,
                                             conformer_name = conformer_name)

                        conformer.save()

                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form


            redirect_to = '../../species/%s/' % species_id

            return HttpResponseRedirect(redirect_to)


    else:
        try:
            cml = request.session['cml']
        except KeyError:
            cml = None

        try:
            smiles = request.session['smiles']
        except KeyError:
            smiles = None

        try:
            mol = request.session['mol']
        except KeyError:
            mol = None

        try:
            names = request.session['names']
        except KeyError:
            names = None

        try:
            structural_formulae = request.session['structural_formulae']
        except KeyError:
            structural_formulae = None

        try:
            database_source = request.session['database_source']
        except KeyError:
            database_source = 0

        try:
            source_database_identifiers = request.session['source_database_identifiers']
        except KeyError:
            source_database_identifiers = None

        try:
            resource_urls = request.session['resource_urls']
        except KeyError:
            resource_urls = None

        try:
            markup_type = request.session['markup_type']
        except KeyError:
            markup_type = 1


        form = AddAliasesForm(initial={'structural_formulae': structural_formulae,
                                       'names': names,
                                       'database_source': database_source,
                                       'source_database_identifiers': source_database_identifiers,
                                       'resource_urls': resource_urls,
                                       'cml': cml,
                                       'mol': mol,
                                       'smiles': smiles,
                                       'markup_type': markup_type})

        # Clear the session.  We want to be able to use this page to add new aliases directly
        request.session.flush()

    return render_to_response('db/molecule.html', {'form' : form, 'species' : species, 'related' : relatedSpecies, 'aliases' : speciesNames, 'db_aliases' : memberDatabaseIds, 'species_resources': resourceURLs, 'species_formulae': speciesStructuralFormulae})






def duplicates(request, species_vamdc_inchikey):
    # Duplicates page will show table of existing molecules with same inchikey
    # Attempt to add existing inchikey will redirect here if there are already
    # more than one related molecule.  Otherwise will redirect to the Molecule
    # page, which will have a link to allow addition of duplicates.

    # Pick up ALL the species with this InChIKey

    # We can't do a simple get_object_or_404 here because we might get more than one object.
    # Use get_list_or_404 instead.

    relatedSpecies = get_list_or_404(VamdcSpecies, inchikey=species_vamdc_inchikey)


    form = None

    # If the code gets this far, there should be at least ONE object.
    inchikey = relatedSpecies[0].inchikey
    inchi = relatedSpecies[0].inchi
    speciesType = relatedSpecies[0].species_type
    mass_number = relatedSpecies[0].mass_number
    charge = relatedSpecies[0].charge
    stoichiometric_formula = relatedSpecies[0].stoichiometric_formula

    if request.method == 'POST':
        form = AddDuplicateInchiForm(request.POST)
        if form.is_valid(): # All validation rules pass
            names_field = unicode(form.cleaned_data['names']).strip()
            structural_formulae_field = str(form.cleaned_data['structural_formulae']).strip()

            conformer_name_field = str(form.cleaned_data['conformer_name']).strip()
            conformer_names = conformer_name_field.split('|')
            exceptions = str(form.cleaned_data['exceptions']).strip()
            smiles = str(form.cleaned_data['smiles']).strip()
            cml = str(form.cleaned_data['cml'])
            mol = str(form.cleaned_data['mol'])

            database_source = int(form.cleaned_data['database_source'])
            source_database_identifiers_field = str(form.cleaned_data['source_database_identifiers']).strip()
            resource_urls_field = str(form.cleaned_data['resource_urls']).strip()
            resource_urls = resource_urls_field.split('|')

            names = names_field.split('|')
            structural_formulae = structural_formulae_field.split('|')

            markup_type = int(form.cleaned_data['markup_type'])

            maxSuffixID = VamdcSpecies.objects.filter(inchikey = inchikey).aggregate(Max('inchikey_duplicate_counter'))['inchikey_duplicate_counter__max']
            if maxSuffixID is None:
                maxSuffixID = 1
            else:
                maxSuffixID += 1

            # 2012-03-20 KWS Don't add a suffix if there is only one InChIKey.  Add a suffix to subsequent duplicate keys.
            if maxSuffixID == 1:
                species_id = "%s" % (inchikey)
            else:
                species_id = "%s-%d" % (inchikey, maxSuffixID)

            if database_source:
                databaseSource = VamdcMemberDatabases.objects.get(pk=database_source)
            else:
                databaseSource = VamdcMemberDatabases.objects.get(pk=0)

            # Add the species - checking for unique constraint violations.

            currentDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Write out the media files
            cmlFilename = None
            if cml:
                cmlFilename = '%s.%s' % (species_id, 'cml')
                f = open(settings.MEDIA_ROOT + cmlFilename, 'w')
                cmlFile = File(f)
                cmlFile.write(cml)
                cmlFile.close()

            molFilename = None
            if mol:
                molFilename = '%s.%s' % (species_id, 'mol')
                f = open(settings.MEDIA_ROOT + molFilename, 'w')
                molFile = File(f)
                molFile.write(mol)
                molFile.close()

            imageFilename = None

            try:
                # For the time being just set the inchikey and vamdc_inchikeys to be equal.

                species = VamdcSpecies(id = species_id,
                                    inchi = inchi,
                                 inchikey = inchikey,
               inchikey_duplicate_counter = maxSuffixID,
                   stoichiometric_formula = stoichiometric_formula,
                              mass_number = mass_number,
                                   charge = charge,
                             species_type = speciesType,
                                      cml = cmlFilename,
                                      mol = molFilename,
                                    image = imageFilename,
                                   smiles = smiles,
                                  created = currentDate,
                          member_database = databaseSource)


                species.save()


            except IntegrityError, e:
                if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                    pass # Do nothing - will eventually raise some errors on the form



            markupType = VamdcMarkupTypes.objects.get(pk=markup_type)

            # Add the names - one at a time, checking for unique constraint violations.


            for name in names:
                name = name.strip()
                if name != '':
                    # Add the name

                    # Get the max search priority id.
                    maxSearchPriority = VamdcSpeciesNames.objects.filter(species = species, markup_type = markupType).aggregate(Max('search_priority'))['search_priority__max']
                    if maxSearchPriority is None:
                        maxSearchPriority = 0

                    try:
                        dbName = VamdcSpeciesNames(species = species,
                                                      name = name,
                                           search_priority = maxSearchPriority + 1,
                                               markup_type = markupType,
                                                   created = currentDate)

                        dbName.save()

                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form


            for formula in structural_formulae:
                formula = formula.strip()
                if formula != '':
                    # Add the formula
            
                    # Get the max search priority id.
                    maxSearchPriority = VamdcSpeciesStructFormulae.objects.filter(species = species).aggregate(Max('search_priority'))['search_priority__max']
                    if maxSearchPriority is None:
                        maxSearchPriority = 0
            
                    try:
                        dbFormula = VamdcSpeciesStructFormulae(species = species,
                                                               formula = formula,
                                                       search_priority = maxSearchPriority + 1,
                                                           markup_type = markupType,
                                                               created = currentDate)

                        dbFormula.save()

                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form


            # Add the source databases aliases if any

            if database_source > 0:
                source_database_identifiers = source_database_identifiers_field.split('|')
                databaseSource = VamdcMemberDatabases.objects.get(pk=database_source)

                for database_species_id in source_database_identifiers:
                    database_species_id = database_species_id.strip()
                    if database_species_id != '':
                        # Add the member database identifier
            
                        try:
                            memberDatabaseId = VamdcMemberDatabaseIdentifiers(species = species,
                                                                  database_species_id = database_species_id,
                                                                      member_database = databaseSource)

                            memberDatabaseId.save()

                        except IntegrityError, e:
                            if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                                pass # Do nothing - will eventually raise some errors on the form

            # Add the exceptions
            for reason in exceptions:
                reason = reason.strip()
                if reason != '':
                    # Add the exceptions

                    try:
                        inchikeyException = VamdcInchikeyExceptions(species = species,
                                                                     reason = reason)

                        inchikeyException.save()

                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form

            # Add the external URL references, if given
            for resourceURL in resource_urls:
                resourceURL = resourceURL.strip()
                if resourceURL != '':

                    # Get the max search priority id.
                    maxSearchPriority = VamdcSpeciesResources.objects.filter(species = species).aggregate(Max('search_priority'))['search_priority__max']
                    if maxSearchPriority is None:
                        maxSearchPriority = 0

                    try:
                        # NOTE: URL description left unset for the time being.
                        speciesResource = VamdcSpeciesResources(species = species,
                                                                    url = resourceURL,
                                                        search_priority = maxSearchPriority + 1,
                                                                created = currentDate)

                        speciesResource.save()

                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form

            # Add the conformer_names
            for conformer_name in conformer_names:
                conformer_name = conformer_name.strip()
                if conformer_name != '':
                    # Add the conformer_names

                    try:
                        conformer = VamdcConformers(species = species,
                                             conformer_name = conformer_name)
            
                        conformer.save()
            
                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form


            redirect_to = '../../species/%s/' % species_id

            return HttpResponseRedirect(redirect_to)

    else:

        try:
            cml = request.session['cml']
        except KeyError:
            cml = None

        try:
            smiles = request.session['smiles']
        except KeyError:
            smiles = None

        try:
            mol = request.session['mol']
        except KeyError:
            mol = None

        try:
            conformer_name = request.session['conformer_name']
        except KeyError:
            conformer_name = None

        try:
            markup_type = request.session['markup_type']
        except KeyError:
            markup_type = 1


        form = AddDuplicateInchiForm(initial={'database_source': 0, 'cml': cml, 'mol': mol, 'smiles': smiles, 'conformer_name': conformer_name, 'markup_type': markup_type})


    return render_to_response('db/duplicates.html', {'form' : form, 'related' : relatedSpecies})



def add(request):
    inchi = None
    inchikey = None
    cml = None
    mol = None
    smiles = None

    if request.method == 'POST':
        form = AddInChIForm(request.POST)
        if form.is_valid(): # All validation rules pass
            inchi = str(form.cleaned_data['inchi']).strip()
            inchikey = str(form.cleaned_data['inchikey']).strip()
            mass_number = int(form.cleaned_data['mass_number'])
            charge = int(form.cleaned_data['charge'])
            stoichiometric_formula = str(form.cleaned_data['stoichiometric_formula']).strip()
            names_field = unicode(form.cleaned_data['names']).strip()
            structural_formulae_field = str(form.cleaned_data['structural_formulae']).strip()
            species_type = int(form.cleaned_data['species_type'])
            markup_type = int(form.cleaned_data['markup_type'])

            database_source = int(form.cleaned_data['database_source'])
            source_database_identifiers_field = str(form.cleaned_data['source_database_identifiers']).strip()
            resource_urls_field = str(form.cleaned_data['resource_urls']).strip()
            resource_urls = resource_urls_field.split('|')

            cml = str(form.cleaned_data['cml'])
            mol = str(form.cleaned_data['mol'])
            smiles = str(form.cleaned_data['smiles']).strip()

            conformer_name_field = str(form.cleaned_data['conformer_name']).strip()
            conformer_names = conformer_name_field.split('|')

            # Now split the aliases by semicolon
            # And add the inchi, inchikey and aliases to the database.
            # Look it up.  If it's not there add it.
            # Otherwise give option to add aliases (prepopulated)
            names = names_field.split('|')
            structural_formulae = structural_formulae_field.split('|')

            # Grab the aliases that were entered into the add molecule form
            request.session['structural_formulae'] = structural_formulae_field
            request.session['names'] = names_field
            request.session['database_source'] = database_source
            request.session['source_database_identifiers'] = source_database_identifiers_field
            request.session['conformer_name'] = conformer_name_field
            request.session['resource_urls'] = resource_urls_field
            request.session['markup_type'] = markup_type

            if database_source:
                databaseSource = VamdcMemberDatabases.objects.get(pk=database_source)
            else:
                databaseSource = VamdcMemberDatabases.objects.get(pk=0)
             
            # OK - now try to add this molecule to the database.  As before CHECK that the molecule
            # doesn't aready exist...  We'll probably need a try/catch block to check that someone
            # didn't add it between my landing at this page and hitting the 'add' button.
            molecule_queryset = VamdcSpecies.objects.filter(inchikey = inchikey)
            if molecule_queryset.count() > 0:
                if molecule_queryset.count() > 1:
                    # There are more than one molecule with this inchikey - probably a nuclear spin isomer or conformer
                    # so which one do we want to modify?
                    # Display a list of the molecules so the user can choose
                    inchikey = molecule_queryset[0].inchikey
                    redirect_to = '../duplicates/%s/' % inchikey
                else:
                    # There's only one molecule
                    # Redirect to the single molecule page.
                    # The page should allow users to add more aliases.
                    species_id = molecule_queryset[0].id

                    redirect_to = '../species/%s/' % species_id

                return HttpResponseRedirect(redirect_to)

            else:
                # Add the molecule.

                # Grab the max suffix ID for this molecule (should always be zero or null at this stage - we're not dealing with duplicates yet)

                maxSuffixID = VamdcSpecies.objects.filter(inchikey = inchikey).aggregate(Max('inchikey_duplicate_counter'))['inchikey_duplicate_counter__max']
                if maxSuffixID is None:
                    maxSuffixID = 1
                else:
                    maxSuffixID += 1

                # 2012-03-20 KWS Don't add a suffix if there is only one InChIKey.  Add a suffix to subsequent duplicate keys.
                if maxSuffixID == 1:
                    species_id = "%s" % (inchikey)
                else:
                    species_id = "%s-%d" % (inchikey, maxSuffixID)

                # Add the species - checking for unique constraint violations.

                currentDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Species type hard wired to 2 = Molecule
                speciesType = VamdcSpeciesTypes.objects.get(pk=species_type)

                # 2012-05-07 KWS Check that the InChI and InChIKey match.  If not, don't
                #                add the molecule.  Best to redirect to a page to warn
                #                the user that the InChI/InChIKey pair is invalid.

                calculatedInChIKey = inchiapi.GetINCHIKeyFromINCHI(inchi,1,1)[1]

                if calculatedInChIKey == inchikey:

                    # Write out the media files
                    cmlFilename = None
                    if cml:
                        cmlFilename = '%s.%s' % (species_id, 'cml')
                        f = open(settings.MEDIA_ROOT + cmlFilename, 'w')
                        cmlFile = File(f)
                        cmlFile.write(cml)
                        cmlFile.close()

                    molFilename = None
                    if mol:
                        molFilename = '%s.%s' % (species_id, 'mol')
                        f = open(settings.MEDIA_ROOT + molFilename, 'w')
                        molFile = File(f)
                        molFile.write(mol)
                        molFile.close()

                    imageFilename = None

                    try:

                        species = VamdcSpecies(id = species_id,
                                            inchi = inchi,
                                         inchikey = inchikey,
                       inchikey_duplicate_counter = maxSuffixID,
                           stoichiometric_formula = stoichiometric_formula,
                                      mass_number = mass_number,
                                           charge = charge,
                                     species_type = speciesType,
                                              cml = cmlFilename,
                                              mol = molFilename,
                                            image = imageFilename,
                                           smiles = smiles,
                                          created = currentDate,
                                  member_database = databaseSource)


                        species.save()


                    except IntegrityError, e:
                        if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                            pass # Do nothing - will eventually raise some errors on the form


                    markupType = VamdcMarkupTypes.objects.get(pk=markup_type)

                    # Add the names - one at a time, checking for unique constraint violations.


                    for name in names:
                        name = name.strip()
                        if name != '':
                            # Add the name

                            # Get the max search priority id.
                            maxSearchPriority = VamdcSpeciesNames.objects.filter(species = species, markup_type = markupType).aggregate(Max('search_priority'))['search_priority__max']
                            if maxSearchPriority is None:
                                maxSearchPriority = 0

                            try:
                                dbName = VamdcSpeciesNames(species = species,
                                                              name = name,
                                                   search_priority = maxSearchPriority + 1,
                                                       markup_type = markupType,
                                                           created = currentDate)

                                dbName.save()

                            except IntegrityError, e:
                                if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                                    pass # Do nothing - will eventually raise some errors on the form


                    for formula in structural_formulae:
                        formula = formula.strip()
                        if formula != '':
                            # Add the formula

                            # Get the max search priority id.
                            maxSearchPriority = VamdcSpeciesStructFormulae.objects.filter(species = species, markup_type = markupType).aggregate(Max('search_priority'))['search_priority__max']
                            if maxSearchPriority is None:
                                maxSearchPriority = 0

                            try:
                                dbFormula = VamdcSpeciesStructFormulae(species = species,
                                                                       formula = formula,
                                                               search_priority = maxSearchPriority + 1,
                                                                   markup_type = markupType,
                                                                       created = currentDate)

                                dbFormula.save()

                            except IntegrityError, e:
                                if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                                    pass # Do nothing - will eventually raise some errors on the form

                    # Add the source databases aliases if any

                    if database_source > 0:
                        source_database_identifiers = source_database_identifiers_field.split('|')
                        databaseSource = VamdcMemberDatabases.objects.get(pk=database_source)

                        for database_species_id in source_database_identifiers:
                            database_species_id = database_species_id.strip()
                            if database_species_id != '':
                                # Add the member database identifier

                                try:
                                    memberDatabaseId = VamdcMemberDatabaseIdentifiers(species = species,
                                                                          database_species_id = database_species_id,
                                                                              member_database = databaseSource)

                                    memberDatabaseId.save()

                                except IntegrityError, e:
                                    if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                                        pass # Do nothing - will eventually raise some errors on the form


                    # Add the external URL references, if given
                    for resourceURL in resource_urls:
                        resourceURL = resourceURL.strip()
                        if resourceURL != '':

                            # Get the max search priority id.
                            maxSearchPriority = VamdcSpeciesResources.objects.filter(species = species).aggregate(Max('search_priority'))['search_priority__max']
                            if maxSearchPriority is None:
                                maxSearchPriority = 0

                            try:
                                # NOTE: URL description left unset for the time being.
                                speciesResource = VamdcSpeciesResources(species = species,
                                                                            url = resourceURL,
                                                                search_priority = maxSearchPriority + 1,
                                                                        created = currentDate)

                                speciesResource.save()

                            except IntegrityError, e:
                                if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                                    pass # Do nothing - will eventually raise some errors on the form

                    # Add the conformer_names
                    for conformer_name in conformer_names:
                        conformer_name = conformer_name.strip()
                        if conformer_name != '':
                            # Add the conformer_names

                            try:
                                conformer = VamdcConformers(species = species,
                                                     conformer_name = conformer_name)
            
                                conformer.save()
            
                            except IntegrityError, e:
                                if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                                    pass # Do nothing - will eventually raise some errors on the form


                    redirect_to = '../species/%s/' % species_id

                else:
                    # The InChIKeys don't match.  Important to check this if we are to
                    # add the InChI/InChIKey manually.
                    redirect_to = '../error/'

                return HttpResponseRedirect(redirect_to)

    else:
        try:
            inchikey = request.session['inchikey']
        except KeyError:
            inchikey = None

        try:
            inchi = request.session['inchi']
        except KeyError:
            inchi = None

        try:
            cml = request.session['cml']
        except KeyError:
            cml = None

        try:
            smiles = request.session['smiles']
        except KeyError:
            smiles = None

        try:
            mol = request.session['mol']
        except KeyError:
            mol = None

        try:
            markup_type = request.session['markup_type']
        except KeyError:
            markup_type = 1

        form = AddInChIForm(initial={'inchikey': inchikey, 'inchi': inchi, 'species_type' : 2, 'markup_type' : markup_type, 'database_source': 0, 'mol': mol, 'cml': cml, 'smiles': smiles})
        # Clear the session.  We want to be able to use this page to add new molecules directly
        request.session.flush()

    return render_to_response('db/add.html', {'form' : form, 'inchi': inchi, 'inchikey': inchikey, 'cml': cml, 'smiles': smiles, 'mol': mol, 'jscml': jsMultilineString(cml), 'jsmol': jsMultilineString(mol)})


# Create a table so we can re-order the species list.
class SpeciesListTable(tables.ModelTable):
    id = tables.Column(name="id")

    class Meta:
        model = SpeciesList


# List all the molecules in the database
def molecules(request):
    species_list = SpeciesList.objects.all()
    table = SpeciesListTable(species_list, order_by=request.GET.get('sort', 'mass'))

    # NOTE: Need to add the context_instance variable for Pagination.
    #       Note also that pagination will NOT work unless the table
    #       rows are passed as a separate variable.
    return render_to_response('db/molecules.html', {'table' : table, 'rows' : table.rows}, context_instance=RequestContext(request))


def error(request):
    return render_to_response('db/error.html', context_instance=RequestContext(request))

