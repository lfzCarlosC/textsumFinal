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

"""Trains a seq2seq model.

WORK IN PROGRESS.

Implement "Abstractive Text Summarization using Sequence-to-sequence RNNS and
Beyond."

"""
import sys
import time
import codecs
import tensorflow as tf
import batch_reader
import data
import seq2seq_attention_decode
import seq2seq_attention_model_test as seq2seq_attention_model

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string('test_data_path',
                           '', 'Path expression to tf.Example.')
tf.app.flags.DEFINE_string('data_path',
                           '', 'Path expression to tf.Example.')
tf.app.flags.DEFINE_string('vocab_path',
                           '', 'Path expression to text vocabulary file.')
tf.app.flags.DEFINE_string('article_key', 'article',
                           'tf.Example feature key for article.')
tf.app.flags.DEFINE_string('abstract_key', 'headline',
                           'tf.Example feature key for abstract.')
tf.app.flags.DEFINE_string('filename_key', 'filename',
                           'tf.Example feature key for filename.')
tf.app.flags.DEFINE_string('log_root', '', 'Directory for model root.')
tf.app.flags.DEFINE_string('train_dir', '', 'Directory for train.')
tf.app.flags.DEFINE_string('eval_dir', '', 'Directory for eval.')
tf.app.flags.DEFINE_string('decode_dir', '', 'Directory for decode summaries.')
tf.app.flags.DEFINE_string('mode', 'train', 'train/eval/decode mode')
tf.app.flags.DEFINE_integer('max_run_steps', 5000,
                            'Maximum number of run steps.')
tf.app.flags.DEFINE_integer('max_article_sentences', 100, #2
                            'Max number of first sentences to use from the '
                            'article')
tf.app.flags.DEFINE_integer('max_abstract_sentences', 100,
                            'Max number of first sentences to use from the '
                            'abstract')
tf.app.flags.DEFINE_integer('beam_size', 0,
                            'beam size for beam search decoding.')
tf.app.flags.DEFINE_integer('eval_interval_secs', 60, 'How often to run eval.')
tf.app.flags.DEFINE_integer('checkpoint_secs', 60, 'How often to checkpoint.')
tf.app.flags.DEFINE_bool('use_bucketing', False,
                         'Whether bucket articles of similar length.')
tf.app.flags.DEFINE_bool('truncate_input', False,
                         'Truncate inputs that are too long. If False, '
                         'examples that are too long are discarded.')
tf.app.flags.DEFINE_integer('num_gpus', 0, 'Number of gpus used.')
tf.app.flags.DEFINE_integer('random_seed', 111, 'A seed value for randomness.')
tf.app.flags.DEFINE_integer('EPOCHS', 0, 'number of epochs')
tf.app.flags.DEFINE_integer('EARLY_STOP_PATIENCE',300, 'early stopping')
tf.app.flags.DEFINE_integer('enc_layers','','encoder layers')
tf.app.flags.DEFINE_integer('enc_timesteps','','encoder sequence')
tf.app.flags.DEFINE_integer('dec_timesteps','','decoder sequence')
tf.app.flags.DEFINE_integer('batch_size','20','batch_size')
tf.app.flags.DEFINE_integer('emb_dim','128','embedding dimension')


def _RunningAvgLoss(loss, running_avg_loss, summary_writer, step, decay=0.999):
  """Calculate the running average of losses."""
  if running_avg_loss == 0:
    running_avg_loss = loss
  else:
    running_avg_loss = running_avg_loss * decay + (1 - decay) * loss
  running_avg_loss = min(running_avg_loss, 12)
  loss_sum = tf.Summary()
  loss_sum.value.add(tag='running_avg_loss', simple_value=running_avg_loss)
  summary_writer.add_summary(loss_sum, step)
  sys.stdout.write('running_avg_loss: %f\n' % running_avg_loss)
  return running_avg_loss


def _Train_test(model, data_batcher,test_batcher):
  """Runs model training."""
  with tf.device('/gpu:0'):
    best_running_avg_loss=1000000
    #EPOCHS
    sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
  
    for i in xrange(1):
      #load new data
      print "empty, reload to queue"
      data_batcher._FillBucketInputQueueShuffle();
      running_avg_loss = 0
      counter=0
      train_running_loss=0
      while data_batcher._bucket_input_queue.qsize()<>0:
         print "batch learn:",counter
         counter=counter+1;
         (article_batch, abstract_batch, targets, article_lens, abstract_lens,
          loss_weights, _, _, _) = data_batcher.NextBatch()
      test_batcher._FillBucketInputQueueShuffle();
      while test_batcher._bucket_input_queue.qsize()<>0:
          (article_batch, abstract_batch, targets, article_lens, abstract_lens,
           loss_weights, _, _, _) = test_batcher.NextBatch()
    return running_avg_loss


def _Train(model, data_batcher,test_batcher):
  """Runs model training."""
  with tf.device('/gpu:0'):
    initW=model._loadWord2Vec()
    model.build_graph()
    saver = tf.train.Saver(max_to_keep=30)
    # Train dir is different from log_root to avoid summary directory
    # conflict with Supervisor.
    summary_writer = tf.train.SummaryWriter(FLAGS.train_dir)
    sv = tf.train.Supervisor(logdir=FLAGS.log_root,
                             is_chief=True,
                             saver=saver,
                             summary_op=None,
                             save_summaries_secs=60,
                             save_model_secs=0,
                             global_step=model.global_step)
    sess = sv.prepare_or_wait_for_session(config=tf.ConfigProto(
        allow_soft_placement=True))
 
    running_avg_loss = 0
    train_running_loss=0
    
    f=codecs.open(FLAGS.train_dir+"/result.log","w")
    best_running_avg_loss=1000000
    #EPOCHS
    for i in xrange(FLAGS.EPOCHS):
      #load new data
      print "empty, reload to queue"
      data_batcher._FillBucketInputQueueShuffle();
      running_avg_loss = 0
      counter=0
      train_running_loss=0
      while not sv.should_stop() and data_batcher._bucket_input_queue.qsize()<>0:
         print "batch learn:",counter
         f.write("batch learn:{0}".format(counter)+"\n")
         counter=counter+1;
         (article_batch, abstract_batch, targets, article_lens, abstract_lens,
          loss_weights, _, _, _) = data_batcher.NextBatch()
         (_, summaries, loss, train_step) = model.run_train_step(
            sess, article_batch, abstract_batch, targets, article_lens,
           abstract_lens, loss_weights,initW)
         train_running_loss = train_running_loss + loss

      #apply model to validation set
      running_avg_loss=validation(sess,model,test_batcher,initW)
      
      if i%10 ==0 and i/10>0:
        save_model(saver,sess, FLAGS.log_root+'/model.ckpt', i )
      #running_avg_loss = running_avg_loss / counter 
      print 'epoch {0} training loss:{1}'.format(i,train_running_loss) 
      print 'epoch {0} test loss:{1}'.format(i,running_avg_loss)
      f.write('epoch {0} training loss:{1}'.format(i,train_running_loss)+"\n")
      f.write('epoch {0} test loss:{1}'.format(i,running_avg_loss)+"\n")


      if running_avg_loss < best_running_avg_loss:
        best_running_avg_loss = running_avg_loss
        current_epoch=i
        print "best one:",current_epoch
        f.write("best one:{0}".format(current_epoch)+"\n")
        #  save_model(saver,sess,"textsum/log_root_all_1/BESTMODEL")
      elif (i-current_epoch) >= FLAGS.EARLY_STOP_PATIENCE:
        print 'stop patience,best epoch:',current_epoch
        f.write('stop patience,best epoch:{0}'.format(current_epoch)+"\n")
        break;
         
      if i % 50 == 0:
        print "step ",i," finished....."
        summary_writer.flush()
    sv.Stop()
    f.close()
    return running_avg_loss

def validation(sess,model,test_batcher,initW,vocab=None):
  """Runs model eval."""
  running_avg_loss = 0
  step = 0
  test_batcher._FillBucketInputQueueShuffle();
  while test_batcher._bucket_input_queue.qsize()<>0:
    (article_batch, abstract_batch, targets, article_lens, abstract_lens,
     loss_weights, _, _, _) = test_batcher.NextBatch()
    (summaries, loss, train_step) = model.run_eval_step(
        sess, article_batch, abstract_batch, targets, article_lens,
        abstract_lens, loss_weights,initW)
    running_avg_loss = running_avg_loss + loss
  print "validation running_avg_loss:",running_avg_loss
  return running_avg_loss


def save_model(saver,sess,save_path, i):
    path=saver.save(sess,save_path,global_step=i)
    print "model saved in  :{0}".format(path)

def _Eval(model, data_batcher, vocab=None):
  """Runs model eval."""
  model.build_graph()
  saver = tf.train.Saver()
  summary_writer = tf.train.SummaryWriter(FLAGS.eval_dir)
  sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
  running_avg_loss = 0
  step = 0
  while True:
    time.sleep(FLAGS.eval_interval_secs)
    try:
      ckpt_state = tf.train.get_checkpoint_state(FLAGS.log_root)
    except tf.errors.OutOfRangeError as e:
      tf.logging.error('Cannot restore checkpoint: %s', e)
      continue

    if not (ckpt_state and ckpt_state.model_checkpoint_path):
      tf.logging.info('No model to eval yet at %s', FLAGS.train_dir)
      continue

    tf.logging.info('Loading checkpoint %s', ckpt_state.model_checkpoint_path)
    saver.restore(sess, ckpt_state.model_checkpoint_path)

    (article_batch, abstract_batch, targets, article_lens, abstract_lens,
     loss_weights, _, _, _) = data_batcher.NextBatch()
    (summaries, loss, train_step) = model.run_eval_step(
        sess, article_batch, abstract_batch, targets, article_lens,
        abstract_lens, loss_weights)
    tf.logging.info(
        'article:  %s',
        ' '.join(data.Ids2Words(article_batch[0][:].tolist(), vocab)))
    tf.logging.info(
        'abstract: %s',
        ' '.join(data.Ids2Words(abstract_batch[0][:].tolist(), vocab)))

    summary_writer.add_summary(summaries, train_step)
    running_avg_loss = _RunningAvgLoss(
        running_avg_loss, loss, summary_writer, train_step)
    if step % 100 == 0:
      summary_writer.flush()


def main(unused_argv):
  vocab = data.Vocab(FLAGS.vocab_path, 1000000)
  # Check for presence of required special tokens.
  assert vocab.WordToId(data.PAD_TOKEN) > 0
  assert vocab.WordToId(data.UNKNOWN_TOKEN) >= 0
  assert vocab.WordToId(data.SENTENCE_START) >= 0
  assert vocab.WordToId(data.SENTENCE_END) >= 0

  batch_size = FLAGS.batch_size
  if FLAGS.mode == 'decode':
    batch_size = FLAGS.beam_size

  hps = seq2seq_attention_model.HParams(
      mode=FLAGS.mode,  # train, eval, decode
      min_lr=0.01,  # min learning rate.
      lr=0.15,  # learning rate
      batch_size=batch_size,
      enc_layers=FLAGS.enc_layers,
      enc_timesteps=FLAGS.enc_timesteps,
      dec_timesteps=FLAGS.dec_timesteps,
      min_input_len=2,  # discard articles/summaries < than this
      num_hidden=64,  # for rnn cell
      emb_dim=FLAGS.emb_dim,  # If 0, don't use embedding
      max_grad_norm=2,
      num_softmax_samples=4096,
      input_dropout=0.5,
      output_dropout=0.5)  # If 0, no sampled softmax.

  batcher = batch_reader.Batcher(
      FLAGS.data_path, vocab, hps, FLAGS.article_key,
      FLAGS.abstract_key, FLAGS.filename_key , FLAGS.max_article_sentences,
      FLAGS.max_abstract_sentences, bucketing=FLAGS.use_bucketing,
      truncate_input=FLAGS.truncate_input, mode="epoch")
  tf.set_random_seed(FLAGS.random_seed)

  if hps.mode == 'train':
    test_batcher = batch_reader.Batcher(
      FLAGS.test_data_path, vocab, hps, FLAGS.article_key,
      FLAGS.abstract_key, FLAGS.filename_key, FLAGS.max_article_sentences,
      FLAGS.max_abstract_sentences, bucketing=FLAGS.use_bucketing,
      truncate_input=FLAGS.truncate_input, mode="epoch")
   
    model = seq2seq_attention_model.Seq2SeqAttentionModel(
        hps, vocab, num_gpus=FLAGS.num_gpus)
    _Train(model, batcher,test_batcher)
  elif hps.mode == 'eval':  

    model = seq2seq_attention_model.Seq2SeqAttentionModel(
        hps, vocab, num_gpus=FLAGS.num_gpus)
    _Eval(model, batcher, vocab=vocab)
  elif hps.mode == 'decode':
    decode_mdl_hps = hps
    # Only need to restore the 1st step and reuse it since
    # we keep and feed in state for each step's output.
    decode_mdl_hps = hps._replace(dec_timesteps=1)
    model = seq2seq_attention_model.Seq2SeqAttentionModel(
        decode_mdl_hps, vocab, num_gpus=FLAGS.num_gpus)
    print "read to create BSDecoder"
    decoder = seq2seq_attention_decode.BSDecoder(model, batcher, hps, vocab)
    decoder.DecodeLoop()
  

if __name__ == '__main__':
  tf.app.run()
