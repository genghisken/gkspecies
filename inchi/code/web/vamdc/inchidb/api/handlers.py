from piston.handler import BaseHandler
from piston.utils import rc, validate
from inchidb.db.utils import getInChIAndInChIKeyFromSMILES, getInChIAndInChIKeyFromCML, getInChIAndInChIKeyFromMOL
from inchidb.db.models import *
from inchidb.db.common import *
import urllib
import inchiapi
from django.db.models import Avg, Max, Min, Count
import datetime
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

# Allow Django to save files
from django.core.files import File

# Need to refer to MEDIA_ROOT until I find the correct way of configuring this
from django.conf import settings

SPECIESTYPE = { 'atom': 1, 'molecule': 2 }
MARKUPTYPE = { 'plain': 1, 'html': 2, 'rest': 3 }

class InchiHandler( BaseHandler ):
    allowed_methods = ('GET','POST',)

    def read( self, request, expression ):
        inchi, inchikey = getInChIAndInChIKeyFromSMILES(str(expression), doNotAddH = False)
        return {'inchi': inchi, 'inchikey': inchikey}


    #@validate(CmlSmilesMolForm, 'POST')
    def create(self, request):

        data = request.data

        smiles = None
        cml = None
        mol = None
        doNotAddH = False
        reconnectMetal = False

        inchi = None
        inchikey = None

        try:
            doNotAddH = data['doNotAddH']
        except KeyError, e:
            pass

        try:
            reconnectMetal = data['reconnectMetal']
        except KeyError, e:
            pass

        try:
            smiles = data['smiles']
            smiles = urllib.unquote(smiles)
        except KeyError, e:
            pass

        try:
            cml = data['cml']
            cml = urllib.unquote(cml)
        except KeyError, e:
            pass

        try:
            mol = data['mol']
            mol = urllib.unquote(mol)
        except KeyError, e:
            pass

        # Process always in this order.  MOL takes priority.
        if mol:
            inchi, inchikey = getInChIAndInChIKeyFromMOL(str(mol), doNotAddH = doNotAddH, reconnectMetal = reconnectMetal)
            if not inchikey:
                response = rc.BAD_REQUEST
                response.content = {'ERROR': 'Please provide a valid MOL value.'}
                return response
        elif cml:
            inchi, inchikey = getInChIAndInChIKeyFromCML(str(cml), doNotAddH = doNotAddH, reconnectMetal = reconnectMetal)
            if not inchikey:
                response = rc.BAD_REQUEST
                response.content = {'ERROR': 'Please provide a valid CML value.'}
                return response
        elif smiles:
            inchi, inchikey = getInChIAndInChIKeyFromSMILES(str(smiles), doNotAddH = doNotAddH, reconnectMetal = reconnectMetal)
            if not inchikey:
                response = rc.BAD_REQUEST
                response.content = {'ERROR': 'Please provide a valid SMILES value.'}
                return response
        else:
            # OK no valid data, so request null inchi/inchikey
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'Please provide a value for "mol", "cml" or "smiles"'}
            return response

        response = rc.CREATED
        response.content = dict({'inchi': inchi, 'inchikey': inchikey})
        return response


class AddInchiHandler( BaseHandler ):
    allowed_methods = ('POST',)

    @validate(AddInChIAPIForm, 'POST')
    def create(self, request):

