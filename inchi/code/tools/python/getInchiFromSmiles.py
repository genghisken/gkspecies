import openbabel as ob
import sys

def getInChIAndInChIKey(smilesString, doNotAddH=True, reconnectMetal=False):

   inchi = None
   inchikey = None

   mol = ob.OBMol()

   conv = ob.OBConversion()

   conv.SetInAndOutFormats("smi", "inchi")
   conv.ReadString(mol, smilesString)

   if doNotAddH:
      conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")

   if reconnectMetal:
      conv.AddOption("X", conv.OUTOPTIONS, "RecMet")

   inchi = conv.WriteString(mol).rstrip()

   conv.SetOptions("K", conv.OUTOPTIONS)

   if doNotAddH:
      conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")

   if reconnectMetal:
      conv.AddOption("X", conv.OUTOPTIONS, "RecMet")

   inchikey = conv.WriteString(mol).rstrip()

   return(inchi, inchikey)


def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 2:
      sys.exit("Usage: getInchiFromSmiles.py <SMILES format>")

   smiles = argv[1]
   inchi, inchikey = getInChIAndInChIKey(smiles, doNotAddH=False, reconnectMetal=False)

   print "InChI: %s" % inchi
   print "InChIKey: %s" % inchikey

   return 0



if __name__ == '__main__':
   main()



