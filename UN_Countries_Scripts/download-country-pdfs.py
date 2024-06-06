import logging
import requests
import os
import re
import shutil
import json
import time
import sys
import glob
import datetime
import multiprocessing
from urllib.parse import urlparse
script_name = os.path.basename(__file__)[:len(os.path.basename(__file__))-3]
root_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = f'{root_dir}/output/{script_name}'

log = logging.getLogger()
log.setLevel(logging.DEBUG)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f'{root_dir}/{script_name}-{datetime.datetime.now().isoformat()}-run.log')
file_handler.setLevel(logging.DEBUG)
log.addHandler(file_handler)
log.addHandler(stdout_handler)


documentation_url = "https://www.ohchr.org/en/hr-bodies/upr/documentation"
documentation_host = f'{urlparse(documentation_url).scheme}://{urlparse(documentation_url).hostname}'
# 1. create output folder
if not os.path.exists(output_dir):
    logging.info(f'creating output directory {output_dir}')
    os.mkdir(output_dir)

# 2. get the main documentation web page
logging.info(f'starting to gather information')
logging.info(f'getting html at {documentation_url}')
documentation_contents = requests.get(documentation_url, headers={'user-agent':'test'})
logging.info(f'received response from {documentation_url}, status: {documentation_contents.status_code}')

# 2.1 save the main documentation web page for debugging purposes
documentation_local_path = f'{output_dir}/documentation.txt'
logging.info(f'writing response from {documentation_url} to {documentation_local_path}')
f = open(documentation_local_path, "w+")
f.write(documentation_contents.text)
f.close()
logging.info(f'finished writing response from {documentation_url} to {documentation_local_path}')

# 3. search the main web page for the country links and names
logging.info(f'searching for all countries links in documentation page')
searched_countries_matches = re.findall('(/en/hr-bodies/upr/.*-index)">(.*)</a>',documentation_contents.text)
logging.info(f'found {len(searched_countries_matches)} countries links in documentation page')

# 4. parse to json format country names and corresponding links
logging.info(f'transforming found countries to json format')
searched_countries_parsed = [{ 'link': f'{documentation_host}{m[0]}', 'country': m[1]} for m in searched_countries_matches]

# 4.1 save the searched countries json for debugging purposes
searched_countries_json = json.dumps(searched_countries_parsed)
searched_countries_local_path = f'{output_dir}/searched_conutries.json'
f = open(searched_countries_local_path, "w+")
f.write(searched_countries_json)
f.close()
logging.info(f'finished writing countries links to {searched_countries_local_path}')

