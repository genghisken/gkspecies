import openbabel as ob
import sys

def getInChIAndInChIKey(inchiString):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("inchi", "inchi")
   #conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")

   # Crucial that this line added when using elements so that we don't add hydrogen implicitly.
   # Note that if you DO add this line, all the hydrogens will be stripped from the returned InChI
   # (which may or may not be desirable).
   # conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")

   mol = ob.OBMol()
   conv.ReadString(mol, inchiString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   #conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)


def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 2:
      sys.exit("Usage: getInchiKeyFromInchi.py <InChI format>")

   inchiInput = argv[1]
   inchi, inchikey = getInChIAndInChIKey(inchiInput)

   print inchiInput
   print inchi
   print inchikey

   return 0



if __name__ == '__main__':
   main()



