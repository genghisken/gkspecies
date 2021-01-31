import openbabel as ob
from elements import *
import sys

def getInChIAndInChIKey(smilesString):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("smi", "inchi")

   mol = ob.OBMol()
   conv.ReadString(mol, smilesString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)


def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 1:
      sys.exit("Usage: getInchiFromSmiles.py")

   for key, value in ELEMENTS_REVERSE_LOOKUP.items():
      # We can only generate InChIs for the first 104 elements
      if int(key) < 105:
         smiles = '[' + value + ']'
         inchi, inchikey = getInChIAndInChIKey(smiles)
         print smiles, inchi, inchikey


   return 0



if __name__ == '__main__':
   main()



