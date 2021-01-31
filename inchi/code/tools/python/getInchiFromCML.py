import openbabel as ob
import sys

def getInChIAndInChIKey(cmlString):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("cml", "inchi")
   conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")

   mol = ob.OBMol()
   conv.ReadString(mol, cmlString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)

cml = """
<molecule id="H2CO-1">
<atomArray>
  <atom id="H1" elementType="H" isotopeNumber="1"/>
  <atom id="H2" elementType="H" isotopeNumber="1"/>
  <atom id="C1" elementType="C" isotopeNumber="12"/>
  <atom id="O1" elementType="O" isotopeNumber="16"/>
</atomArray>
<bondArray>
  <bond atomRefs2="H1 C1" id="H1_C1" order="S"/>
  <bond atomRefs2="H2 C1" id="H2_C1" order="S"/>
  <bond atomRefs2="C1 O1" id="C1_O1" order="D"/>
</bondArray>
</molecule>
"""

def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 2:
      print argv[1]
      sys.exit("Usage: getInchiFromCML.py <CML format>")

   inchi, inchikey = getInChIAndInChIKey(cml)

   print inchi
   print inchikey

   return 0



if __name__ == '__main__':
   main()



