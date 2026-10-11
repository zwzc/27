# coding: utf-8 -*-
"""
剧屋影视 (juwu) —— TVBox / 影视仓 Python 插件（基类 py 蜘蛛）

由 剧屋影视 dr3 源（v3 完整修复版）移植为 Python 版。
API: https://m.juwu.tv/api.php/provide/vod/ (maccms 标准 JSON API)
图片域名 img.test.com 已 502，替换为 static.juwu.tv
线路：modum3u8/bfzym3u8/mtm3u8/hhm3u8

本文件仅用于个人学习爬虫技术，请勿用于商业用途。
"""

import os
import re
import json
import time
import urllib.parse
import urllib.request

try:
    import requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False

try:
    from base.spider import Spider as BaseSpider
except Exception:  # 便于在非 TVBox 环境下单独调试
    class BaseSpider(object):
        pass

# ---------------------------------------------------------------- 常量

HOST = 'https://m.juwu.tv'
API = HOST + '/api.php/provide/vod/'
TIMEOUT = 8

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Referer': HOST + '/',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

CLASSES = [
    {'type_name': '短剧', 'type_id': '1'},
    {'type_name': '电影', 'type_id': '2'},
    {'type_name': '热榜', 'type_id': 'v_hot'},
    {'type_name': '古装仙侠', 'type_id': 'v_guzhuang'},
    {'type_name': '现代都市', 'type_id': 'v_xiandai'},
    {'type_name': '今日更新', 'type_id': 'v_today'},
]

VIRTUAL_CATS = {
    'v_hot': {'pool_tid': None, 'keywords': None, 'sort': 'hits', 'today_only': False},
    'v_guzhuang': {'pool_tid': '1', 'keywords': ['古装仙侠'], 'sort': None, 'today_only': False},
    'v_xiandai': {'pool_tid': '1', 'keywords': ['现代都市', '现代言情'], 'sort': None, 'today_only': False},
    'v_today': {'pool_tid': None, 'keywords': None, 'sort': None, 'today_only': True},
}

LINE_NAMES = {
    'modum3u8': '魔豆M3U8',
    'bfzym3u8': '暴风M3U8',
    'mtm3u8': '秒播M3U8',
    'hhm3u8': '花花M3U8',
}

_YEAR_FILTER = {'key': 'year', 'name': '年份', 'value': [
    {'n': '全部', 'v': ''}, {'n': '2026', 'v': '2026'}, {'n': '2025', 'v': '2025'},
    {'n': '2024', 'v': '2024'}, {'n': '2023', 'v': '2023'}, {'n': '2022', 'v': '2022'},
    {'n': '2021', 'v': '2021'}, {'n': '2020', 'v': '2020'}, {'n': '2019', 'v': '2019'},
]}

_BY_FILTER = {'key': 'by', 'name': '排序', 'value': [
    {'n': '最新', 'v': 'time'}, {'n': '最热', 'v': 'hits'}, {'n': '评分', 'v': 'score'},
]}

_CLASS_FILTERS = {
    '1': [{'n': '全部', 'v': ''}, {'n': '现代言情', 'v': '现代言情'}, {'n': '古装仙侠', 'v': '古装仙侠'},
          {'n': '穿越现代', 'v': '穿越现代'}, {'n': '现代都市', 'v': '现代都市'}, {'n': '甜宠', 'v': '甜宠'},
          {'n': '虐恋', 'v': '虐恋'}, {'n': '悬疑', 'v': '悬疑'}, {'n': '喜剧', 'v': '喜剧'}],
    '2': [{'n': '全部', 'v': ''}, {'n': '剧情', 'v': '剧情'}, {'n': '爱情', 'v': '爱情'},
          {'n': '喜剧', 'v': '喜剧'}, {'n': '恐怖', 'v': '恐怖'}, {'n': '动作', 'v': '动作'},
          {'n': '科幻', 'v': '科幻'}, {'n': '悬疑', 'v': '悬疑'}, {'n': '犯罪', 'v': '犯罪'}],
}

