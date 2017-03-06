# -*- coding: utf-8 -*-
"""Example of Converting TextSum model data.
Usage:
python textsum_data_convert.py --command text_to_binary --in_directories dailymail/stories --out_files dailymail-train.bin,dailymail-validation.bin,dailymail-test.bin --split 0.8,0.15,0.05
python textsum_data_convert.py --command text_to_vocabulary --in_directories cnn/stories,dailymail/stories --out_files vocab
"""
import collections
import struct
import sys
import codecs
import os
from os import listdir
from os.path import isfile, join

from nltk.tokenize import sent_tokenize
from nltk.tokenize import WordPunctTokenizer
from nltk.tokenize import word_tokenize

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

exceptions={}
dicMap={}

#import tensorflow as tf
#from tensorflow.core.example import example_pb2


#FLAGS = tf.app.flags.FLAGS
#tf.app.flags.DEFINE_string('command', 'text_to_binary',
#                           'Either text_to_vocabulary or text_to_binary.'
#                           'Specify FLAGS.in_directories accordingly.')
#tf.app.flags.DEFINE_string('in_directories', '', 'path to directory')
#tf.app.flags.DEFINE_string('out_files', '', 'comma separated paths to files')
#tf.app.flags.DEFINE_string('split', '', 'comma separated fractions of data')

def _text_to_binary(text_directory,  title_directories,  output_filename, split_fractions,randomTime):
  input_directories=[]
  title_filenames={}
  for filename in os.listdir(text_directory):
      input_directories.append(text_directory+"/"+filename);

  for title_path in  os.listdir(title_directories):

      titleComp = title_path.split(".")
      folder_prefix=titleComp[0]
      folder_prefix=folder_prefix.lower()+"t"
      title_filename=".".join(titleComp[-2:])
      title_filenames[folder_prefix+":"+title_filename]=title_directories+"/"+title_path

  text_filenames =_get_filenames(input_directories)
  print "text_filenames:",text_filenames

  start_from_index = 0
  #for index, output_filename in enumerate(output_filenames):
    #sample_count = int(len(filenames) * split_fractions[index])
    #print(output_filename + ': ' + str(sample_count))
    #end_index = min(start_from_index + sample_count, len(filenames))
  _convert_files_to_binary(text_filenames,title_filenames , output_filename)
    #start_from_index = end_index

def _text_to_vocabulary(base_vocab_filename,result_files,vocabulary_filename, max_words=200000,choose_base_vocab_filename='no'):
  input_directories=[]
  counter = collections.Counter() 
  if choose_base_vocab_filename == 'yes':
          vocab_file = open(base_vocab_filename,'r');
          for wordString in vocab_file:
              wordString = str.strip(wordString)
              wordEntry=wordString.split(" ")
              counter[wordEntry[0]]=int(wordEntry[1]);

  for result_file in result_files:
    f=codecs.open(result_file)
    for line in f:
      seg=line.split("\t")
      article=seg[0].split("=")[1]
      abstract=seg[1].split("=")[1]
      article = article.replace("<d> <p> <s> ","")
      article = article.replace(" </s> <s>","")
      article = article.replace("</s> </p> </d>","")
      abstract = abstract.replace("<d> <p> <s>","")
      abstract = abstract.replace(" </s> <s>","")
      abstract = abstract.replace("</s> </p> </d>","")
      wordEntry=article.strip().split(" ")
      counter.update(wordEntry)
      wordEntry=abstract.strip().split(" ")
      counter.update(wordEntry)
   
  with open(vocabulary_filename, 'w') as writer:
    for word, count in counter.most_common(max_words - 2):
      writer.write(word + ' ' + str(count) + '\n')

    if '<UNK>' not in counter:
        writer.write('<UNK> 0\n')
    if '<PAD>' not in counter:
        writer.write('<PAD> 0\n')
 
def _text_to_vocabulary_old(base_vocab_filename,text_directories,title_directory, vocabulary_filename, max_words=200000,choose_base_vocab_filename='no'):
  input_directories=[]
  counter = collections.Counter()
  for text_directory in text_directories:
      for filename in os.listdir(text_directory):
          input_directories.append(text_directory+"/"+filename);
  
      text_filenames = _get_filenames(input_directories)
  
      #load base vocab original dictionary and increment counter for words in your corpus
      #reference: https://github.com/tensorflow/models/issues/622
      if choose_base_vocab_filename == 'yes':
          vocab_file = open(base_vocab_filename,'r');
          for wordString in vocab_file:
              wordString = str.strip(wordString)
              wordEntry=wordString.split(" ")
              counter[wordEntry[0]]=int(wordEntry[1]);
  
      for filename in text_filenames:
        with open(filename, 'r') as f:
