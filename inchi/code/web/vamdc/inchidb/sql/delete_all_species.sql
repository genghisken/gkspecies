select 'Deleting from Conformers';
delete from vamdc_conformers;
alter table vamdc_conformers auto_increment = 1;
select 'Deleting from Exceptions';
delete from vamdc_inchikey_exceptions;
alter table vamdc_inchikey_exceptions auto_increment = 1;
select 'Deleting from Names';
delete from vamdc_species_names;
alter table vamdc_species_names auto_increment = 1;
select 'Deleting from Resources';
delete from vamdc_species_resources;
alter table vamdc_species_resources auto_increment = 1;
select 'Deleting from Struct Formulae';
delete from vamdc_species_struct_formulae;
alter table vamdc_species_struct_formulae auto_increment = 1;
select 'Deleting from Member DB Identifiers';
delete from vamdc_member_database_identifiers;
alter table vamdc_member_database_identifiers auto_increment = 1;
select 'Deleting from Species';
delete from vamdc_species;
