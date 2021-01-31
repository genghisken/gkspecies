import sys, os, base64
import re
from db_utils import *
from elements import *

from getInchiFromSmiles import getInChIAndInChIKey

# 2012-05-07 KWS Added InChI API

import inchiapi

def countElements(molecule, elementToTest):
    """Go through the molecule and count all the instances of a given element"""

    # The algorithm required is this
    # 1. Read all struct_names that don't refer to isotopologues (no brackets, no D)
    # 2. Using a regular expression match, go through the formula and apply the element dictionary
    #     2.1 Use the two-letter elements first
    #
    #
    #
    # 3. For each occurrence of an element, increment a counter
    # 4. For each charge symbol (+ or -) increment a counter
    # 5. Build the stoichiometric formula by increasing atomic number and counter if counter > 0
    # 6. Append the charge symbol and counter


    # 2012-04-07 KWS Could modify this function to return total mass for the given element and total charge


    # ASSUMPTION: No more than 99 occurrences of a single element in this molecule (not dealing with large fullerenes)

    # This is the regex for 1 or more elements - e.g. C6H6, C60.
    elementRepetitionRegex = '[0-9]{0,2}'
    compiledElementRepetitionRegex = re.compile(elementRepetitionRegex)

    # This is the regex for 2 or more elements, but not one - e.g. CH4.
    elementRepetitionGreaterThan1Regex = '([0-9]+)$'
    compiledElementRepetitionGreaterThan1Regex = re.compile(elementRepetitionGreaterThan1Regex)

    # We need to modify the regex depending on which "element" we give to the function, and we need
    # to escape certain characters which can be mistaken for regex characters, such as +, - and brackets
    if elementToTest == '+' or elementToTest == '-':
        elementPlusRepetitionsRegex = '\\' + elementToTest + elementRepetitionRegex
    elif elementToTest.find('(') >= 0:
        escapedString = elementToTest.replace('(','\\(')
        escapedString = escapedString.replace(')','\\)')
        elementPlusRepetitionsRegex = escapedString + elementRepetitionRegex
    else:
        elementPlusRepetitionsRegex = elementToTest + elementRepetitionRegex
        #elementPlusRepetitionsRegex = '\([0-9]{1,3}\){0,1}' + elementToTest + elementRepetitionRegex

    compiledElementPlusRepetitionsRegex = re.compile(elementPlusRepetitionsRegex)

    remainder = compiledElementPlusRepetitionsRegex.sub('', molecule)

    # Abort if the element is not present
    if remainder == molecule:
        return remainder, {}

    singleElementList = compiledElementPlusRepetitionsRegex.findall(molecule)

    # The counter should be at least 1.  If it remains zero, something went wrong.
    counter = 0
    for element in singleElementList:
        countString = compiledElementRepetitionGreaterThan1Regex.search(element)
        if countString:
            counter += int(countString.group(1))
        else:
            counter += 1

    if counter == 0:
        print "Something went wrong"

    elementFrequency = { elementToTest: counter }

    return remainder, elementFrequency


# Similar to countElements, but we're not so concerned about frequency as
# position of the element within the original string.  Also, we want to be
# able to search for methyl, ethyl, ammonia groups.

