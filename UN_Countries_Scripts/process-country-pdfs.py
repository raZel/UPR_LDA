# this script is responsible for creating and maintaining the tagging for each document
# we maintain a csv file (table) and we append tags as we need by using this script
# General schema of the table:
# path, name, country, search(Human Rights Defenders),more tags

import csv
import argparse
import logging
import os
import re
import shutil
import sys
import datetime
import time
import webbrowser
from pdf2image import convert_from_path
import pytesseract
from multiprocessing.pool import Pool
import nltk, gensim, spacy
from gensim.parsing.preprocessing import STOPWORDS as gensim_stopwords
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis
import pyLDAvis.urls
import numpy as np
import pathlib
from gensim.models.coherencemodel import CoherenceModel
script_name = os.path.basename(__file__)[:len(os.path.basename(__file__))-3]
root_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = f'{root_dir}/output/{script_name}'
logger = None
def set_logger():
	global logger
	if logger == None:
		logging.getLogger().setLevel(logging.DEBUG)
		logger = logging.getLogger(script_name)
		logger.setLevel(logging.DEBUG)
		stdout_handler = logging.StreamHandler(sys.stdout)
		stdout_handler.setLevel(logging.DEBUG)
		logs_dir = f'{output_dir}/logs'
		if not os.path.exists(logs_dir):
			os.mkdir(logs_dir)
		file_handler = logging.FileHandler(f'{logs_dir}/{script_name}-{datetime.datetime.now().isoformat()}-run.log')
		file_handler.setLevel(logging.DEBUG)
		logger.addHandler(file_handler)
		logger.addHandler(stdout_handler)
	return logger

#constants
model_type_lda = 'lda'
models_dir = f'{output_dir}/models'
nltk_data_dir = f'{models_dir}/nltk_data'
trained_lda_dir = f'{models_dir}/trained_lda'
local_d3_path = pyLDAvis.urls.D3_LOCAL
local_ldavis_path = pyLDAvis.urls.LDAVIS_LOCAL
local_ldavis_css_path = pyLDAvis.urls.LDAVIS_CSS_LOCAL

# headers
header_file_name = 'name'
header_file_path = 'path'
header_txt_path = 'txt_path'
header_preprocessed_txt_path = 'preprocessed_txt_path'
header_country = 'country'
header_region = 'region'
header_oecd = 'oecd'
header_income = 'income'
header_democracy_index = 'democracy_index'
header_search_prefix = 'search'
header_topic_prefix = 'topic'
header_topic_prevalence_prefix = 'topic_prevalence'

def search_term_header(term):
		return f'{header_search_prefix}({term})'

def topic_header(topic):
		return f'{header_topic_prefix}({topic})'

def topic_prevalence_header(topic):
		return f'{header_topic_prevalence_prefix}({topic})'

# use regex to check if header is topic header
def is_topic_header(header):
		return re.match(f'{header_topic_prefix}\(.*\)', header) != None

# create
def create_csv(path: str):
	with open(path, 'w') as f:
		log.info(f'creating file {path}')

def read_csv(path: str) -> list[dict]:
	if not os.path.exists(path):
		create_csv(path)
	with open(path, 'r') as f:
		log.info(f'reading file {path}')
		reader = csv.DictReader(f)
		return [row for row in reader]
	
def write_csv(path: str, rows: list[dict]):
	fieldnames = []
	for row in rows:
		for k in row.keys():
			if k not in fieldnames:
				fieldnames.append(k)

	with open(path, 'w') as f:
		log.info(f'writing file {path}')
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(rows)

tags_path=None #set from parser
def read_tags_csv() -> list[dict]:
	return read_csv(tags_path)
def write_tags_csv(rows: list[dict]):
	return write_csv(tags_path, rows)

def create_output_dir():
	# 1. create output folder
	if not os.path.exists(output_dir):
		log.info(f'creating output directory {output_dir}')
		os.mkdir(output_dir)


# ------ input command functions
def test_csv():
	test_csv_path = f'{output_dir}/test.csv'
	log.info(f'starting test-csv writing to file {test_csv_path}')
	write_csv(test_csv_path, [{"A":1, "B":1}, {"A":2, "B":2}])

def search_text(term: str, dry_run: bool):
	term = term.lower()
	log.info(f'starting search for term {term}')
	rows = read_tags_csv()
	searched_files_count = 0
	found_term_files_count = 0
	not_found_term_files_count = 0
	missing_files = []
	for row in rows:
		file_path = row.get(header_txt_path) if row.get(header_txt_path) != None else ''
		d = os.getcwd()
		if not os.path.exists(file_path):
			log.warning(f'country {row[header_country]} missing file with name {row[header_file_name]} at path: {row[header_file_path]}')
			missing_files.append(file_path)
		else:
			with open(file_path, 'r') as f:
				found = term in f.read().lower()
			row[search_term_header(term)] = found
			if found:
				found_term_files_count += 1
			else:
				not_found_term_files_count += 1
			searched_files_count += 1
	
	if not dry_run:
		write_tags_csv(rows)
	
	log.info(f'finished searching term')
	log.info(f'{searched_files_count} files searched for {term}')
	log.info(f'{found_term_files_count} files contained term: {term}')
	log.info(f'{not_found_term_files_count} files did not contain term: {term}')
	log.info(f'files missing: {missing_files}')

