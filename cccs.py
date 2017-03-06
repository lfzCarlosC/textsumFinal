# -*- coding: utf-8 -*-
# encoding: utf-8
import codecs
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


def _get_Text(text_path):
    result=""
    f=codecs.open(text_path,'r','utf-8')
    flag=False
    for text in f:
        if text.startswith('<overlap>'):
            arr_temp = text.split(":")
            for idx in range(len(arr_temp)):
                if idx > 0:
                    str=arr_temp[idx][:len(arr_temp[idx])-1]
                    str = applyFilter(str)
                    if flag==False:
                        str=removeLessSentence(str)

                    if str.strip()<>'':
                        #print str.strip()
                        result = result + str.strip() +" $$$$$ ";
                        flag=True;
        else:
            str=text[text.find(':')+1:]
            str = applyFilter(str)
            if flag==False:
               str=removeLessSentence(str)

            if str.strip()<>'':
                result = result+str.strip() +" $$$$$ ";
                flag=True;
   
    #getfilename
    textfilename = text_path.split("/")[len(text_path.split("/"))-1]
    textfilename = textfilename.strip()
    tempname=textfilename.split(".")[0]+"_syn."+textfilename.split(".")[1];
    print "result:",result 
    return tempname,result,textfilename.split(".")[0]

import re

def applyFilter(text):
    text=removeTag(text)
    text=capticalToSmall(text)
    text=exceptionList(text)
    text=clearCRLF(text)   
    return text

def removeLessSentence(text):
    if len(text.split())<=10:
        text = ''
    return text

def capticalToSmall(text):
    return text.lower()
    
def exceptionList(text):
    text=text.replace("+"," ")
    text=text.replace("...","")
    text=text.replace("yes.","")
    text=text.replace("yes,","")
    text=text.replace("no.","")
    text=text.replace("no,","")
    text=text.replace("yes","")
    text=text.replace("i.e.","")
    text=text.replace("good bye","")
    text=text.replace("&apos;","'")
    return text 

def adjustSingleQuote(text):
    text=text.replace("' ","'")
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
    str=""
    for line in f:
       if line.strip()<>'\n' and line.strip() <> '':
            if len(line.replace('\n',''))>len(str):
                str = line.replace('\n','')
    return applyFilter(str.split('\t')[2]);

#getTitle('pkg/CCCS-Decoda-FR-EN-training_2015-01-30/EN/auto/synopsis/EN_20091112_RATP_SCD_0005_syn.txt')
_get_Text('pkg/CCCS-Decoda-FR-EN-training_2015-01-30/EN/auto/text/EN_20091112_RATP_SCD_0090.txt')
