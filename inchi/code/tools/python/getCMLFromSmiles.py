import openbabel as ob
import sys

def getCMLFromSmiles(smiles):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("smiles", "cml")

   mol = ob.OBMol()
   conv.ReadString(mol, smiles)
   conv.SetOptions("h", conv.OUTOPTIONS)
   cml = conv.WriteString(mol).rstrip()
   return(cml)


def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 2:
      sys.exit("Usage: getCMLFromSmiles.py <SMILES String>")

   smiles = argv[1]

   cml = getCMLFromSmiles(smiles)

   print cml

   return 0



if __name__ == '__main__':
   main()



