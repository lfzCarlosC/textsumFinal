export CUDA_VISIBLE_DEVICES=2
mkdir textsum/log_root_cccs_WE_fr
python dataset_preprocessing_cccs_ext.py FR
python randomSelection_fr.py
python data_convert_example.py --command text_to_binary --in_file result_train_cccs_fr.txt --out_file result_train_cccs_fr.bin
python data_convert_example.py --command text_to_binary --in_file result_test_cccs_fr.txt --out_file   result_test_cccs_fr.bin

python seq2seq_attention_cccs_epoch_1200_test.py  --mode=train   --article_key=article   --abstract_key=abstract --emb_dim=52 --data_path=result_train_cccs_fr.bin --test_data_path=result_test_cccs_fr.bin  --vocab_path=test_vocab_cccs_all_fr  --log_root=textsum/log_root_cccs_WE_fr --train_dir=textsum/log_root_cccs_WE_fr/train --EPOCHS=1000 --enc_layers=6 --enc_timesteps=500  --dec_timesteps=50 --batch_size=23 --word2vec=./we_fr.txt


#decoding
#python data_convert_example.py --command text_to_binary --in_file result_test_cccs_all_fr.txt --out_file   result_test_cccs_all_fr.bin
#python seq2seq_attention_cccs_epoch_1200_test.py  --mode=decode --article_key=article --abstract_key=abstract --emb_dim=52 --data_path=result_test_cccs_all_fr.bin --vocab_path=test_vocab_cccs_all_fr  --log_root=textsum/log_root_cccs_WE_fr  --decode_dir=textsum/log_root_cccs_WE_fr/decode  --beam_size=25 --enc_layers=6 --enc_timesteps=500  --dec_timesteps=50 --word2vec=./we_fr.txt
