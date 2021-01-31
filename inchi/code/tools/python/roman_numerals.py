# convert an integer to a roman numeral
# keep it reasonable since from 5000 on special characters are used
# see also: http://en.wikipedia.org/wiki/Roman_numerals
# tested with Python24       vegaseat        25jan2007

# 2011-06-20 KWS Roman numerals required to set spectroscopic ionization status for elements.
#                We have a list of many ions from the VALD database.

def int2roman(number):
    numerals = {
                 1 : "I",
                 4 : "IV",
                 5 : "V",
                 9 : "IX",
                10 : "X",
                40 : "XL", 
                50 : "L",
                90 : "XC",
               100 : "C",
               400 : "CD",
               500 : "D",
               900 : "CM",
              1000 : "M"
               }
    result = ""
    for value, numeral in sorted(numerals.items(), reverse=True):
        while number >= value:
            result += numeral
            number -= value
    return result

#print int2roman(input("Enter an integer (1 to 4999): "))

