# UPR_LDA

Data acquisition and LDA topic modeling of civil society submissions to the UPR

## installation

- install conda at least 3.5
- create new conda env
  `conda env create -f environment.yml`  

## development

- save conda env using `conda env export --no-build | grep -v "^prefix: " > environment.yml`

## use in vscode

- select python phd
  `Command + Shift + P -> Python: Select Interpreter -> choose conda phd`
- to configure open .vscode/launch.json
- to run press the triangle and bug button

### Index Files

create the initial csv indexing all the files by country - overwrites  
find csv file in output/tag-country-pdfs/tags.csv

### Text Extract

reads the pdfs and extracts text to txt file

### Text Search Term

search a term in the files and add tag to csv  
open launch.json - `"args": ["text", "search", "Human Rights Defenders"]`
change the term to whatever you need and run Search Term

## use in Terminal

- activate phd env
  `conda activate phd`
- cd to UN_Countries_dir
  `cd UN_Countries_dir`

## download

use script download-country-pdfs.py
  `python download-country-pdfs.py`

### tagging

use script tag-country-pdfs.py with the needed command  
`python tag-country-pdfs.py`  

for help run  
`python tag-country-pdfs.py -h`  
*when using index command tags-file might be overwritten*
