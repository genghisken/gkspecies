import csv

ionRows = csv.reader(open('vald_ions.txt'), delimiter='\t')

previousAtomicNumber = None

for ionRow in ionRows:
   atomicNumber = ionRow[0]

   if atomicNumber == previousAtomicNumber:
      print ionRow[2],
   else:
      print ""
      print ionRow[0],
      print ionRow[1],
      print ionRow[2],
      previousAtomicNumber = atomicNumber

