# -*- coding: utf-8 -*-
# encoding: utf-8
import codecs
import os
import sys
import shutil
from nltk.tokenize import WordPunctTokenizer
from nltk.tokenize import  sent_tokenize
from nltk.tokenize import word_tokenize
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


def _get_Text(text_path):
    result=""
    f=codecs.open(text_path,'r','utf-8')
    for text in f:
        if not text.startswith('[edi'):
            result = result + text.strip()+" ";
            result=applyFilter(result)
    #getfilename
    textfilename = text_path.split("/")[len(text_path.split("/"))-1]
    textfilename = textfilename.strip()
    tempname=textfilename.split("_")[0]+"_summary."+textfilename.split(".")[1];
    print "result:",result 
    return tempname,result,textfilename.split("_")[0]

import re

def applyFilter(text):
    text=capticalToSmall(text)
    text=exceptionList(text)
    text=convertDoubleQuote(text)
    text=clearCRLF(text)   
    return text

def convertDoubleQuote(text):
    text=text.replace("''",'"')
    text=text.replace("„",'"')
    text=text.replace("“",'"')
    return text

def removeLessSentence(text):
    if len(text.split())<=10:
        text = ''
    return text

def capticalToSmall(text):
    return text.lower()
    
def exceptionList(text):
    text=text.replace("="," ")
    text=text.replace(u'\ufffd'," ")
    text=text.replace("...","")
    text=text.replace("i.e.","")
    text=text.replace("&apos;","'")
    return text 

def adjust(text):
    text=adjustAndQuote(text)
    return text 
    
def adjustAndQuote(text):
    text=text.replace(" & ","&")
    return text

def adjustSingleQuote(text):
    text=text.replace("' s ","'s ")
    return text


def removeTag(text):
    replace_reg = re.compile(r"<[^<]*>")
    text = replace_reg.sub('', text) 
    return text
   
def removeTag_bak(text):

    text = text.replace("<entities_loc.geo>","")
    text = text.replace("</entities_loc.geo>","")
    text = text.replace("<entities_pers.agent.nom/>","")
    text = text.replace("<entities_loc.edu>","")
    text = text.replace("</entities_loc.edu>","")
    text = text.replace("<entities_loc.geo.line/>","")  
    text = text.replace("<entities_org>","")  
    text = text.replace("<entities_org.edu>","")
    text = text.replace("</entities_org.edu>","")
    text = text.replace("<noise_conv/>","")
    text = text.replace("<noise_r/>","")
    text = text.replace("<entities_pers.agent.pseudo/>","")
    text = text.replace("<noise_mic>","")
    text = text.replace("</noise_mic>","")
    text = text.replace("<noise_b/>","")
    text = text.replace("<noise_i/>","")
    text = text.replace("<noise_bc/>","")
    text = text.replace("<noise_bb/>","")
    text = text.replace('<noise_tonalité/>',"") 
    text = text.replace("<pronounce_b/>","")
    text = text.replace("<pronounce_pi/>","")
    text = text.replace("<noise_mic/>","")
    text = text.replace("</noise_mic>","")
    text = text.replace("<noise_mic>","")
    return text;

def clearCRLF(str):
    str=str.replace("\n","")
    str=str.replace("\r","")
    return str

def getTitle(titleFilePath):
    #read first line
    f=codecs.open(titleFilePath,'r','utf-8');
    result=""
    for line in f:
        result += line
    result = applyFilter(result)
    return result

def langCode2File(langList,filePath):
  lang=langList.split(",")
  result=[]
  for i in lang:
    temp=filePath+"/"+i
    if os.path.isdir(temp):
      result.append(temp)
  return result

#langCode2File("cs,en,de,hu,sv,el,it,da,fr,fi,es,bg","/tmp/textsum/mlg/multilingMss2015Training/body/text")
#langCode2File("cs,en,de,hu,sv,el,it,da,fr,fi,es,bg","/tmp/textsum/mlg/multilingMss2015Training/summary")
#getTitle('/tmp/textsum/mlg/multilingMss2015Training/summary/en/05cd7ebf19355e466944dd0a83e4c564_summary.txt')
(_,sen,_)=_get_Text('/tmp/textsum/mlg/multilingMss2015Training/body/text/en/05cd7ebf19355e466944dd0a83e4c564_body.txt')
print WordPunctTokenizer().tokenize(sen)
#print "|".join(sent_tokenize(sen))
#print word_tokenize(sen)
