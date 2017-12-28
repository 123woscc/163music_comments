from concurrent.futures import ThreadPoolExecutor, as_completed
import math

import execjs
import requests
import tqdm

import settings


def get_post_data(sid, page):
    with open('core.js', 'r') as f:
        offset = (page - 1) * 20
        h = execjs.compile(f.read()).call('d', '{id:%s,offset:%d,total:"true",limit:20,csrf_token:""}' % (sid, offset),
                                 settings.NETEASE_P2,
                                 settings.NETEASE_P3,
                                 settings.NETEASE_P4)
        params = h['encText']
        encSecKey = h['encSecKey']
        return params, encSecKey


def get_comments(sid, page=1):
    params, encSecKey = get_post_data(sid, page)
    headers = {
        'Host': 'music.163.com',
        'Connection': 'keep-alive',
        'Content-Length': '484',
        'Cache-Control': 'max-age=0',
        'Origin': 'http://music.163.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'DNT': '1',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Cookie': 'JSESSIONID-WYYY=b66d89ed74ae9e94ead89b16e475556e763dd34f95e6ca357d06830a210abc7b685e82318b9d1d5b52ac4f4b9a55024c7a34024fddaee852404ed410933db994dcc0e398f61e670bfeea81105cbe098294e39ac566e1d5aa7232df741870ba1fe96e5cede8372ca587275d35c1a5d1b23a11e274a4c249afba03e20fa2dafb7a16eebdf6%3A1476373826753; _iuqxldmzr_=25; _ntes_nnid=7fa73e96706f26f3ada99abba6c4a6b2,1476372027128; _ntes_nuid=7fa73e96706f26f3ada99abba6c4a6b2; __utma=94650624.748605760.1476372027.1476372027.1476372027.1; __utmb=94650624.4.10.1476372027; __utmc=94650624; __utmz=94650624.1476372027.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
    }
    url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_{0}?csrf_token='.format(sid)
    data = {
             "params": params,
             "encSecKey": encSecKey
        }
    html = requests.post(url, headers=headers, data=data)
    comments = html.json()
    # print('first', comments['comments'][0]['content'])
    return comments


def get_total_pages(sid):
    comments = get_comments(sid)
    total = comments['total']
    pages = math.ceil(int(total)/20)
    return total, pages


def get_all_comments(sid):
    total, pages = get_total_pages(sid)
    # print(total)
    with ThreadPoolExecutor(max_workers=3) as executor:
        to_do = []
        for page in range(1, pages+1):
            future = executor.submit(parse_comments, sid, page)
            to_do.append(future)

        done_iter = as_completed(to_do)
        done_iter = tqdm.tqdm(done_iter, total=pages)

        result = []
        for future in done_iter:
            res = future.result()
            result.extend(res)
        return result


def parse_comments(sid, page):
    comments = get_comments(sid, page)
    return [comment['content'] for comment in comments['comments']]


def main():
    sid = '796919'
    comments = get_all_comments(sid)
    with open('comments.txt', 'w', encoding='utf8') as f:
        f.write('\n'.join(comments))


if __name__ == '__main__':
    main()
