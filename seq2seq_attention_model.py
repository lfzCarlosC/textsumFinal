# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Sequence-to-Sequence with attention model for text summarization.
"""
from collections import namedtuple

import numpy as np
import tensorflow as tf
import seq2seq_lib
import data
import codecs
FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string("word2vec", None, "Word2vec file with pre-trained embeddings (default: None)")

HParams = namedtuple('HParams',
                     'mode, min_lr, lr, batch_size, '
                     'enc_layers, enc_timesteps, dec_timesteps, '
                     'min_input_len, num_hidden, emb_dim, max_grad_norm, '
                     'num_softmax_samples, input_dropout, output_dropout')


def _extract_argmax_and_embed(embedding, output_projection=None,
                              update_embedding=True):
  """Get a loop_function that extracts the previous symbol and embeds it.

  Args:
    embedding: embedding tensor for symbols.
    output_projection: None or a pair (W, B). If provided, each fed previous
      output will first be multiplied by W and added B.
    update_embedding: Boolean; if False, the gradients will not propagate
      through the embeddings.

  Returns:
    A loop function.
  """
  def loop_function(prev, _):
    """function that feed previous model output rather than ground truth."""
    if output_projection is not None:
      prev = tf.nn.xw_plus_b(
          prev, output_projection[0], output_projection[1])
    prev_symbol = tf.argmax(prev, 1)
    # Note that gradients will not propagate through the second parameter of
    # embedding_lookup.
    emb_prev = tf.nn.embedding_lookup(embedding, prev_symbol)
    if not update_embedding:
      emb_prev = tf.stop_gradient(emb_prev)
    return emb_prev
  return loop_function


class Seq2SeqAttentionModel(object):
  """Wrapper for Tensorflow model graph for text sum vectors."""

  def __init__(self, hps, vocab, num_gpus=0):
    self._hps = hps
    self._vocab = vocab
    self._num_gpus = num_gpus
    self._cur_gpu = 0

  def run_train_step(self, sess, article_batch, abstract_batch, targets,
                     article_lens, abstract_lens, loss_weights):
    to_return = [self._train_op, self._summaries, self._loss, self.global_step]
    return sess.run(to_return,
                    feed_dict={self._articles: article_batch,
                               self._abstracts: abstract_batch,
                               self._targets: targets,
                               self._article_lens: article_lens,
                               self._abstract_lens: abstract_lens,
                               self._loss_weights: loss_weights})

  def run_eval_step(self, sess, article_batch, abstract_batch, targets,
                    article_lens, abstract_lens, loss_weights):
    to_return = [self._summaries, self._loss, self.global_step]
    return sess.run(to_return,
                    feed_dict={self._articles: article_batch,
                               self._abstracts: abstract_batch,
                               self._targets: targets,
                               self._article_lens: article_lens,
                               self._abstract_lens: abstract_lens,
                               self._loss_weights: loss_weights})

  def run_decode_step(self, sess, article_batch, abstract_batch, targets,
                      article_lens, abstract_lens, loss_weights):
    to_return = [self._outputs, self.global_step]
    return sess.run(to_return,
                    feed_dict={self._articles: article_batch,
                               self._abstracts: abstract_batch,
                               self._targets: targets,
                               self._article_lens: article_lens,
                               self._abstract_lens: abstract_lens,
                               self._loss_weights: loss_weights})

  def _next_device(self):
    """Round robin the gpu device. (Reserve last gpu for expensive op)."""
    if self._num_gpus == 0:
      return ''
    dev = '/gpu:%d' % self._cur_gpu
    if self._num_gpus > 1:
      self._cur_gpu = (self._cur_gpu + 1) % (self._num_gpus-1)
    return dev

  def _get_gpu(self, gpu_id):
    if self._num_gpus <= 0 or gpu_id >= self._num_gpus:
      return ''
    return '/gpu:%d' % gpu_id

  def _add_placeholders(self):
    """Inputs to be fed to the graph."""
    hps = self._hps
    self._articles = tf.placeholder(tf.int32,
                                    [hps.batch_size, hps.enc_timesteps],
                                    name='articles')
    self._abstracts = tf.placeholder(tf.int32,
                                     [hps.batch_size, hps.dec_timesteps],
                                     name='abstracts')
    self._targets = tf.placeholder(tf.int32,
                                   [hps.batch_size, hps.dec_timesteps],
                                   name='targets')
    self._article_lens = tf.placeholder(tf.int32, [hps.batch_size],
                                        name='article_lens')
    self._abstract_lens = tf.placeholder(tf.int32, [hps.batch_size],
                                         name='abstract_lens')
    self._loss_weights = tf.placeholder(tf.float32,
                                        [hps.batch_size, hps.dec_timesteps],
                                        name='loss_weights')

  def _loadWord2Vec(self,embedding,emb_dim):
    sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
    vsize = self._vocab.NumIds()
    sess.run(tf.initialize_all_variables())
    if FLAGS.word2vec:
        # initial matrix with random uniform
        initW = np.random.uniform(-0.25,0.25,(vsize, emb_dim))
        # load any vectors from the word2vec
        print("Load word2vec file {}\n".format(FLAGS.word2vec))
        f= codecs.open(FLAGS.word2vec, "r")
        for line in f:
           str=line.split(" ")
           word=str[0]
           value = " ".join(x for x in str[1:])
           idx = data.GetWordIds(word,self._vocab)
           if idx != None:
              initW[idx] = np.fromstring(value, dtype='float32',sep=' ')

        f.close()

        sess.run(embedding.assign(initW))
        sess.run(embedding)

  def _loadWord2VecGo(self,emb_dim):
    sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
    vsize = self._vocab.NumIds()
    with tf.variable_scope('goEmbedding'), tf.device('/gpu:0'):
      embedding = tf.get_variable(
            'embedding', [vsize, emb_dim], dtype=tf.float32,
         trainable=False,
         initializer=tf.truncated_normal_initializer(stddev=1e-4))
      sess.run(tf.initialize_all_variables())
    if FLAGS.word2vec:
        # initial matrix with random uniform
        initW = np.random.uniform(-0.25,0.25,(vsize, emb_dim))
        # load any vectors from the word2vec
        print("Load word2vec file {}\n".format(FLAGS.word2vec))
        with open(FLAGS.word2vec, "rb") as f:
            header = f.readline()
            vocab_size, layer1_size = map(int, header.split())
            binary_len = np.dtype('float32').itemsize * layer1_size
            for line in xrange(vocab_size):
                word = []
                while True:
                    ch = f.read(1)
                    if ch == ' ':
                        word = ''.join(word)
                        break
                    if ch != '\n':
                        word.append(ch)   
                idx = data.GetWordIds(word,self._vocab)
                if idx != None:
                    initW[idx] = np.fromstring(f.read(binary_len), dtype='float32')  
                else:
                    f.read(binary_len)    
        print "embedding first loaded:",embedding
        print(sess.run(tf.nn.embedding_lookup(embedding, 2)))
        sess.run(embedding.assign(initW))
        print "function loaded:",embedding
        print(sess.run(tf.nn.embedding_lookup(embedding, 2)))
        return sess

  def _add_seq2seq(self):
    hps = self._hps
    vsize = self._vocab.NumIds()
    with tf.variable_scope('seq2seq'):
      encoder_inputs = tf.unpack(tf.transpose(self._articles))
      decoder_inputs = tf.unpack(tf.transpose(self._abstracts))
      targets = tf.unpack(tf.transpose(self._targets))
      loss_weights = tf.unpack(tf.transpose(self._loss_weights))
      article_lens = self._article_lens
      sess= tf.get_default_session()
      print sess
      with tf.variable_scope('Embedding'), tf.device('/gpu:0'):
      # Embedding shared by the input and outputs.
      #embedding = tf.get_variable(
      #      'embedding', [vsize, hps.emb_dim], dtype=tf.float32,
      #   trainable=False,
      #      initializer=tf.truncated_normal_initializer(stddev=1e-4))
        embedding = tf.get_variable(
            'embedding', [vsize, hps.emb_dim], dtype=tf.float32,
             trainable=False,
             initializer=tf.truncated_normal_initializer(stddev=1e-4))
        sess.run(tf.initialize_all_variables())
        if FLAGS.word2vec:
            # initial matrix with random uniform
            initW = np.random.uniform(-0.25,0.25,(vsize,hps.emb_dim ))
            # load any vectors from the word2vec
            print("Load word2vec file {}\n".format(FLAGS.word2vec))
            with open(FLAGS.word2vec, "rb") as f:
              header = f.readline()
              vocab_size, layer1_size = map(int, header.split())
              binary_len = np.dtype('float32').itemsize * layer1_size
              for line in xrange(vocab_size):
                word = []
                while True:
                    ch = f.read(1)
                    if ch == ' ':
                        word = ''.join(word)
                        break
                    if ch != '\n':
                        word.append(ch)
                idx = data.GetWordIds(word,self._vocab)
                if idx != None:
                    initW[idx] = np.fromstring(f.read(binary_len), dtype='float32')
                else:
                    f.read(binary_len)
        sess.run(embedding.assign(initW))
        encoder_inputs=[2,4,6,8]
        emb_encoder_inputs = [tf.nn.embedding_lookup(embedding, x)
                              for x in encoder_inputs]
        print emb_encoder_inputs

  def _add_seq2seq_old(self,sess):
    hps = self._hps
    vsize = self._vocab.NumIds()
    with tf.variable_scope('seq2seq'):
      encoder_inputs = tf.unpack(tf.transpose(self._articles))
      decoder_inputs = tf.unpack(tf.transpose(self._abstracts))
      targets = tf.unpack(tf.transpose(self._targets))
      loss_weights = tf.unpack(tf.transpose(self._loss_weights))
      article_lens = self._article_lens
      with tf.variable_scope('Embedding'), tf.device('/gpu:0'):
#==============================================================================
      # Embedding shared by the input and outputs.
      #embedding = tf.get_variable(
      #      'embedding', [vsize, hps.emb_dim], dtype=tf.float32,
      #   trainable=False,
      #      initializer=tf.truncated_normal_initializer(stddev=1e-4))
      #sess.run(tf.initialize_all_variables())
#==============================================================================
        vsize = self._vocab.NumIds()
        embedding = tf.get_variable(
            'embedding', [vsize, hps.emb_dim], dtype=tf.float32,
             trainable=False,
             initializer=tf.truncated_normal_initializer(stddev=1e-4))
        sess.run(tf.initialize_all_variables())
        if FLAGS.word2vec:
            # initial matrix with random uniform
            initW = np.random.uniform(-0.25,0.25,(vsize,hps.emb_dim ))
            # load any vectors from the word2vec
            print("Load word2vec file {}\n".format(FLAGS.word2vec))
            with open(FLAGS.word2vec, "rb") as f:
              header = f.readline()
              vocab_size, layer1_size = map(int, header.split())
              binary_len = np.dtype('float32').itemsize * layer1_size
              for line in xrange(vocab_size):
                word = []
                while True:
                    ch = f.read(1)
                    if ch == ' ':
                        word = ''.join(word)
                        break
                    if ch != '\n':
                        word.append(ch)
                idx = data.GetWordIds(word,self._vocab)
                if idx != None:
                    initW[idx] = np.fromstring(f.read(binary_len), dtype='float32')
                else:
                    f.read(binary_len)
               
        print "to test ... .. . . embedding first loaded:"
        print(sess.run(tf.nn.embedding_lookup(embedding, 2)))
        sess.run(embedding.assign(initW))
        print "to test ... .. .. . function loaded:"
        print(sess.run(tf.nn.embedding_lookup(embedding, 2)))
#===============================================================================

        # Embedding shared by the input and outputs.
        emb_encoder_inputs = [tf.nn.embedding_lookup(embedding, x)
                              for x in encoder_inputs]
        emb_decoder_inputs = [tf.nn.embedding_lookup(embedding, x)
                              for x in decoder_inputs]
      
      #matrix factorization
     ## s,u,v=tf.svd(emb_encoder_inputs,compute_uv=True)
     ## eigenSum=tf.reduce_sum(s)
     ## eigen=0
     ## threshold=0
     ## i=0;
     ## for i in range(len(s)):
     ##   eigen=s(i)
     ##   if((eigen/eigenSum)>threshold)
     ##     break;
      #rebuild eigenvector with i length
     ## new_eigenMatrix = tf.Variable(tf.zeros([i,i]))
     ## for j in range(i):
     ##   new_eigenMatrix[j,j]=s(j)
      #decrease embedding dim  [vsize,64]
    ##emb_encoder_inputs=tf.batch_matmul(u[,:j],new_eigenMatrix)
     # new_embedding=u*s
     #or decrease word length [N,128]
     # new_embedding=v*s

      for layer_i in xrange(hps.enc_layers):
        with tf.variable_scope('encoder%d'%layer_i), tf.device(
            self._next_device()):
          #bidirectional rnn cell
          cell_fw = tf.nn.rnn_cell.LSTMCell(
              hps.num_hidden,
              initializer=tf.random_uniform_initializer(-0.1, 0.1, seed=123),
              state_is_tuple=False)
          cell_bw = tf.nn.rnn_cell.LSTMCell(
              hps.num_hidden,
              initializer=tf.random_uniform_initializer(-0.1, 0.1, seed=113),
              state_is_tuple=False)
          cell_fw = tf.nn.rnn_cell.DropoutWrapper(cell_fw, input_keep_prob=hps.input_dropout, output_keep_prob=hps.output_dropout)
          cell_bw = tf.nn.rnn_cell.DropoutWrapper(cell_bw, input_keep_prob=hps.input_dropout, output_keep_prob=hps.output_dropout)
          (emb_encoder_inputs, fw_state, _) = tf.nn.bidirectional_rnn(
              cell_fw, cell_bw, emb_encoder_inputs, dtype=tf.float32,
              sequence_length=article_lens)
      encoder_outputs = emb_encoder_inputs
      print "fw_state:",fw_state
      with tf.variable_scope('output_projection'):
        w = tf.get_variable(
            'w', [hps.num_hidden, vsize], dtype=tf.float32,
            initializer=tf.truncated_normal_initializer(stddev=1e-4))
        w_t = tf.transpose(w)
        v = tf.get_variable(
            'v', [vsize], dtype=tf.float32,
            initializer=tf.truncated_normal_initializer(stddev=1e-4))

      with tf.variable_scope('decoder'), tf.device(self._next_device()):
        # When decoding, use model output from the previous step
        # for the next step.
        loop_function = None
        if hps.mode == 'decode':
          loop_function = _extract_argmax_and_embed(
              embedding, (w, v), update_embedding=False)
        cell = tf.nn.rnn_cell.LSTMCell(
            hps.num_hidden,
            initializer=tf.random_uniform_initializer(-0.1, 0.1, seed=113),
            state_is_tuple=False)
        cell=tf.nn.rnn_cell.DropoutWrapper(cell, input_keep_prob=hps.input_dropout, output_keep_prob=hps.output_dropout)
        encoder_outputs = [tf.reshape(x, [hps.batch_size, 1, 2*hps.num_hidden])
                           for x in encoder_outputs]
        self._enc_top_states = tf.concat(1, encoder_outputs)
        self._dec_in_state = fw_state
        # During decoding, follow up _dec_in_state are fed from beam_search.
        # dec_out_state are stored by beam_search for next step feeding.
        initial_state_attention = (hps.mode == 'decode')
        decoder_outputs, self._dec_out_state = tf.nn.seq2seq.attention_decoder(
            emb_decoder_inputs, self._dec_in_state, self._enc_top_states,
            cell, num_heads=1, loop_function=loop_function,
            initial_state_attention=initial_state_attention)
      
    
        print "====emb_decoder_inputs:",emb_decoder_inputs
        print "====self._dec_in_state:",self._dec_in_state
        print "====self._enc_top_states:",self._enc_top_states
        print "====decoder_outputs:",decoder_outputs
        print "====self._dec_out_state:",self._dec_out_state
      with tf.variable_scope('output'), tf.device(self._next_device()):
        model_outputs = []
        for i in xrange(len(decoder_outputs)):
          if i > 0:
            tf.get_variable_scope().reuse_variables()
          model_outputs.append(
              tf.nn.xw_plus_b(decoder_outputs[i], w, v))

      if hps.mode == 'decode':
        with tf.variable_scope('decode_output'), tf.device('/gpu:0'):
          best_outputs = [tf.argmax(x, 1) for x in model_outputs]
          tf.logging.info('best_outputs%s', best_outputs[0].get_shape())
          self._outputs = tf.concat(
              1, [tf.reshape(x, [hps.batch_size, 1]) for x in best_outputs])

          self._topk_log_probs, self._topk_ids = tf.nn.top_k(
              tf.log(tf.nn.softmax(model_outputs[-1])), hps.batch_size*2)

      with tf.variable_scope('loss'), tf.device(self._next_device()):
        def sampled_loss_func(inputs, labels):
          with tf.device('/gpu:0'):  # Try gpu.
            labels = tf.reshape(labels, [-1, 1])
            tf.logging.info('num_sampled%s',hps.num_softmax_samples)
            return tf.nn.sampled_softmax_loss(w_t, v, inputs, labels,
                                              hps.num_softmax_samples, vsize)

        if hps.num_softmax_samples != 0 and hps.mode == 'train':
          self._loss = seq2seq_lib.sampled_sequence_loss(
              decoder_outputs, targets, loss_weights, sampled_loss_func)
        else:
          self._loss = tf.nn.seq2seq.sequence_loss(
              model_outputs, targets, loss_weights)
        tf.scalar_summary('loss', tf.minimum(12.0, self._loss))

  def _add_train_op(self):
    """Sets self._train_op, op to run for training."""
    hps = self._hps

    self._lr_rate = tf.maximum(
        hps.min_lr,  # min_lr_rate.
        tf.train.exponential_decay(hps.lr, self.global_step, 30000, 0.98))

    tvars = tf.trainable_variables()
    with tf.device(self._get_gpu(self._num_gpus-1)):
      grads, global_norm = tf.clip_by_global_norm(
          tf.gradients(self._loss, tvars), hps.max_grad_norm)
    tf.scalar_summary('global_norm', global_norm)
    optimizer = tf.train.GradientDescentOptimizer(self._lr_rate)
    tf.scalar_summary('learning rate', self._lr_rate)
    self._train_op = optimizer.apply_gradients(
        zip(grads, tvars), global_step=self.global_step, name='train_step')

  def encode_top_state(self, sess, enc_inputs, enc_len):
    """Return the top states from encoder for decoder.

    Args:
      sess: tensorflow session.
      enc_inputs: encoder inputs of shape [batch_size, enc_timesteps].
      enc_len: encoder input length of shape [batch_size]
    Returns:
      enc_top_states: The top level encoder states.
      dec_in_state: The decoder layer initial state.
    """
    results = sess.run([self._enc_top_states, self._dec_in_state],
                       feed_dict={self._articles: enc_inputs,
                                  self._article_lens: enc_len})
    return results[0], results[1][0]

  def decode_topk(self, sess, latest_tokens, enc_top_states, dec_init_states):
    """Return the topK results and new decoder states."""
    feed = {
        self._enc_top_states: enc_top_states,
        self._dec_in_state:
            np.squeeze(np.array(dec_init_states)),
        self._abstracts:
            np.transpose(np.array([latest_tokens])),
        self._abstract_lens: np.ones([len(dec_init_states)], np.int32)}

    results = sess.run(
        [self._topk_ids, self._topk_log_probs, self._dec_out_state],
        feed_dict=feed)

    ids, probs, states = results[0], results[1], results[2]
    new_states = [s for s in states]
    return ids, probs, new_states

  def build_graph(self):
    self._add_placeholders()
    self._add_seq2seq()

  def build_grapha_old(self):
    self._add_placeholders()
    self._add_seq2seq()
    self.global_step = tf.Variable(0, name='global_step', trainable=False)
    if self._hps.mode == 'train':
      self._add_train_op()
    self._summaries = tf.merge_all_summaries()