def index_countries(countries_dir: str, dry_run: bool):
	if not os.path.exists(countries_dir):
		raise Exception(f'countries_dir {countries_dir} does not exist')
	
	countries = [(f.name,f.path) for f in os.scandir(countries_dir) if f.is_dir()]
	log.info(f'found {len(countries)} countries to index. this operation will overwrite tags file')
	#go over each country dir and index each pdf.txt file
	rows = []
	indexed_files_count = 0
	indexed_countries_count = 0
	missing_countries = []
	for c_tup in countries:
		country_files_path = f'{c_tup[1]}/Civil Society'
		if os.path.exists(country_files_path):
			country_files = [f for f in os.scandir(country_files_path)]
			indexed_countries_count += 1
		else:
			log.warning(f'country {c_tup[0]} missing Civil Society folder')
			missing_countries.append(c_tup[0])
			country_files = []
			
		c_files = [(f.name,f.path) for f in country_files if f.name.endswith('.pdf')]
		for f_tup in c_files:
			indexed_files_count += 1
			rows.append({header_file_name: f_tup[0], header_file_path: f_tup[1], header_country: c_tup[0]})
	if not dry_run:
		write_tags_csv(rows)
	log.info(f'finished indexing countries.')
	log.info(f'{indexed_files_count} files indexed for {indexed_countries_count} countries')
	log.info(f'countries missing Civil Society records: {missing_countries}')

def extract_text_from_pdf(input: dict):
	row = input['row']
	dry_run = input['dry_run']
	skip_existing = input['skip_existing']
	file_path = row[header_file_path]
	text_file_path = f'{file_path}.txt'
	if os.path.exists(text_file_path) and skip_existing:
		return (file_path, text_file_path)
	text = []
	if os.path.getsize(file_path) > 0:
		doc = convert_from_path(file_path)
		for page_number, page_data in enumerate(doc):
			page_text = pytesseract.image_to_string(page_data)
			text.append(page_text)
	if not dry_run:
		with open(text_file_path, 'w+') as f:
			f.write("\n\n".join(text))
	return (file_path, text_file_path)

def extract_text(dry_run: bool):
	log.info(f'starting text extraction')
	rows = read_tags_csv()
	extracted_files_count = 0
	inputs = [{'row': row, 'dry_run': dry_run, 'skip_existing': True} for row in rows]
	results = {}
	start = time.perf_counter()
	with Pool() as pool:
		for result in pool.map(extract_text_from_pdf, inputs):
			results[result[0]]=result[1]
	end = time.perf_counter()
	log.info(f'finished extracting text in {end-start} seconds')
	for row in rows:
		row[header_txt_path] = results[row[header_file_path]]
		extracted_files_count += 1
	
	if not dry_run:
		write_tags_csv(rows)
	
	log.info(f'finished extracting text')
	log.info(f'{extracted_files_count} files extracted')

