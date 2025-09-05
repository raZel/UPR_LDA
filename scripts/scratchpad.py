import logging
from collections import Counter
import csv
import io
from UPR_LDA.utils import get_settings, init_logger, get_data_store, get_pdf_fetcher
from UPR_LDA.html_crawler import crawl_upr_for_civil_society_submissions
from typing import Iterable, Dict, List, Optional
from UPR_LDA.data_store import UPRDataStore
from pprint import pprint


_ALL_COUNTRIES = ['Afghanistan','Albania','Algeria','Andorra','Angola','Antigua and Barbuda','Argentina','Armenia','Australia','Austria','Azerbaijan','Bahamas','Bahrain','Bangladesh','Barbados','Belarus','Belgium','Belize','Benin','Bhutan','Bolivia Plurinational State of','Bosnia and Herzegovina','Botswana','Brazil','Brunei Darussalam','Bulgaria','Burkina Faso','Burundi','Cabo Verde','Cambodia','Cameroon','Canada','Central African Republic','Chad','Chile','China','Colombia','Comoros','Congo','Costa Rica','Cote dIvoire','Croatia','Cuba','Cyprus','Czechia','Democratic Peoples Republic of Korea','Democratic Republic of the Congo','Denmark','Djibouti','Dominica','Dominican Republic','Ecuador','Egypt','El Salvador','Equatorial Guinea','Eritrea','Estonia','Eswatini','Ethiopia','Fiji','Finland','France','Gabon','Gambia','Georgia','Germany','Ghana','Greece','Grenada','Guatemala','Guinea','Guinea-Bissau','Guyana','Haiti','Honduras','Hungary','Iceland','India','Indonesia','Iran Islamic Republic of','Iraq','Ireland','Israel','Italy','Jamaica','Japan','Jordan','Kazakhstan','Kenya','Kiribati','Kuwait','Kyrgyzstan','Lao Peoples Democratic Republic','Latvia','Lebanon','Lesotho','Liberia','Libya','Liechtenstein','Lithuania','Luxembourg','Madagascar','Malawi','Malaysia','Maldives','Mali','Malta','Marshall Islands','Mauritania','Mauritius','Mexico','Micronesia Federated States of','Monaco','Mongolia','Montenegro','Morocco','Mozambique','Myanmar','Namibia','Nauru','Nepal','Netherlands Kingdom of the','New Zealand','Nicaragua','Niger','Nigeria','North Macedonia','Norway','Oman','Pakistan','Palau','Panama','Papua New Guinea','Paraguay','Peru','Philippines','Poland','Portugal','Qatar','Republic of Korea','Republic of Moldova','Romania','Russian Federation','Rwanda','Saint Kitts and Nevis','Saint Lucia','Saint Vincent and the Grenadines','Samoa','San Marino','Sao Tome and Principe','Saudi Arabia','Senegal','Serbia','Seychelles','Sierra Leone','Singapore','Slovakia','Slovenia','Solomon Islands','Somalia','South Africa','South Sudan','Spain','Sri Lanka','Sudan','Suriname','Sweden','Switzerland','Syrian Arab Republic','Tajikistan','Thailand','Timor-Leste','Togo','Tonga','Trinidad and Tobago','Tunisia','Turkiye','Turkmenistan','Tuvalu','Uganda','Ukraine','United Arab Emirates','United Kingdom of Great Britain and Northern Ireland the','United Republic of Tanzania','United States of America','Uruguay','Uzbekistan','Vanuatu','Venezuela Bolivarian Republic of','Viet Nam','Yemen','Zambia','Zimbabwe']
regions = {}
regions["African States"] = ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros", "Congo", "Cote dIvoire", "Democratic Republic of the Congo", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Togo", "Tunisia", "Uganda", "United Republic of Tanzania", "Zambia", "Zimbabwe"]
regions["Asia-Pacific States"] = ["Afghanistan", "Bahrain", "Bangladesh", "Bhutan", "Brunei Darussalam", "Cambodia", "China", "Cyprus", "Democratic Peoples Republic of Korea", "Fiji", "India", "Indonesia", "Iran Islamic Republic of", "Iraq", "Japan", "Jordan", "Kazakhstan", "Kiribati", "Kuwait", "Kyrgyzstan", "Lao Peoples Democratic Republic", "Lebanon", "Malaysia", "Maldives", "Marshall Islands", "Micronesia Federated States of", "Mongolia", "Myanmar", "Nauru", "Nepal", "Oman", "Pakistan", "Palau", "Papua New Guinea", "Philippines", "Qatar", "Republic of Korea", "Samoa", "Saudi Arabia", "Singapore", "Solomon Islands", "Sri Lanka", "Syrian Arab Republic", "Tajikistan", "Thailand", "Timor-Leste", "Tonga", "Turkiye", "Turkmenistan", "Tuvalu", "United Arab Emirates", "Uzbekistan", "Vanuatu", "Viet Nam", "Yemen"]
regions["Eastern European States"] = ["Albania", "Armenia", "Azerbaijan", "Belarus", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Czechia", "Estonia", "Georgia", "Hungary", "Latvia", "Lithuania", "Montenegro", "North Macedonia", "Poland", "Republic of Moldova", "Romania", "Russian Federation", "Serbia", "Slovakia", "Slovenia", "Ukraine"]
regions["Latin American and Caribbean States"] = ["Antigua and Barbuda", "Argentina", "Bahamas", "Barbados", "Belize", "Bolivia Plurinational State of", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba", "Dominica", "Dominican Republic", "Ecuador", "El Salvador", "Grenada", "Guatemala", "Guyana", "Haiti", "Honduras", "Jamaica", "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Suriname", "Trinidad and Tobago", "Uruguay", "Venezuela Bolivarian Republic of"]
regions["Western European and other States"] = ["Andorra", "Australia", "Austria", "Belgium", "Canada", "Denmark", "Finland", "France", "Germany", "Greece", "Iceland", "Ireland", "Israel", "Italy", "Liechtenstein", "Luxembourg", "Malta", "Monaco", "Netherlands Kingdom of the", "New Zealand", "Norway", "Portugal", "San Marino", "Spain", "Sweden", "Switzerland", "Turkiye", "United Kingdom of Great Britain and Northern Ireland the", "United States of America"]

oecd = {}
oecd["OECD States"] = ["Australia", "Austria", "Belgium", "Canada", "Chile", "Colombia", "Costa Rica", "Czechia", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Israel", "Italy", "Japan", "Republic of Korea", "Latvia", "Lithuania", "Luxembourg", "Mexico", "Netherlands Kingdom of the", "New Zealand", "Norway", "Poland", "Portugal", "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Turkiye", "United Kingdom of Great Britain and Northern Ireland the", "United States of America"]

income = {}
income["High Income"] = ["Andorra", "United Arab Emirates", "Antigua and Barbuda", "Australia", "Austria", "Italy", "Belgium", "Bahrain", "Bahamas", "Barbados", "Brunei Darussalam", "Canada", "Switzerland", "Chile", "Cyprus", "Czechia", "Germany", "Denmark", "Spain", "Estonia", "Finland", "France", "United Kingdom of Great Britain and Northern Ireland the", "Greece", "Guyana", "Croatia", "Hungary", "Ireland", "Iceland", "Israel", "Japan", "Saint Kitts and Nevis", "Republic of Korea", "Kuwait", "Lithuania", "Luxembourg", "Latvia", "Monaco", "Malta", "Netherlands Kingdom of the", "Norway", "Nauru", "New Zealand", "Oman", "Panama", "Poland", "Portugal", "Qatar", "Romania", "Saudi Arabia", "Singapore", "San Marino", "Slovakia", "Slovenia", "Sweden", "Seychelles", "Trinidad and Tobago", "Uruguay", "United States of America"]
income["Low Income"] = ["Afghanistan", "Burundi", "Burkina Faso", "Central African Republic", "Democratic Republic of the Congo", "Eritrea", "Ethiopia", "Gambia", "Guinea-Bissau", "Liberia", "Madagascar", "Mali", "Mozambique", "Malawi", "Niger", "Democratic Peoples Republic of Korea", "Rwanda", "Sudan", "Sierra Leone", "Somalia", "South Sudan", "Syrian Arab Republic", "Chad", "Togo", "Uganda", "Yemen"]
income["Lower Middle Income"] = ["Angola", "Benin", "Bangladesh", "Bolivia Plurinational State of", "Bhutan", "Cote dIvoire", "Cameroon", "Congo", "Comoros", "Cabo Verde", "Djibouti", "Algeria", "Egypt", "Micronesia Federated States of", "Ghana", "Guinea", "Honduras", "Haiti", "India", "Iran Islamic Republic of", "Jordan", "Kenya", "Kyrgyzstan", "Cambodia", "Kiribati", "Lao Peoples Democratic Republic", "Lebanon", "Sri Lanka", "Lesotho", "Morocco", "Myanmar", "Mongolia", "Mauritania", "Nigeria", "Nicaragua", "Nepal", "Pakistan", "Philippines", "Papua New Guinea", "Senegal", "Solomon Islands", "Sao Tome and Principe", "Eswatini", "Tajikistan", "Timor-Leste", "Tunisia", "United Republic of Tanzania", "Ukraine", "Uzbekistan", "Viet Nam", "Vanuatu", "Samoa", "Zambia", "Zimbabwe"]
income["Upper Middle Income"] = ["Albania", "Argentina", "Armenia", "Azerbaijan", "Bulgaria", "Bosnia and Herzegovina", "Belarus", "Belize", "Brazil", "Botswana", "China", "Colombia", "Costa Rica", "Cuba", "Dominica", "Dominican Republic", "Ecuador", "Fiji", "Gabon", "Georgia", "Equatorial Guinea", "Grenada", "Guatemala", "Indonesia", "Iraq", "Jamaica", "Kazakhstan", "Libya", "Saint Lucia", "Republic of Moldova", "Maldives", "Mexico", "Marshall Islands", "North Macedonia", "Montenegro", "Mauritius", "Malaysia", "Namibia", "Peru", "Palau", "Paraguay", "Russian Federation", "El Salvador", "Serbia", "Suriname", "Thailand", "Turkmenistan", "Tonga", "Turkiye", "Tuvalu", "Saint Vincent and the Grenadines", "South Africa"]
income["Not Rated"] = ["Venezuela Bolivarian Republic of"]

democracy_index = {}
democracy_index["Free"] = ["Andorra", "Antigua and Barbuda", "Argentina", "Australia", "Austria", "Bahamas", "Barbados", "Belgium", "Belize", "Botswana", "Brazil", "Bulgaria", "Cabo Verde", "Canada", "Chile", "Colombia", "Costa Rica", "Croatia", "Cyprus", "Czechia", "Denmark", "Dominica", "Ecuador", "Estonia", "Finland", "France", "Germany", "Ghana", "Greece", "Grenada", "Guyana", "Iceland", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Kiribati", "Latvia", "Lesotho", "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Marshall Islands", "Mauritius", "Micronesia Federated States of", "Monaco", "Mongolia", "Namibia", "Nauru", "Netherlands Kingdom of the", "New Zealand", "Norway", "Palau", "Panama", "Poland", "Portugal", "Romania", "Samoa", "San Marino", "Sao Tome and Principe", "Seychelles", "Slovakia", "Slovenia", "Solomon Islands", "South Africa", "Republic of Korea", "Spain", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Suriname", "Sweden", "Switzerland", "Timor-Leste", "Tonga", "Trinidad and Tobago", "Tuvalu", "United Kingdom of Great Britain and Northern Ireland the", "United States of America", "Uruguay", "Vanuatu"]
democracy_index["Not Free"] = ["Afghanistan", "Algeria", "Angola", "Azerbaijan", "Bahrain", "Belarus", "Brunei Darussalam", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Central African Republic", "Chad", "China", "Congo", "Democratic Republic of the Congo", "Cuba", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Guinea", "Haiti", "Iran Islamic Republic of", "Iraq", "Jordan", "Kazakhstan", "Kyrgyzstan", "Lao Peoples Democratic Republic", "Libya", "Mali", "Myanmar", "Nicaragua", "Democratic Peoples Republic of Korea", "Oman", "Qatar", "Russian Federation", "Rwanda", "Saudi Arabia", "Somalia", "South Sudan", "Sudan", "Syrian Arab Republic", "Tajikistan", "Thailand", "Turkiye", "Turkmenistan", "Uganda", "United Arab Emirates", "Uzbekistan", "Venezuela Bolivarian Republic of", "Viet Nam", "Yemen", "Zimbabwe"]
democracy_index["Partly Free"] = ["Albania", "Armenia", "Bangladesh", "Benin", "Bhutan", "Bolivia Plurinational State of", "Bosnia and Herzegovina", "Comoros", "Cote dIvoire", "Dominican Republic", "El Salvador", "Fiji", "Georgia", "Guatemala", "Guinea-Bissau", "Honduras", "Hungary", "India", "Indonesia", "Kenya", "Kuwait", "Lebanon", "Liberia", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mauritania", "Mexico", "Republic of Moldova", "Montenegro", "Morocco", "Mozambique", "Nepal", "Niger", "Nigeria", "North Macedonia", "Pakistan", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Senegal", "Serbia", "Sierra Leone", "Singapore", "Sri Lanka", "United Republic of Tanzania", "Gambia", "Togo", "Tunisia", "Ukraine", "Zambia"]


def doc_count_by_country_and_cycle(store: UPRDataStore):
    all_docs = store.all()
    counts = Counter((d.country,d.cycle) for d in all_docs)
    countries = {k:{} for k in _ALL_COUNTRIES}
    for count in counts:
        countries[count[0]][count[1]] = counts[count]

    fieldnames = ['country','First','Second','Third']
    # Create an in-memory text buffer
    csv_string_buffer = io.StringIO()

    # Create a DictWriter object that writes to the buffer
    writer = csv.DictWriter(csv_string_buffer, fieldnames=fieldnames)

    # Write the header row
    writer.writeheader()

    # Write the data rows
    writer.writerows([{'country':k, 'First':v.get('First','-'), 'Second':v.get('Second','-'), 'Third':v.get('Third','-')} for k,v in countries.items()])

    # Get the complete CSV string from the buffer
    csv_string = csv_string_buffer.getvalue()
    pprint(csv_string)


def remove_countries_from_store(store: UPRDataStore, countries: Iterable[str]):
    docs = store.filter_by_country(countries)
    with store.autoPersist:
        for doc in docs:
            if not doc.key:
                _logger.warning("found doc with no key in store: %s", doc)   
                continue 
            store.remove(doc.key)

def clean_name_of_organization(store: UPRDataStore):
    with store.autoPersist:
        updated_docs = []
        for doc in store.all():
            doc.organization_name = doc.organization_name.removeprefix('Name of organisation')
            updated_docs.append(doc)
        for doc in updated_docs:
            store.add_or_update(doc)

def add_region_data(store: UPRDataStore):
    with store.autoPersist:
        for doc in store.all():
            key = find_key_for_country(regions, doc.country)
            if key is None:
                _logger.error('no region found for country %s', doc.country)
            else:
                doc.region = key

def add_oecd_data(store: UPRDataStore):
    with store.autoPersist:
        for doc in store.all():
            key = find_key_for_country(oecd, doc.country)
            doc.is_oecd = key != None

def add_income_data(store: UPRDataStore):
    with store.autoPersist:
        for doc in store.all():
            key = find_key_for_country(income, doc.country)
            if key is None:
                _logger.error('no income found for country %s', doc.country)
            else:
                doc.income_level = key

def add_democracy_data(store: UPRDataStore):
    with store.autoPersist:
        for doc in store.all():
            key = find_key_for_country(democracy_index, doc.country)
            if key is None:
                _logger.error('no democracy found for country %s', doc.country)
            else:
                doc.democracy_level = key

def find_key_for_country(dict: Dict[str,List[str]], country: str) -> Optional[str]:
    for k,countries in dict.items():
        if country in countries:
            return k
    return None

def validate_keys_for_countries(dict: Dict[str,List[str]]) -> Optional[str]:
    _logger.info("validating countries")
    for k,countries in dict.items():
        for country in countries:
            if country not in _ALL_COUNTRIES:
                _logger.error("country error: %s", country)
    _logger.info("validated countries")

def print_organizations(store):
    counts = Counter(doc.organization_name for doc in store.all())
    pprint(counts)

def validte_doc_files(store, fetcher):
    for doc in store.all():
        continue



init_logger()
_logger = logging.getLogger(__name__)
_logger.info("scratchpad started")
store = get_data_store()
# fetcher = get_pdf_fetcher()
breakpoint()
# validte_doc_files(store,fetcher)
_logger.info("scratchpad ended")





