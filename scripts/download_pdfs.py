import logging
from UPR_LDA.utils import get_settings, init_logger, get_data_store, get_pdf_fetcher
from UPR_LDA.html_crawler import crawl_upr_for_civil_society_submissions

def main():
    """
    Main function to run the UPR scraper.
    """
    # Load environment variables from .env file
    
    init_logger()
    _logger = logging.getLogger(__name__)

    start_url = "https://www.ohchr.org/en/hr-bodies/upr/documentation"
    _logger.info(f"Starting to download pdfs from: {start_url}")
    store = get_data_store()
    crawl_upr_for_civil_society_submissions(start_url, store)
    _logger.info(f"Crawl finished. have %s documents saved", len(store.all()))


if __name__ == "__main__":
    main()