FILTERS = {}
for c in CLASSES:
    tid = c['type_id']
    if tid in _CLASS_FILTERS:
        FILTERS[tid] = [{'key': 'class', 'name': '类型', 'value': _CLASS_FILTERS[tid]}, _YEAR_FILTER, _BY_FILTER]
    else:
        FILTERS[tid] = [_YEAR_FILTER, _BY_FILTER]

# ---------------------------------------------------------------- 工具与缓存

_MEMO = {}

def log_it(msg):
    try:
        print('[剧屋] ' + str(msg))
    except Exception:
        pass

def memo_get(key):
    """获取内存缓存"""
    if key in _MEMO:
        t, v = _MEMO[key]
        if time.time() - t < 300:  # 默认 5 分钟过期
            return v
        else:
            del _MEMO[key]
    return None

def memo_set(key, val):
    _MEMO[key] = (time.time(), val)

# ─── 图片修复：\/ 转义 + 死域名替换 + HTTPS 统一 + 协议补全 ───
def fix_pic(pic):
    p = str(pic or '').replace('\\/', '/').strip()
    if not p:
        return ''
    p = p.replace('img.test.com', 'static.juwu.tv')
    if p.startswith('http://'):
        p = 'https://' + p[7:]
    elif p.startswith('//'):
        p = 'https:' + p
    elif p.startswith('/'):
        p = HOST + p
    return p

def card_of(v):
    if not v:
        return None
    return {
        'vod_id': str(v.get('vod_id', '')),
        'vod_name': v.get('vod_name', ''),
        'vod_pic': fix_pic(v.get('vod_pic')),
        'vod_remarks': v.get('vod_remarks') or v.get('vod_year') or 'HD',
    }

# 解析 play_from / play_url，空线路连名带集一起跳过，避免错位
def parse_play(from_raw, url_raw):
    if not from_raw or not url_raw:
        return [], []
    froms = str(from_raw).split('$$$')
    groups = str(url_raw).split('$$$')
    names, urls = [], []
    for i in range(len(froms)):
        if i >= len(groups):
            break
        eps = []
        for ep in groups[i].split('#'):
            ep = ep.replace('\\/', '/').strip()
            if not ep:
                continue
            at = ep.find('$')
            if at > 0:
                eps.append(ep[:at] + '$' + ep[at+1:])
            else:
                eps.append('第' + str(len(eps) + 1) + '集$' + ep)
        if eps:
            names.append(LINE_NAMES.get(froms[i].strip(), froms[i].strip()))
            urls.append('#'.join(eps))
    return names, urls

# 直链媒体判断
def is_direct(u):
    u = str(u or '').lower()
    return 'm3u8' in u or bool(re.search(r'\.(mp4|flv|mkv|ts|mov|avi)(\?|$)', u))

# 提取纯数字 vod_id：兼容数组 / 「分类$」前缀 / 纯数字
def to_vid(id_val):
    if isinstance(id_val, (list, tuple)):
        id_val = id_val[0] if id_val else ''
    s = str(id_val if id_val is not None else '')
    at = s.rfind('$')
    if at >= 0:
        s = s[at+1:]
    return re.sub(r'\D', '', s)

# ---------------------------------------------------------------- HTTP 请求

def get_json(qs):
    url = API + (qs or '')
    try:
        if _HAS_REQUESTS:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
        else:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read().decode('utf-8')
                return json.loads(data)
    except Exception as e:
        log_it('net 请求失败: %s' % e)
    return None

# ---------------------------------------------------------------- 池子与过滤逻辑

def fetch_pool(tid):
    key = 'pool:' + (str(tid) if tid else 'all')
    cached = memo_get(key)
    if cached is not None:
        return cached
    
    qs = '?ac=videolist&pg=1&pagesize=100' + (('&t=' + str(tid)) if tid else '')
    data = get_json(qs)
    result = []
    if data and data.get('code') == 1 and data.get('list'):
        result = data['list']
    
    memo_set(key, result)
    return result