# 5. handle_country function accepts the name of the country and the link to the country documentation page
def handle_country(input):
    country = input['country']
    link = input['link']
    logging.info(f'start handling {country}')
    # 5.0 check if handled already
    country_dir_local_path = f'{output_dir}/Countries/{country}'
    civil_society_local_path = f'{country_dir_local_path}/Civil Society'
    done_file_path = f'{country_dir_local_path}/done.txt'
    if os.path.exists(done_file_path):
        logging.info(f'already handled country {country}')
        downloaded_pdf_files = glob.glob(f'{civil_society_local_path}/*.pdf')
        logging.info(f'finished downloading files {country},{len(downloaded_pdf_files)}')
        return
    elif os.path.exists(country_dir_local_path):
        logging.info(f'removing country output directory {country_dir_local_path} old data will be lost')
        shutil.rmtree(country_dir_local_path)

    # 5.1 create country output directory 
    logging.info(f'creating country output directory {country_dir_local_path}')
    os.mkdir(country_dir_local_path)
    logging.info(f'creating country civil society output directory {civil_society_local_path}')
    os.mkdir(civil_society_local_path)

    # 5.2 get the country documentation page
    logging.info(f'getting html at {link}')
    country_documentation_contents = requests.get(link, headers={'user-agent':'test'})
    logging.info(f'received response from {link}, status: {country_documentation_contents.status_code}')
    
    # 5.3 save the country documentation web page for debugging purposes
    country_documentation_local_path = f'{country_dir_local_path}/country_documentation.txt'
    logging.info(f'writing response from {link} to {country_documentation_local_path}')
    f = open(country_documentation_local_path, "w+")
    f.write(country_documentation_contents.text)
    f.close()
    logging.info(f'finished writing response from {link} to {country_documentation_local_path}')

    # 5.4 only look at Third Cycle
    article_start_index = country_documentation_contents.text.index('<article')
    article_end_index = country_documentation_contents.text.index('</article>')
    only_article_content = country_documentation_contents.text[article_start_index:article_end_index]
    third_cycle_heading_index = only_article_content.lower().index('third cycle')
    third_cycle_content = only_article_content[third_cycle_heading_index:]
    second_cycle_heading_index = third_cycle_content.lower().index('second cycle')
    third_cycle_content = third_cycle_content[:second_cycle_heading_index]

    # 5.5. search the third sup link
    logging.info(f'searching for 3rd sup link in country documentation page')
    third_sup_match = re.search('stakeholders.*>3.*</sup>',third_cycle_content)
    logging.info(f'found {third_sup_match}')
    third_sup_link = re.search('href="([^ ]*)"',third_sup_match.group())
    
    # 5.6 get the country page with the stakeholders downloads
    country_download_page_link = f'{documentation_host}{third_sup_link.group(1)}'
    logging.info(f'getting html at {country_download_page_link}')
    country_download_page_contents = requests.get(country_download_page_link, headers={'user-agent':'test'})
    logging.info(f'received response from {country_download_page_link}, status: {country_download_page_contents.status_code}')

    # 5.7 save the country downloads web page for debugging purposes
    country_download_page_local_path = f'{country_dir_local_path}/country_download_page_documentation.txt'
    logging.info(f'writing response from {country_download_page_link} to {country_download_page_local_path}')
    f = open(country_download_page_local_path, "w+")
    f.write(country_download_page_contents.text)
    f.close()
    logging.info(f'finished writing response from {country_download_page_link} to {country_download_page_local_path}')

    # 5.8. search for the iframe that holds the actual download links
    logging.info(f'searching for iframe with downloads in country download page')
    download_iframe_match = re.search('iframe.*src="(.*uprdoc.ohchr.org/uprweb/docsview[^ >]*)"',country_download_page_contents.text)
    logging.info(f'found {download_iframe_match}')

    # 5.9 get the country page with the stakeholders downloads
    download_iframe_link = download_iframe_match.group(1).replace('&amp;','&')
    download_iframe_document_root = f'{urlparse(download_iframe_link).scheme}://{urlparse(download_iframe_link).hostname}{"/".join(urlparse(download_iframe_link).path.split("/")[:-1])}'
    logging.info(f'getting html at {download_iframe_link}')
    download_iframe_contents = requests.get(download_iframe_link, headers={'user-agent':'test'})
    logging.info(f'received response from {download_iframe_link}, status: {download_iframe_contents.status_code}')

    # 5.10 save the iframe downloads web page for debugging purposes
    download_iframe_local_path = f'{country_dir_local_path}/download_iframe.txt'
    logging.info(f'writing response from {download_iframe_link} to {download_iframe_local_path}')
    f = open(download_iframe_local_path, "w+")
    f.write(download_iframe_contents.text)
    f.close()
    logging.info(f'finished writing response from {download_iframe_link} to {download_iframe_local_path}')

    # 5.11 search for the civil society table
    civil_society_start_index = download_iframe_contents.text.index('Civil Society Organisations')
    civil_society_end_index = download_iframe_contents.text.index('/table>', civil_society_start_index)
    civil_society_table_content = download_iframe_contents.text[civil_society_start_index:civil_society_end_index]

    logging.info(f'searching for all file download links in Civil Society table')
    download_file_matches = re.findall('href="(.*downloadfile.*)">E</a>',civil_society_table_content)
    logging.info(f'found {len(download_file_matches)} download files links in civil society table')

    # 5.12 download all files
    for link in download_file_matches:
        file_download_link = f'{download_iframe_document_root}/{link}'.replace('&amp;','&')
        logging.info(f'downloading file from {file_download_link}')
        file_download_content = requests.get(file_download_link, headers={'user-agent':'test'})
        # 5.13 get the file name from the headers
        cd = file_download_content.headers.get('content-disposition')
        file_name = re.search('filename="(.+)"', cd)[1]
        # 5.14 save the file
        file_download_local_path = f'{civil_society_local_path}/{file_name}'
        logging.info(f'saving file to {file_download_local_path}')
        f = open(file_download_local_path, "wb+")
        f.write(file_download_content.content)
        f.close()
        logging.info(f'saved file to {file_download_local_path}')
        if os.path.getsize(file_download_local_path) == 0:
            logging.warn(f'found zero size file {file_download_local_path}. skipping text conversion')
            continue

    downloaded_pdf_files = glob.glob(f'{civil_society_local_path}/*.pdf')
    logging.info(f'finished downloading files {country},{len(downloaded_pdf_files)}')
    f = open(done_file_path, "w+")
    f.write(datetime.datetime.now().isoformat())
    f.close()
    logging.info(f'writing done file for {country}')

# 4. parse to json format country names and corresponding links
logging.info(f'transforming found countries to json format')
searched_countries_parsed = [{ 'link': f'{documentation_host}{m[0]}', 'country': m[1]} for m in searched_countries_matches]



#6 call the handle country function for each country
with multiprocessing.Pool(10) as p:
		p.map(handle_country, searched_countries_parsed)
    