#result = _get_Text(filename)      
          result = cs._get_Text(filename)
          body = result[1].decode('utf8').replace('\n', ' ').replace('\t', ' ').replace('$$$$$','')
      
          title_array = cs.getTitle(title_directory+"/"+result[0])
      
          for title in title_array:

              title = " ".join(WordPunctTokenizer().tokenize(title))
              document = " ".join(WordPunctTokenizer().tokenize(body))
              title = cs.adjustSingleQuote(title)
              document= cs.adjustSingleQuote(document) 
              #document = f.read()
              articleWords = document.split()
              titleWords = title.split()
              counter.update(articleWords)
              counter.update(titleWords)
  
  with open(vocabulary_filename, 'w') as writer:
    for word, count in counter.most_common(max_words - 2):
      writer.write(word + ' ' + str(count) + '\n')
    
    if '<UNK>' not in counter:
        writer.write('<UNK> 0\n')
    if '<PAD>' not in counter:
        writer.write('<PAD> 0\n')

try: 
  import xml.etree.cElementTree as ET 
except ImportError: 
  import xml.etree.ElementTree as ET 
import sys 


def _get_Text(text_path):
    try: 
        temp_string = open(text_path,'r').read()
        #add HTML parsing
        temp_string = temp_string.replace("&AMP;","&amp;amp;")
        
        root = ET.fromstring(temp_string)   
        DOCNO = str.strip(root.find('DOCNO').text)
        TEXT = str.strip(root.find('TEXT').text)
    except Exception, e: 
        print "Error:cannot parse file:",text_path
        print e
        sys.exit(1) 
    return  DOCNO,TEXT

def _get_filenames(input_directories):
  filenames = []
  for directory_name in input_directories:
    if isfile(directory_name):
        filenames.extend([directory_name] )
    else:
        filenames.extend([join(directory_name, f) for f in listdir(directory_name) if isfile(join(directory_name, f))])
  return filenames

def puredTokenize(text):
  return word_tokenize(text)


def getTitle(path):
    f=codecs.open(path,'r','utf-8');
    strs=""
    for line in f:
        strs = strs+line;
    return strs;

def _convert_files_to_binary(text_filePaths, title_filenames, output_filename):
  with codecs.open(output_filename, 'w','utf-8') as writer: 
    for text_filePath in text_filePaths:
      text_comp=text_filePath.split("/")
      key4title_filenames=":".join(text_comp[-2:])
      result = _get_Text(text_filePath)
      if key4title_filenames in title_filenames:
          title_filePath=title_filenames[key4title_filenames]
      else :
          print "this must be the decode mode",result[2]
          title_filePath="/tmp/textsum/pkg/CCCS-Luna-IT-EN-test_2015-04-10/EN/manual/synopsis/test.txt"
          print "apply pusedo reference file:",title_filePath
          return

      title_content = getTitle(title_filePath)
      title_content = title_content.encode('utf-8')
      title_content = str.strip(title_content)
      title_content = title_content.decode('utf-8')
      title_contents= sent_tokenize(title_content)
      tempTitle=' '.join(['<s> ' + " ".join(WordPunctTokenizer().tokenize(title_sen.decode('utf-8'))) + ' </s>' for title_sen in title_contents])
      tempTitle = tempTitle.encode('utf-8')
      tempTitle = str.strip(tempTitle)
      tempTitle = tempTitle.decode('utf-8')
      if tempTitle == '' :
        continue
      title = '<d> <p> ' + tempTitle + ' </p> </d> '
          
      #get articles
      filename_key=result[0]
      body = result[1].replace('\n', ' ').replace('\t', ' ')
      sentences=sent_tokenize(body)
      temp = ' '.join(['<s> ' + " ".join(WordPunctTokenizer().tokenize(sentence)) + ' </s>' for sentence in sentences])
      temp= str.strip(temp)
      if temp == '' :
        continue
      body = '<d> <p> ' + temp + ' </p> </d> '
      body = "article=" + body + "\tabstract=" + title+  "\tfilename=" + filename_key  + "\tpublisher=AFP"
      writer.write(body+"\n"); 

#train&test
_text_to_binary("/tmp/textsum/duc2004/docs","/tmp/textsum/duc2004/eval/models/1","result_train_duc_all.txt","",1)
_text_to_vocabulary("vocab",["result_train_duc_all.txt"],"test_vocab_duc",choose_base_vocab_filename="yes")
