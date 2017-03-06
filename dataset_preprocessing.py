# -*- coding: utf-8 -*-
"""Example of Converting TextSum model data.
Usage:
python textsum_data_convert.py --command text_to_binary --in_directories dailymail/stories --out_files dailymail-train.bin,dailymail-validation.bin,dailymail-test.bin --split 0.8,0.15,0.05
python textsum_data_convert.py --command text_to_vocabulary --in_directories cnn/stories,dailymail/stories --out_files vocab
"""
import cccs as cs
import collections
import struct
import sys

import os
from os import listdir
from os.path import isfile, join

from nltk.tokenize import sent_tokenize
from nltk.tokenize import WordPunctTokenizer

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)


#import tensorflow as tf
#from tensorflow.core.example import example_pb2


#FLAGS = tf.app.flags.FLAGS
#tf.app.flags.DEFINE_string('command', 'text_to_binary',
#                           'Either text_to_vocabulary or text_to_binary.'
#                           'Specify FLAGS.in_directories accordingly.')
#tf.app.flags.DEFINE_string('in_directories', '', 'path to directory')
#tf.app.flags.DEFINE_string('out_files', '', 'comma separated paths to files')
#tf.app.flags.DEFINE_string('split', '', 'comma separated fractions of data')

def _text_to_binary(text_directory,  title_directories,  output_filename, split_fractions):
  input_directories=[]
  title_filenames={}
  for filename in os.listdir(text_directory):
      input_directories.append(text_directory+"/"+filename);

  for title_path in  os.listdir(title_directories):
      title_path_comp = title_path.split("/")
      title_filename = title_path_comp[len(title_path_comp)-1]
      title_filename_comp = title_filename.split(".")
      title_filename_suffix = ".".join(title_filename_comp[len(title_filename_comp)-2:len(title_filename_comp)])
      title_filenames[title_filename_suffix]=title_directories+"/"+title_path

  text_filenames = _get_filenames(input_directories)
  
  start_from_index = 0
  #for index, output_filename in enumerate(output_filenames):
    #sample_count = int(len(filenames) * split_fractions[index])
    #print(output_filename + ': ' + str(sample_count))
    #end_index = min(start_from_index + sample_count, len(filenames))
  _convert_files_to_binary(text_filenames,title_filenames , output_filename)
    #start_from_index = end_index

def _text_to_vocabulary(text_directory, vocabulary_filename, max_words=200000):
  input_directories=[]
  for filename in os.listdir(text_directory):
      input_directories.append(text_directory+"/"+filename);
  
  text_filenames = _get_filenames(input_directories)

  counter = collections.Counter()
    
  for filename in text_filenames:
    with open(filename, 'r') as f:
      #result = _get_Text(filename)      
result = cs._get_Text(filename)
      body = result[1].decode('utf8').replace('\n', ' ').replace('\t', ' ')
      document = " ".join(WordPunctTokenizer().tokenize(body))
      #document = f.read()
    words = document.split()
    counter.update(words)

  with open(vocabulary_filename, 'w') as writer:
    for word, count in counter.most_common(max_words - 2):
      writer.write(word + ' ' + str(count) + '\n')
    writer.write('<UNK> 0\n')
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
        
        root = ET.fromstring(temp_string)     #打开xml文档 
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
        
def _convert_files_to_binary(text_filePaths, title_filenames, output_filename):
  with open(output_filename, 'wb') as writer: 
    for text_filePath in text_filePaths:
      #with open(filename, 'r') as f:
      #  document = f.read()
      result = _get_Tetx(text_filePath)
#result = cs._get_Text(text_filePath)
      if result[0] in title_filenames :
          title_filePath = title_filenames[result[0]]
      else :
          print "no file for key:",result[0]
          sys.exit(1)
      
      title_content = open(title_filePath,'r').read()
#title_content = cs.getTitle(title_filePath)
      title = '<d> <p> <s> ' + str.strip(title_content) + ' </s> </p> </d>'
 
    
      body = result[1].replace('\n', ' ').replace('\t', ' ')
      body=body.decode('utf-8')
#sentences=body.split("$$$$$")
      sentences = sent_tokenize(body)
      print sentences
      body = '<d> <p> ' + ' '.join(['<s> ' + " ".join(WordPunctTokenizer().tokenize(sentence)) + ' </s>' for sentence in sentences]) + ' </p> </d> '
      body = "article=" + body + "\tabstract=" + title+  "\tpublisher=AFP"
      writer.write(body+"\n"); 

_text_to_vocabulary("pkg/CCCS-Decoda-FR-EN-training_2015-01-30/EN/auto/text","test_vocab_cccs")
#_text_to_binary("pkg/CCCS-Decoda-FR-EN-training_2015-01-30/EN/auto/text","pkg/CCCS-Decoda-FR-EN-training_2015-01-30/EN/auto/synopsis","result.bin","")
