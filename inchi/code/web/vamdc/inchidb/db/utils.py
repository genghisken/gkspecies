# Utilities file
import urllib
import urllib2
import urlparse
import time
import os

import openbabel as ob


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


def getInChIAndInChIKeyFromSMILES(smilesString, doNotAddH = True, reconnectMetal = False):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("smi", "inchi")
   if doNotAddH == True:
      conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   if reconnectMetal:
      conv.AddOption("X", conv.OUTOPTIONS, "RecMet")


   mol = ob.OBMol()
   conv.ReadString(mol, smilesString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   if doNotAddH == True:
      conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   if reconnectMetal:
      conv.AddOption("X", conv.OUTOPTIONS, "RecMet")

   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)


def getInChIAndInChIKeyFromCML(cmlString, doNotAddH = True, reconnectMetal = False):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("cml", "inchi")
   if doNotAddH == True:
      conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   if reconnectMetal:
      conv.AddOption("X", conv.OUTOPTIONS, "RecMet")


   mol = ob.OBMol()
   conv.ReadString(mol, cmlString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   if doNotAddH == True:
      conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   if reconnectMetal:
      conv.AddOption("X", conv.OUTOPTIONS, "RecMet")

   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)


def getInChIAndInChIKeyFromMOL(molString, doNotAddH = True, reconnectMetal = False):
   conv = ob.OBConversion()
   conv.SetInAndOutFormats("mol", "inchi")
   if doNotAddH == True:
      conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   if reconnectMetal:
      conv.AddOption("X", conv.OUTOPTIONS, "RecMet")

   mol = ob.OBMol()
   conv.ReadString(mol, molString)
   inchi = conv.WriteString(mol).rstrip()
   conv.SetOptions("K", conv.OUTOPTIONS)
   if doNotAddH == True:
      conv.AddOption("X", conv.OUTOPTIONS, "DoNotAddH")
   if reconnectMetal:
      conv.AddOption("X", conv.OUTOPTIONS, "RecMet")
   inchikey = conv.WriteString(mol).rstrip()
   return(inchi, inchikey)


def jsMultilineString(string):
   """ Split a multiline string into javascript compatible statement """
   stringjs = None

   if string:
      stringLines = string.split('\n')
      stringjs = ""
      for line in stringLines[:-1]:
         stringjs += "'%s\\n' +\n" % line.rstrip()
      stringjs += "'%s\\n'" % stringLines[-1].rstrip()

   return stringjs

