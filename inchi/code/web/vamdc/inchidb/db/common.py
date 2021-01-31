from django import forms
from inchidb.db.models import *
from django.db import IntegrityError

class CMLandSMILESForm(forms.Form):
    inchikey = forms.CharField(required=False, min_length=27, widget=forms.TextInput(attrs={'size':'40'}))
    mol = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}))
    cml = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 25}))
    smiles = forms.CharField(required=False, widget=forms.TextInput(attrs={'size':'60'}))
    doNotAddH = forms.BooleanField(label="Do Not Add Hydrogen", initial=False, widget=forms.CheckboxInput(), required=False)
    reconnectMetal = forms.BooleanField(label="Reconnect Metal", initial=False, widget=forms.CheckboxInput(), required=False)


class AddInChIForm(forms.Form):
    inchikey = forms.CharField(required=True, min_length=27, widget=forms.TextInput(attrs={'size':'40'}))
    inchi = forms.CharField(required=True, min_length=8, widget=forms.Textarea(attrs={'cols': 80, 'rows': 5}))
    charge = forms.IntegerField(required=True, widget=forms.TextInput(attrs={'size':'5'}))
    mass_number = forms.IntegerField(required=True, min_value=0, widget=forms.TextInput(attrs={'size':'5'}))
    stoichiometric_formula = forms.CharField(required=True, min_length=1, widget=forms.TextInput(attrs={'size':'80'}))
    markup_type = forms.ChoiceField(required=True, label='Markup Type', widget=forms.Select, choices=())
    names = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 5}))
    structural_formulae = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 60, 'rows': 4}))
    species_type = forms.ChoiceField(required=True, label='Species Type', widget=forms.Select, choices=())
    database_source = forms.ChoiceField(required=False, label='Database Source', widget=forms.Select, choices=())
    source_database_identifiers = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 60, 'rows': 2}))
    resource_urls = forms.CharField(required=False, label='External URL(s) for this species', widget=forms.Textarea(attrs={'cols': 80, 'rows': 2}))
    conformer_name = forms.CharField(required=False, label="Conformer name (if relevant)", widget=forms.TextInput(attrs={'size':'40'}))
    mol = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}))
    cml = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 25}))
    smiles = forms.CharField(required=False, widget=forms.TextInput(attrs={'size':'60'}))

    def __init__(self, *args, **kwargs):
        super(AddInChIForm, self).__init__(*args, **kwargs)
        speciesTypes = [(st.id, st.name) for st in VamdcSpeciesTypes.objects.all()]
        self.fields['species_type'].choices = speciesTypes
        markupTypes = [(st.id, st.name) for st in VamdcMarkupTypes.objects.all()]
        self.fields['markup_type'].choices = markupTypes
        databaseSources = [(db.id, db.short_name) for db in VamdcMemberDatabases.objects.all().order_by('short_name')]
        #databaseSources.append(('0', 'None'))
        self.fields['database_source'].choices = databaseSources



class AddAliasesForm(forms.Form):
    structural_formulae = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 60, 'rows': 4}))
    markup_type = forms.ChoiceField(required=True, label='Markup Type', widget=forms.Select, choices=())
    names = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 5}))
    database_source = forms.ChoiceField(required=False, label='Database Source', widget=forms.Select, choices=())
    source_database_identifiers = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 60, 'rows': 2}))
    resource_urls = forms.CharField(required=False, label='External URL(s) for this species', widget=forms.Textarea(attrs={'cols': 80, 'rows': 2}))
    conformer_name = forms.CharField(required=False, label="Conformer name (if relevant)", widget=forms.TextInput(attrs={'size':'40'}))
    mol = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}))
    cml = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 25}))
    smiles = forms.CharField(required=False, widget=forms.TextInput(attrs={'size':'60'}))

    def __init__(self, *args, **kwargs):
        super(AddAliasesForm, self).__init__(*args, **kwargs)
        markupTypes = [(st.id, st.name) for st in VamdcMarkupTypes.objects.all()]
        self.fields['markup_type'].choices = markupTypes
        databaseSources = [(db.id, db.short_name) for db in VamdcMemberDatabases.objects.all()]
        #databaseSources.append(('0', 'None'))
        self.fields['database_source'].choices = databaseSources


