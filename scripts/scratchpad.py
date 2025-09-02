import logging
from collections import Counter
import csv
import io
from UPR_LDA.utils import get_settings, init_logger, get_data_store
from UPR_LDA.html_crawler import crawl_upr_for_civil_society_submissions
from typing import Iterable
from UPR_LDA.data_store import UPRDataStore
from pprint import pprint

def doc_count_by_country_and_cycle(store: UPRDataStore):
    all_docs = store.all()
    counts = Counter((d.country,d.cycle) for d in all_docs)
    countries = {k:{} for k in ['Afghanistan','Albania','Algeria','Andorra','Angola','Antigua and Barbuda','Argentina','Armenia','Australia','Austria','Azerbaijan','Bahamas','Bahrain','Bangladesh','Barbados','Belarus','Belgium','Belize','Benin','Bhutan','Bolivia Plurinational State of','Bosnia and Herzegovina','Botswana','Brazil','Brunei Darussalam','Bulgaria','Burkina Faso','Burundi','Cabo Verde','Cambodia','Cameroon','Canada','Central African Republic','Chad','Chile','China','Colombia','Comoros','Congo','Costa Rica','Cote dIvoire','Croatia','Cuba','Cyprus','Czechia','Democratic Peoples Republic of Korea','Democratic Republic of the Congo','Denmark','Djibouti','Dominica','Dominican Republic','Ecuador','Egypt','El Salvador','Equatorial Guinea','Eritrea','Estonia','Eswatini','Ethiopia','Fiji','Finland','France','Gabon','Gambia','Georgia','Germany','Ghana','Greece','Grenada','Guatemala','Guinea','Guinea-Bissau','Guyana','Haiti','Honduras','Hungary','Iceland','India','Indonesia','Iran Islamic Republic of','Iraq','Ireland','Israel','Italy','Jamaica','Japan','Jordan','Kazakhstan','Kenya','Kiribati','Kuwait','Kyrgyzstan','Lao Peoples Democratic Republic','Latvia','Lebanon','Lesotho','Liberia','Libya','Liechtenstein','Lithuania','Luxembourg','Madagascar','Malawi','Malaysia','Maldives','Mali','Malta','Marshall Islands','Mauritania','Mauritius','Mexico','Micronesia Federated States of','Monaco','Mongolia','Montenegro','Morocco','Mozambique','Myanmar','Namibia','Nauru','Nepal','Netherlands Kingdom of the','New Zealand','Nicaragua','Niger','Nigeria','North Macedonia','Norway','Oman','Pakistan','Palau','Panama','Papua New Guinea','Paraguay','Peru','Philippines','Poland','Portugal','Qatar','Republic of Korea','Republic of Moldova','Romania','Russian Federation','Rwanda','Saint Kitts and Nevis','Saint Lucia','Saint Vincent and the Grenadines','Samoa','San Marino','Sao Tome and Principe','Saudi Arabia','Senegal','Serbia','Seychelles','Sierra Leone','Singapore','Slovakia','Slovenia','Solomon Islands','Somalia','South Africa','South Sudan','Spain','Sri Lanka','Sudan','Suriname','Sweden','Switzerland','Syrian Arab Republic','Tajikistan','Thailand','Timor-Leste','Togo','Tonga','Trinidad and Tobago','Tunisia','Turkiye','Turkmenistan','Tuvalu','Uganda','Ukraine','United Arab Emirates','United Kingdom of Great Britain and Northern Ireland the','United Republic of Tanzania','United States of America','Uruguay','Uzbekistan','Vanuatu','Venezuela Bolivarian Republic of','Viet Nam','Yemen','Zambia','Zimbabwe']}
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

def print_organizations(store):
    counts = Counter(doc.organization_name for doc in store.all())
    pprint(counts)

init_logger()
_logger = logging.getLogger(__name__)
_logger.info("scratchpad started")
store = get_data_store()

breakpoint()
_logger.info("scratchpad ended")