def topic_model_preprocess(dry_run: bool):
	log.info(f'preprocess for topic modeling')
	nltk.data.path.append(os.path.abspath(f'{nltk_data_dir}'))
	# add stop words from different sources
	stopwords = nltk.corpus.stopwords.words('english')
	stopwords.extend(gensim_stopwords)
	# load all stopwords from extra_stopwords dir
	extra_stopwords_dir = f'{models_dir}/extra_stopwords'
	for filename in os.listdir(extra_stopwords_dir):
		f_path = os.path.join(extra_stopwords_dir, filename)
		# checking if it is a file
		if os.path.isfile(f_path):
			with open(f_path, 'r') as f:
				extra_words = [l.rstrip().lower() for l in f]
				stopwords.extend(extra_words)
	
	# init lemmatization and pos tagging
	lemmatization_allowed_post_tags = ['NOUN', 'ADJ', 'VERB', 'ADV']
	nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
	rows = read_tags_csv()
	log.info(f'read all texts')
	texts_to_read = [(row.get(header_file_name), row.get(header_txt_path)) for row in rows]
	texts = {}
	count = 0
	for tup in texts_to_read:
		text = ''
		with open(tup[1], 'r') as f:
			text = f.read().lower()
		# remove links and urls
		text, num_of_urls = re.subn(r'http\S+', '', text)
		log.info(f'removed {num_of_urls} urls from text {tup[0]}')
		text, num_of_emails = re.subn(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+', '', text)
		log.info(f'removed {num_of_emails} emails from text {tup[0]}')
		text, num_of_websites = re.subn(r'www.[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+', '', text)
		log.info(f'removed {num_of_websites} websites from text {tup[0]}')
		texts[tup[0]] = {'text':text}
		count += 1
		log.info(f'read text {count}/{len(texts_to_read)}')

	log.info(f'preprocess gensim and remove stopwords')
	count = 0
	for key in texts.keys():
		texts[key]['tokenized'] = gensim.utils.simple_preprocess(doc=texts[key]['text'], deacc=True, min_len=3)
		texts[key]['no_stop_words'] = [word for word in texts[key]['tokenized'] if word not in stopwords]
		count += 1
		log.info(f'preprocess and stopwords {count}/{len(texts_to_read)}')
	
	log.info(f'build bigram model from all texts')
	bigram = gensim.models.Phrases([texts[key]['no_stop_words'] for key in texts.keys()], min_count=5, threshold=100)
	bigram_mod = gensim.models.phrases.Phraser(bigram)
	log.info(f'run bigram model')
	count = 0
	for key in texts.keys():
		texts[key]['bigram'] = bigram_mod[texts[key]['no_stop_words']]
		count += 1
		log.info(f'bigram {count}/{len(texts_to_read)}')
	
	count = 0
	for row in rows:
		preprocessed_text = [token.lemma_ for token in nlp(" ".join(texts[row.get(header_file_name)]['bigram'])) if token.pos_ in lemmatization_allowed_post_tags]
		text_path = row.get(header_txt_path)
		preprocessed_text_path = f'{text_path}.preprocessed'
		log.info(f'saving preprocessed file at {preprocessed_text_path}')
		with open(preprocessed_text_path, 'w+') as f:
			f.writelines(line+'\n' for line in preprocessed_text)
		row[header_preprocessed_txt_path] = preprocessed_text_path
		count += 1
		log.info(f'saved preprocessed file {count}/{len(texts_to_read)}')
	if not dry_run:
		write_tags_csv(rows)
	log.info(f'finished preprocess for topic modeling')

class LdaParams(object):
	def __init__(self, num_topics = 20, random_state = 100, update_every = 1, iterations = 50, chunk_size = 100, passes = 10, alpha = 'symmetric',eta = None, per_word_topics = False, no_below = 5, no_above = 0.9) -> None:
		self.num_topics = num_topics
		self.random_state = random_state
		self.update_every = update_every
		self.chunk_size = chunk_size
		self.passes = passes
		self.alpha = alpha
		self.eta = eta
		self.per_word_topics = per_word_topics
		self.no_below = no_below
		self.no_above = no_above
		self.iterations = iterations

class FilterFromHeaders(object):
	def from_args(args: list[str]) -> 'FilterFromHeaders':
		filters = {}
		if args is not None:
			for arg in args:
				if '=' in arg:
					key, value = arg.split('=')
					filters[key] = value
		return FilterFromHeaders(filters)

	def __init__(self, filters: dict[str,str] = {}) -> None:
		self.filters = filters
	
	# must match all filters to pass
	def is_passing(self, row: dict[str,str]) -> bool:
		for key in self.filters.keys():
			if row.get(key) != self.filters[key]:
				return False
		return True
	def to_string(self):
		return str(self.filters)

def optimize_model_parameters(dry_run: bool, results_path: str, num_topics: str, num_passes: str ,filter_from_header: FilterFromHeaders = FilterFromHeaders(), ignore_words: list[str] = [], name_prefix: str = ''):
	num_topics_parsed = [int(i) for i in num_topics.split(':')]
	num_topics_parsed[1] += 1
	num_passes_parsed = [int(i) for i in num_passes.split(':')]
	num_passes_parsed[1] += 1

	name_prefix = name_prefix if name_prefix != '' else f'lda_model'
	model_prefix = name_prefix if name_prefix.endswith('_') else f'{name_prefix}_'
	log.info(f'optimizing model parameters for topics')
	
	summaries = {}
	for i_topics in range(num_topics_parsed[0], num_topics_parsed[1], num_topics_parsed[2]):
		for i_passes in range(num_passes_parsed[0], num_passes_parsed[1], num_passes_parsed[2]):
			log.info(f'running model with {i_topics} topics and {i_passes} passes')
			model_summary = model_topic_lda(dry_run, filter_from_header, LdaParams(num_topics=i_topics, passes=i_passes), ignore_words=ignore_words, unique_model_name=f'{model_prefix}{i_topics}_topics_{i_passes}_passes')
			log.info(f'finished model with {i_topics} topics and {i_passes} passes')
			summaries[f'{i_topics}_{i_passes}'] = model_summary
	
	if not dry_run and results_path is not None:
		# create base dir if not exists
		base_dir = os.path.dirname(results_path)
		if not os.path.exists(base_dir):
			os.makedirs(base_dir, exist_ok=True)

		with open(results_path, 'w') as f:
			# write passes headers
			passes_header = ','.join([str(i) for i in range(num_passes_parsed[0], num_passes_parsed[1], num_passes_parsed[2])])
			f.write(f'topics\\passes,{passes_header}\n')
			for i_topics in range(num_topics_parsed[0], num_topics_parsed[1], num_topics_parsed[2]):
				f.write(f'{i_topics}')
				for i_passes in range(num_passes_parsed[0], num_passes_parsed[1], num_passes_parsed[2]):
					model_summary = summaries[f'{i_topics}_{i_passes}']
					f.write(f',{model_summary.coherence_score}')
				f.write('\n')

class TrainedLdaModelSummary(object):
	def __init__(self, model_name: str, model_path: str, coherence_score: float) -> None:
		self.model_name = model_name
		self.model_path = model_path
		self.coherence_score = coherence_score


def model_topic_lda(dry_run: bool, filter_from_header: FilterFromHeaders = FilterFromHeaders(), lda_params: LdaParams = LdaParams(), ignore_words: list[str] = [], unique_model_name: str = None, open_browser_on_finish: bool = False, update_tags_file: bool = False) -> TrainedLdaModelSummary:
	log.info(f'modeling topics with LDA')
	rows = read_tags_csv()
	preprocessed_texts_paths = [(row.get(header_file_name),row.get(header_preprocessed_txt_path), row.get(header_country)) for row in rows if filter_from_header.is_passing(row)]
	log.info(f'processing {len(preprocessed_texts_paths)} out of {len(rows)} documents filtered by {filter_from_header.to_string()}')
	preprocessed_texts = {}
	text_property = "text"
	bag_of_words_property = "bow"
	file_name_property = "file_name"
	country_property = "country"
	topics_property = "topics"
	for tup in preprocessed_texts_paths:
		path = tup[1]
		file_name = tup[0]
		country = tup[2]
		with open(path, 'r') as f:
			text = [w for w in [l.rstrip() for l in f]]
			preprocessed_texts[file_name] = {text_property: text, file_name_property: file_name, country_property: country}
	log.info(f'read {len(preprocessed_texts)} texts into memory')
	# build the words dictionary - takes words from all documents into a single dictionaty and gives them ids
	preprocessed_texts_list = [preprocessed_texts[key][text_property] for key in preprocessed_texts.keys()]
	id_to_word = gensim.corpora.Dictionary(preprocessed_texts_list)
	if len(ignore_words) > 0:
		bad_ids = [i for i in id_to_word.doc2idx(ignore_words, -1) if i != -1]
		id_to_word.filter_tokens(bad_ids=bad_ids)
	most_common_before_extremes = id_to_word.most_common()
	id_to_word.filter_extremes(no_below=lda_params.no_below, no_above=lda_params.no_above)
	most_common_after_extremes = id_to_word.most_common()
	# create corpus mapping between word_id and the frequency per document
	corpus = []
	for k in preprocessed_texts.keys():
		bow = id_to_word.doc2bow(preprocessed_texts[k][text_property])
		corpus.append(bow)
		preprocessed_texts[k][bag_of_words_property] = bow
	log.info(f'created corpus with {len(corpus)} documents')
	# run lda to create topics based on the corpus
	log.info(f'running lda model with {vars(lda_params)}')
	lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus,
												id2word=id_to_word,
												num_topics=lda_params.num_topics, 
												random_state=lda_params.random_state,
												update_every=lda_params.update_every,
												chunksize=lda_params.chunk_size,
												passes=lda_params.passes,
												alpha=lda_params.alpha,
												eta=lda_params.eta,
												per_word_topics=lda_params.per_word_topics)
	log.info(f'finished running lda model with {vars(lda_params)}')
	log.info(f'calculating model coherence')
	umass_cm = CoherenceModel(model=lda_model, corpus=corpus, coherence='u_mass')
	umass_coherence = umass_cm.get_coherence()
	umass_coherence_per_topic = umass_cm.get_coherence_per_topic()
	unique_model_name = unique_model_name if unique_model_name is not None else datetime.datetime.now().isoformat()
	trained_results_dir = f'{trained_lda_dir}/{unique_model_name}'
	model_path = f'{trained_results_dir}/lda.model'

	# calculate per document topics
	log.info(f'calculating topic distribution per document')
	for k in preprocessed_texts.keys():
		topics = lda_model.get_document_topics(preprocessed_texts[k][bag_of_words_property], minimum_probability=1e-8)
		preprocessed_texts[k][topics_property] = topics

	# calculate topic terms
	topic_terms_ids = [lda_model.get_topic_terms(t, None) for t in range(len(lda_model.get_topics()))]
	topic_terms_words = [[(id_to_word[tup[0]],tup[1]) for tup in topic_i] for topic_i in topic_terms_ids]

	if not dry_run:
		if not os.path.exists(trained_results_dir):
			log.info(f'creating trained results dir {trained_results_dir}')
			os.makedirs(trained_results_dir, exist_ok=True)
		log.info(f'saving lda model')
		lda_model.save(f'{model_path}')
		log.info(f'save coherence')
		with open(f'{trained_results_dir}/coherence.txt', 'w') as f:
			f.write(f'umass_coherence={umass_coherence}\n')
			for i,val in enumerate(umass_coherence_per_topic):
				f.write(f'umass_coherence_topic_{i}={val}\n')

		log.info(f'saving most common words')
		with open(f'{trained_results_dir}/lda_dict_before_extremes.txt', 'w') as f:
			f.writelines([f'{tup[0]}-{str(tup[1])}\n'for tup in most_common_before_extremes])
		with open(f'{trained_results_dir}/lda_dict_after_extremes.txt', 'w') as f:
			f.writelines([f'{tup[0]}-{str(tup[1])}\n'for tup in most_common_after_extremes])
		
		log.info(f'saving topic terms')
		longest = max([len(l) for l in topic_terms_words])
		with open(f'{trained_results_dir}/topic_terms.csv', 'w') as f:
			model_topics = [i for i in range(len(lda_model.get_topics()))]
			topic_headers_string = ','.join([topic_header(i) + ',' + topic_prevalence_header(i) for i in sorted(model_topics)])
			f.write(f'{topic_headers_string}\n')
			for i in range(longest):
				row = []
				for t in model_topics:
					if len(topic_terms_words[t]) > i:
						row.extend([topic_terms_words[t][i][0],str(topic_terms_words[t][i][1])])
					else:
						row.extend(['',''])
				f.write(f'{",".join(row)}\n')

		log.info(f'saving topics per document')
		with open(f'{trained_results_dir}/topics_per_document.csv', 'w') as f:
			model_topics = [i for i in range(len(lda_model.get_topics()))]
			topic_headers_string = ','.join([topic_header(i) for i in sorted(model_topics)])
			f.write(f'file_name,country,{topic_headers_string}\n')
			for k in preprocessed_texts.keys():
				document_topics_dict = {preprocessed_texts[k][topics_property][i][0]: preprocessed_texts[k][topics_property][i][1] for i in range(len(preprocessed_texts[k][topics_property]))}
				for i in model_topics:
					if document_topics_dict.get(i) == None:
						document_topics_dict[i] = 0
				f.write(f'{preprocessed_texts[k][file_name_property]},{preprocessed_texts[k][country_property]},{",".join([str(document_topics_dict[k]) for k in sorted(document_topics_dict.keys())])}\n')
		
		log.info(f'creating lda visualization')
		vis = gensimvis.prepare(lda_model, corpus, id_to_word)
		# fix for complex numbers
		vis.topic_coordinates['x'] = np.real(vis.topic_coordinates['x'])
		vis.topic_coordinates['y'] = np.real(vis.topic_coordinates['y'])
		# create visualization
		vis_html_path = f'{trained_results_dir}/index.html'
		log.info('copy needed visualization files to trained results dir')
		vis_d3_path = shutil.copy(local_d3_path, trained_results_dir)
		vis_lda_path = shutil.copy(local_ldavis_path, trained_results_dir)
		vis_css_path = shutil.copy(local_ldavis_css_path, trained_results_dir)
		rel_d3_path = os.path.relpath(vis_d3_path, trained_results_dir)
		rel_lda_path = os.path.relpath(vis_lda_path, trained_results_dir)
		rel_css_path = os.path.relpath(vis_css_path, trained_results_dir)
		pyLDAvis.save_html(vis, vis_html_path, d3_url=rel_d3_path, ldavis_url=rel_lda_path, ldavis_css_url=rel_css_path)
		if open_browser_on_finish:
			webbrowser.open_new_tab(pathlib.Path(vis_html_path).as_uri())
		model_summary = TrainedLdaModelSummary(model_name=unique_model_name, model_path=model_path, coherence_score=umass_coherence)
		return model_summary

