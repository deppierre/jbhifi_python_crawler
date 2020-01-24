#Import libraries
#Driver here: https://github.com/mozilla/geckodriver/releases
import requests, json, time
import os, sys
import threading
from pathlib import Path
from time import perf_counter
from bs4 import BeautifulSoup

#Class
import data_from_selenium, data_from_request

#Variables
if 'jbhifi_python_crawler' in (os.getcwd().split('\\')):
    project_path = os.getcwd()
    driver_path = project_path + '\\bin\\geckodriver.exe'
else:
    print('error: wrong project directory')
    sys.exit()

#GET SOUP DATA
def getSoupCollections(url, filename):
    getraw_from_request = data_from_request.getRawHtml()
    html = getraw_from_request.getRawHtml(url)

    if getraw_from_request.error_code in [1, 2]:
        print('error: request socket error for collection')
        return None 
    elif getraw_from_request.error_code == 3:
        print('error: no collection data')
        return None 
    else:
        #If raw data
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            soup_collections = { (item.attrs['data-nav-title']).strip().lower(): {'url': item.attrs['href'], 'process': 0} for item in soup.find_all(class_='link-element') if '/collections' in item.attrs['href'] }
            if soup_collections: 
                cacheData(filename,soup_collections)
                return soup_collections
            else:
                return None

#GET SOUP PRODUCTS
def getSoupProducts(name, url, filename, output, driver=driver_path):
    soup_t1_start = perf_counter()
    getraw_from_selenium = data_from_selenium.getRawHtmlFromSelenium(driver)
    html = getraw_from_selenium.getData(url)

    if getraw_from_selenium.error_code == 2:
        print('error: timeout for collection {0}'.format(name))
        return None
    elif getraw_from_selenium.error_code == 3:
        print('error: selenium unknown error for collection {0}\ndetails: {1}'.format(name, getraw_from_selenium.error_details))
        return None
    elif getraw_from_selenium.error_code == 1:
        print('error: selenium socket error for collection {0}'.format(name))
        return None
    else:
        soup = BeautifulSoup(html, 'html.parser')
        soup_products_raw = soup.find_all('script', type='application/ld+json')

        #If raw data
        if soup_products_raw:
            soup_products = {}
            for product_json in soup_products_raw:
                json_products = json.loads(product_json.text)
                soup_products[json_products['sku']] = { 'name': json_products['name'], 'price': json_products['offers']['price'], 'currency': json_products['offers']['priceCurrency'], 'barcode': json_products['gtin13'], 'date': getraw_from_selenium.price_date, 'time': getraw_from_selenium.price_time }
            
            cacheData(filename,soup_products)
            output[name]['process'] = 1
            output[name]['process_details'] = { 'nb_items': len(soup_products), 'filename': filename, 'process_time': '{0:.2f}'.format(perf_counter() - soup_t1_start) }
            return soup_products

        else:
            print('error: no products for collection {0}\ndetails: \n\t- soup length: {1} \n\t- json length: {2}'.format((name),len(soup),len(soup_products_raw)))
            return None

def cacheData(filename, dict_to_cache):
    with open(filename,'w+') as filename_:
        json.dump(dict_to_cache, filename_)

def printOutput(soup, soup_file):
    product_downloads = sum([ soup[key]['process_details']['nb_items'] for key in soup.keys() if soup[key]['process'] == 1 ])
    total = len([ soup[key]['process'] for key in soup.keys() if soup[key]['process'] in [1,2] ])
    caches = len([ soup[key]['process'] for key in soup.keys() if soup[key]['process'] == 2 ])
    rejects = len([ soup[key]['process'] for key in soup.keys() if soup[key]['process'] <= 0 ])

    if total > 0:
        cacheData(soup_file, soup)
    
    #RECAP:
    print('-' * 40)
    print('-- Summary:')
    print('-' * 40)
    print('-- {0} collections rejected'.format(rejects))
    print('-- {0} collections already cached'.format(caches))
    print('-- {0} collections processed'.format(total))
    print('-- {0} products downloaded'.format(product_downloads))
    print('-' * 40)

def newThread(function, *_args):
    #https://realpython.com/intro-to-python-threading/
    thread = threading.Thread(target=function, args=_args)
    while threading.active_count() < 6:
        thread.start()
        while thread.is_alive():
            time.sleep(1)
            print('info: new thread {0} for collection - {1}'.format(thread, _args[0]))
            return thread

def main():
    #GLOBAL VARIABLES
    base_url = 'https://www.jbhifi.com.au'
    current_date = time.strftime('%Y%m%d')
    current_time = time.strftime('%I%M%S')
    data_folder = '{0}\\data'.format(project_path)
    output_folder = '{0}\\output'.format(project_path)
    cache_file_collections_base = '{0}\\{1}_collections'.format(data_folder,current_date)
    cache_file_collections_output = '{0}\\{1}_{2}_collections_done.json'.format(output_folder,current_date,current_time)
    cache_file_products_base = '{0}\\{1}_products_'.format(data_folder,current_date)
    filter_collections_exclusions = ['music', 'vinyl','all computer accessories','all audio-visual accessories','iphone accessories','phone cases']

    #COLLECTIONS
    cache_file_collections = '{0}.json'.format(cache_file_collections_base)
    if Path(cache_file_collections).is_file():
        with open(cache_file_collections,'r') as filename:
            soup_collection, result = json.load(filename), 'cache file: {0}'.format(cache_file_collections.lower())
    else:
        soup_collection, result = getSoupCollections(base_url, cache_file_collections), 'download'

    if soup_collection:
        soup_collection_result = soup_collection.copy()
        print('info: {0} collections loaded ({1})'.format(len(soup_collection), result))
    else:
        sys.exit()

    #PRODUCTS
    #Data collect
    for name, data in soup_collection.items():
        soup_products, result = {}, 0
        cache_file_products = cache_file_products_base + data['url'].split('/')[2] + '.json'
        if Path(cache_file_products).is_file():
            with open(cache_file_products,'r') as filename:
                soup_products, soup_collection_result[name]['process'] = json.load(filename), 2
                soup_collection_result[name]['process_details'] = { 'nb_items': len(soup_products), 'filename': cache_file_products }

        else:  
            if name not in filter_collections_exclusions:
                newThread(getSoupProducts, name, base_url + data['url'], cache_file_products, soup_collection_result)

    #Console summary
    while threading.active_count() > 1:
        pass
    else:
        printOutput(soup_collection_result, cache_file_collections_output)

if __name__ == '__main__':
    main()
