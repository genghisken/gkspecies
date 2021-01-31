# Open the elements file (tab separated)
# Open the isotopes file (space separated)
# Read the elements into a 2-d array - atomic number, name
# For each element, read isotope list
# For each isotope, for each ion, generate InChI & InChIKey
# PROBLEM - how to generate the ions - NOT trivial - need monatomic ion table

import MySQLdb
import os, sys
import csv
import openbabel as ob
from roman_numerals import *

def dbConnect(lhost, luser, lpasswd, ldb):
   try:
      conn = MySQLdb.connect (host = lhost,
                              user = luser,
                            passwd = lpasswd,
                                db = ldb)
   except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])
      sys.exit (1)

   return conn


def insertAlias(conn, species_id, aliasType, name):
   try:
      cursor = conn.cursor (MySQLdb.cursors.DictCursor)

      cursor.execute ("""
          insert into aliases (species_id, name, alias_type, search_priority)
          values (%s, %s, %s, %s)
          """, (species_id, name, aliasType, aliasType))

   except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])

   cursor.close ()
   return conn.insert_id()


def insertSpecies(conn, id, inchikey, inchi, massNumber, charge):
   try:
      cursor = conn.cursor (MySQLdb.cursors.DictCursor)

      cursor.execute ("""
          insert into species (id, inchikey, inchi, vamdc_inchikey, vamdc_inchikey_suffix, vamdc_inchi, mass_number, charge, species_type, created)
          values (%s, %s, %s, %s, 1, %s, %s, %s, 1, now())
          """, (id, inchikey, inchi, inchikey, inchi, massNumber, charge))

   except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])

   cursor.close ()
   return conn.insert_id()




def getInChIAndInChIKey(smilesString):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("smi", "inchi")

   mol = ob.OBMol()
   conv.ReadString(mol, smilesString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)


def sign(value):
   signString = '+'
   if value < 0:
      signString = '-'
   return signString



def insertElementInChIKeys(conn):
   elements = []
   isotopes = []
   ions = []

   isotopeRows = csv.reader(open('babel_data/kws_isotope.txt'), delimiter=' ')
   elementRows = csv.reader(open('babel_data/kws_element.txt'), delimiter='\t')
   ionRows = csv.reader(open('vald_data/kws_vald_ions.txt'), delimiter=' ')

   for elementRow in elementRows:
      erow = []
      for elementItem in elementRow:
         erow.append(elementItem)
      elements.append(erow)

   for isotopeRow in isotopeRows:
      irow = []
      for isotopeItem in isotopeRow:
         irow.append(isotopeItem)
      isotopes.append(irow)

   for ionRow in ionRows:
      iorow = []
      for ionItem in ionRow:
         iorow.append(ionItem)
      ions.append(iorow)

   for e in range(1, len(elements)):
      elementName = elements[e][1]
      elementLongName = elements[e][14]
      elementAverageMass = int(round(float(elements[e][7])))
      for i in range(1,len(isotopes[e]), 2): # Always an even number
          isotopePrefix = ''
          rstIsotopePrefix = ''
          if isotopes[e][i] == '0' or int(isotopes[e][i]) == elementAverageMass:
             species = '%s' % (elementName)
             mass = elementAverageMass
          else:
             species = '%s%s' % (isotopes[e][i], elementName)
             isotopePrefix = '(%s)' % isotopes[e][i]
             rstIsotopePrefix = '\ :sup:`%s`\ ' % isotopes[e][i]
             mass = int(isotopes[e][i])

          smiles = '[%s]' % species

          ionName = "%s%s" % (isotopePrefix, elementName)
          rstIonName = "%s%s" % (rstIsotopePrefix, elementName)
          ionAlias = "%s %s" % (ionName, int2roman(0+1))
          rstIonAlias = "%s %s" % (rstIonName, int2roman(0+1))

          charge = 0
          inchi, inchikey = getInChIAndInChIKey(smiles)
          if inchi:
             print "%10s %30s %28s %s %s %s %s %d %d %s %s" % (smiles, inchi, inchikey, elementName, elementLongName, ionName, ionAlias, mass, charge, rstIonAlias, rstIonName)

             id = inchikey
             insertSpecies(conn, id, inchikey, inchi, mass, charge)
             insertAlias(conn, id, 1, elementLongName)
             insertAlias(conn, id, 1, ionAlias)
             insertAlias(conn, id, 2, ionName)
             insertAlias(conn, id, 3, ionName)
             insertAlias(conn, id, 4, ionName)
             insertAlias(conn, id, 1, rstIonAlias)
             insertAlias(conn, id, 2, rstIonName)
             insertAlias(conn, id, 3, rstIonName)
             insertAlias(conn, id, 4, rstIonName)

          # Generate the ions as well

          if len(ions[e]) > 3:
             for j in range(3, len(ions[e])):
                charge = int(ions[e][j])
                ionisedSpecies = '%s%s%s' % (species, sign(int(ions[e][j])), abs(int(ions[e][j])))
                smiles = '[%s]' % ionisedSpecies


                if int(ions[e][j]) < 0:
                   print "HERE"

                if abs(int(ions[e][j])) > 1:
                   ionName = "%s%s%s%s" % (isotopePrefix, elementName, abs(int(ions[e][j])), sign(int(ions[e][j])))
                   rstIonName = "%s%s\ :sup:`%s%s`" % (rstIsotopePrefix, elementName, abs(int(ions[e][j])), sign(int(ions[e][j])))
                else:
                   ionName = "%s%s%s" % (isotopePrefix, elementName, sign(int(ions[e][j])))
                   rstIonName = "%s%s\ :sup:`%s`" % (rstIsotopePrefix, elementName, sign(int(ions[e][j])))


                if int(ions[e][j]) >= 0:
                   ionAlias = "%s%s %s" % (isotopePrefix, elementName, int2roman(int(ions[e][j])+1))
                   rstIonAlias = "%s%s %s" % (rstIsotopePrefix, elementName, int2roman(int(ions[e][j])+1))
                else:
                   ionAlias = ''


                inchi, inchikey = getInChIAndInChIKey(smiles)
                if inchi:
                   print "%10s %30s %28s %s %s %s %s %d %d %s %s" % (smiles, inchi, inchikey, elementName, elementLongName, ionName, ionAlias, mass, charge, rstIonAlias, rstIonName)
                   id = inchikey
                   insertSpecies(conn, id, inchikey, inchi, mass, charge)
                   insertAlias(conn, id, 1, elementLongName)
                   insertAlias(conn, id, 1, ionAlias)
                   insertAlias(conn, id, 1, rstIonAlias)
                   insertAlias(conn, id, 2, ionName)
                   insertAlias(conn, id, 3, ionName)
                   insertAlias(conn, id, 4, ionName)
                   insertAlias(conn, id, 2, rstIonName)
                   insertAlias(conn, id, 3, rstIonName)
                   insertAlias(conn, id, 4, rstIonName)

   return




def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 5:
      sys.exit("Usage: generateInChIKeysForElementsInsertIntoDB.py <username> <password> <database> <host>")

   dbuser = argv[1]
   dbpass = argv[2]
   dbname = argv[3]
   dbhost = argv[4]

   conn = dbConnect(dbhost, dbuser, dbpass, dbname)

   insertElementInChIKeys(conn)

   return 0



if __name__ == '__main__':
   main()

