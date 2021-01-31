import inchiapi
import sys
from db_utils import getVamdcPortalSpecies, dbConnect

def main(argv = None):
   if argv is None:
      argv = sys.argv

   if len(argv) != 1:
      sys.exit("Usage: checkPortalInchis.py")

   conn = dbConnect('psdb', 'kws', '', 'umist_django')

   results = getVamdcPortalSpecies(conn)

   for row in results:
      inchi = row['inchi']
      inchikey = row['inchikey']
      calculatedInChIKey = inchiapi.GetINCHIKeyFromINCHI(inchi,1,1)[1]
      if 'InChI=1/' in inchikey:
         print inchi, inchikey, "are not standard"
      if calculatedInChIKey != inchikey:
         print inchi, inchikey, "are not a pair"

   return 0



if __name__ == '__main__':
   main()



