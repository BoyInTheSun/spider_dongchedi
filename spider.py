import requests
from lxml import etree
import json
import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from concurrent.futures import ThreadPoolExecutor


from table import Review

engine = create_engine('sqlite:///commets.sqlite')


def get_index(brand_id='x'):
    r = requests.get(
        'https://www.dongchedi.com/auto/library/x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-{}-x-x'.format(brand_id),
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "priority": "u=0, i",
            "upgrade-insecure-requests": "1",
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        }
    )
    html = etree.HTML(r.text)
    data = json.loads(html.xpath('//script[@id="__NEXT_DATA__"]/text()')[0])
    return data
    
def get_review(series_id):
    count = 50
    total = 0
    page = 1
    result = list()
    while True:
        print('series_id: {} page: {} / {}'.format(series_id, page, total // count + 1))
        r = requests.get(
            'https://m.dongchedi.com/motor/pc/car/series/get_review_list',
            params={
                'series_id': series_id,
                'part_id': 'S0',
                'page': page,
                'count': count,
            },
            headers={
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'referer': 'https://m.dongchedi.com',
                'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36',
            }
        )
        data = json.loads(r.text)['data']
        total = data['total_count']
        if data['review_list']: result += data['review_list']
        if data['has_more']:
            page += 1
        else:
            return result

def get_review_by_series_id(series_id, brand_id, brand_name):
    db_session = Session()
    if db_session.query(Review).filter_by(series_id=series_id).all():
        print(series_id, '已存在')
        return
    reviews = get_review(series_id)
    for review in reviews:
        review_data = Review(
            id=review.get('gid'),
            user_id=review['user_info'].get('user_id'),
            user_name=review['user_info'].get('name'),
            brand_id=brand_id,
            brand_name=brand_name,
            car_id=review.get('car_id'),
            car_name=review.get('car_name'),
            create_time=datetime.datetime.fromtimestamp(review.get('create_time', 0)),
            series_id=review.get('series_id'),
            series_name=review.get('series_name'),
            content=review.get('content'),
            bought_time=datetime.datetime.strptime(review['buy_car_info'].get('bought_time', '1970-01') or '1970-01', '%Y-%m') if review.get('buy_car_info') else datetime.datetime.fromtimestamp(0),
        )
        db_session.add(review_data)
    db_session.commit()
    db_session.close()
        

if __name__ == '__main__':
    gids = list()
    Session = sessionmaker(bind=engine)
    index = get_index()
    with open('index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False)
    index_brand = index['props']['pageProps']['allBrands']['brand']
    brands = {x['info']['brand_id']: x['info']['brand_name'] for x in index_brand if x['type'] == 1001}
    for brand_id in brands:
        brand_name = brands[brand_id]
        this_index = get_index(brand_id)
        this_index_series = this_index['props']['pageProps']['seriesInfo'].get('series')
        if not this_index_series:
            continue
        this_series_ids = [x['id'] for x in this_index_series]
        print(brand_id, brand_name)
        with ThreadPoolExecutor(16) as pool:
            for series_id in this_series_ids:
                pool.submit(get_review_by_series_id, series_id, brand_id, brand_name)
                # get_review_by_series_id(series_id, brand_id, brand_name)