class AddDuplicateInchiForm(forms.Form):
    structural_formulae = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 60, 'rows': 4}))
    markup_type = forms.ChoiceField(required=True, label='Markup Type', widget=forms.Select, choices=())
    names = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 5}))
    exceptions = forms.CharField(required=False, label="Exception explanation (if not conformer)", widget=forms.TextInput(attrs={'size':'40'}))
    conformer_name = forms.CharField(required=False, label="Conformer name (if relevant)", widget=forms.TextInput(attrs={'size':'40'}))
    database_source = forms.ChoiceField(required=False, label='Database Source', widget=forms.Select, choices=())
    source_database_identifiers = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 60, 'rows': 2}))
    resource_urls = forms.CharField(required=False, label='External URL(s) for this species', widget=forms.Textarea(attrs={'cols': 80, 'rows': 2}))
    mol = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}))
    cml = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 25}))
    smiles = forms.CharField(required=False, widget=forms.TextInput(attrs={'size':'60'}))

    def __init__(self, *args, **kwargs):
        super(AddDuplicateInchiForm, self).__init__(*args, **kwargs)
        markupTypes = [(st.id, st.name) for st in VamdcMarkupTypes.objects.all()]
        self.fields['markup_type'].choices = markupTypes
        databaseSources = [(db.id, db.short_name) for db in VamdcMemberDatabases.objects.all()]
        #databaseSources.append(('0', 'None'))
        self.fields['database_source'].choices = databaseSources

#    def clean(self):
#        cleaned_data = super(AddDuplicateInchiForm, self).clean()
#        exceptions = cleaned_data.get("exceptions")
#        conformer_name = cleaned_data.get("conformer_name")
#
#        if not conformer_name and not exceptions:
#            # If neither field is set, raise an error.
#            raise forms.ValidationError("Please add at least ONE exception or conformer name.")


class CmlSmilesMolForm(forms.Form):
    cml = forms.CharField(required=False)
    mol = forms.CharField(required=False)
    smiles = forms.CharField(required=False)
    doNotAddH = forms.BooleanField(initial=False, required=False)
    reconnectMetal = forms.BooleanField(initial=False, required=False)


# add_duplicate = if there is an existing inchikey, create a new instance
# duplicate_instance = associate the data in the request with the specified instance
class AddInChIAPIForm(forms.Form):
    inchikey = forms.CharField(required=True, min_length=27)
    inchi = forms.CharField(required=True, min_length=8)
    charge = forms.IntegerField(required=True)
    mass_number = forms.IntegerField(required=True, min_value=0)
    species_type = forms.CharField(required=True)
    stoichiometric_formula = forms.CharField(required=True)
    markup_type = forms.CharField(required=True)
    add_duplicate = forms.BooleanField(initial=False, required=False)
    structural_formulae = forms.CharField(required=False)
    names = forms.CharField(required=False)
    database_source = forms.CharField(required=False)
    source_database_identifiers = forms.CharField(required=False)
    conformer_name = forms.CharField(required=False)
    exceptions = forms.CharField(required=False)
    resource_urls = forms.CharField(required=False)
    duplicate_instance = forms.IntegerField(required=False, min_value=2)
    cml = forms.CharField(required=False)
    mol = forms.CharField(required=False)
    smiles = forms.CharField(required=False)



def addAliases(species, names, aliasType, databaseAlias=False):

    # Add the names - one at a time, checking for unique constraint violations.
    for name in names:
        name = name.strip()
        if name != '':
            # Add the name

            try:
                if databaseAlias:
                    dbAlias = VamdcDatabaseAliases(database_species_id = name,
                                                               species = species,
                                                        vamdc_database = aliasType)

                    dbAlias.save()

                else:
                    alias = Aliases(name = name,
                                 species = species,
                              alias_type = aliasType,
                         search_priority = aliasType.id)

                    alias.save()

            except IntegrityError, e:
                if e[0] == 1062: # Duplicate Key error - don't bother doing anything.
                    pass # Do nothing - will eventually raise some errors on the form
    return 0



