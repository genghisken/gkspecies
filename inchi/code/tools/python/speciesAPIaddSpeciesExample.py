import json, sys
import urllib
import httplib, base64

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


def main (argv = None):
    if argv is None:
        argv = sys.argv


    dataDict = {'inchikey':'YUZRZFQHUCKACF-UHFFFAOYSA-N',
                'inchi':'InChI=1S/CN.K/c1-2;',
                'charge':0,
                'mass_number':65,
                'species_type':'molecule',
                'stoichiometric_formula':'CKN',
                'structural_formulae':'KNC',
                'names': 'Potassium isocyanide',
                'markup_type': 'html',
                'add_duplicate':False,
                'smiles':'[K][N][C]',
                'exceptions':'Reconnected metal'}

    data = json.dumps(dataDict)
    print data

    server = 'psweb.mp.qub.ac.uk'
    posturl = '/vamdc/inchiservice/api/add/'

    #server = 'localhost'
    #posturl = '/vamdc/inchi/api/add/'

    user = 'vamdc'
    password = 'v4mdc'

    credentials = {}
    credentials['user'] = user
    credentials['pass'] = password

    response = sendRequest(server, posturl, data, credentials)

    try:
        result = json.loads(response)
        print result
    except ValueError, e:
        print response


    return 0

if __name__ == '__main__':
    main()
