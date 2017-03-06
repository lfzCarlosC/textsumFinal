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
import codecs
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

def _text_to_vocabulary(base_vocab_filename,text_directory,title_directory, vocabulary_filename, max_words=200000,choose_base_vocab_filename='no'):
  input_directories=[]
  for filename in os.listdir(text_directory):
      input_directories.append(text_directory+"/"+filename);
  
  text_filenames = _get_filenames(input_directories)
  
  counter = collections.Counter()
 
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
      
      title = cs.getTitle(title_directory+"/"+result[0])
      
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
  with codecs.open(output_filename, 'w','utf-8') as writer: 
    for text_filePath in text_filePaths:
      #with open(filename, 'r') as f:
      #  document = f.read()
#result = _get_Tetx(text_filePath)
      result = cs._get_Text(text_filePath)
      filename_key=result[2]
      if result[0] in title_filenames :
          title_filePath = title_filenames[result[0]]
      else :
          print "no file for key:",result[0]
          sys.exit(1)
      
#title_content = open(title_filePath,'r').read()
      title_content = cs.getTitle(title_filePath)
      print "====",title_filePath,title_content
      #without sentence splitting
      #title = '<d> <p> <s> ' + str.strip(title_content) + ' </s> </p> </d>'
      #with sentence splitting
      title_content=title_content.encode('utf-8')
      title_content = str.strip(title_content)
      title_contents=title_content.split(".")
      if title_contents[len(title_contents)-1]=='':
          title_contents=title_contents[0:len(title_contents)-1]
      title = '<d> <p> ' + ' '.join(['<s> ' + " ".join(WordPunctTokenizer().tokenize(title_sen.decode('utf-8'))) + ' </s>' for title_sen in title_contents]) + ' </p> </d> '

      body = result[1].replace('\n', ' ').replace('\t', ' ')
      sentences=body.split("$$$$$")
      sentences = sentences[0:len(sentences)-1]
#sentences = sent_tokenize(body)
      #print sentences
      print "=====before:",body
      body = '<d> <p> ' + ' '.join(['<s> ' + " ".join(WordPunctTokenizer().tokenize(sentence)) + ' </s>' for sentence in sentences]) + ' </p> </d> '
      print "=====after:",body
      body=cs.adjustSingleQuote(body)
      title=cs.adjustSingleQuote(title)
      body = "article=" + body + "\tabstract=" + title+ "\tfilename=" + filename_key+ "\tpublisher=AFP"
      print "insert to file:",body
      writer.write(body+"\n"); 

#_text_to_vocabulary("data/vocab",["/tmp/textsum/pkg/train/text","/tmp/textsum/pkg/test/text"],"/tmp/textsum/pkg/synopsis","test_vocab_cccs_all",choose_base_vocab_filename="yes")
#_text_to_binary("/tmp/textsum/pkg/train/text","/tmp/textsum/pkg/synopsis","result_train.txt","")
_text_to_binary("/tmp/textsum/pkg/test/text","/tmp/textsum/pkg/synopsis","result_test.txt","")
