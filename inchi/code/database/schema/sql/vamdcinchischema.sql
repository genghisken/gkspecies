-- 2012-07-17 VAMDC InChI database schema version 0.2
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL';

CREATE SCHEMA IF NOT EXISTS `vamdcspecies` DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ;
USE `vamdcspecies` ;

-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_species_types`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_species_types` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_species_types` (
  `id` INT NOT NULL COMMENT 'Species Types IDs are currently 1=atom, 2=molecule, 3=particle, 4=solid.  The latter two are not currently supported.' ,
  `name` VARCHAR(150) NOT NULL COMMENT 'Atom, Molecule, Particle, Solid.' ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB
COMMENT = 'Type of species (only Atom and Molecule currently supported)\n\n1=Atom\n2=Molecule\n3=Particle\n4=Solid' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_member_databases`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_member_databases` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_member_databases` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'The assigned database ID.' ,
  `short_name` VARCHAR(20) NOT NULL COMMENT 'The VAMDC member database (short) name.' ,
  `description` VARCHAR(255) NULL COMMENT 'An optional more complete description of the member database (designed to be used on web pages, etc).' ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB
COMMENT = 'VAMDC Member Databases.  The current contents are set to:\n\n0 Unspecified\n1 UMIST\n2 HITRAN\n3 BASECOL\n4 CDMS\n5 VALD\n6 CHIANTI\n7 KIDA\n8 ICBDM\n9 CDSD\n10 OACTLASP\n11 TOPBASE\n12 TSBPAH\n13 TIPBASE\n14 GSMARSMPO\n15 GSMARE\n16 GHOSST\n17 LLSD\n18 STARKB\n19 SPECTRW3\n20 WIADIS\n21 JPL\n22 VALDM' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_species`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_species` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_species` (
  `id` VARCHAR(40) NOT NULL COMMENT 'The ID column type is a VARCHAR(40), not an INT because this is in fact the InChIKey.  An optional hyphen and a number (the inchikey_duplicate_counter) is appended to the InChIKey to make the ID if the counter\'s value is greater than 1.' ,
  `inchi` LONGTEXT NOT NULL COMMENT 'The Standard InChI and ONLY the Standard InChI.  No exceptions.  Created as a LONGTEXT because InChI values can potentially be very long.' ,
  `inchikey` VARCHAR(30) NOT NULL COMMENT 'The Standard InChIKey and ONLY the Standard InChIKey.  No exceptions.  Any duplicates should be created by incrementing the inchikey_duplicate_counter, whose value is normally 1.' ,
  `inchikey_duplicate_counter` INT NOT NULL DEFAULT 1 COMMENT 'This is a counter whose value is normally 1.  If this value is 1 then the VAMDC species registry ID will be equal to the InChIKey.  Otherwise the species registry ID is the InChIKey + hyphen + inchikey_duplication_counter.  It is used when creating species whose InChIKeys are identical - e.g. Conformers or Disconnected Metal species like metal cyanides and isocyanides.\n\nIt is MANDATORY to add a value to the inchikey_exceptions table if the value of the counter > 1.\n\nIt is also additionally MANDATORY to add a value to the conformers table if the exception is because of conformerism.' ,
  `stoichiometric_formula` VARCHAR(150) NOT NULL COMMENT 'The stoichiometric formula, with elements arranged in PURELY ALPHABETICAL ORDER.\n\nThe field also includes any charges, even though charge is also described in a separate column.  Multiple charges MUST be represented as (e.g.) +2 or +3, NOT ++ or +++.\n\nNo isotope information must be present in this field.' ,
  `mass_number` INT NOT NULL COMMENT 'The relative mass number, which is an integer, NOT the rounded total mass.' ,
  `charge` INT NOT NULL COMMENT 'Despite the fact that charge is included in stoichiometric formula, it is included here in a separate column - mainly to assist in the formation of valid XSAMS.' ,
  `species_type` INT NOT NULL COMMENT 'Identifies what kind of species this is.  A foreign key to the species_types table.' ,
  `cml` VARCHAR(255) NULL COMMENT 'A reference to an associated file, not the file contents.  The name of the file will always be the vamdc species ID.cml' ,
  `mol` VARCHAR(255) NULL COMMENT 'A reference to an associated file, not the file contents.  The name of the file will always be the vamdc species ID.mol' ,
  `image` VARCHAR(255) NULL COMMENT 'A reference to an associated file, not the file contents.  The name of the file will always be the vamdc species ID.png.\n\nPNG files MUST be the default.' ,
  `smiles` LONGTEXT NULL COMMENT 'The SMILES information can be used to reconstruct a model of the species, though note that bond angle information is not represented.  Note that because SMILES strings can be very long, this has been created as a LONGTEXT column.' ,
  `created` DATETIME NOT NULL COMMENT 'The date the species was added to the database.' ,
  `member_databases_id` INT NOT NULL DEFAULT 0 COMMENT 'The source database from which this species was originally inserted. A value of zero indicates that the species information was generated or acquired from a source that is not one of the VAMDC member databases.' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_species_type_idx` (`species_type` ASC) ,
  INDEX `inchi_idx` (`inchi`(64) ASC) ,
  INDEX `inchikey_idx` (`inchikey` ASC) ,
  INDEX `fk_vamdc_member_database_idx` (`member_databases_id` ASC) ,
  INDEX `stoichiometric_formula_idx` (`stoichiometric_formula` ASC) ,
  INDEX `mass_number_idx` (`mass_number` ASC) ,
  INDEX `charge_idx` (`charge` ASC) ,
  INDEX `cml_idx` (`cml` ASC) ,
  INDEX `mol_idx` (`mol` ASC) ,
  INDEX `image_idx` (`image` ASC) ,
  INDEX `created_idx` (`created` ASC) ,
  INDEX `member_database_idx` (`member_databases_id` ASC) ,
  UNIQUE INDEX `inchikey_inchikeyduplicate_idx` (`inchikey` ASC, `inchikey_duplicate_counter` ASC) COMMENT 'A unique index to stop the addition of duplicate InChIKeys and associated InChIKey counters.  The web application combines the two columns to form the ID, but this is an extra constraint in an attempt to preserve the integrity of the database.',
  INDEX `smiles_idx` (`smiles`(64) ASC) ,
  CONSTRAINT `fk_species_species_types1`
    FOREIGN KEY (`species_type` )
    REFERENCES `vamdcspecies`.`vamdc_species_types` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_vamdc_species_registry_vamdc_member_databases1`
    FOREIGN KEY (`member_databases_id` )
    REFERENCES `vamdcspecies`.`vamdc_member_databases` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'Table to store all the VAMDC species identifiers a.k.a VAMDC Registry IDs.  The difference between them and the InChIKey is normally nothing.  For conformers (in particular) a hyphen and a digit (greater than 1) will be appended to the InChIKey and form the unique ID.\n\nNOTE 1:  No separate Isomer or Isotopologue table will be created for the time being.  This is because isomers can be grouped into isomers by stoichiometric formula and isotopologues by the first 14 characters of the InChIKey.\n\nNOTE 2:  The image, CML and MOL columns refer to FILES that contain the relevant data, not the data themselves.  If an image, CML or MOL file is provided we will assume that its name is identical to its species identifier (registry ID).  Although the columns appear redundant, they provide the user with a way of selecting only the data with an associated file. (The downside of this approach is that the database requires synchronisation with the files.)' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_markup_types`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_markup_types` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_markup_types` (
  `id` INT NOT NULL COMMENT 'Contains defined values only.  Current Values are:\n\n1 = Plain Text,\n2 = HTML\n3 = ReStructured Text' ,
  `name` VARCHAR(30) NOT NULL COMMENT 'The markup type:\n\nPlain Text\nHTML\nReStructured Text' ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB
COMMENT = 'Table to hold different markup types for describing names or formulae - e.g. text (i.e. plain text), HTML, reStructured Text.' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_species_names`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_species_names` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_species_names` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'An internal counter.' ,
  `species_id` VARCHAR(40) NOT NULL COMMENT 'The species ID.  Foreign key reference to the species table.' ,
  `name` VARCHAR(150) NOT NULL COMMENT 'The chemical name of the species.' ,
  `markup_type_id` INT NOT NULL DEFAULT 1 COMMENT 'The kind of markup used to represent the name.' ,
  `search_priority` INT NOT NULL COMMENT 'Search priority allows the names to be ordered in a custom manner.' ,
  `created` DATETIME NOT NULL COMMENT 'The date the species name was added.' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_speciesid_idx` (`species_id` ASC) ,
  UNIQUE INDEX `speciesid_name_markup_idx` (`species_id` ASC, `name` ASC, `markup_type_id` ASC) COMMENT 'Unique index to stop same name being added more than once for a species.',
  INDEX `fk_markuptypeid_idx` (`markup_type_id` ASC) ,
  INDEX `name_idx` (`name` ASC) ,
  INDEX `created_idx` (`created` ASC) ,
  CONSTRAINT `fk_aliases_species`
    FOREIGN KEY (`species_id` )
    REFERENCES `vamdcspecies`.`vamdc_species` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_vamdc_species_names_vamdc_markup_types1`
    FOREIGN KEY (`markup_type_id` )
    REFERENCES `vamdcspecies`.`vamdc_markup_types` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'Contains all possible names for the species.\n\nIf the name is to be represented in HTML or reStructured Text, it should be added as a separate entry with the markup type set accordingly.\n\nThis is done so that the HTML or reStructured Text value of an item is always unique (i.e. does not get added more than once by accident).' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_member_database_identifiers`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_member_database_identifiers` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_member_database_identifiers` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'An internal counter.' ,
  `species_id` VARCHAR(40) NOT NULL COMMENT 'The species ID.  Foreign key reference to the species table.' ,
  `database_species_id` VARCHAR(150) NOT NULL COMMENT 'The internal ID of the species in the VAMDC member database.  This might be an integer or a string, hence the VARCHAR definition for this column.' ,
  `member_database_id` INT NOT NULL COMMENT 'The ID of the member database - a foreign key reference to the member_databases table.  The database from where the internal database_species_id came.' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_speciesid_idx` (`species_id` ASC) ,
  INDEX `fk_member_database_id_idx` (`member_database_id` ASC) ,
  UNIQUE INDEX `speciesid_databaseid_memberdatabase_idx` (`species_id` ASC, `database_species_id` ASC, `member_database_id` ASC) COMMENT 'Unique index to prevent repetition of species_id, database_species_id, and member_database_id combination.',
  CONSTRAINT `fk_vamdc_database_aliases_species1`
    FOREIGN KEY (`species_id` )
    REFERENCES `vamdcspecies`.`vamdc_species` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_vamdc_database_aliases_vamdc_databases1`
    FOREIGN KEY (`member_database_id` )
    REFERENCES `vamdcspecies`.`vamdc_member_databases` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'A table to link the VAMDC species to the equivalent identifier in the source database.' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_species_struct_formulae`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_species_struct_formulae` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_species_struct_formulae` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'An internal counter.' ,
  `species_id` VARCHAR(40) NOT NULL COMMENT 'The species ID.  Foreign key reference to the species table.' ,
  `formula` VARCHAR(150) NOT NULL COMMENT 'The structural formula.  More than one of these may exist, and the plain text version will have different preferred representations.' ,
  `markup_type_id` INT NOT NULL DEFAULT 1 COMMENT 'The kind of markup used to represent the structural formula.' ,
  `search_priority` INT NOT NULL COMMENT 'Allows the names to be ordered in a custom preferred mannner.' ,
  `created` DATETIME NOT NULL COMMENT 'The date the structural formula was added.' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_speciesid_idx` (`species_id` ASC) ,
  INDEX `fk_markuptypeid_idx` (`markup_type_id` ASC) ,
  UNIQUE INDEX `speciesid_formula_markup_idx` (`species_id` ASC, `formula` ASC, `markup_type_id` ASC) COMMENT 'Unique index to avoid duplication of formulae for a species.' ,
  INDEX `formula_idx` (`formula` ASC) ,
  INDEX `created_idx` (`created` ASC) ,
  CONSTRAINT `fk_vamdc_species_struct_formulae_vamdc_species_registry1`
    FOREIGN KEY (`species_id` )
    REFERENCES `vamdcspecies`.`vamdc_species` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_vamdc_species_struct_formulae_vamdc_markup_types1`
    FOREIGN KEY (`markup_type_id` )
    REFERENCES `vamdcspecies`.`vamdc_markup_types` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'Many databases express the structural formula in different ways - especially when isotopologues are involved.  This table allows all the different versions to coexist.\n\nOne potential problem with allowing HTML and REST formulations is the fact that the same HTML might exist for different ways of representing structural formula.  E.g. C-14, (14)C and (14C) are all represented by the same HTML and reStructuredText.\n\nTherefore, if the name is to be represented in HTML or reStructured Text, it should be added as a separate row with the markup type set accordingly.\n\nUsing a unique index on species ID, formula and markup type ensures that the plain text, HTML or reStructured Text value of an item is always unique (i.e. does not get added more than once by accident).' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_species_resources`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_species_resources` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_species_resources` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'An internal ID which just identifies the order of insertion of the data.' ,
  `species_id` VARCHAR(40) NOT NULL COMMENT 'The species ID.  Foreign key reference to the species table.' ,
  `url` VARCHAR(255) NOT NULL COMMENT 'The URL of the a definition of the species (e.g. in NIST).  Note that it is not possible to index a field larger than 768 bytes, so url is limited in length to 255.' ,
  `description` VARCHAR(150) NOT NULL COMMENT 'Describes the URL origin.  Allows any web pages built for this database to embed the description in the URL anchor.' ,
  `search_priority` INT NOT NULL COMMENT 'Search priority allows the URLs to be ordered in a custom preferred mannner.' ,
  `created` DATETIME NOT NULL COMMENT 'The date the resource was added.' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_speciesid_idx` (`species_id` ASC) ,
  UNIQUE INDEX `speciesid_url_idx` (`species_id` ASC, `url` ASC) COMMENT 'A unique index to ensure avoid duplication of the URL and species ID combination.',
  INDEX `url_idx` (`url` ASC) ,
  INDEX `description_idx` (`description` ASC) ,
  INDEX `created_idx` (`created` ASC) ,
  CONSTRAINT `fk_vamdc_species_resources_vamdc_species_registry1`
    FOREIGN KEY (`species_id` )
    REFERENCES `vamdcspecies`.`vamdc_species` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'A table to reference the external URLs, e.g. NIST, relating to a species.  (There may be more than one URL per species.)' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_conformers`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_conformers` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_conformers` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'An auto-incrementing counter.' ,
  `species_id` VARCHAR(40) NOT NULL COMMENT 'The species ID.  Foreign key reference to the species table.' ,
  `conformer_name` VARCHAR(150) NOT NULL COMMENT 'The name of the conformer - e.g. cis, trans.' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_speciesid_idx` (`species_id` ASC) ,
  CONSTRAINT `fk_vamdc_conformers_vamdc_species1`
    FOREIGN KEY (`species_id` )
    REFERENCES `vamdcspecies`.`vamdc_species` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'This table is similar to the inchikey_exceptions table except that conformers are a well known exception to Standard InChIKey.  All conformers should be added to both this table and the inchikey_exceptions table.' /* comment truncated */;


-- -----------------------------------------------------
-- Table `vamdcspecies`.`vamdc_inchikey_exceptions`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `vamdcspecies`.`vamdc_inchikey_exceptions` ;

CREATE  TABLE IF NOT EXISTS `vamdcspecies`.`vamdc_inchikey_exceptions` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'An auto-incrementing counter.' ,
  `species_id` VARCHAR(40) NOT NULL COMMENT 'The species ID.  Foreign key reference to the species table.' ,
  `reason` VARCHAR(255) NOT NULL COMMENT 'Why was this InChIKey exception added?  We should enforce an entry addition to this table every time we depart from Standard InChIKey.  At the moment this field is freeform text, because reasons can be combinations - e.g. reconnected metal, conformer.' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_speciesid_idx` (`species_id` ASC) ,
  CONSTRAINT `fk_vamdc_inchikey_exceptions_vamdc_species1`
    FOREIGN KEY (`species_id` )
    REFERENCES `vamdcspecies`.`vamdc_species` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'A table to store all exceptions to Standard InChIKey which will be used to differentiate species when Standard InChIKey is not sufficient to identify the species uniquely.  This table was create in place of the vamdc_registry_suffixes table (which has been dropped) because it was not possible to agree a distinct set of reasons for departure from Standard InChIKey.  This is because the reasons for departure from Standard InChIKey may be combined, and there may be other reasons for new cases for which we are not yet aware.' /* comment truncated */;



SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- -----------------------------------------------------
-- Data for table `vamdcspecies`.`vamdc_species_types`
-- -----------------------------------------------------
START TRANSACTION;
USE `vamdcspecies`;
INSERT INTO `vamdcspecies`.`vamdc_species_types` (`id`, `name`) VALUES (1, 'Atom');
INSERT INTO `vamdcspecies`.`vamdc_species_types` (`id`, `name`) VALUES (2, 'Molecule');
INSERT INTO `vamdcspecies`.`vamdc_species_types` (`id`, `name`) VALUES (3, 'Particle');
INSERT INTO `vamdcspecies`.`vamdc_species_types` (`id`, `name`) VALUES (4, 'Solid');

COMMIT;

-- -----------------------------------------------------
-- Data for table `vamdcspecies`.`vamdc_member_databases`
-- -----------------------------------------------------
START TRANSACTION;
USE `vamdcspecies`;
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (0, 'Unspecified', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (1, 'UMIST', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (2, 'HITRAN', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (3, 'BASECOL', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (4, 'CDMS', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (5, 'VALD', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (6, 'CHIANTI', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (7, 'KIDA', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (8, 'ICBDM', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (9, 'CDSD', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (10, 'OACTLASP', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (11, 'TOPBASE', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (12, 'TSBPAH', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (13, 'TIPBASE', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (14, 'GSMARSMPO', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (15, 'GSMARE', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (16, 'GHOSST', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (17, 'LLSD', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (18, 'STARKB', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (19, 'SPECTRW3', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (20, 'WIADIS', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (21, 'JPL', NULL);
INSERT INTO `vamdcspecies`.`vamdc_member_databases` (`id`, `short_name`, `description`) VALUES (22, 'VALDM', NULL);

COMMIT;

-- -----------------------------------------------------
-- Data for table `vamdcspecies`.`vamdc_markup_types`
-- -----------------------------------------------------
START TRANSACTION;
USE `vamdcspecies`;
INSERT INTO `vamdcspecies`.`vamdc_markup_types` (`id`, `name`) VALUES (1, 'Plain Text');
INSERT INTO `vamdcspecies`.`vamdc_markup_types` (`id`, `name`) VALUES (2, 'HTML');
INSERT INTO `vamdcspecies`.`vamdc_markup_types` (`id`, `name`) VALUES (3, 'ReStructured Text');

COMMIT;
