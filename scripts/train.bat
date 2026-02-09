@echo off
setlocal

:: Thiet lap thu muc lam viec
set work_dir=.
cd %work_dir%

set "dataset=goodreads"
python ./utils/train_sasrec.py --data_dir ./data/%dataset% --epochs 100

set "dataset=amazon"
python ./utils/train_sasrec.py --data_dir ./data/%dataset% --epochs 100

set "dataset=yelp"
python ./utils/train_sasrec.py --data_dir ./data/%dataset% --epochs 100


