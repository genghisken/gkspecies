import json, sys
import urllib
import httplib, base64
from db_utils import dbConnect
from elements import *
import MySQLdb
from generateInChIKeysForUMISTSpecies import generateStoichiometricFormula
import re

DUMMY_MASS_NUMBER = 9999

from docutils import core

SPECIESTYPES = {1:'atom', 2:'molecule'}

def remove_html_paragraph_tags(data):
    p = re.compile(r'<[/]{0,1}[p]>')
    return p.sub('', data)


def reST_to_html_fragment(a_str):
    parts = core.publish_parts(
                          source=a_str,
                          writer_name='html')
    return remove_html_paragraph_tags(parts['body_pre_docinfo']+parts['fragment'].strip())


def isStringCompatibleWithHTMLandPlainText(data):
    """ Get strings that are BOTH plain text AND HTML """

    compatible = True
    # Does it have isotope prefix brackets?  If so, it's NOT HTML compatible

    regexBrackets = re.compile(r'\([0-9][0-9]{0,1}\)[A-Z][a-z]{0,1}')
    resultBrackets = re.search(regexBrackets, data)
    if resultBrackets:
        compatible = False
        return compatible

    # Is there a charge?  If so, it's NOT HTML compatible
    regexCharge = re.compile(r'[+-]$')
    resultCharge = re.search(regexCharge, data)

    if resultCharge:
        compatible = False
        return compatible

    regexElementMultiplier = re.compile(r'[A-Z][a-z]{0,1}[0-9][0-9]{0,1}')
    resultElementMultiplier = re.search(regexElementMultiplier, data)

    if resultElementMultiplier:
        compatible = False

    return compatible


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


def readSpeciesFromInChIDB(conn):
    '''Get the species info from the old database'''


    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select distinct inchi,
                   inchikey,
                   charge,
                   mass_number,
                   species_type,
                   name stoichiometric_formula
              from species s, aliases a
             where s.id = a.species_id
               and a.alias_type = 3
               and a.name not like '%%`%%'
          order by inchikey
        """)

        resultSet = cursor.fetchall ()
        cursor.close ()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit (1)

    return resultSet



def readMemberDatabaseIdsFromInChIDB(conn, inchikey):
    '''Get the remote database identifiers from the old portal species database'''

    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select database_species_id,
                   species_id,
                   name
              from vamdc_database_aliases a, vamdc_databases d
             where d.id = a.vamdc_database_id
               and a.species_id = %s
        """, (inchikey))

        resultSet = cursor.fetchall ()
        cursor.close ()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit (1)

    return resultSet


def getStructuralFormulae(conn, inchikey):
    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select name
              from aliases
             where alias_type = 2
               and species_id = %s
        """, (inchikey))

        resultSet = cursor.fetchall ()
        cursor.close ()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit (1)

    return resultSet



def getNames(conn, inchikey):
    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select name
              from aliases
             where alias_type = 1
               and species_id = %s
        """, (inchikey))

        resultSet = cursor.fetchall ()
        cursor.close ()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit (1)

    return resultSet


def plainText(data):
    """ Is the data PURE plain text """

    plainTextTest = True

    if '`' in data:
        plainTextTest = False

    return plainTextTest, data




def htmlOrRest(data, rest = False):
    """ Is the data HTML (ReST) or plain text that could also be HTML (ReST) """

    htmlTextTest = False

    if '`' in data:
        # The data is in re-structured text format
        htmlTextTest = True
        if not rest:
            returnData = reST_to_html_fragment(data)
        else:
            returnData = data
    elif isStringCompatibleWithHTMLandPlainText(data): 
        # Is the data compatible with HTML - e.g. CO, NaCl
        htmlTextTest = True
        returnData = data
    else:
        returnData = None


    return htmlTextTest, returnData

    



