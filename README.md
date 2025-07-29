# UPR_LDA

Data acquisition and LDA topic modeling of civil society submissions to the UPR

## General

This project contains code to downloads relevant pdf documetns from the UPR to be used as input to train an LDA Topic Model and gain important insights.

The general process is as follows:

- search for and download all english PDF reports of the UPR third cycle under civil society.
- transform pdf to textual data using google tesseract OCR.
- tag documents by different apsects such as OECD status, democracy status and so on.
- filter documents by search terms and other tags.
- run preprocessing including, lemmatization, bigrams, stop words and more.
- run LDA topic model training on a corpus created by the filtered and preprocessed set of documents using gensim
- present a visual representation of the trained model using LDAVIS

## Install

This project uses conda to manage dependencies required by the code.
Find Installation instructions [here](https://www.anaconda.com/docs/getting-started/miniconda/install)

With conda properly installed cd to the upr_lda directory and run create the conda environment to run the upr_lda code.
`conda env create`

## Develop (macos)

- `brew install miniconda --cask`
- `conda init zsh`
- `conda create -n upr_lda python=3.12`
- `conda activate upr_lda`
- `conda env export > environment.yml` (run everytime conda or pip packages are updated in an activated env)
- run tests with `pytest -vvv` from project root
