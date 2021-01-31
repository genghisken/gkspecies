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


def getInChIAndInChIKey(smilesString):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("smi", "inchi")

   mol = ob.OBMol()
   conv.ReadString(mol, smilesString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)


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
   for i in range(1,len(isotopes[e]), 2): # Always an even number
       if isotopes[e][i] == '0':
          species = '%s' % (elementName)
       else:
          species = '%s%s' % (isotopes[e][i], elementName)

       smiles = '[%s]' % species

       inchi, inchikey = getInChIAndInChIKey(smiles)
       print "%10s %30s %28s" % (smiles, inchi, inchikey)

       # Generate the ions as well

       if len(ions[e]) > 3:
          for j in range(3, len(ions[e])):
             ionisedSpecies = '%s+%s' % (species, ions[e][j])
             smiles = '[%s]' % ionisedSpecies
             inchi, inchikey = getInChIAndInChIKey(smiles)
             print "%10s %30s %28s" % (smiles, inchi, inchikey)








