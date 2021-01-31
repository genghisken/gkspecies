import json, sys
import urllib
import httplib, base64
from db_utils import dbConnect
from elements import *
import MySQLdb
from generateInChIKeysForUMISTSpecies import generateStoichiometricFormula

DUMMY_MASS_NUMBER = 9999

def sendRequest(server, posturl, data, credentials):
    """ Uses httplib NOT urllib2 because urllib2 raises an exception if the response type is not 2xx """

    headers = {"Content-type": "application/json", "Accept": "*/*", 'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
    if credentials:
        auth = base64.b64encode("%s:%s" % (credentials['user'], credentials['pass']))
        authorization = "Basic %s" % auth
        headers["Authorization"] = authorization

    conn = httplib.HTTPConnection(server, 80)

    conn.request("POST", posturl, data, headers)

    resp = conn.getresponse()

    status = resp.status
    reason = resp.reason
    response = resp.read()
    conn.close()

    return response


def readSpeciesFromOldPortalDB(conn):
    '''Get the species info from the old database'''

    # The main problem is that we don't have MASS NUMBER in the portal database at the moment
    # Since I've made it illegal to enter a mass number of less than 1, I'll use a dummy value
    # of 9999.


    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select InChI,
                   InChIKey,
                   stoichiometric_formula, 
                   charge, 
                   ordinary_formula,
                   ordinary_formula_html,
                   common_name name,
                   cml,
                   ref
              from species_species
              union 
            select i.InChI,
                   i.InChIKey,
                   s.stoichiometric_formula,
                   s.charge,
                   i.iso_name ordinary_formula,
                   i.iso_name_html ordinary_formula_html,
                   s.common_name name,
                   i.cml,
                   i.ref
              from species_iso i, species_species s
             where i.species_id = s.id
        """)

        resultSet = cursor.fetchall ()
        cursor.close ()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit (1)

    return resultSet



def readMemberDatabaseIdsFromOldPortalDB(conn, inchikey):
    '''Get the remote database identifiers from the old portal species database'''

    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select name dbname,
                   InChIKey,
                   speciesID internal_db_id
              from species_species_db sdb, species_species s
             where sdb.species_id = s.id
               and InChIKey = %s
            union all
            select name dbname,
                   InChIKey,
                   isoID internal_db_id
              from species_iso_db sidb, species_iso i
             where sidb.iso_id = i.id
               and InChIKey = %s
        """, (inchikey, inchikey))

        resultSet = cursor.fetchall ()
        cursor.close ()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit (1)

    return resultSet




def migrateOldPortalDataIntoNewSpeciesDB(conn, server, url, credentials):
    '''Move the contents of the old portal database into the new one'''

    portalSpecies = readSpeciesFromOldPortalDB(conn)

    # Note that this will return all species identifers both KIDA and HITRAN.
    # We have to send these in separate requests (or repeat the full request with each database
    # and rely on the database to police unique constraints.)

    for species in portalSpecies:
        dataDict = {}
        portalMemberDatabaseIds = readMemberDatabaseIdsFromOldPortalDB(conn, species["InChIKey"])

        for markup in ('plain', 'html'):
            for row in portalMemberDatabaseIds:
                dataDict["inchi"] = species["InChI"]
                dataDict["inchikey"] = species["InChIKey"]
                dataDict["charge"] = species["charge"]
                dataDict["mass_number"] = DUMMY_MASS_NUMBER
                dataDict["names"] = species["name"]
                dataDict["database_source"] = row["dbname"]
                dataDict["source_database_identifiers"] = row["internal_db_id"]

                # NOTE: The stoichiometric formula needs to be fixed.
                (formula, atomicNumberList, mass, charge, newStoicFormula) = generateStoichiometricFormula(species['stoichiometric_formula'], sortByAtomicNumber=False)
                if newStoicFormula != species['stoichiometric_formula']:
                    print "Stoic in DB =", species['stoichiometric_formula'], "Stoic should be =", newStoicFormula

                dataDict["stoichiometric_formula"] = newStoicFormula

                if markup == 'plain':
                    dataDict["markup_type"] = markup
                    dataDict["structural_formulae"] = species["ordinary_formula"]

                if markup == 'html':
                    dataDict["markup_type"] = markup
                    dataDict["structural_formulae"] = species["ordinary_formula_html"]

                if species["cml"]:
                    dataDict["cml"] = urllib.quote(species["cml"])

                #if species["ref"]:
                #    dataDict["resource_urls"] = species["ref"]

                # There is currently no indicator in the existing portal database to show species type
                # Will have to assume "molecule" for the time being and fix afterwards.

                # An alternative solution would be to add atoms with charges in the database first from another database (e.g. mine).

                dataDict["species_type"] = 'molecule'

                data = json.dumps(dataDict)

                response = sendRequest(server, url, data, credentials)

                try:
                    result = json.loads(response)
                    print result
                except ValueError, e:
                    print response


def main(argv = None):

    if argv is None:
        argv = sys.argv

    if len(argv) != 5:
        sys.exit("Usage: migratePortalDataIntoSpeciesDB.py <username> <password> <database> <hostname>")

    username = argv[1]
    password = argv[2]
    database = argv[3]
    hostname = argv[4]

    conn = dbConnect(hostname, username, password, database)

    server = 'localhost'
    posturl = '/vamdc/inchi/api/add/'

    #user = 'vamdc'
    #password = 'v4mdc'

    credentials = {}
    #credentials['user'] = user
    #credentials['pass'] = password

    migrateOldPortalDataIntoNewSpeciesDB(conn, server, posturl, credentials)

    return 0

if __name__ == '__main__':
    main()
