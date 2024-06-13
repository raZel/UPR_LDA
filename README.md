# UPR_LDA

Data acquisition and LDA topic modeling of civil society submissions to the UPR

This project has 2 main scripts written in Python.

* `download-country-pdfs.py` crawls the [UPR documentations](https://www.ohchr.org/en/hr-bodies/upr/documentation) website, filters and downloads all english submissions of the third cycle Civil Society submissions.
* `process-country-pdfs.py` is the main tool for analyzing the data recovered including text conversion, model training, tag extraction per document and so on.

## installation

* install conda minimum version 23.5.0  
[miniconda](https://docs.anaconda.com/free/miniconda/miniconda-install/)
* create a new conda env from env fileby running the follwoing command from the repo root dir  
  `conda env create -f environment.yml`  
  this will create a new `upr_lda` conda environment and install the required dependencies  

## usage

before using any of the scripts, conda env must be activated by calling
  `conda activate upr_lda`

### downloading the relevant pdf files to serve as data

* call `python download-country-pdfs.py` to run the script to download the pdf countries.  
  results are saved to `UN_Countries_Scripts/output/download-country-pdfs` dir

### analyzing the data by processing it with defferent commands

## development

save conda env using  
`conda env export --no-build | grep -v "^prefix: " > environment.yml`

## use in vscode

* select python phd
  `Command + Shift + P -> Python: Select Interpreter -> choose conda phd`
* to configure open .vscode/launch.json
* to run press the triangle and bug button

### Index Files

create the initial csv indexing all the files by country - overwrites  
find csv file in output/prcoess-country-pdfs/tags.csv

### Text Extract

reads the pdfs and extracts text to txt file

### Text Search Term

search a term in the files and add tag to csv  
open launch.json - `"args": ["text", "search", "Human Rights Defenders"]`
change the term to whatever you need and run Search Term

## use in Terminal

* activate phd env
  `conda activate phd`
* cd to UN_Countries_dir
  `cd UN_Countries_dir`

## download

use script download-country-pdfs.py
  `python download-country-pdfs.py`

### tagging

use script process-country-pdfs.py with the needed command  
`python process-country-pdfs.py`  

for help run  
`python process-country-pdfs.py -h`  
*when using index command tags-file might be overwritten*