#        if request.form.is_valid():
#            response = rc.CREATED
#            inchikey = str(request.form.cleaned_data['inchikey']).strip()
#            response.content = {'inchikey': inchikey}
#            return response

        smiles = None
        cml = None
        mol = None
        conformer_name = None

        speciesAdded = True
        duplicate_instance = 0

        inchi = urllib.unquote(str(request.form.cleaned_data['inchi']).strip())
        inchikey = str(request.form.cleaned_data['inchikey']).strip()
        mass_number = int(request.form.cleaned_data['mass_number'])
        charge = int(request.form.cleaned_data['charge'])
        stoichiometric_formula = urllib.unquote(str(request.form.cleaned_data['stoichiometric_formula']).strip())
        add_duplicate = request.form.cleaned_data['add_duplicate']

        duplicate_instance = request.form.cleaned_data['duplicate_instance']
        if duplicate_instance:
            duplicate_instance = int(duplicate_instance)

        cml = urllib.unquote(str(request.form.cleaned_data['cml']))
        mol = urllib.unquote(str(request.form.cleaned_data['mol']))
        smiles = urllib.unquote(str(request.form.cleaned_data['smiles']).strip())

        conformer_name_field = str(request.form.cleaned_data['conformer_name']).strip()
        conformer_names = conformer_name_field.split('|') if conformer_name_field else []

        exceptions_field = str(request.form.cleaned_data['exceptions']).strip()
        exceptions = exceptions_field.split('|') if exceptions_field else []

        # Now check that an exception is stated or a conformer name is added if "add_duplicate" is set
        if add_duplicate and (not exceptions and not conformer_names):
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'Set conformer name or set exception reason (when not a conformer)'}
            return response

        # Now check that conformers and exceptions not both set
        if exceptions and conformer_names:
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'Set conformer name OR exception reason (one or the other, not both)'}
            return response

        try:
            species_type = SPECIESTYPE[str(request.form.cleaned_data['species_type']).strip()]
        except KeyError, e:
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'Species type must be "atom" or "molecule"'}
            return response

        try:
            markup_type = MARKUPTYPE[str(request.form.cleaned_data['markup_type']).strip()]
        except KeyError, e:
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'Markup type must be "plain" or "html" or "rest"'}
            return response

        # Now check that the inchi and inchikey are partners
        if inchikey != inchiapi.GetINCHIKeyFromINCHI(inchi,1,1)[1]:
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'inchi and inchikey are not a pair'}
            return response

        if 'InChI=1/' in inchi:
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'Sorry - Non-standard InChI/InChiKey pairs are not allowed for the time being. Consider using "add_duplicate"'}
            return response


        names_field = urllib.unquote(unicode(request.form.cleaned_data['names']).strip())
        structural_formulae_field = urllib.unquote(str(request.form.cleaned_data['structural_formulae']).strip())

        resource_urls_field = str(request.form.cleaned_data['resource_urls']).strip()
        resource_urls = resource_urls_field.split('|') if resource_urls_field else []

        database_source = str(request.form.cleaned_data['database_source']).strip()

        if database_source:
            try:
                databaseSource = VamdcMemberDatabases.objects.get(short_name=database_source)
                source_database_identifiers_field = str(request.form.cleaned_data['source_database_identifiers']).strip()
            except ObjectDoesNotExist, e:
                response = rc.BAD_REQUEST
                databasesResultSet = VamdcMemberDatabases.objects.all()
                databases = []
                for row in databasesResultSet:
                    databases.append(row.short_name)
                response.content = {'ERROR': 'Specified database does not exist. Databases are: %s' % ', '.join(databases)}
                return response
        else:
            # Use the default database source of 0
            databaseSource = VamdcMemberDatabases.objects.get(pk=0)


        # Now split the aliases by semicolon
        names = names_field.split('|')
        structural_formulae = structural_formulae_field.split('|')

        # Both of these conditions can't be true at the same time.
        if duplicate_instance and add_duplicate:
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'Cannot specify an instance and to create a new instance in the same request'}
            return response

        speciesList = VamdcSpecies.objects.filter(inchikey = inchikey)
        if len(speciesList) < duplicate_instance:
            response = rc.BAD_REQUEST
            response.content = {'ERROR': 'Cannot specify an instance that does not exist'}
            return response


        if add_duplicate:
            maxSuffixID = VamdcSpecies.objects.filter(inchikey = inchikey).aggregate(Max('inchikey_duplicate_counter'))['inchikey_duplicate_counter__max']
        else:
            maxSuffixID = None

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


        # For the time being hard wire the markup type to 1
        markupType = VamdcMarkupTypes.objects.get(pk=markup_type)

        # Species type hard wired to 2 = Molecule
        speciesType = VamdcSpeciesTypes.objects.get(pk=species_type)

        try:
            # For the time being just set the inchikey and vamdc_inchikeys to be equal.
            # 2012-09-06 KWS Need to define Stoichiometric Formula and all the other new columns.

            cmlFilename = None
            # Write out the media files
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
            species.save(force_insert=True)


        except IntegrityError, e:
            if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                # The object already exists.  Pass a message back to inform the user.
                speciesAdded = False

        # Make sure that the following data is associated with the right species. We know
        # that it exists if we got this far.
        if duplicate_instance:
            species_id = "%s-%d" % (inchikey, duplicate_instance)
            species = VamdcSpecies.objects.get(pk=species_id)

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

        if databaseSource.id > 0:
            source_database_identifiers = source_database_identifiers_field.split('|')

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


        response = rc.CREATED
        response.content = dict({'inchi': inchi, 'inchikey': inchikey, 'mass_number': mass_number, 'charge': charge, 'names': names, 'structural_formulae': structural_formulae, 'stoichiometric_formula': stoichiometric_formula, 'species_added': speciesAdded, 'smiles': smiles})
        return response

