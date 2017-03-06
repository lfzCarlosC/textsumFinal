# -*- coding: utf-8 -*-
"""Example of Converting TextSum model data.
Usage:
python textsum_data_convert.py --command text_to_binary --in_directories dailymail/stories --out_files dailymail-train.bin,dailymail-validation.bin,dailymail-test.bin --split 0.8,0.15,0.05
python textsum_data_convert.py --command text_to_vocabulary --in_directories cnn/stories,dailymail/stories --out_files vocab
"""
import mlg as mlg
import collections
import struct
import sys
import codecs
import os
from os import listdir
from os.path import isfile, join
import shutil
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
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


def _text_to_binary(text_directories,  title_directories,  output_filename, split_fractions):
  input_directories=[]
  title_filenames={}
  for text_directory in text_directories:
      for filename in os.listdir(text_directory):
          input_directories.append(text_directory+"/"+filename);

  for title_directory in title_directories:
      for title_path in  os.listdir(title_directory):
          title_path_comp = title_path.split("/")
          title_filename = title_path_comp[len(title_path_comp)-1]
          title_filename_comp = title_filename.split(".")
          title_filename_suffix = ".".join(title_filename_comp[len(title_filename_comp)-2:len(title_filename_comp)])
          title_filenames[title_filename_suffix]=title_directory+"/"+title_path

  text_filenames = _get_filenames(input_directories)
  
  start_from_index = 0
  #for index, output_filename in enumerate(output_filenames):
    #sample_count = int(len(filenames) * split_fractions[index])
    #print(output_filename + ': ' + str(sample_count))
    #end_index = min(start_from_index + sample_count, len(filenames))
  _convert_files_to_binary(text_filenames,title_filenames , output_filename)
    #start_from_index = end_index

def _text_to_vocabulary(base_vocab_filename,text_directories,title_directory, vocabulary_filename, max_words=200000,choose_base_vocab_filename='no'):
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
          langCode = filename.split("/")[-2]
          result = mlg._get_Text(filename)
          body = result[1].decode('utf8').replace('\n', ' ').replace('\t', ' ').replace('$$$$$','')
      
          title_array = mlg.getTitle(title_directory+"/"+langCode+"/"+result[0])
          title_array = title_array.split("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
          for title in title_array:

              title=" ".join(word_tokenize(title))
              document=" ".join(word_tokenize(body))
#title = " ".join(WordPunctTokenizer().tokenize(title))
#document = " ".join(WordPunctTokenizer().tokenize(document))
              title = mlg.adjust(title)
              document= mlg.adjust(document) 
              #document = f.read()
              articleWords = [ langCode+":"+i for i in document.split()]
              titleWords = [langCode+":"+i for i in title.split()]
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
import codecs
def sentenceByLine(text):
    f=codecs.open("sentence_vector_sum.txt","w")
    for t in text:
      t1=t.strip()
      if len(t1)>10:
          f.write(t.strip()+"\n")
    f.close()

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
      
      result = mlg._get_Text(text_filePath)
      filename_key=result[2]
      if result[0] in title_filenames :
          title_filePath = title_filenames[result[0]]
      else :
          print "this must be the decode mode",result[2]
          title_filePath="/tmp/textsum/pkg/CCCS-Luna-IT-EN-test_2015-04-10/EN/manual/synopsis/test.txt"
          print "apply pusedo reference file:",title_filePath
     
      langCode=title_filePath.split("/")[-2]
      title_array = mlg.getTitle(title_filePath)
      #originally duplicated title to augment data but here is just one damn long summary
      title_array = title_array.split("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
      for title_content in title_array:
          #print "====",title_filePath,title_content
          title_content=title_content.encode('utf-8')
          title_content = str.strip(title_content)
          title_contents=sent_tokenize(title_content.decode('utf-8'))
          if title_contents[len(title_contents)-1]=='':
              title_contents=title_contents[0:len(title_contents)-1]
          title = '<d> <p> ' + ' '.join(['<s> ' + " ".join([langCode+":"+ i for i in word_tokenize(title_sen)]) + ' </s>' for title_sen in title_contents]) + ' </p> </d> '

          body = result[1].replace('\n', ' ').replace('\t', ' ')
          sentences=sent_tokenize(body)
          sentences = sentences[0:len(sentences)-1]
         # print "=====before:",body
          body = '<d> <p> ' + ' '.join(['<s> ' + " ".join([langCode+":"+ i for i in word_tokenize(sentence)]) + ' </s>' for sentence in sentences]) + ' </p> </d> '
         # print "=====after:",body
          body=mlg.adjust(body)
          title=mlg.adjust(title)
          body = "article=" + body + "\tabstract=" + title+  "\tfilename=" + filename_key  + "\tpublisher=AFP"
          #print "insert to file:",body
          writer.write(body+"\n"); 

#bodyList=mlg.langCode2File("cs,en,de,hu,sv,el,it,da,fr,fi,es,bg","/tmp/textsum/mlg/multilingMss2015Training/body/text")
#summaryList=mlg.langCode2File("cs,en,de,hu,sv,el,it,da,fr,fi,es,bg","/tmp/textsum/mlg/multilingMss2015Training/summary")
#_text_to_vocabulary("data/vocab",bodyList,"/tmp/textsum/mlg/multilingMss2015Training/summary","test_vocab_mlg",choose_base_vocab_filename="no")
#_text_to_binary(bodyList,summaryList,"result_train_mlg.txt","")

#new vector
text=mlg._get_Text('/tmp/textsum/mlg/multilingMss2015Training/summary/en/05cd7ebf19355e466944dd0a83e4c564_summary.txt')
texts = text[1].split(".")
sentenceByLine(texts)
#decode
#_text_to_binary("/tmp/textsum/pkg/CCCS-Luna-IT-EN-test_2015-04-10/EN/manual/text","/tmp/textsum/pkg/CCCS-Luna-IT-EN-test_2015-04-10/EN/manual/synopsis","result_decode.txt","")

#train&test
#_text_to_binary("/tmp/textsum/mlg/multilingMss2015Training/body/text/en","/tmp/textsum/mlg/multilingMss2015Training/summary/en","result_train_mlg_en.txt","")
#_text_to_binary("/tmp/textsum/pkg/test/text","/tmp/textsum/pkg/synopsis","result_test_ext.txt","")