def apply_virtual(pool, cfg, year):
    out = pool
    if cfg.get('keywords'):
        out = [v for v in out if any(kw.lower() in str(v.get('vod_class', '')).lower() for kw in cfg['keywords'])]
    if cfg.get('sort') == 'hits':
        out = sorted(out, key=lambda x: float(x.get('vod_hits', 0) or 0), reverse=True)
    if cfg.get('today_only'):
        ymd = time.strftime('%Y-%m-%d')
        out = [v for v in out if ymd in str(v.get('vod_time', ''))]
    if year:
        out = [v for v in out if str(v.get('vod_year', '')) == str(year)]
    return out

def empty_payload(page, limit):
    return {'page': page or 1, 'pagecount': 1, 'limit': limit or 60, 'total': 0, 'list': []}

# ---------------------------------------------------------------- 插件主体

class Spider(BaseSpider):

    def getName(self):
        return '剧屋影视'

    def init(self, extend=''):
        pass

    # ---------------- 首页分类 ----------------

    def homeContent(self, filter=False):
        try:
            classes = [{'type_id': c['type_id'], 'type_name': c['type_name']} for c in CLASSES]
            return {'class': classes, 'filters': FILTERS}
        except Exception as e:
            log_it('homeContent 异常: %s' % e)
            return {'class': []}

    # ---------------- 首页推荐 ----------------

    def homeVideoContent(self):
        try:
            cached = memo_get('home')
            if cached is not None:
                return cached
            
            data = get_json('?ac=videolist&pg=1&pagesize=60')
            lst = []
            if data and data.get('code') == 1:
                lst = [card_of(v) for v in data.get('list', []) if card_of(v)]
            else:
                log_it('homeVod 空结果: %s' % str(data)[:200])
            
            result = {'list': lst}
            memo_set('home', result)
            return result
        except Exception as e:
            log_it('homeVod 异常: %s' % e)
            return {'list': []}

    # ---------------- 分类内容 ----------------

    def categoryContent(self, tid, pg, filter, extend):
        page = max(1, int(pg) if str(pg).isdigit() else 1)
        ext = extend or {}
        if isinstance(ext, str):
            try:
                ext = json.loads(ext)
            except Exception:
                ext = {}
        
        class_kw = ext.get('class', '')
        year_kw = ext.get('year', '')
        by_kw = ext.get('by', '')
        limit = 60

        cache_key = 'cat:%s|%s|%s|%s|%s' % (tid, page, class_kw, year_kw, by_kw)
        cached = memo_get(cache_key)
        if cached is not None:
            return cached

        try:
            vods = []
            pagecount = 1
            total = 0

            if str(tid).startswith('v_'):
                # ===== 虚拟分类：池子 + 本地过滤 + 客户端分页 =====
                cfg = VIRTUAL_CATS.get(tid)
                if cfg:
                    pool = fetch_pool(cfg.get('pool_tid'))
                    filtered = apply_virtual(pool, cfg, year_kw)
                    total = len(filtered)
                    pagecount = max(1, (total + limit - 1) // limit)
                    start = (page - 1) * limit
                    vods = [card_of(v) for v in filtered[start:start+limit] if card_of(v)]
                
                result = {'page': page, 'pagecount': pagecount, 'limit': limit, 'total': total, 'list': vods}
                memo_set(cache_key, result)
                return result

            # ===== 真实分类 =====
            qs = '?ac=videolist&t=%s&pg=%s&pagesize=%s' % (tid, page, limit)
            if by_kw:
                qs += '&by=' + by_kw
            data = get_json(qs)
            
            if data and data.get('code') == 1:
                raw = data.get('list', [])
                pagecount = int(data.get('pagecount', 1) or 1)
                total = int(data.get('total', len(raw)) or len(raw))
                
                if class_kw:
                    raw = [v for v in raw if class_kw in str(v.get('vod_class', ''))]
                if year_kw:
                    raw = [v for v in raw if str(v.get('vod_year', '')) == year_kw]
                
                vods = [card_of(v) for v in raw if card_of(v)]
            else:
                log_it('category 无效响应 tid=%s: %s' % (tid, str(data)[:200]))

            result = {'page': page, 'pagecount': pagecount, 'limit': limit, 'total': total, 'list': vods}
            memo_set(cache_key, result)
            return result

        except Exception as e:
            log_it('category 异常: %s' % e)
            return empty_payload(page, limit)

    # ---------------- 详情 ----------------

    def detailContent(self, ids):
        vid = to_vid(ids)
        if not vid:
            log_it('detail 无效 id: %s' % str(ids))
            return {'list': []}

        cache_key = 'd:' + vid
        cached = memo_get(cache_key)
        if cached is not None:
            return cached

        try:
            data = get_json('?ac=detail&ids=' + vid)
            d = None
            if data and data.get('code') == 1 and data.get('list'):
                d = data['list'][0]
            
            if not d:
                log_it('detail 空数据 vid=%s: %s' % (vid, str(data)[:200]))
                return {'list': []}

            names, urls = parse_play(d.get('vod_play_from'), d.get('vod_play_url'))
            if not urls:
                log_it('detail 无播放线路 vid=%s' % vid)
                return {'list': []}

            vod = {
                'vod_id': vid,
                'vod_name': d.get('vod_name') or vid,
                'vod_pic': fix_pic(d.get('vod_pic')),
                'type_name': d.get('type_name', ''),
                'vod_year': d.get('vod_year', ''),
                'vod_area': d.get('vod_area', ''),
                'vod_remarks': d.get('vod_remarks') or 'HD',
                'vod_actor': d.get('vod_actor', ''),
                'vod_director': d.get('vod_director', ''),
                'vod_content': re.sub(r'<[^>]+>', '', str(d.get('vod_content', ''))).strip()[:500],
                'vod_play_from': '$$$'.join(names) if names else '剧屋影视',
                'vod_play_url': '$$$'.join(urls),
            }
            
            result = {'list': [vod]}
            memo_set(cache_key, result)
            return result

        except Exception as e:
            log_it('detail 异常 vid=%s: %s' % (vid, e))
            return {'list': []}

    # ---------------- 搜索 ----------------

    def searchContent(self, key, quick=False, pg='1'):
        page = max(1, int(pg) if str(pg).isdigit() else 1)
        wd = str(key or '').strip()
        if not wd:
            return {'page': 1, 'pagecount': 1, 'limit': 30, 'total': 0, 'list': []}

        cache_key = 's:%s:%s' % (wd, page)
        cached = memo_get(cache_key)
        if cached is not None:
            return cached

        try:
            qs = '?wd=%s&pg=%s&pagesize=30' % (urllib.parse.quote(wd), page)
            data = get_json(qs)
            
            lst = []
            if data and data.get('code') == 1:
                lst = [card_of(v) for v in data.get('list', []) if card_of(v)]
            
            result = {'page': page, 'pagecount': 1, 'limit': 30, 'total': len(lst), 'list': lst}
            memo_set(cache_key, result)
            return result
        except Exception as e:
            log_it('search 异常: %s' % e)
            return {'page': 1, 'pagecount': 1, 'limit': 30, 'total': 0, 'list': []}

    # ---------------- 播放 ----------------

    def playerContent(self, flag, id, vipFlags=None):
        raw = str(id or '').replace('\\/', '/')
        if not raw:
            return {'parse': 0, 'playUrl': '', 'url': ''}

        if is_direct(raw):
            ref = HOST + '/'
            m = re.match(r'^https?://[^/]+', raw, re.I)
            if m:
                ref = m.group(0) + '/'
            return {
                'parse': 0,
                'playUrl': '',
                'url': raw,
                'header': {'User-Agent': HEADERS['User-Agent'], 'Referer': ref},
            }
        
        return {'parse': 0, 'playUrl': '', 'url': raw, 'header': HEADERS}

    # ---------------- 其它 ----------------

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass