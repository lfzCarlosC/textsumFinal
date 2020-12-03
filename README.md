# textsumThesis
Text summrization project copied from https://github.com/tensorflow/models/tree/master/textsum

trained Model: https://clarin06.ims.uni-stuttgart.de/lfz_carlos/textsumFinal


to run the model, plese "#" for the  line open train mode and decode mode and use the command:
sh run_E_FR.sh

What is each file's role:
  
dataset_preprocessing_duc.py  - for data pre-processing   
seq2seq_attention_cccs_epoch_1200_test.py   -  setting trianing parameter   
seq2seq_attention_model_test.py    - strucutre of the model    
seq2seq_attention_decode.py  - decoding logic    
beam_search.py  -  how the topk are chosen and generate best sequence    
batch_reader.py - input data access    
seq2seq_lib.py  - libraries such as loss definition    

This script is for duc dataset.    
There are also other task in this folder:    

Data pre-processing:    
for cccs task: python dataset_preprocessing_cccs_ext.py (data augmentation due to multi abstract for an article)   
for duc task: python dataset_preprocessing_duc.py     

Then change --data_path  --test_data_path to the specific task dataset
How to generate dataset the model can access is written in the run.sh

following parameters can be set in run.sh:

--data_path=result_train_duc.bin     
--test_data_path=result_test_duc.bin      
--vocab_path=test_vocab_duc      
--log_root=textsum/log_root_duc_noneWE         # this folder means the folder in run-time. So please create folder textsum/log_root_duc_noneWE under this README.md file    
--train_dir=textsum/log_root_duc_noneWE/train     # no need to create train, it will be created automatically      
--EPOCHS=1000      
--enc_layers=4      
--enc_timesteps=1100      
--dec_timesteps=100     
--batch_size=25    

for pre-trained word embedding setting, please add parameter:     
--word2vec=./GoogleNews-vectors-negative300.bin and download GoogleNews-vectors-negative300.bin from      
https://github.com/mmihaltz/word2vec-GoogleNews-vectors/blob/master/GoogleNews-vectors-negative300.bin.gz     
or    
access /tmp/textsum_new in kiwi    


following parameters can be set in seq2seq_attention_cccs_epoch_1200_test.py(training parameter setting):     
mode=FLAGS.mode,  # train, eval, decode     
min_lr=0.01,  # min learning rate.    
lr=0.15,  # learning rate    
batch_size=batch_size,    
enc_layers=FLAGS.enc_layers,     
enc_timesteps=FLAGS.enc_timesteps,     
dec_timesteps=FLAGS.dec_timesteps,     
num_hidden=128,  # for rnn cell     
emb_dim=300,  # If 0, don't use embedding     
max_grad_norm=2,     
num_softmax_samples=4096,     
input_dropout=0.5,  # ratio of dropout     
output_dropout=0.5  # ratio of dropout


the role of each are illustrated in thesis template    

The entire copy of runnable code are made in    
 /tmp/textsum_new in kiwi machine.    




Current baseline:

System EN FR IT   
Attn-LSTM(non pre-trained WE) 0.009 not yet not yet    
Attn-LSTM(pre-trained WE) 0.063 not yet not yet    
NTNU:1 0.023 0.035 0.013    
NTNU:2 0.031 0.027 0.015    
NTNU:3 0.024 0.034 0.012    
Baseline-MMR 0.029 0.045 0.020    
Baseline-L 0.023 0.040 0.015    
Baseline-LB 0.025 0.046 0.027    



Annotator EN-man EN-auto    
Attn-LSTM(non pre-trained WE) 0.011 0.009     
Attn-LSTM(pre-trained WE) 0.048 0.076      
NTNU:1 0.018 0.023      
NTNU:2 0.019 0.031      
NTNU:3 0.015 0.024    
Baseline-MMR 0.024 0.033     
Baseline-L 0.015 0.030     
Baseline-LB 0.023 0.027    




