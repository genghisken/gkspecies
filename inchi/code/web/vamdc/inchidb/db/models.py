# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

class VamdcSpeciesTypes(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=450)
    class Meta:
        db_table = u'vamdc_species_types'

class VamdcMemberDatabases(models.Model):
    id = models.IntegerField(primary_key=True)
    short_name = models.CharField(max_length=60)
    description = models.CharField(max_length=765, blank=True)
    class Meta:
        db_table = u'vamdc_member_databases'

class VamdcSpecies(models.Model):
    id = models.CharField(max_length=120, primary_key=True)
    inchi = models.TextField()
    inchikey = models.CharField(max_length=90)
    inchikey_duplicate_counter = models.IntegerField(unique=True)
    stoichiometric_formula = models.CharField(max_length=450)
    mass_number = models.IntegerField()
    charge = models.IntegerField()
    species_type = models.ForeignKey(VamdcSpeciesTypes, db_column='species_type')
    cml = models.CharField(max_length=765, blank=True)
    mol = models.CharField(max_length=765, blank=True)
    image = models.CharField(max_length=765, blank=True)
    smiles = models.TextField(blank=True)
    created = models.DateTimeField()
    member_database = models.ForeignKey(VamdcMemberDatabases, db_column='member_databases_id')
    class Meta:
        db_table = u'vamdc_species'

class VamdcConformers(models.Model):
    id = models.IntegerField(primary_key=True)
    species = models.ForeignKey(VamdcSpecies)
    conformer_name = models.CharField(max_length=450)
    class Meta:
        db_table = u'vamdc_conformers'

class VamdcInchikeyExceptions(models.Model):
    id = models.IntegerField(primary_key=True)
    species = models.ForeignKey(VamdcSpecies)
    reason = models.CharField(max_length=765)
    class Meta:
        db_table = u'vamdc_inchikey_exceptions'

class VamdcMarkupTypes(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=90)
    class Meta:
        db_table = u'vamdc_markup_types'

class VamdcMemberDatabaseIdentifiers(models.Model):
    id = models.IntegerField(primary_key=True)
    species = models.ForeignKey(VamdcSpecies)
    database_species_id = models.CharField(max_length=255, unique=True)
    member_database = models.ForeignKey(VamdcMemberDatabases)
    class Meta:
        db_table = u'vamdc_member_database_identifiers'

class VamdcSpeciesNames(models.Model):
    id = models.IntegerField(primary_key=True)
    species = models.ForeignKey(VamdcSpecies)
    name = models.CharField(max_length=450)
    markup_type = models.ForeignKey(VamdcMarkupTypes)
    search_priority = models.IntegerField()
    created = models.DateTimeField()
    class Meta:
        db_table = u'vamdc_species_names'

class VamdcSpeciesResources(models.Model):
    id = models.IntegerField(primary_key=True)
    species = models.ForeignKey(VamdcSpecies)
    url = models.CharField(max_length=765)
    description = models.CharField(max_length=450)
    search_priority = models.IntegerField()
    created = models.DateTimeField()
    class Meta:
        db_table = u'vamdc_species_resources'

class VamdcSpeciesStructFormulae(models.Model):
    id = models.IntegerField(primary_key=True)
    species = models.ForeignKey(VamdcSpecies)
    formula = models.CharField(max_length=450)
    markup_type = models.ForeignKey(VamdcMarkupTypes)
    search_priority = models.IntegerField()
    created = models.DateTimeField()
    class Meta:
        db_table = u'vamdc_species_struct_formulae'
