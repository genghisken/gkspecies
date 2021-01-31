import MySQLdb
import urllib2
import urllib
import hashlib
import os,sys

# Sort a list by word length - used to sort the elements by two-letter
# ones first
def bylength(word1, word2):
    """
    write your own compare function:
    returns value < 0 of word1 longer then word2
    returns value = 0 if the same length
    returns value > 0 of word2 longer than word1
    """
    return len(word2) - len(word1)




def find_key(dic, val):
    """return the key of dictionary dic given the value"""
    return [k for k, v in dic.iteritems() if v == val][0]

def find_value(dic, key):
    """return the value of dictionary dic given the key"""
    return dic[key]


class DictLookup(dict):
    """
    a dictionary which can lookup value by key, or keys by value
    """
    def __init__(self, items=[]):
        """items can be a list of pair_lists or a dictionary"""
        dict.__init__(self, items)

    def get_key(self, value):
        """find the key(s) as a list given a value"""
        return [item[0] for item in self.items() if item[1] == value]

    def get_value(self, key):
        """find the value given a key"""
        return self[key]


# MD5 sum program - stolen from the interweb...
def md5(fileName, excludeLine="", includeLine=""):
   """Compute md5 hash of the specified file"""
   m = hashlib.md5()
   try:
      fd = open(fileName,"rb")
   except IOError:
      print "Unable to open the file in readmode:", fileName
      return
   content = fd.readlines()
   fd.close()
   for eachLine in content:
      if excludeLine and eachLine.startswith(excludeLine):
         continue
      m.update(eachLine)
   m.update(includeLine)
   return m.hexdigest()


def dbConnect(lhost, luser, lpasswd, ldb):
   try:
      conn = MySQLdb.connect (host = lhost,
                              user = luser,
                            passwd = lpasswd,
                                db = ldb)
   except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])
      sys.exit (1)

   return conn

def getMolecules(conn):
   # Had to exclude GRAIN0 and GRAIN- because this is not a molecule.
   # NOTE that I've also created a duplicate umist_species table with
   # a minor correction to make sure all 'names' entries are semicolon
   # separated.
   try:
      cursor = conn.cursor (MySQLdb.cursors.DictCursor)
      cursor.execute ("""
         select * from umist_species
         where struct_name not like 'GRAIN%'
         and species_id not in (select distinct cast(database_species_id as unsigned) from vamdcinchi.vamdc_database_aliases)
         order by species_id
      """)
      moleculeArray = []
      resultSet = cursor.fetchall ()

      cursor.close ()

   except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])
      sys.exit (1)

   return resultSet


# Aliases is a dictionary
def addMoleculeToDatabase(conn, moleculeId, stoicFormula, dataOrigin, aliases, originalId=None):
   try:
      cursor = conn.cursor (MySQLdb.cursors.DictCursor)

      cursor.execute ("""
          insert into vamdc_species (molecule_id, stoichiometric_formula, data_origin, data_origin_id)
          values (%s, %s, %s, %s)
          """, (moleculeId, stoicFormula, dataOrigin, originalId))

      moleculeEntryId = conn.insert_id()

      print moleculeEntryId
      print aliases

      for alias in aliases:
          if moleculeEntryId > 0:
              cursor.execute ("""
                  insert into vamdc_aliases (name, vamdc_species_id, alias_type, search_priority)
                  values (%s, %s, %s, %s)
                  """, (alias[0], moleculeEntryId, alias[1], alias[2]))

   except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])

   cursor.close ()
   conn.commit()
   return conn.insert_id()


# 2011-11-24 KWS New code for grabbing species from UMIST database for SMILES->InChI generation
def getUMISTSpecies(conn):
   try:
      cursor = conn.cursor (MySQLdb.cursors.DictCursor)
      cursor.execute ("""
         select * from umist_django.species
         where struct_name not like 'GRAIN%'
         and species_id not in (select distinct cast(database_species_id as unsigned) from vamdcinchi.vamdc_database_aliases)
     --    and species_id in (select distinct cast(database_species_id as unsigned) from vamdcinchi.vamdc_database_aliases)
         and species_id = 499
         order by species_id
      """)
      resultSet = cursor.fetchall ()

      cursor.close ()

   except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])
      sys.exit (1)

   return resultSet


def getVamdcPortalSpecies(conn):
   try:
      cursor = conn.cursor (MySQLdb.cursors.DictCursor)
      cursor.execute ("""
         select inchi, inchikey from vamdc_portal.species_species
         union
         select inchi, inchikey from vamdc_portal.species_iso
      """)
      resultSet = cursor.fetchall ()

      cursor.close ()

   except MySQLdb.Error, e:
      print "Error %d: %s" % (e.args[0], e.args[1])
      sys.exit (1)

   return resultSet