def splitMolecule(molecule, elementToTest):
    """Go through the molecule and count all the instances of a given element"""

    # ASSUMPTION: No more than 99 occurrences of a single element in this molecule (not dealing with large fullerenes)

    if elementToTest == 'D':
        elementToTest = '(2)H'

    if elementToTest == 'T':
        elementToTest = '(3)H'

    # This is the regex for 1 or more elements - e.g. C6H6, C60.
    elementRepetitionRegex = '[0-9]{0,2}'
    compiledElementRepetitionRegex = re.compile(elementRepetitionRegex)

    # This is the regex for 2 or more elements, but not one - e.g. CH4.
    elementRepetitionGreaterThan1Regex = '([0-9]+)$'
    compiledElementRepetitionGreaterThan1Regex = re.compile(elementRepetitionGreaterThan1Regex)

    # We need to modify the regex depending on which "element" we give to the function, and we need
    # to escape certain characters which can be mistaken for regex characters, such as +, - and brackets
    if elementToTest.find('-') >= 0:
        escapedString = elementToTest.replace('-','\\-')
        elementPlusRepetitionsRegex = escapedString + elementRepetitionRegex
    elif elementToTest.find('+') >= 0:
        escapedString = elementToTest.replace('+','\\+')
        elementPlusRepetitionsRegex = escapedString + elementRepetitionRegex
    elif elementToTest.find('(') >= 0:
        escapedString = elementToTest.replace('(','\\(')
        escapedString = escapedString.replace(')','\\)')
        elementPlusRepetitionsRegex = escapedString + elementRepetitionRegex
    else:
        elementPlusRepetitionsRegex = elementToTest + elementRepetitionRegex

    compiledElementPlusRepetitionsRegex = re.compile(elementPlusRepetitionsRegex)

    remainder = compiledElementPlusRepetitionsRegex.sub('', molecule)

    # Abort if the element is not present
    if remainder == molecule:
        return remainder, []

    singleElementList = compiledElementPlusRepetitionsRegex.findall(molecule)
    discoveries = compiledElementPlusRepetitionsRegex.finditer(molecule)

    elementRecurrences = []
    for m in discoveries:
        elementRecurrences.append([m.group(0), m.start(), m.end()])

    return remainder, elementRecurrences

def grabElementAndMass(element):
    """Pick out the element mass from the mass table."""

    # Currently we store all the isotopes of the elements in our ELEMENTS dict
    # in the form of (optional brackets) and element.  E.g. (13)C.
    # In this function we'd like to pick out the (average) masses and
    # override them if necessary by the bracketed value.

    # This function will be used (amongst other things) for generating the SMILES
    # mass-element string - e.g. (13)CO = [13C][O]

    mass = None
    nonIsotopicElementSymbol = None

    bracketCheckRegex = '\\(([0-9]{1,2})\\)'
    compiledBracketCheckRegex = re.compile(bracketCheckRegex)

    bracketString = compiledBracketCheckRegex.search(element)
    if bracketString:
        mass = int(bracketString.group(1))
        nonIsotopicElementSymbol = compiledBracketCheckRegex.sub('', element)
    else:
        if ELEMENTS[element] > 0 and ELEMENTS[element] < 1000:
            mass = ELEMENT_MASSES[element][0] # i.e. use AVERAGE mass
            nonIsotopicElementSymbol = element

    return nonIsotopicElementSymbol, mass