def migrateInChIDBintoNewSpeciesDB(conn, server, url, credentials):
    '''Move the contents of the old portal database into the new one'''

    inchiDBSpecies = readSpeciesFromInChIDB(conn)

    # Have introduced some new ReST to HTML code above.  We should check for ReST
    # data tags.  If present, convert to HTML and add as HTML.  If not present,
    # we need to search for numbers and brackets.  If numbers and brackets use as plain,
    # if no numbers, assume both plain and html.

    # Add all non-ReST text (check for common ReST tags) as plain into the database.
    # The unique constraints on the database should take care of duplicate names.

    # To check for ReST, we only need to search for a backquote (`) in the name.






    for species in inchiDBSpecies:
        dataDict = {}
        umistDatabaseIds = readMemberDatabaseIdsFromInChIDB(conn, species["inchikey"])

        names = getNames(conn, species["inchikey"])
        plainTextNames = []
        htmlNames = []
        restNames = []

        for name in names:
            result, name["name"] = plainText(name["name"])
            if result:
                plainTextNames.append(name["name"])

            result, modifiedName = htmlOrRest(name["name"])
            if result:
                htmlNames.append(modifiedName)

            result, modifiedName = htmlOrRest(name["name"], rest=True)
            if result:
                restNames.append(modifiedName)


        structuralFormulae = getStructuralFormulae(conn, species["inchikey"])
        plainTextStructuralFormulae = []
        htmlStructuralFormulae = []
        restStructuralFormulae = []

        namesDict = {}
        structuralFormulaeDict = {}

        for formula in structuralFormulae:
            result, formula["name"] = plainText(formula["name"])
            if result:
                plainTextStructuralFormulae.append(formula["name"])

            result, modifiedFormula = htmlOrRest(formula["name"])
            if result:
                htmlStructuralFormulae.append(modifiedFormula)

            result, modifiedFormula = htmlOrRest(formula["name"], rest=True)
            if result:
                restStructuralFormulae.append(modifiedFormula)

        namesDict["plain"] = '|'.join(plainTextNames)
        namesDict["html"] = '|'.join(htmlNames)
        namesDict["rest"] = '|'.join(restNames)

        structuralFormulaeDict["plain"] = '|'.join(plainTextStructuralFormulae)
        structuralFormulaeDict["html"] = '|'.join(htmlStructuralFormulae)
        structuralFormulaeDict["rest"] = '|'.join(restStructuralFormulae)

        for markup in ('plain', 'html', 'rest'):
            for row in umistDatabaseIds:
                dataDict["inchi"] = species["inchi"]
                dataDict["inchikey"] = species["inchikey"]
                dataDict["charge"] = species["charge"]
                dataDict["mass_number"] = species["mass_number"]
                dataDict["species_type"] = SPECIESTYPES[species["species_type"]]

                dataDict["markup_type"] = markup
                dataDict["names"] = namesDict[markup]
                dataDict["structural_formulae"] = structuralFormulaeDict[markup]

                dataDict["database_source"] = row["name"]
                dataDict["source_database_identifiers"] = row["database_species_id"]

                # NOTE: The stoichiometric formula needs to be fixed.
                (formula, atomicNumberList, mass, charge, newStoicFormula) = generateStoichiometricFormula(species['stoichiometric_formula'], sortByAtomicNumber=False)
                if newStoicFormula != species['stoichiometric_formula']:
                    print "Stoic in DB =", species['stoichiometric_formula'], "Stoic should be =", newStoicFormula

                dataDict["stoichiometric_formula"] = newStoicFormula

                data = json.dumps(dataDict)

                print data

                #continue
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
        sys.exit("Usage: migrateInChIDBIntoSpeciesDB.py <username> <password> <database> <hostname>")

    username = argv[1]
    password = argv[2]
    database = argv[3]
    hostname = argv[4]

    conn = dbConnect(hostname, username, password, database)

    #server = 'localhost'
    #posturl = '/vamdc/inchi/api/add/'
    #user = 'vamdc'
    #password = 'v4mdc'

    credentials = {}

    server = 'star.pst.qub.ac.uk'
    posturl = '/vamdc/inchiservice/api/add/'
    user = 'vamdc'
    password = 'v4mdc'

    credentials['user'] = user
    credentials['pass'] = password

    migrateInChIDBintoNewSpeciesDB(conn, server, posturl, credentials)

    return 0

if __name__ == '__main__':
    main()
