
import json, sys, urllib, httplib, base64

def sendRequest(server, posturl, data, credentials):
    """
        Uses httplib NOT urllib2 because urllib2 raises an exception
        if the response type is not 2xx
    """

    conn = httplib.HTTPConnection(server, 80)
    headers = {"Content-type": "application/json"}

    if credentials:
        auth = base64.b64encode("%s:%s" % (credentials['user'], credentials['pass']))
        authorization = "Basic %s" % auth
        headers["Authorization"] = authorization

    headers ["User-Agent"] = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

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

    helpstring = "speciesAPIgetInchiExample.py <mol id type> <mol string>\ne.g. inchiRemoteExample.py 'smiles' '[H][O][H]'"
    if len(argv) < 3:
        sys.exit(helpstring)

    molIDType = argv[1]
    molID = urllib.quote(argv[2])

    dataDict = {molIDType:molID, 'doNotAddH':True, 'reconnectMetal':False }
    data = json.dumps(dataDict)

    posturl = '/vamdc/inchiservice/api/'
    server = 'star.pst.qub.ac.uk'
    user = 'vamdc'
    password = 'v4mdc'

    credentials = {}
    credentials['user'] = user
    credentials['pass'] = password

    response = sendRequest(server, posturl, data, credentials)

    try:
        result = json.loads(response)
        print
        print "                    ", result
        print
    except ValueError, e:
        print response

    return 0

if __name__ == '__main__':
    main()



