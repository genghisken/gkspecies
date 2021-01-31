import xml.dom.minidom
import urllib2, urllib
 
class XsamsSpeciesParser(object):
 
    def __init__(self, url, flag='url'):
        self.list = []
        self.molecule_list = {}        
        self.atom_list = {}        
        self.flag = flag
        xml = self.getXml(url) 
        #print xml
        self.handleXml(xml)
 
    def getXml(self, url):
        try:
            f = urllib2.urlopen(url)
        except Exception, e:
            print e 
            f = url
        #print f
        doc = xml.dom.minidom.parse(f)
        node = doc.documentElement        

        #if node.nodeType == xml.dom.Node.ELEMENT_NODE:
        #    print 'Element name: %s' % node.nodeName
        #    for (name, value) in node.attributes.items():
        #        print '    Attr -- Name: %s  Value: %s' % (name, value)
 
        return node
 
    def handleXml(self, xml):
        #species = xml.getElementsByTagName('Species')        
        atoms = xml.getElementsByTagName("Atom")
        molecules = xml.getElementsByTagName("Molecule")
        #self.handleSpeciesList(species)
        self.handleMoleculeList(molecules)
        self.handleAtomList(atoms)
 
    def getElement(self, element):
        return self.getText(element.childNodes)
 
    def handleMoleculeList(self, molecules):
        for molecule in molecules:
            self.handleMolecule(molecule)
 
    def handleAtomList(self, atoms):
        for atom in atoms:
            self.handleAtom(atom)
 
    def handleMolecule(self, molecule):
        moleculeid = molecule.getAttributeNode('speciesID').nodeValue
        moleculeattributes = {}
        moleculenames = []
        moleculecharge = 0  # For molecules there is no charge, so we'll have to colculate it from the moleculeordinarystructuralformula
        moleculeordinarystructuralformula = []
        molecularweight = 0
        moleculeinchi = ""
        moleculeinchikey = ""
        moleculevamdcspeciesid = ""

        # Stoichiometric formula is mandatory.  No need to check for existence.
        moleculestoichiometricformula = molecule.getElementsByTagName("StoichiometricFormula")[0].firstChild.nodeValue

        moleculeinchielement = molecule.getElementsByTagName("InChI")
        if moleculeinchielement:
            if moleculeinchielement[0].firstChild:
                moleculeinchi = moleculeinchielement[0].firstChild.nodeValue

        moleculeinchikeyelement = molecule.getElementsByTagName("InChIKey")
        if moleculeinchikeyelement:
            if moleculeinchikeyelement[0].firstChild:
                moleculeinchikey = moleculeinchikeyelement[0].firstChild.nodeValue

        moleculevamdcspeciesidelement = molecule.getElementsByTagName("VAMDCSpeciesID")
        if moleculevamdcspeciesidelement:
            if moleculevamdcspeciesidelement[0].firstChild:
                moleculevamdcspeciesid = moleculevamdcspeciesidelement[0].firstChild.nodeValue


        ordinarystructuralformulae = molecule.getElementsByTagName("OrdinaryStructuralFormula")
        if ordinarystructuralformulae:
            if ordinarystructuralformulae[0].firstChild:
                for value in ordinarystructuralformulae[0].getElementsByTagName("Value"):
                    moleculeordinarystructuralformula.append(value.firstChild.nodeValue)


        molecularweights = molecule.getElementsByTagName("MolecularWeight")
        if molecularweights:
            for value in molecularweights[0].getElementsByTagName("Value"):
                molecularweight = float(value.firstChild.nodeValue)


        chemicalnames = molecule.getElementsByTagName("ChemicalName")
        if chemicalnames:
            for value in chemicalnames[0].getElementsByTagName("Value"):
                moleculenames.append(value.firstChild.nodeValue)
 
        #self.list.append(chemicalname)
        if self.flag == 'file':
 
            try:
                pass
            except Exception, e:
                print e
 
        moleculeattributes = {"moleculenames": moleculenames,
                              "moleculecharge": moleculecharge,
                              "molecularweight": molecularweight,
                              "moleculeordinarystructuralformula": moleculeordinarystructuralformula,
                              "moleculestoichiometricformula": moleculestoichiometricformula,
                              "moleculeinchi": moleculeinchi,
                              "moleculeinchikey": moleculeinchikey,
                              "moleculevamdcspeciesid": moleculevamdcspeciesid
                             }
        self.molecule_list[moleculeid] = moleculeattributes
 

    def handleAtom(self, atom):
        # Ion element is mandatory, as is speciesID attribute, so no need for existence checks
        atomid = atom.getElementsByTagName("Ion")[0].getAttributeNode('speciesID').nodeValue

        atomattributes = {}
        atomnames = []
        atomcharge = 0  # For molecules there is no charge, so we'll have to colculate it from the moleculeordinarystructuralformula
        atommassnumber = 0
        atominchi = ""
        atominchikey = ""
        atomvamdcspeciesid = ""

        # Stoichiometric formula is mandatory.  No need to check for existence.
        atomelementsymbol = atom.getElementsByTagName("ElementSymbol")[0].firstChild.nodeValue

        atominchielement = atom.getElementsByTagName("InChI")
        if atominchielement:
            if atominchielement[0].firstChild:
                atominchi = atominchielement[0].firstChild.nodeValue

        atominchikeyelement = atom.getElementsByTagName("InChIKey")
        if atominchikeyelement:
            if atominchikeyelement[0].firstChild:
                atominchikey = atominchikeyelement[0].firstChild.nodeValue


        atommassnumbers = atom.getElementsByTagName("MassNumber")
        if atommassnumbers:
            if atommassnumbers[0].firstChild:
                atommassnumber = int(atommassnumbers[0].firstChild.nodeValue)


        #chemicalnames = atom.getElementsByTagName("ChemicalName")
        #if chemicalnames:
        #    for value in chemicalnames[0].getElementsByTagName("Value"):
        #        atomnames.append(value.firstChild.nodeValue)
 
        if self.flag == 'file':
 
            try:
                pass
            except Exception, e:
                print e
 
        atomattributes = {\
                              "atomcharge": atomcharge,
                              "atommassnumber": atommassnumber,
                              "atomelementsymbol": atomelementsymbol,
                              "atominchi": atominchi,
                              "atominchikey": atominchikey
                         }
        self.atom_list[atomid] = atomattributes
 


    def getText(self, nodelist):
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc
