# -*- coding: utf-8 -*-
"""Example of Converting TextSum model data.
Usage:
python textsum_data_convert.py --command text_to_binary --in_directories dailymail/stories --out_files dailymail-train.bin,dailymail-validation.bin,dailymail-test.bin --split 0.8,0.15,0.05
python textsum_data_convert.py --command text_to_vocabulary --in_directories cnn/stories,dailymail/stories --out_files vocab
"""
import cccs_ext as cs
import collections
import struct
import sys
import codecs
import os
from os import listdir
from os.path import isfile, join

from nltk import WhitespaceTokenizer
from nltk.tokenize import sent_tokenize
from nltk.tokenize import WordPunctTokenizer
from nltk.tokenize import word_tokenize
from nltk.tokenize import  TreebankWordTokenizer
import data

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

def _text_to_binary(text_directory,  title_directories,  output_filename, split_fractions,randomTime,lang):
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
  _convert_files_to_binary(text_filenames,title_filenames , output_filename,lang)
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
      #article = article.replace("<d> <p> <s> ","")
      #article = article.replace(" </s> <s>","")
      #article = article.replace("</s> </p> </d>","")
      #abstract = abstract.replace("<d> <p> <s>","")
      #abstract = abstract.replace(" </s> <s>","")
      #abstract = abstract.replace("</s> </p> </d>","")
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

def puredTokenize(text):
  return word_tokenize(text)

def _convert_files_to_binary(text_filePaths, title_filenames, output_filename, lang):
  tokenizer=TreebankWordTokenizer().tokenize
  
  with codecs.open(output_filename, 'w','utf-8') as writer: 
    for text_filePath in text_filePaths:
      result = cs._get_Text(text_filePath,lang)
      filename_key=result[2]
      if result[0] in title_filenames :
          title_filePath = title_filenames[result[0]]
      else :
          title_filePath="/tmp/textsum/pkg/CCCS-Luna-IT-EN-test_2015-04-10/EN/manual/synopsis/test.txt"

      title_array = cs.getTitle(title_filePath,lang)
      for title_content in title_array:
          title_content=title_content.encode("utf-8")
          title_content = str.strip(title_content)
          title_content=title_content.decode("utf-8")
          title_contents=sent_tokenize(title_content)
          if title_contents[len(title_contents)-1]=='':
              title_contents=title_contents[0:len(title_contents)-1]
          title = '<d> <p> ' + ' '.join(['<s> ' + " ".join(tokenizer(title_sen.decode('utf-8'))) + ' </s>' for title_sen in title_contents]) + ' </p> </d> '
          #WordPunctTokenizer().tokenize
          #get articles
          body = result[1].replace('\n', ' ').replace('\t', ' ').strip()
          sentences=body.split("$$$$$")
          sentences = sentences[0:len(sentences)-1]
          if len(sentences)==0 or (len(sentences)==1 and sentences[0]==""):
            continue;
          else:
            body = '<d> <p> ' + ' '.join(['<s> ' + " ".join(tokenizer(sentence)) + ' </s>' for sentence in sentences]) + ' </p> </d> '
            body = "article=" + body + "\tabstract=" + title+  "\tfilename=" + filename_key  + "\tpublisher=AFP"
            writer.write(body+"\n"); 



import shutil
import copy
def _extract_we_text(output_file,vocab_file,we_dic):
    vocab = data.Vocab(vocab_file, 1000000)
    vsize = vocab.NumIds()
    m=copy.deepcopy(vocab._word_to_id)
    unknown_ids=[vocab.WordToId(UNKNOWN_TOKEN)]
    output = codecs.open(output_file,"w","utf-8")
    with open(we_dic, "rb") as f:
        for line in f:
           string=line.split(" ")
           word=string[0].strip()
           value = " ".join(x for x in string[1:])
           idx = data.GetWordIds(word,vocab)
           if idx != None and idx!=unknown_ids and word in m:
               del m[word]
               output.write(word+' '+value)
    print "====:",m
    print "---:",len(m)

    f.close()
    output.close()

    #this operation wants to garuantee that words in WE and words in vocab file must be the same
    del m['<s>']
    del m['</s>']
    del m['<d>']
    del m['</d>']
    del m['<p>']
    del m['</p>']
    tt=m.keys()
    
    vocab_new=vocab_file+"_new"
    with open(vocab_file,'r') as f:
      with open (vocab_new,'w') as g:
        for line in f.readlines():
            if all(string not in line for string in tt) :
                 g.write(line)
        if '<UNK>' in m:
          g.write('<UNK> 0\n')
        if  '<PAD>' in m: 
          g.write('<PAD> 0\n')
    shutil.move(vocab_new, vocab_file)
    f.close()
    g.close()



UNKNOWN_TOKEN = '<UNK>'
def _extract_we_binary(output_file,vocab_file,we_dic):
    vocab = data.Vocab(vocab_file, 1000000) 
    vsize = vocab.NumIds()
    output = codecs.open(output_file,"w","utf-8")
    unknown_ids=[vocab.WordToId(UNKNOWN_TOKEN)]
    with open(we_dic, "rb") as f:
        header = f.readline()
        vocab_size, layer1_size = map(int, header.split())
        binary_len = np.dtype('float32').itemsize * layer1_size
        print "layer1_size:",layer1_size
        for line in xrange(vocab_size):
           word = []
           while True:
                ch = f.read(1)
                if ch == ' ':
                      word = ''.join(word)
                      break
                if ch != '\n':
                       word.append(ch)
           idx = data.GetWordIds(word,vocab)
           if idx != None and idx!=unknown_ids and word=="<s>":
              print idx,":",word
              output.write(word+' '+' '.join(map(str,np.fromstring(f.read(binary_len), dtype='float32')))+'\n')
           elif  idx==unknown_ids:
              f.read(binary_len)
           else:
              f.read(binary_len)
    f.close()
    output.close()
 

import numpy as np
from polyglot.mapping import Embedding
def _extract_we_polyglot(output_file,vocab_file,we_dic):
  #vocabulary
  vocabf=codecs.open(vocab_file,"r","utf-8")
  vocab=[]
  vecList=[]
  for line in vocabf:
    vocab.append(line.split(" ")[0])
  #export
  embeddings = Embedding.load(we_dic)
  f = codecs.open(output_file,"w","utf-8") 
  for token in vocab:
  
    token=token.decode("utf-8")
    if token in embeddings:
      vector=embeddings[token].tolist()
      vector.insert(0,token)
      vecList.append(vector)
    else:
      print "====",token
  f.write("\n".join(" ".join(map(str,x)) for x in vecList))
  f.close()
  vocabf.close()


def main(args):
  print "language is:",args
  if args[0]=='FR':
    #train&test
    _text_to_binary("pkg/train_fr/text","pkg/synopsis_fr","result_train_cccs_all_fr.txt","",1,"FR")
    _text_to_binary("pkg/test_fr/text","pkg/synopsis_fr","result_test_cccs_all_fr.txt","",1,"FR")
    _text_to_vocabulary("vocab",["result_train_cccs_all_fr.txt","result_test_cccs_all_fr.txt"],"test_vocab_cccs_all_fr",choose_base_vocab_filename="no")

    #_extract_we_polyglot("output_fr.txt","test_vocab_cccs_all_fr","../polyglot-fr.pkl")#3000+/4435

    _extract_we_text("we_fr.txt","test_vocab_cccs_all_fr","embed_tweets_fr_300M_52D") # 4285/4435

    #_extract_we_binary("output_fr.txt","test_vocab_cccs_all_fr","wac....")#Das gibt nicht genueg daten 3900+/4435

  if args[0]=='IT':
    _text_to_binary("pkg/train_it/text","pkg/synopsis_it","result_train_cccs_all_it.txt","",1,"IT")
    _text_to_binary("pkg/test_it/text","pkg/synopsis_it","result_test_cccs_all_it.txt","",1,"IT")
    print "load italien:::::"
    _text_to_vocabulary("vocab",["result_train_cccs_all_it.txt","result_test_cccs_all_it.txt"],"test_vocab_cccs_all_it",choose_base_vocab_filename="no")
    _extract_we_text("we_it.txt","test_vocab_cccs_all_it","embed_tweets_it_200M_200D")



if __name__ == "__main__":
   main(sys.argv[1:])
   