def generateStoichiometricFormula(molecule, sortByAtomicNumber = True):

    # This function should NOT return any isotope specifiers.

    # 2012-04-06 KWS Complete rewrite of this function.

    # We're going to rewrite this to deliver two formulae:
    # * sorted by increasing atomic number
    # * sorted in Hill order
    # AND
    # * the total mass
    # * the total charge


    elementTuples = sorted(ELEMENTS.iteritems(), key=lambda (k,v): (v,k))

    # Build an element list in ascending atomic number order
    elementList = []
    for tuple in elementTuples:
       elementList.append(tuple[0])

    # Copy this list into a new list
    sortedElements = list(elementList)

    if not sortByAtomicNumber:
        # Then sort alphabetically
        sortedElements.sort()
        # And make sure that + and - are at the end
        sortedElements.remove('+')
        sortedElements.append('+')
        sortedElements.remove('-')
        sortedElements.append('-')

    # Now sort the original list by element symbol length (reversed)
    # We need to do this so that long regular expressions are matched
    # before the short ones.
    elementList.sort(cmp=bylength)

    #molecule = inputMolecule = 'HHeLiBeeBCN3OCH3CH2wCH2CH2CH3CHOCH4Si6YBUArNOTiO2+++++++++++-'
    inputMolecule = molecule

    print inputMolecule

    # Nibble through the molecule until there is nothing left.
    # 2012-05-26 KWS Problem here is that isotopes not correctly counted.  Need to fix!

    # 2012-06-09 KWS Create an atomic number element dictionary
    #                Let's create a dict like this:
    #                AtomicNumber: ['ElementSymbol', frequency]
    #                We're keeping atomic number because later we might
    #                want to sort by atomic number or by element name
    #                (or Hill sorting).

    atomicNumberElementDict = {}

    moleculeElements = {}
    for element in elementList:
        (molecule, elementFrequency) = countElements(molecule, element)
        if elementFrequency:
            moleculeElements.update(elementFrequency)

            # 2012-06-09 KWS Increment the frequency of the element or add a new one to the dict.
            #                Don't bother checking for things like c- t- or l-
            if ELEMENTS[element] > 0:
                try:
                    atomicNumberElementDict[ELEMENTS[element]][1] += elementFrequency[element]
                except KeyError, e:
                    atomicNumberElementDict[ELEMENTS[element]] = [ELEMENTS_REVERSE_LOOKUP[str(ELEMENTS[element])], elementFrequency[element]]

        if len(molecule) == 0:
            break

    # OK - Now we have a dictionary containing the elements and their frequency.
    # Now let's build the stoichiometric formula. First we need our elements
    # sorted in atomic number order.

    mass = 0
    charge = 0
    stoichiometricFormula = ''
    atomicNumberString = ''
    atomicNumberFrequencies = []
    previousElement = None


    for element in sortedElements:
        if element in moleculeElements and ELEMENTS[element] > 0:

            # Build the formula with atomic numbers.  We'll use this later to allocated isomer
            # and isotopomer numbers
            #atomicNumberString += 'Z%dn%d' % (ELEMENTS[element], moleculeElements[element])

            # Let's build an array of element frequencies representing each atomic number component
            # If the current element is the same as the previous one (e.g. HD) then increment the
            # counter of the last one in the current list of element frequencies.

            if ELEMENTS[element] == previousElement:
                atomicNumberFrequencies[-1][1] = atomicNumberFrequencies[-1][1] + 1
            else:
                atomicNumberFrequencies.append([ELEMENTS[element], moleculeElements[element]])

            previousElement = ELEMENTS[element]

            if moleculeElements[element] == 1:
                stoichiometricFormula += '%s' % (element)
            else:
                stoichiometricFormula += '%s%d' % (element, moleculeElements[element])

            # Calculate the total mass and charge

            if ELEMENTS[element] < 1000:
                mass += moleculeElements[element] * grabElementAndMass(element)[1]

            if ELEMENTS[element] >= 2000:
                if element == '+':
                    charge += 1 * moleculeElements[element]
                if element == '-':
                    charge -= 1 * moleculeElements[element]

    # We want a sorted list of values.
    print atomicNumberElementDict

    # for element in moleculeElements:
    #     print 'Element: %s, Z: %s, Frequency: %s' % (element, ELEMENTS[element], moleculeElements[element])

    print "Atomic Number Frequences = ", atomicNumberFrequencies

    for numericElement in atomicNumberFrequencies:
        uniqueElement = ELEMENTS_REVERSE_LOOKUP['%d' % numericElement[0]]
        if numericElement[1] == 1:
            atomicNumberString += '%s' % (uniqueElement)
        else:
            atomicNumberString += '%s%d' % (uniqueElement, numericElement[1])

    # 2012-06-09 KWS Build the new stoichiometric formula.
    stoicList = []
    chargeList = []
    for k,v in sorted(atomicNumberElementDict.iteritems()):
        if k == 2000 or k == 2001:
            chargeList.append(v)
        else:
            stoicList.append(v)

    if not sortByAtomicNumber:
        # Sort alphabetically
        stoicList.sort()

    # Append the charges to the end
    if chargeList:
        stoicList += chargeList

    newStoichiometricFormula = ''
    for row in stoicList:
        if row[1] > 1:
            newStoichiometricFormula += row[0] + str(row[1])
        else:
            newStoichiometricFormula += row[0]

    return stoichiometricFormula, atomicNumberString, mass, charge, newStoichiometricFormula
    

def generateEmpiricalFormula(formula):
    # Could use the Stoichiometric formula and just reorder the elements alphabetically.
    # using the Hill sorting algorithm (i.e. C first, H, then the rest)

    return


