import openbabel as ob
import sys

def getInChIAndInChIKey(molString):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("mol", "inchi")

   mol = ob.OBMol()
   conv.ReadString(mol, molString)
   conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)

mol = """
ChemWindow

  5  4  0  0  0  0  0  0  0  0  1 V2000
    2.2994    2.0277    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    3.2617    0.3611    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.2994    0.9166    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.3372    0.3611    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.3750    0.9166    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
  3  1  2  0
  3  2  1  0
  4  3  1  0
  5  4  1  0
M  END
"""

def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 2:
      sys.exit("Usage: getInchiFromMOL.py <MOL format>")

   inchi, inchikey = getInChIAndInChIKey(mol)

   print inchi
   print inchikey

   return 0



if __name__ == '__main__':
   main()