def calculate_document_topics(dry_run: bool, model_path: str, filter_from_header: FilterFromHeaders = FilterFromHeaders(), include_per_document_topics: bool = False, results_path: str = None):
	log.info(f'calculating document topics dry_run={dry_run} model_path={model_path} filter_from_header={filter_from_header.to_string()}')
	# load lda model
	model_path_abs = os.path.abspath(model_path)
	log.info(f'loading lda model from {model_path_abs}')
	lda_model = gensim.models.ldamodel.LdaModel.load(model_path_abs)
	id_to_word = lda_model.id2word
	rows = read_tags_csv()
	preprocessed_texts_paths = [(row.get(header_file_name),row.get(header_preprocessed_txt_path)) for row in rows if filter_from_header.is_passing(row)]
	log.info(f'processing {len(preprocessed_texts_paths)} out of {len(rows)} documents filtered by {filter_from_header.to_string()}')
	preprocessed_texts = {}
	text_property = "text"
	bag_of_words_property = "bow"
	for tup in preprocessed_texts_paths:
		path = tup[1]
		file_name = tup[0]
		with open(path, 'r') as f:
			text = [w for w in [l.rstrip() for l in f]]
			preprocessed_texts[file_name] = {text_property: text}
	log.info(f'read {len(preprocessed_texts)} texts into memory')
	# calc bag of words for new texts
	log.info(f'calculating bag of words for new texts')
	for key in preprocessed_texts.keys():
		preprocessed_texts[key][bag_of_words_property] = id_to_word.doc2bow(preprocessed_texts[key][text_property])
	# calc group bag of words
	log.info(f'calculating group bag of words')
	min_propability = 1e-8
	grouped_text = []
	for key in preprocessed_texts.keys():
		grouped_text.extend(preprocessed_texts[key][text_property])
	group_bow = id_to_word.doc2bow(grouped_text)
	group_topics = lda_model.get_document_topics(group_bow, minimum_probability=min_propability)
	log.info(f'calculated for topics for group of documents using model_path={model_path} filter_from_header={filter_from_header.to_string()}\n{group_topics}')

	document_topics = {}
	if include_per_document_topics:
		# # save topic distribution per document
		log.info(f'calculating topic distribution per document')
		for row in rows:
			if preprocessed_texts.get(row.get(header_file_name)) == None:
				continue
			topics = lda_model.get_document_topics(preprocessed_texts[row.get(header_file_name)][bag_of_words_property], minimum_probability=min_propability)
			document_topics[row.get(header_file_name)] = topics
	
	if  not dry_run and results_path is not None:
		log.info(f'writing document topics to {results_path}')
		with open(results_path, 'w') as f:
			model_topics = [i for i in range(len(lda_model.get_topics()))]
			topic_headers_string = ','.join([topic_header(i) for i in sorted(model_topics)])
			f.write(f'file_name,{topic_headers_string}\n')
			average_topic_distribution = {i: 0 for i in model_topics}
			for entry in document_topics.keys():
				document_topics_dict = {document_topics[entry][i][0]: document_topics[entry][i][1] for i in range(len(document_topics[entry]))}
				for i in model_topics:
					if document_topics_dict.get(i) == None:
						document_topics_dict[i] = 0
					average_topic_distribution[i] += document_topics_dict[i]
				f.write(f'{entry},{",".join([str(document_topics_dict[k]) for k in sorted(document_topics_dict.keys())])}\n')
			average_topic_distribution = {i: average_topic_distribution[i]/len(document_topics.keys()) for i in model_topics}
			f.write(f'average_topics_distribution-{filter_from_header.to_string().replace(",","-")},{",".join([str(average_topic_distribution[k]) for k in sorted(average_topic_distribution.keys())])}\n')
			group_topics_dict = {group_topics[i][0]: group_topics[i][1] for i in range(len(group_topics))}
			for i in model_topics:
				if group_topics_dict.get(i) == None:
					group_topics_dict[i] = 0
			f.write(f'group_topics_from_model-{filter_from_header.to_string().replace(",","-")},{",".join([str(group_topics_dict[k]) for k in sorted(group_topics_dict.keys())])}\n')

