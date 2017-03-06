import codecs
import random

lst=range(1,499)
read = codecs.open("result_train_cccs_all_it.txt","r")
train=codecs.open("result_train_cccs_it.txt","w")
out = codecs.open("result_test_cccs_it.txt","w")
slic=random.sample(lst,100)
j=0
for i in read:
    j=j+1
    if j in slic:
        out.write(i)
    else:
        train.write(i)

read.close()
out.close()
train.close()
