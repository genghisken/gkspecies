from XsamsSpeciesParser import XsamsSpeciesParser
import sys

def main (argv = None):
    if argv is None:
        argv = sys.argv

    helpstring = """\
       xsamsSpeciesReader.py <url or filename>
       E.g. xsamsSpeciesReader.py 'http://cdms.ph1.uni-koeln.de/vamdcspeciesdb/tap/sync?LANG=VSS2&REQUEST=doQuery&FORMAT=XSAMS&QUERY=SELECT%20SPECIES'
       or
       xsamsSpeciesReader.py './speciesList.xml' """

    if len(argv) < 2:
        sys.exit(helpstring)

    flag = 'file'

    url = argv[1]

    if 'http' in url:
        flag = 'url'
    else:
        flag = 'file'

    xml = XsamsSpeciesParser(url, flag=flag)
    for k,v in xml.molecule_list.iteritems():
        print k, v
    for k,v in xml.atom_list.iteritems():
        print k, v

    # TO DO...  Now that we have the species in a dictionary format,
    # Use the Species API to add the species to the Species Database.
    # Note that we should add code to check one line at a time to make sure that we're not
    # adding junk to the Species database.

    return 0


if __name__ == '__main__':
    main()
