import openbabel as ob
import sys

def getInChIAndInChIKey(smilesString):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("smi", "inchi")
   conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")

   mol = ob.OBMol()
   conv.ReadString(mol, smilesString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)


def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 5:
      sys.exit("Usage: getInchiFromSmiles.py <umist struct_name> <SMILES format> <VAMDC SMILES format> <1 = atom 2 = molecule>")

   structName = argv[1]
   smiles = argv[2]
   smilesVamdc = argv[3]
   atomOrMolecule = int(argv[4])

   inchi, inchikey = getInChIAndInChIKey(smiles)
   vamdcInchi, vamdcInchikey = getInChIAndInChIKey(smilesVamdc)

   print "update new_species set species_type = %d, inchi = '%s', inchikey = '%s', vamdc_inchi = '%s', vamdc_inchikey = '%s' where species_type is null and struct_name = '%s';" % (atomOrMolecule, inchi, inchikey, vamdcInchi, vamdcInchikey, structName)

   return 0



if __name__ == '__main__':
   main()