regions = {}
regions["African States"] = ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros", "Congo", "Côte d'Ivoire", "Cote d'Ivoire", "Democratic Republic of the Congo", "Democratic Republic of the Congo", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Gunea-Bissau", "Guinea-Bissau", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe", "São Tomé and Príncipe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Togo", "Tunisia", "Uganda", "United Republic of Tanzania", "Tanzania", "Zambia", "Zimbabwe"]
regions["Asia-Pacific States"] = ["Afghanistan", "Bahrain", "Bangladesh", "Bhutan", "Brunei Darussalam", "Cambodia", "China", "Cyprus", "Democratic People's Republic of Korea", "Democratic People's Republic of Korea", "Fiji", "India", "Indonesia", "Iran (Islamic Republic of)", "Iran", "Iraq", "Japan", "Jordan", "Kazakhstan", "Kiribati", "Kuwait", "Kyrgyzstan", "Lao People’s Democratic Republic", "Lao People's Democratic Republic", "Lebanon", "Malaysia", "Maldives", "Marshall Islands", "Micronesia (Federated States of)", "Micronesia", "Mongolia", "Myanmar", "Nauru", "Nepal", "Oman", "Pakistan", "Palau", "Papua New Guinea", "Philippines", "Qatar", "Republic of Korea", "Samoa", "Saudi Arabia", "Singapore", "Solomon Islands", "Sri Lanka", "Syrian Arab Republic", "Tajikistan", "Thailand", "Timor-Leste", "Tonga", "Turkey", "Türkiye", "Turkmenistan", "Tuvalu", "UAE", "United Arab Emirates", "Uzbekistan", "Vanuatu", "Viet Nam", "Yemen"]
regions["Eastern European States"] = ["Albania", "Armenia", "Azerbaijan", "Belarus", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Czechia", "Czech Republic", "Estonia", "Georgia", "Hungary", "Latvia", "Lithuania", "Montenegro", "North Macedonia", "Poland", "Republic of Moldova","Moldova", "Romania", "Russian Federation", "Serbia", "Slovakia", "Slovenia", "Ukraine"]
regions["Latin American and Caribbean States"] = ["Antigua and Barbuda", "Argentina", "Bahamas", "Barbados", "Belize", "Bolivia (Plurinational State of)", "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba", "Dominica", "Dominican Republic", "Ecuador", "El Salvador", "Grenada", "Guatemala", "Guyana", "Haiti", "Honduras", "Jamaica", "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Suriname", "Trinidad and Tobago", "Uruguay", "Venezuela"]
regions["Western European and other States"] = ["Andorra", "Australia", "Austria", "Belgium", "Canada", "Denmark", "Finland", "France", "Germany", "Greece", "Iceland", "Ireland", "Israel", "Italy", "Liechtenstein", "Luxembourg", "Malta", "Monaco", "Netherlands", "Netherlands (Kingdom of the)", "New Zealand", "Norway", "Portugal", "San Marino", "Spain", "Sweden", "Switzerland", "Turkey", "UK", "United Kingdom of Great Britain and Northern Ireland", "USA", "United States of America"]

def country_to_region(country: str) -> str:
	for region, countries in regions.items():
		if country in countries:
			return region
	return ""

def add_region_tag(dry_run: bool, filter_from_header: FilterFromHeaders = FilterFromHeaders()):
	log.info(f'adding region tag dry_run={dry_run} filter_from_header={filter_from_header.to_string()}')
	rows = read_tags_csv()
	for row in rows:
		if filter_from_header.is_passing(row):
			row[header_region] = country_to_region(row[header_country])
	if not dry_run:
		log.info(f'writing region tag to tags csv')
		write_tags_csv(rows)


oecd = {}
oecd["OECD States"] = ["Australia", "Austria", "Belgium", "Canada", "Chile", "Colombia", "Costa Rica", "Czech Republic", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Israel", "Italy", "Japan", "Republic of Korea", "Lativa", "Lithuania", "Luxembourg", "Mexico", "Netherlands (Kingdom of the)", "New Zealand", "Norway", "Poland", "Portugal", "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey", "United Kingdom of Great Britain and Northern Ireland", "United States of America"]

def country_to_oecd(country: str) -> str:
	for k, countries in oecd.items():
		if country in countries:
			return True
	return False

def add_oecd_tag(dry_run: bool, filter_from_header: FilterFromHeaders = FilterFromHeaders()):
	log.info(f'adding oecd tag dry_run={dry_run} filter_from_header={filter_from_header.to_string()}')
	rows = read_tags_csv()
	for row in rows:
		if filter_from_header.is_passing(row):
			row[header_oecd] = country_to_oecd(row[header_country])
	if not dry_run:
		log.info(f'writing oecd tag to tags csv')
		write_tags_csv(rows)

income = {}
income["High Income"] = ["Andorra", "United Arab Emirates", "Antigua and Barbuda", "Australia", "Austria", "Italy", "Belgium", "Bahrain", "Bahamas", "Barbados", "Brunei Darussalam", "Canada", "Switzerland", "Chile", "Cyprus", "Czech Republic", "Germany", "Denmark", "Spain", "Estonia", "Finland", "France", "United Kingdom of Great Britain and Northern Ireland", "Greece", "Guyana", "Croatia", "Hungary", "Ireland", "Iceland", "Israel", "Japan", "Saint Kitts and Nevis", "Republic of Korea", "Kuwait", "Lithuania", "Luxembourg", "Latvia", "Monaco", "Malta", "Netherlands (Kingdom of the)", "Norway", "Nauru", "New Zealand", "Oman", "Panama", "Poland", "Puerto Rico", "Portugal", "Qatar", "Romania", "Saudi Arabia", "Singapore", "San Marino", "Slovakia", "Slovenia", "Sweden", "Seychelles", "Trinidad and Tobago", "Uruguay", "United States of America"]
income["Low Income"] = ["Afghanistan", "Burundi", "Burkina Faso", "Central African Republic", "Democratic Republic of the Congo", "Eritrea", "Ethiopia", "Gambia", "Guinea-Bissau", "Liberia", "Madagascar", "Mali", "Mozambique", "Malawi", "Niger", "Democratic People's Republic of Korea", "Rwanda", "Sudan", "Sierra Leone", "Somalia", "South Sudan", "Syrian Arab Republic", "Chad", "Togo", "Uganda", "Yemen"]
income["Lower Middle Income"] = ["Angola", "Benin", "Bangladesh", "Bolivia", "Bhutan", "Cote d'Ivoire", "Cameroon", "Congo", "Comoros", "Cabo Verde", "Djibouti", "Algeria", "Egypt", "Micronesia", "Ghana", "Guinea", "Honduras", "Haiti", "India", "Iran", "Jordan", "Kenya", "Kyrgyzstan", "Cambodia", "Kiribati", "Lao People's Democratic Republic", "Lebanon", "Sri Lanka", "Lesotho", "Morocco", "Myanmar", "Mongolia", "Mauritania", "Nigeria", "Nicaragua", "Nepal", "Pakistan", "Philippines", "Papua New Guinea", "Senegal", "Solomon Islands", "Sao Tome and Principe", "Eswatini", "Tajikistan", "Timor-Leste", "Tunisia", "Tanzania", "Ukraine", "Uzbekistan", "Viet Nam", "Vanuatu", "Samoa", "Zambia", "Zimbabwe"]
income["Upper Middle Income"] = ["Albania", "Argentina", "Armenia", "Azerbaijan", "Bulgaria", "Bosnia and Herzegovina", "Belarus", "Belize", "Brazil", "Botswana", "China", "Colombia", "Costa Rica", "Cuba", "Dominica", "Dominican Republic", "Ecuador", "Fiji", "Gabon", "Georgia", "Equatorial Guinea", "Grenada", "Guatemala", "Indonesia", "Iraq", "Jamaica", "Kazakhstan", "Libya", "Saint Lucia", "Moldova", "Maldives", "Mexico", "Marshall Islands", "North Macedonia", "Montenegro", "Mauritius", "Malaysia", "Namibia", "Peru", "Palau", "Paraguay", "Russian Federation", "El Salvador", "Serbia", "Suriname", "Thailand", "Turkmenistan", "Tonga", "Turkey", "Tuvalu", "Saint Vincent and the Grenadines", "South Africa"]
income["Not Rated"] = ["Venezuela"]

def country_to_income(country: str) -> str:
	for inc, countries in income.items():
		if country in countries:
			return inc
	return ''

def add_income_tag(dry_run: bool, filter_from_header: FilterFromHeaders = FilterFromHeaders()):
	log.info(f'adding income tag dry_run={dry_run} filter_from_header={filter_from_header.to_string()}')
	rows = read_tags_csv()
	for row in rows:
		if filter_from_header.is_passing(row):
			row[header_income] = country_to_income(row[header_country])
	if not dry_run:
		log.info(f'writing income tag to tags csv')
		write_tags_csv(rows)

democracy_index = {}
democracy_index["Free"] = ["Andorra", "Antigua and Barbuda", "Argentina", "Australia", "Austria", "Bahamas", "Barbados", "Belgium", "Belize", "Botswana", "Brazil", "Bulgaria", "Cabo Verde", "Canada", "Chile", "Colombia", "Costa Rica", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Dominica", "Ecuador", "Estonia", "Finland", "France", "Germany", "Ghana", "Greece", "Grenada", "Guyana", "Iceland", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Kiribati", "Latvia", "Lesotho", "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Marshall Islands", "Mauritius", "Micronesia", "Monaco", "Mongolia", "Namibia", "Nauru", "Netherlands (Kingdom of the)", "New Zealand", "Norway", "Palau", "Panama", "Poland", "Portugal", "Romania", "Samoa", "San Marino", "Sao Tome and Principe", "Seychelles", "Slovakia", "Slovenia", "Solomon Islands", "South Africa", "Republic of Korea", "Spain", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Suriname", "Sweden", "Switzerland", "Timor-Leste", "Tonga", "Trinidad and Tobago", "Tuvalu", "United Kingdom of Great Britain and Northern Ireland", "United States of America", "Uruguay", "Vanuatu"]
democracy_index["Not Free"] = ["Afghanistan", "Algeria", "Angola", "Azerbaijan", "Bahrain", "Belarus", "Brunei Darussalam", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Central African Republic", "Chad", "China", "Congo", "Democratic Republic of the Congo", "Cuba", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Guinea", "Haiti", "Iran", "Iraq", "Jordan", "Kazakhstan", "Kyrgyzstan", "Lao People's Democratic Republic", "Libya", "Mali", "Myanmar", "Nicaragua", "Democratic People's Republic of Korea", "Oman", "Qatar", "Russian Federation", "Rwanda", "Saudi Arabia", "Somalia", "South Sudan", "Sudan", "Syrian Arab Republic", "Tajikistan", "Thailand", "Turkey", "Turkmenistan", "Uganda", "United Arab Emirates", "Uzbekistan", "Venezuela", "Viet Nam", "Yemen", "Zimbabwe"]
democracy_index["Partly Free"] = ["Albania", "Armenia", "Bangladesh", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Comoros", "Cote d'Ivoire", "Dominican Republic", "El Salvador", "Fiji", "Georgia", "Guatemala", "Guinea-Bissau", "Honduras", "Hungary", "India", "Indonesia", "Kenya", "Kuwait", "Lebanon", "Liberia", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mauritania", "Mexico", "Moldova", "Montenegro", "Morocco", "Mozambique", "Nepal", "Niger", "Nigeria", "North Macedonia", "Pakistan", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Senegal", "Serbia", "Sierra Leone", "Singapore", "Sri Lanka", "Tanzania", "Gambia", "Togo", "Tunisia", "Ukraine", "Zambia"]

def country_to_democracy_index(country: str) -> str:
	for di, countries in democracy_index.items():
		if country in countries:
			return di
	return ''

def add_democracy_index_tag(dry_run: bool, filter_from_header: FilterFromHeaders = FilterFromHeaders()):
	log.info(f'adding democracy index tag dry_run={dry_run} filter_from_header={filter_from_header.to_string()}')
	rows = read_tags_csv()
	for row in rows:
		if filter_from_header.is_passing(row):
			row[header_democracy_index] = country_to_democracy_index(row[header_country])
	if not dry_run:
		log.info(f'writing democracy index tag to tags csv')
		write_tags_csv(rows)

def add_extra_country_tags(dry_run: bool, filter_from_header: FilterFromHeaders = FilterFromHeaders()):
	add_region_tag(dry_run, filter_from_header)
	add_oecd_tag(dry_run, filter_from_header)
	add_income_tag(dry_run, filter_from_header)
	add_democracy_index_tag(dry_run, filter_from_header)

def update_stopwords(dry_run: bool):
	log.info(f'updating stopwords')
	download_dir = os.path.abspath(f'{nltk_data_dir}')
	if not dry_run:
		nltk.download('stopwords', download_dir=download_dir)
	log.info(f'downloaded stopwords to dir {download_dir}')

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--tags-file', default=f'{output_dir}/tags.csv', help=f'optional location for tags csv')
	parser.add_argument('--dry-run', action=argparse.BooleanOptionalAction, default=False, help=f'dry run without writing files')
	subparsers = parser.add_subparsers(dest='command')
	test_csv_parser = subparsers.add_parser('testcsv', help='create a test csv with dummy data')
	
	index_parser = subparsers.add_parser('index', help='index countries and pdfs')
	index_parser.add_argument('countries_dir', help='path to countries directory with .pdf files')

	tags_parser = subparsers.add_parser('tags', help='various tags operations')
	tags_parser.add_argument('--calculate-country-extra-tags', action=argparse.BooleanOptionalAction, default=False, help=f'calcualte extra tags for countries')
	tags_parser.add_argument('--filter-by-header', type=str, action='append', default=None, help='tags header used to filter the files to tag')

	text_parser = subparsers.add_parser('text', help='text manipulation related commands on the pdfs')
	text_subparsers = text_parser.add_subparsers(dest='text_command')
	text_subparsers.add_parser('extract', help='extract text from pdfs')
	search_parser = text_subparsers.add_parser('search', help='find a term in pdfs and add to tagging table')
	search_parser.add_argument('term', help='term to search in the pdfs')
	
	topic_parser = subparsers.add_parser('topic', help='topic modeling on text files')
	topic_subparsers = topic_parser.add_subparsers(dest='topic_command')
	topic_subparsers.add_parser('update_stopwords', help='create topic modeling')
	topic_subparsers.add_parser('preprocess', help='preprocess for topic modeling')

	model_parser = topic_subparsers.add_parser('model', help='create topic modeling')
	model_parser.add_argument('--filter-by-header', type=str, action='append', default=None, help='tags header used to filter the files to model')
	model_parser.add_argument('--unique-model-name', type=str, default=None, help='unique model name, overrides previous results with same name')
	model_parser.add_argument('--num-topics', type=int, default=20, help='number of topics')
	model_parser.add_argument('--random-state', type=int, default=100, help='random state')
	model_parser.add_argument('--update-every', type=int, default=1, help='update every')
	model_parser.add_argument('--chunk-size', type=int, default=100, help='chunk size')
	model_parser.add_argument('--passes', type=int, default=10, help='passes')
	model_parser.add_argument('--alpha', default='symmetric', help='alpha')
	model_parser.add_argument('--eta', default=None, help='eta')
	model_parser.add_argument('--no-below', type=int, default=5, help='filter extremes no below')
	model_parser.add_argument('--no-above', type=float, default=0.9, help='filter extremes no above')
	model_parser.add_argument('--iterations', type=int, default=50, help='number of iterations to run')
	model_parser.add_argument('--per-word-topics', action=argparse.BooleanOptionalAction, default=True, help='per word topics')
	model_parser.add_argument('--ignore-words', type=str, default='', help='list of words to remove seperated by comma')
	model_parser.add_argument('--update-tags-file', action=argparse.BooleanOptionalAction, default=False, help='write topics to tags file - overrides older topics')

	calculate_parser = topic_subparsers.add_parser('calculate', help='calculate topic modeling on trained model for files')
	calculate_parser.add_argument('--lda-path', type=str, help='path to trained lda model', required=True)
	calculate_parser.add_argument('--filter-by-header', type=str, action='append', default=None, help='tags header used to filter the files to model')
	calculate_parser.add_argument('--include-per-document-topics', action=argparse.BooleanOptionalAction, default=False, help=f'claculate per document topic')
	calculate_parser.add_argument('--results-path', type=str, default=None, help='path to save results')
	optimize_parser = topic_subparsers.add_parser('optimize', help='optimize topic modeling by running with different parameters and computing coherence')

	optimize_parser.add_argument('--filter-by-header', type=str, action='append', default=None, help='tags header used to filter the files to model')
	optimize_parser.add_argument('--name-prefix', type=str, default='', help='prefix for unique model name')
	optimize_parser.add_argument('--num-topics', type=str, default='2:1:10', help='number of topics in format min:max:step')
	optimize_parser.add_argument('--passes', type=str, default='1:1:10', help='number of passes in format min:max:step')
	optimize_parser.add_argument('--ignore-words', type=str, default='', help='list of words to remove seperated by comma')
	optimize_parser.add_argument('--results-path', type=str, default=None, help='file path to save results of the coherence matrix')
	args = parser.parse_args()

	log = set_logger()
	create_output_dir()
	tags_path = args.tags_file
	log.info(f'using tags file in path: {tags_path}')
	log.info(f'running in dry_run mode: {args.dry_run}')
	
	if args.command == 'testcsv':
		test_csv()
	elif args.command == 'index':
		index_countries(args.countries_dir, args.dry_run)
	elif args.command == 'tags':
		if args.calculate_country_extra_tags:
			add_extra_country_tags(args.dry_run, filter_from_header=FilterFromHeaders.from_args(args.filter_by_header))
	elif args.command == 'text':
		if args.text_command == 'extract':
			extract_text(args.dry_run)
		elif args.text_command == 'search':
			search_text(args.term, args.dry_run)
	elif args.command == 'topic':
		if args.topic_command == 'model':
			try:
				if args.alpha is not None:
					args.alpha = float(args.alpha)
			except ValueError:
				logger.info(f'alpha {args.alpha} is not float')
			try:
				
				if args.eta is not None:
					args.eta = float(args.eta)
			except ValueError:
				logger.info(f'eta {args.eta} is not float')
			lda_params = LdaParams(num_topics=args.num_topics, update_every=args.update_every, iterations=args.iterations, random_state=args.random_state, passes=args.passes, chunk_size=args.chunk_size, alpha=args.alpha, eta=args.eta, per_word_topics=args.per_word_topics, no_below=args.no_below, no_above=args.no_above)
			model_topic_lda(dry_run=args.dry_run,filter_from_header=FilterFromHeaders.from_args(args.filter_by_header), lda_params=lda_params, ignore_words=args.ignore_words.split(','), unique_model_name=args.unique_model_name, open_browser_on_finish=True, update_tags_file=args.update_tags_file)
		elif args.topic_command == 'update_stopwords':
			update_stopwords(args.dry_run)
		elif args.topic_command == 'preprocess':
			topic_model_preprocess(args.dry_run)
		elif args.topic_command == 'calculate':
			calculate_document_topics(args.dry_run, args.lda_path, FilterFromHeaders.from_args(args.filter_by_header), args.include_per_document_topics, args.results_path)
		elif args.topic_command == 'optimize':
			optimize_model_parameters(args.dry_run, num_topics=args.num_topics, num_passes=args.passes, filter_from_header=FilterFromHeaders.from_args(args.filter_by_header), name_prefix=args.name_prefix, ignore_words=args.ignore_words.split(','), results_path=args.results_path)
	log.info(f'Done')
		




