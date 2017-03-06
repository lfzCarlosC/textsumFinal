export CUDA_VISIBLE_DEVICES=1
mkdir textsum/log_root_cccs_WE_it
python dataset_preprocessing_cccs_ext.py IT
python randomSelection_it.py
head -n 2 result_test_cccs_it.txt  >> result_train_cccs_it.txt 
python data_convert_example.py --command text_to_binary --in_file result_train_cccs_it.txt --out_file result_train_cccs_it.bin
python data_convert_example.py --command text_to_binary --in_file result_test_cccs_it.txt --out_file   result_test_cccs_it.bin


python seq2seq_attention_cccs_epoch_1200_test.py  --mode=train   --article_key=article   --abstract_key=abstract --emb_dim=200 --data_path=result_train_cccs_it.bin --test_data_path=result_test_cccs_it.bin  --vocab_path=test_vocab_cccs_all_it  --log_root=textsum/log_root_cccs_WE_it --train_dir=textsum/log_root_cccs_WE_it/train --EPOCHS=1000 --enc_layers=4 --enc_timesteps=400  --dec_timesteps=50 --batch_size=25 --word2vec=./we_it.txt



#decoding
#python data_convert_example.py --command text_to_binary --in_file result_test_cccs_all_it.txt --out_file   result_test_cccs_all_it.bin

#python seq2seq_attention_cccs_epoch_1200_test.py  --mode=decode --article_key=article --abstract_key=abstract --emb_dim=200 --data_path=result_test_cccs_all_it.bin --vocab_path=test_vocab_cccs_all_it  --log_root=textsum/log_root_cccs_WE_it  --decode_dir=textsum/log_root_cccs_WE_it/decode  --beam_size=25 --enc_layers=4 --enc_timesteps=400  --dec_timesteps=50 --word2vec=./we_it.txt
