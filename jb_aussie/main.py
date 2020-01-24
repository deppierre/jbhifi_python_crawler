#Import libraries
#USING OF https://github.com/mozilla/geckodriver/releases
import requests, json, time
import os, sys
import threading
from pathlib import Path
from time import perf_counter
from bs4 import BeautifulSoup

#Class
import data_from_selenium, data_from_request

#Variables
#DEBUG : 
#os.chdir('c:\\Users\\pdepretz\\Google Drive\\#1DOCUMENTS\\#11 TEMP\\PYTHON\\projects\\aussie_tech_prices')
# C:\Users\pdepretz\Google Drive\#1DOCUMENTS\#11 TEMP\PYTHON\projects\aussie_tech_prices
if 'aussie_tech_prices' in (os.getcwd().split('\\')):
    project_path = os.getcwd()
    driver_path = project_path + '\\bin\\geckodriver.exe'
else:
    print('error: wrong project directory')
    sys.exit()

#GET SOUP DATA
def getSoupCollections(url):
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
                return soup_collections
            else:
                return None

#GET SOUP PRODUCTS
def getSoupProducts(name, url, driver=driver_path):
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
        else:
            print('error: no products for collection {0}\ndetails: \n\t- soup length: {1} \n\t- json length: {2}'.format((name),len(soup),len(soup_products_raw)))
            return None
    return soup_products

def cacheData(filename,dict_to_cache):
    with open(filename,'w+') as filename_:
        json.dump(dict_to_cache, filename_)

def printOutput(soup, soup_file, rejects = 0, caches = 0, downloads = 0):
    total = len([ soup[key]['process'] for key in soup.keys() if soup[key]['process'] in [1,2] ])
    
    #RECAP:
    print('-' * 40)
    print('-- Summary:')
    print('-' * 40)
    print('-- {0} collections rejected'.format(rejects))
    print('-- {0} collections already cached'.format(caches))
    print('-- {0} collections processed'.format(total))
    print('-- {0} products downloaded'.format(downloads))
    print('-' * 40)
    if total > 0:
        cacheData(soup_file, soup)

def newThread(name, function, args):
    #https://realpython.com/intro-to-python-threading/
    print('Thread starting')
    thread = threading.Thread(target=function, args=(args))
    time.sleep(2)
    thread.start()
    print('Thread finishing')

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
    filter_collections_exclusions = ['music', 'vinyl']
    filter_collections_inclusions = ['apple macbooks','40\" to 44\" tvs','vinyl']
    number_collections_rejected = 0
    number_collections_cached = 0
    number_products_downloaded = 0

    #COLLECTIONS
    cache_file_collections = '{0}.json'.format(cache_file_collections_base)
    if Path(cache_file_collections).is_file():
        with open(cache_file_collections,'r') as filename:
            soup_collection, result = json.load(filename), 'cache file: {0}'.format(cache_file_collections.lower())
    else:
        soup_collection, result = getSoupCollections(base_url), 'download'
        cacheData(cache_file_collections,soup_collection)

    if soup_collection:
        soup_collection_result = soup_collection.copy()
        print('info: {0} collections loaded ({1})'.format(len(soup_collection), result))
    else:
        sys.exit()

    #PRODUCTS
    #Data collect
    for name, data in soup_collection.items():
        soup_products, result = {}, 0
        cache_file_products, soup_t1_start = cache_file_products_base + data['url'].split('/')[2] + '.json', perf_counter()  
        if Path(cache_file_products).is_file():
            with open(cache_file_products,'r') as filename:
                number_collections_cached += 1
                soup_products, result = json.load(filename), 2
        else:  
            if name in filter_collections_inclusions:
                soup_products, result = getSoupProducts(name, base_url + data['url']), 1
                if soup_products:
                    cacheData(cache_file_products,soup_products)
                    print('info: {0} products downloaded - {1}'.format(len(soup_products),name))
                    number_products_downloaded += len(soup_products)
                else:
                    number_collections_rejected += 1
                    result = -1
            else:
                number_collections_rejected += 1
                    
        #Output file (1 = download, 2 = cache, -1 = error, 0 = not processed/rejected)
        soup_collection_result[name]['process'] = result
        if result > 0:
            soup_collection_result[name]['process_details'] = { 'nb_items': len(soup_products), 'filename': cache_file_products,'date': current_date, 'time': current_time, 'process_time': '{0:.2f}'.format(perf_counter() - soup_t1_start) }
    
    #Console summart
    printOutput(soup_collection_result, cache_file_collections_output, number_collections_rejected, number_collections_cached, number_products_downloaded)

if __name__ == '__main__':
    main()
