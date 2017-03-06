
mkdir backup
cp -r *.py ./backup/
cp -r *.txt ./backup/
cp -r *.sh ./backup/

zip -r backup.zip ./backup/
mv backup.zip ~/models/textsum
rm -rf backup
