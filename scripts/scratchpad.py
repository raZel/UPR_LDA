import logging
from collections import Counter
import csv
import io
from UPR_LDA.utils import get_settings, init_logger, get_data_store
from UPR_LDA.html_crawler import crawl_upr_for_civil_society_submissions
from typing import Iterable, Dict, List, Optional
from UPR_LDA.data_store import UPRDataStore
from pprint import pprint


_ALL_COUNTRIES = ['Afghanistan','Albania','Algeria','Andorra','Angola','Antigua and Barbuda','Argentina','Armenia','Australia','Austria','Azerbaijan','Bahamas','Bahrain','Bangladesh','Barbados','Belarus','Belgium','Belize','Benin','Bhutan','Bolivia Plurinational State of','Bosnia and Herzegovina','Botswana','Brazil','Brunei Darussalam','Bulgaria','Burkina Faso','Burundi','Cabo Verde','Cambodia','Cameroon','Canada','Central African Republic','Chad','Chile','China','Colombia','Comoros','Congo','Costa Rica','Cote dIvoire','Croatia','Cuba','Cyprus','Czechia','Democratic Peoples Republic of Korea','Democratic Republic of the Congo','Denmark','Djibouti','Dominica','Dominican Republic','Ecuador','Egypt','El Salvador','Equatorial Guinea','Eritrea','Estonia','Eswatini','Ethiopia','Fiji','Finland','France','Gabon','Gambia','Georgia','Germany','Ghana','Greece','Grenada','Guatemala','Guinea','Guinea-Bissau','Guyana','Haiti','Honduras','Hungary','Iceland','India','Indonesia','Iran Islamic Republic of','Iraq','Ireland','Israel','Italy','Jamaica','Japan','Jordan','Kazakhstan','Kenya','Kiribati','Kuwait','Kyrgyzstan','Lao Peoples Democratic Republic','Latvia','Lebanon','Lesotho','Liberia','Libya','Liechtenstein','Lithuania','Luxembourg','Madagascar','Malawi','Malaysia','Maldives','Mali','Malta','Marshall Islands','Mauritania','Mauritius','Mexico','Micronesia Federated States of','Monaco','Mongolia','Montenegro','Morocco','Mozambique','Myanmar','Namibia','Nauru','Nepal','Netherlands Kingdom of the','New Zealand','Nicaragua','Niger','Nigeria','North Macedonia','Norway','Oman','Pakistan','Palau','Panama','Papua New Guinea','Paraguay','Peru','Philippines','Poland','Portugal','Qatar','Republic of Korea','Republic of Moldova','Romania','Russian Federation','Rwanda','Saint Kitts and Nevis','Saint Lucia','Saint Vincent and the Grenadines','Samoa','San Marino','Sao Tome and Principe','Saudi Arabia','Senegal','Serbia','Seychelles','Sierra Leone','Singapore','Slovakia','Slovenia','Solomon Islands','Somalia','South Africa','South Sudan','Spain','Sri Lanka','Sudan','Suriname','Sweden','Switzerland','Syrian Arab Republic','Tajikistan','Thailand','Timor-Leste','Togo','Tonga','Trinidad and Tobago','Tunisia','Turkiye','Turkmenistan','Tuvalu','Uganda','Ukraine','United Arab Emirates','United Kingdom of Great Britain and Northern Ireland the','United Republic of Tanzania','United States of America','Uruguay','Uzbekistan','Vanuatu','Venezuela Bolivarian Republic of','Viet Nam','Yemen','Zambia','Zimbabwe']

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
    regions = {}
    regions["African States"] = ["Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros", "Congo", "Cote dIvoire", "Democratic Republic of the Congo", "Democratic Republic of the Congo", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Gunea-Bissau", "Guinea-Bissau", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe", "São Tomé and Príncipe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan", "Togo", "Tunisia", "Uganda", "United Republic of Tanzania", "Tanzania", "Zambia", "Zimbabwe"]
    regions["Asia-Pacific States"] = ["Afghanistan", "Bahrain", "Bangladesh", "Bhutan", "Brunei Darussalam", "Cambodia", "China", "Cyprus", "Democratic Peoples Republic of Korea", "Fiji", "India", "Indonesia", "Iran Islamic Republic of", "Iraq", "Japan", "Jordan", "Kazakhstan", "Kiribati", "Kuwait", "Kyrgyzstan", "Lao Peoples Democratic Republic", "Lebanon", "Malaysia", "Maldives", "Marshall Islands", "Micronesia Federated States of", "Mongolia", "Myanmar", "Nauru", "Nepal", "Oman", "Pakistan", "Palau", "Papua New Guinea", "Philippines", "Qatar", "Republic of Korea", "Samoa", "Saudi Arabia", "Singapore", "Solomon Islands", "Sri Lanka", "Syrian Arab Republic", "Tajikistan", "Thailand", "Timor-Leste", "Tonga", "Türkiye", "Turkmenistan", "Tuvalu", "UAE", "United Arab Emirates", "Uzbekistan", "Vanuatu", "Viet Nam", "Yemen"]
    regions["Eastern European States"] = ["Albania", "Armenia", "Azerbaijan", "Belarus", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Czechia", "Czech Republic", "Estonia", "Georgia", "Hungary", "Latvia", "Lithuania", "Montenegro", "North Macedonia", "Poland", "Republic of Moldova","Moldova", "Romania", "Russian Federation", "Serbia", "Slovakia", "Slovenia", "Ukraine"]
    regions["Latin American and Caribbean States"] = ["Antigua and Barbuda", "Argentina", "Bahamas", "Barbados", "Belize", "Bolivia Plurinational State of", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba", "Dominica", "Dominican Republic", "Ecuador", "El Salvador", "Grenada", "Guatemala", "Guyana", "Haiti", "Honduras", "Jamaica", "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Suriname", "Trinidad and Tobago", "Uruguay", "Venezuela Bolivarian Republic of"]
    regions["Western European and other States"] = ["Andorra", "Australia", "Austria", "Belgium", "Canada", "Denmark", "Finland", "France", "Germany", "Greece", "Iceland", "Ireland", "Israel", "Italy", "Liechtenstein", "Luxembourg", "Malta", "Monaco", "Netherlands Kingdom of the", "New Zealand", "Norway", "Portugal", "San Marino", "Spain", "Sweden", "Switzerland", "Turkiye", "UK", "United Kingdom of Great Britain and Northern Ireland the", "USA", "United States of America"]
    
    with store.autoPersist:
        for doc in store.all():
            region = find_key_for_country(regions, doc.country)
            if region is None:
                _logger.error('no region found for country %s', doc.country)
            else:
                doc.region = region

def add_oecd_data(store: UPRDataStore):
    oecd = {}
    oecd["OECD States"] = ["Australia", "Austria", "Belgium", "Canada", "Chile", "Colombia", "Costa Rica", "Czech Republic", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Israel", "Italy", "Japan", "Republic of Korea", "Latvia", "Lithuania", "Luxembourg", "Mexico", "Netherlands Kingdom of the", "New Zealand", "Norway", "Poland", "Portugal", "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Türkiye", "United Kingdom of Great Britain and Northern Ireland the", "United States of America"]
    
    with store.autoPersist:
        for doc in store.all():
            oecd = find_key_for_country(oecd, doc.country)
            doc.is_oecd = oecd != None

def find_key_for_country(dict: Dict[str,List[str]], country: str) -> Optional[str]:
    for k,countries in dict.items():
        if country in countries:
            return k
    return None

def validate_keys_for_countries(dict: Dict[str,List[str]]) -> Optional[str]:
    for k,countries in dict.items():
        for country in countries:
            if country not in _ALL_COUNTRIES:
                _logger.error("country error: %s", country)




def print_organizations(store):
    counts = Counter(doc.organization_name for doc in store.all())
    pprint(counts)

init_logger()
_logger = logging.getLogger(__name__)
_logger.info("scratchpad started")
store = get_data_store()
# breakpoint()
add_region_data(store)
_logger.info("scratchpad ended")





