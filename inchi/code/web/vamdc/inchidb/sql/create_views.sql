-- Nice use of a new group function built into MySQL
  create or replace view vamdc_view_species_list as
  select id, mass_number mass,
         (select group_concat(name  order by search_priority separator '; ') from vamdc_species_names n where n.species_id = s.id and n.markup_type_id = 1) name,
         stoichiometric_formula,
         (select group_concat(formula  order by search_priority separator '; ') from vamdc_species_struct_formulae f where f.species_id = s.id and f.markup_type_id = 1) structural_formula
    from vamdc_species s
;