def sendWebServiceRequest(server, posturl, data, credentials):
    """ Uses httplib NOT urllib2 because urllib2 raises an exception if the response type is not 2xx """

    import httplib, urllib
    auth = base64.b64encode("%s:%s" % (credentials['user'], credentials['pass']))
    authorization = "Basic %s" % auth

    conn = httplib.HTTPConnection(server, 80)
    headers = {"Content-type": "application/json", "Accept": "*/*", 'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
    headers["Authorization"] = authorization

    conn.request("POST", posturl, data, headers)

    resp = conn.getresponse()

    status = resp.status
    reason = resp.reason
    response = resp.read()
    conn.close()

    return response


def addInChIToDatabase (server, posturl, dataDict, credentials):
    import json

    #dataDict = {'inchikey':'QVGXLOLLOCUKJST-UHFFAOYSA-N','inchi':'InChI=1S/O', 'charge':0, 'mass_number':16, 'species_type':'atom'}
    data = json.dumps(dataDict)
    print data

    #server = 'psweb.mp.qub.ac.uk'
    #posturl = '/vamdc/inchi/api/add/'

    response = sendWebServiceRequest(server, posturl, data, credentials)

    try:
        result = json.loads(response)
        print result
    except ValueError, e:
        print response
        return 1

    return 0


def getMoleculeComponents(molecule):
    """Spit out the SMILES representation of the structural formula"""

    # This code is based on the stoichiometric formula code.  Need to alter.
    # Need to split out multiple atoms and order them as stated in the struct
    # formula

    # To do this, we'll do use the finditer() method, which we can use to find
    # start and end positions of all the matches.

    # Create a new ELEMENTS dictionary, this time with some extra elements for
    # methyl groups, etc

    COMBINED_ELEMENTS = dict(ELEMENTS, **SMILES_MOLECULE_COMPONENTS)

    elementTuples = sorted(COMBINED_ELEMENTS.iteritems(), key=lambda (k,v): (v,k))

    originalMoleculeLength = len(molecule)

    # Build an element list in ascending atomic number order
    elementList = []
    for tuple in elementTuples:
       elementList.append(tuple[0])

    # Now sort the original list by element symbol length (reversed)
    # We need to do this so that long regular expressions are matched
    # before the short ones.
    elementList.sort(cmp=bylength)

    inputMolecule = molecule

    # Nibble through the molecule until there is nothing left.
    moleculeComponents = []
    i = 0
    for element in elementList:
        originalLength = len(molecule)
        (molecule, elementRecurrences) = splitMolecule(molecule, element)
        if elementRecurrences:
            moleculeComponents.append([i, originalLength, elementRecurrences])
            i += 1

        if len(molecule) == 0:
            break

    if len(molecule) > 0:
        print "Can't reduce any more. Remainder = %s" % molecule
        return ''

    # Now create a dictionary of our molecule componenets
    moleculeDict = {}

    # What we need to do is record the original positions of the components of
    # the molecule in the original molecule string.  This will allow us to
    # reconstruct the molecule from its components in the right order.

    positionArray = range(originalMoleculeLength)
    gapArray = list(positionArray)
    #print "ORIGINAL GAP ARRAY = ", gapArray

    # We gave now rows containing: iteration, length, recurrences
    for row in moleculeComponents:
        #print 'ROW = ',row
        # Get array of gaps - should equal length of next iteration
        for recurrence in row[2][:]:
            #print recurrence

            # Remove elements from list
            for item in range(recurrence[2]-recurrence[1]):
                gapArray.remove(positionArray[recurrence[1]+item])

            moleculeDict[positionArray[recurrence[1]]] = recurrence[0]
            #print "GAPArray = ", gapArray
            #print "POSITION ARRAY = ", positionArray

        # Now reset the position array to be the new gap array
        positionArray = list(gapArray)

    # Now we have a dictionary that contains:
    # key = position in original molecule string
    # value = the element or molecular substring

    # We want to be able to recreate the original molecule substring by substring
    # (so that we can bracket the substrings for SMILES).  However, we can't sort
    # a dict.  So create a list of the values sorted by key.

    moleculeListOfTuples = [x for x in moleculeDict.iteritems()]

    return moleculeListOfTuples


def expandOutElements(moleculeComponent):

    elementRepetitionGreaterThan1Regex = '([0-9]+)$'
    compiledElementRepetitionGreaterThan1Regex = re.compile(elementRepetitionGreaterThan1Regex)

    expandedComponents = []

    # Don't want to expand any of our methyl groups etc
    try:
        if SMILES_MOLECULE_COMPONENTS[moleculeComponent]:
            expandedComponents = [moleculeComponent]


    except KeyError, e:
        # It's not one of our methyl groups etc - just something like O2 or C6
        countString = compiledElementRepetitionGreaterThan1Regex.search(moleculeComponent)

        if countString:
            elementCount = int(countString.group(1))
            # Pick out the first characters minus the element count.  Not a simple substitution
            # because we might also have an isotope specifier.  We do know however that this
            # count is always at the end of the molecule.
            moleculeComponentWithoutCount = moleculeComponent[0:len(moleculeComponent) - len(str(elementCount))]
            for i in range(elementCount):
                expandedComponents.append(moleculeComponentWithoutCount)
        else:
            expandedComponents = [moleculeComponent]

    return expandedComponents


def generateSMILESFromStructuralFormula(molecule):

    # For SMILES we need to replace brackets with a mass prefix
    bracketCheckRegex = '\\(([0-9]{1,2})\\)'
    compiledBracketCheckRegex = re.compile(bracketCheckRegex)


    brackets = ['[',']']
    moleculeComponents = getMoleculeComponents(molecule)

    smiles = ''

    if not moleculeComponents:
        return smiles

    # Now create a SMILES string
    for component in moleculeComponents:

        expandedComponents = expandOutElements(component[1])
        if len(expandedComponents) > 1:
            brackets = ['([', '])']
        else:
            brackets = ['[', ']']

        numberOfComponents = len(expandedComponents)
        i = 0
        for expComponent in expandedComponents:

            if i > 0 and expComponent != 'C':
                brackets = ['([', '])']
            else:
                brackets = ['[', ']']

            bracketString = compiledBracketCheckRegex.search(expComponent)
            if bracketString:
                mass = int(bracketString.group(1))
                nonIsotopicComponent = compiledBracketCheckRegex.sub('', expComponent)
                smiles += '%s%d%s%s' % (brackets[0], mass, nonIsotopicComponent, brackets[1])
            else:
                smiles += '%s%s%s' % (brackets[0], expComponent, brackets[1])
            i += 1

    # Now we need to fix the charge.

    if '[+]' in smiles:
        smiles = smiles.replace('[+]', '+')

    if '[-]' in smiles:
        smiles = smiles.replace('[-]', '-')

    if ']+' in smiles:
        smiles = smiles.replace(']+', '+')

    if ']-' in smiles:
        smiles = smiles.replace(']-', '-')

    if '])-' in smiles:
        smiles = smiles.replace('])-', '-])')

    if '])+' in smiles:
        smiles = smiles.replace('])+', '+])')

    if smiles[-1] == '+' or smiles[-1] == '-':
        smiles += ']'

    return smiles


def restructuredTextify(formula):
    """Check for isotope prefix, repetition, charge suffix"""

    # Any number, except a charge sign, should be changed a subscript,
    # except for any charge signs, which should be superscripted.

    # This nearly works.  Need to figure out how NOT to replace last.  Maybe another replace operation.
    restFormula = re.sub(r'([A-Za-z]+)([0-9]{1,2})', r'\1\\ :sub:`\2`\\ ', formula)

    # Second pass.  Look for +/- signs.

    restFormula = re.sub(r'([\\+\\-]+)([0-9]{0,2})$', r'\\ :sup:`\1\2`', restFormula)

    # Third pass.  Replace bracketed isotope specifiers.

    restFormula = re.sub(r'\(([0-9]+)\)', r'\ :sup:`\1`\\ ', restFormula)

    # Fourth pass.  Correct problems caused by first pass - e.g. extra \ at end of formula

    restFormula = re.sub(r'\\ $', r'', restFormula)

    # Fifth pass.  Correct problems caused by third pass - e.g. extra \ at beginning of formula

    restFormula = re.sub(r'^\\ ', r'', restFormula)

    # Sixth pass.  Correct occurrences of '\ \ '.

    restFormula = re.sub(r'\\ \\ ', r'\\ ', restFormula)

    return restFormula




def main(argv = None):

    if argv is None:
        argv = sys.argv

    if len(argv) != 5:
        sys.exit("Usage: generateInChIKeysForUMISTSpecies.py <username> <password> <database> <hostname>")

    username = argv[1]
    password = argv[2]
    database = argv[3]
    hostname = argv[4]

    conn = dbConnect(hostname, username, password, database)

    server = 'psweb.mp.qub.ac.uk'
    posturl = '/vamdc/inchi/api/add/'

    httpuser = 'vamdc'
    httppass = 'v4mdc'

    credentials = {}
    credentials['user'] = httpuser
    credentials['pass'] = httppass

    # We want to read all the structural formulae and empirical formulae.
    # The structural formulae will be used to generate the stoichiometric formulae.
    # One could probably use the same code to regenerate the empirical formulae, but
    # we might as well use the empirical formulae already present (though it would be
    # an interesting exercise to compare them and useful for other database sources).

    # We MUST have a table of most abundant atomic mass numbers and a table of elements
    # whose atomic masses must ALWAYS be specified.

    # We'll use this table to calculate the mass of the species, unless overridden by the
    # isotope specifier.

    # NOTE that when specifying SMILES, look for (e.g.) Ethyl CH2 and Methyl CH3 groups.  This
    # makes is easier to more reliably generate the correct InChI.

    # We should also probably calculate the mass on the fly.  There are one or two errors
    # in the UMIST database.

    # First, grab all the species.

    umistSpeciesResultSet = getUMISTSpecies(conn)

    sFormulaAtomicNumberDict = {}

    atomicDict = {}

    for row in umistSpeciesResultSet:
        (formula, atomicNumberList, mass, charge, newStoicFormula) = generateStoichiometricFormula(row['struct_name'], sortByAtomicNumber=False)
        #print '%s, %s, %s' % (row['struct_name'], row['empirical'], formula)




        # Create a python dictionary of species (depracated code)

        if atomicNumberList in sFormulaAtomicNumberDict:
            sFormulaAtomicNumberDict[atomicNumberList] = sFormulaAtomicNumberDict[atomicNumberList] + 1
            # append a list of lists [[instance number, stoic, struct]]
            # First need to get max instance number from exiting list

            # We've already got the max above, so try this...

            atomicDict[atomicNumberList].append([sFormulaAtomicNumberDict[atomicNumberList], formula, row['struct_name'], row['names'], row['species_id'], mass, charge, row['empirical'], row['mass'], newStoicFormula])
            if mass != row['mass']:
                print "WARNING - Mass inconsistent"
                print "Species: %s" % row['struct_name']
                print "Calculated Mass: %d" % mass
                print "Stored Mass: %d" % row['mass']
                print ""

        else:
            sFormulaAtomicNumberDict[atomicNumberList] = 1
            atomicDict[atomicNumberList] = [[sFormulaAtomicNumberDict[atomicNumberList], formula, row['struct_name'], row['names'], row['species_id'], mass, charge, row['empirical'], row['mass'], newStoicFormula]]
            if mass != row['mass']:
                print "WARNING - Mass inconsistent"
                print "Species: %s" % row['struct_name']
                print "Calculated Mass: %d" % mass
                print "Stored Mass: %d" % row['mass']
                print ""

    #print sFormulaAtomicNumberDict

    for k,v in sFormulaAtomicNumberDict.items():
        if v > -1:
            print '%s -> %d' % (k,v)

    # OK - we need to write these into a new database table.

    for k,v in atomicDict.items():
        print ''
        #print '** Molecule ID: %s' % k
        for item in v:
            #print 'Molecule ID: %s-%d - Stoichiometric Formula: %s - UMIST Structural Formula: %s - Aliases: %s' % (k, item[0], item[1], item[2], item[3])
            print ''
            print ''
            print '**********************************************'
            print ''
            print 'MoleculeID: %s, UMIST ID: %s, Stoichiometric Formula: %s - UMIST Structural Formula: %s - Aliases: %s' % (k, item[4], item[9], item[2], item[3])
            if item[5] != item[8]:
                print '*** MASS INCONSISTENCY *** Species ID: %s, struct_name: %s, empirical: %s, Calculated Mass: %d, UMIST Stored Mass: %d' % (item[4], item[9], item[7], item[5], item[8])
            else:
                print "Calculated Mass = %d, Stored Mass = %d" % (item[5], item[8])
            print "Charge = %d" % item[6]
            print "Empirical = %s" % item[7]
            print "Structural = %s" % item[2]
            print "Stoichiometric = %s" % item[9]

            #print 'STOICS FOR UPDATE:', item[4], item[9]+';'+restructuredTextify(item[9])
            #continue

            smiles = generateSMILESFromStructuralFormula(item[2])
            print smiles

            doNotAddH = True
            reconnectMetal = False
            print "Enter alternative SMILES conversion. (Hydrogens are NOT added by default. Metal Disconnected by default.)"
            print "Append ';addh' to the SMILES if you want to add Hydrogen automatically."
            print "Append ';recmet' to the SMILES if you want to force metal reconnection (not normally recommended).."
            alternateSmiles = raw_input()

            alternateSmilesList = alternateSmiles.strip().split(';')

            if alternateSmilesList[0].strip() != '':
                smiles = alternateSmilesList[0].strip()

            if len(alternateSmilesList) > 1 and len(alternateSmilesList) < 4:
                if alternateSmilesList[1].strip() == 'addh':
                    doNotAddH = False
                if alternateSmilesList[1].strip() == 'recmet':
                    reconnectMetal = True

                if len(alternateSmilesList) > 2:
                    if alternateSmilesList[2].strip() == 'recmet':
                        reconnectMetal = True
                    if alternateSmilesList[2].strip() == 'addh':
                        doNotAddH = False

            inchi, inchikey = getInChIAndInChIKey(smiles, doNotAddH = doNotAddH, reconnectMetal = reconnectMetal)

            calculatedInChIKey = inchiapi.GetINCHIKeyFromINCHI(inchi,1,1)[1]

            if inchi:
                print inchi
                print inchikey

                dataDict = {}

                dataDict['inchi'] = inchi
                dataDict['inchikey'] = inchikey
                dataDict['charge'] = item[6]
                dataDict['mass_number'] = item[5]
                dataDict['species_type'] = 'molecule' # Should be able to guess this from the stoichiometric formula calculation

                dataDict['stoichiometric_formulae'] = item[9] + ';' + restructuredTextify(item[9])

                dataDict['structural_formulae'] = item[2] + ';' + restructuredTextify(item[2])

                dataDict['empirical_formulae'] = item[7] + ';' + restructuredTextify(item[7])

                print restructuredTextify(item[2])
                if item[3]:
                    dataDict['names'] = item[3]
                dataDict['database_source'] = 'UMIST'
                dataDict['source_database_identifiers'] = str(item[4])

                addToDatabase = raw_input('Add this molecule to the database? y/1/2 = yes or n = no, q = quit:  ')
                if addToDatabase.strip() == 'q':
                    print "Exiting..."
                    sys.exit(0)

                if addToDatabase.strip() == 'n':
                    continue

                if addToDatabase.strip() not in ['y', '1', '2']:
                    continue

                if addToDatabase.strip() == '1':
                    dataDict['species_type'] = 'atom'

                addInChIToDatabase (server, posturl, dataDict, credentials)


            if calculatedInChIKey != inchikey:
                print "WARNING: Calculated inchikey: %s does not match submitted inchikey: %s" % (calculatedInChIKey, inchikey)

            aliases = [[item[2], 'structural', 1]]
            if item[3]:
                names = item[3].split('; ')
                if names:
                    for name in names:
                        if not aliases:
                            aliases = [[name, 'other',2]]
                        else:
                            aliases.append([name, 'other',2])

#            addMoleculeToDatabase(conn, '%s_%d'%(k,item[0]), item[1], 'UMIST', aliases, item[4])

#        print formula
    
    #look = DictLookup(ELEMENTS)
    #print look.get_key(1)
    #print look.get_value('H')





# ###########################################################################################
#                                         Main hook
# ###########################################################################################


if __name__=="__main__":
    main()

