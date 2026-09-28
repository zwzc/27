# -*- coding: utf-8 -*-
"""
TVB云播 / HKTV影视（含弹幕支持）
ext 用法：
  "http://app.tuxianimg.com"                                                              # 只指定 host
  {"host":"http://app.tuxianimg.com","danmu":"http://xxx/api/v2/fongmi/danmaku"}           # host + 弹幕API
  "{\"host\":\"http://app.tuxianimg.com\",\"danmu\":\"http://xxx/api/v2/fongmi/danmaku\"}" # ext 字符串形式
"""
import re
import json
import base64
import zlib
import random
import requests
from urllib.parse import quote, unquote
from Crypto.Cipher import AES
from base.spider import Spider as BaseSpider

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass


# ------------------------------------------------------------------ #
# AES 解密（key/iv 来自 libnmmp.so）
# ------------------------------------------------------------------ #
_AES_KEY = b"MickwrKuMickwrKu"
_AES_IV = b"MickwrKuMickwrKu"


def _decrypt_data(b64text):
    """data 字段(base64) -> 明文 JSON 字符串"""
    if not b64text:
        return None
    try:
        raw = base64.b64decode(b64text)
        pt = AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV).decrypt(raw)
        pad = pt[-1]
        if 1 <= pad <= 16:
            pt = pt[:-pad]
        try:
            return zlib.decompress(pt, 16 + zlib.MAX_WBITS).decode('utf-8', 'ignore')
        except Exception:
            return pt.decode('utf-8', 'ignore')
    except Exception as e:
        print(f"[hktv] decrypt fail: {e}")
        return None


# ------------------------------------------------------------------ #
# 弹幕模块
# ------------------------------------------------------------------ #
DEFAULT_DANMAKU_API = (
    "http://47.103.92.65:9321/DMQlCpHvSpxj4uQofGTafer8y_aL1XDa"
    "/api/v2/fongmi/danmaku"
)
_DM_CACHE = {}
_DM_CACHE_MAX = 50


def _clean_dm_name(name):
    """清洗影片名，提高弹幕匹配率"""
    s = str(name or "")
    s = re.sub(r'正在播放\s*[:：]?', ' ', s)
    s = re.sub(r'\[.*?\]', ' ', s)
    s = re.sub(r'【.*?】', ' ', s)
    s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'(1080p|720p|480p|2160p|4k|8k|hd|sd|uhd|fhd)', ' ', s, flags=re.I)
    s = re.sub(r'(国语|粤语|中字|中英|繁体|简体|完整版|未删减|蓝光|高清|超清)', ' ', s)
    s = re.sub(r'第\s*\d+\s*[集期话].*$', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s or str(name or '')


def _norm_episode(ep):
    """归一化集数名，如 '01' → '第1集'"""
    s = str(ep or '').strip()
    if not s:
        return '第1集'
    m = re.search(r'第\s*(\d+)\s*[集期话]', s)
    if m:
        return '第%s集' % m.group(1)
    m = re.search(r'^(\d+)$', s)
    if m:
        return '第%s集' % m.group(1)
    m = re.search(r'(?:ep|e|正片)?\s*(\d+)', s, re.I)
    if m:
        return '第%s集' % m.group(1)
    return s


def search_danmaku(api, vod_name, episode):
    """搜索弹幕，返回 [{"name":"...", "url":"..."}]；失败返回 []"""
    if not api or not vod_name:
        return []
    cname = _clean_dm_name(vod_name)
    ep = _norm_episode(episode)
    key = cname + '||' + ep
    if key in _DM_CACHE:
        return _DM_CACHE[key]

    try:
        url = '%s?name=%s&episode=%s' % (
            api.rstrip('/'),
            quote(cname, safe=''),
            quote(ep, safe=''),
        )
        r = requests.get(url, timeout=6, verify=False)
        data = r.json()
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get('list') or data.get('data') or data.get('danmaku') or []

        out = []
        for it in items:
            if not isinstance(it, dict):
                continue
            u = str(it.get('url') or '').strip()
            if u:
                out.append({
                    'name': str(it.get('name') or '弹幕')[:80],
                    'url': u,
                })

        if len(_DM_CACHE) > _DM_CACHE_MAX:
            _DM_CACHE.clear()
        _DM_CACHE[key] = out
        return out
    except Exception as e:
        print('[danmaku] search failed: %s' % e)
        return []


# ------------------------------------------------------------------ #
# 线路名中文映射
# ------------------------------------------------------------------ #
_LINE_CN = {
    'mp4': 'MP4 高清',
    'YYNB': '优优牛播',
    'wsym3u8': '微视云 M3U8',
    'bfzym3u8': '暴风影视 M3U8',
    'lzm3u8': '量子 M3U8',
    'hkm3u8': '港剧 M3U8',
    '1080zyk': '1080 自愈库',
    'tkm3u8': '天空 M3U8',
    'wjm3u8': '无尽 M3U8',
    'sdm3u8': '闪电 M3U8',
    'ffm3u8': '非凡 M3U8',
    'kuaikan': '快看 M3U8',
    'ukm3u8': 'U酷 M3U8',
    'ikm3u8': 'iKun M3U8',
    'wlm3u8': '卧龙 M3U8',
}


def _line_cn(name):
    return _LINE_CN.get(name, name)


# 随机机型池
_DEVICE_MODELS = [
    'ZXV10S100V7', 'MIBOX4', 'MIBOX3', 'ADT-2', 'ADT-3',
    'HWVTR-H', 'EC6108V9', 'Q21A', 'B860H', 'S905X3',
    'FiberHome-HG680', 'ZTE-B860AV2.1', 'Skyworth-E900V21E',
    'SM-S918B', 'SM-G998B', 'SM-S901B', 'Pixel-7', 'Pixel-8-Pro',
    '2201123G', 'M2012K11AG', 'PHK110', 'PAHM00', 'RMX3370',
]


def _rand_device_model():
    return random.choice(_DEVICE_MODELS)


# ------------------------------------------------------------------ #
# Spider
# ------------------------------------------------------------------ #
class Spider(BaseSpider):
    def getName(self):
        return 'HKTV影视'

    def init(self, extend=""):
        """初始化，支持 ext 传 host / danmu"""
        self.host = 'http://app.tuxianimg.com'
        self.danmaku_api = DEFAULT_DANMAKU_API
        self.extend = extend or ""

        if extend:
            ext = str(extend).strip()
            # 先尝试 JSON
            try:
                obj = json.loads(ext)
                if isinstance(obj, dict):
                    if obj.get('host'):
                        self.host = str(obj['host']).rstrip('/')
                    if obj.get('danmu'):
                        self.danmaku_api = str(obj['danmu']).strip()
                    return {'init': 0}
            except Exception:
                pass
            # 字符串 URL
            if ext.startswith('http'):
                self.host = ext.rstrip('/')
        return {'init': 0}

    def __init__(self):
        self.name = 'HKTV影视'
        self.host = 'http://app.tuxianimg.com'
        self.danmaku_api = DEFAULT_DANMAKU_API
        self.extend = ""
        self.timeout = 25
        self.device_model = _rand_device_model()

        self.header = {
            'App-Device-Id': '2c84565e46955353d875e3d964d87e1c6',
            'App-Os-Type': 'android',
            'App-Ui-Mode': 'light',
            'App-Version-Code': '100',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/3.14.9',
        }
        self.play_header = {
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 15; %s Build/b5cc949.1)'
                          % self.device_model,
            'accept-encoding': 'gzip',
            'allowcrossprotocolredirects': 'true',
            'connection': 'Keep-Alive',
        }
        self.class_names = []
        self.class_urls = []
        self.type_extend = {}
        self._cur_vod = ''   # 当前影片名（给弹幕用）
        self._cur_ep = ''    # 当前集数名（给弹幕用）

    # -------------------------------------------------------------- #
    # 内部：统一 API 请求 + 解密
    # -------------------------------------------------------------- #
    def _api(self, endpoint, params=None):
        url = '%s/api/vod/%s' % (self.host, endpoint)
        try:
            resp = requests.post(url, data=params or {}, headers=self.header,
                                 timeout=self.timeout, verify=False)
            resp.encoding = 'utf-8'
            if resp.status_code != 200:
                print('[hktv] %s HTTP %s' % (endpoint, resp.status_code))
                return None
            try:
                obj = resp.json()
            except Exception:
                m = re.search(r'\{.*\}', resp.text, re.S)
                obj = json.loads(m.group(0)) if m else None
            if not obj:
                return None
            plain = _decrypt_data(obj.get('data'))
            if not plain:
                return None
            return json.loads(plain)
        except Exception as e:
            print('[hktv] request %s failed: %s' % (endpoint, e))
            return None

    @staticmethod
    def _pic(pic):
        return pic or ''

    def _vod_item(self, v):
        pic = v.get('vod_pic') or v.get('vod_pic_slide') or ''
        return {
            'vod_id': str(v.get('vod_id', '') or ''),
            'vod_name': v.get('vod_name', '') or '',
            'vod_pic': self._pic(pic),
            'vod_remarks': v.get('vod_remarks', '') or '',
        }

    # -------------------------------------------------------------- #
    # 首页
    # -------------------------------------------------------------- #
    def homeContent(self, filter):
        try:
            result = {'class': [], 'list': []}
            init = self._api('init')
            if init:
                for c in init.get('type_list', []):
                    tid = str(c.get('type_id', ''))
                    tname = c.get('type_name', '')
                    if not tid or not tname:
                        continue
                    if tid == '0' and tname == '全部':
                        continue
                    self.class_names.append(tname)
                    self.class_urls.append(tid)
                    ext = c.get('type_extend', '')
                    if ext:
                        try:
                            self.type_extend[tid] = json.loads(ext)
                        except Exception:
                            pass
                for v in init.get('recommend_list', []):
                    item = self._vod_item(v)
                    if item['vod_id'] and item['vod_name']:
                        result['list'].append(item)

            for name, cid in zip(self.class_names, self.class_urls):
                result['class'].append({'type_name': name, 'type_id': cid})

            if filter:
                result['filters'] = {}
                for cid in self.class_urls:
                    result['filters'][cid] = self.get_filter_data(cid)
            return result
        except Exception as e:
            print('Error in homeContent: %s' % e)
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        # 首页推荐已在 homeContent 里给出
        return {'list': []}

    def get_filter_data(self, tid):
        """筛选维度来自 init 的 type_extend"""
        try:
            ext = self.type_extend.get(str(tid))
            if ext:
                out = []
                label_map = {
                    'class': '类型', 'area': '地区', 'lang': '语言',
                    'year': '年份', 'sort': '排序', 'star': '明星',
                    'director': '导演', 'state': '状态', 'version': '版本',
                }
                for key, label in label_map.items():
                    vals = ext.get(key)
                    if not vals:
                        continue
                    items = [{'n': '全部', 'v': ''}]
                    for v in str(vals).split(','):
                        v = v.strip()
                        if v:
                            items.append({'n': v, 'v': v})
                    out.append({'key': key, 'name': label, 'value': items})
                if out:
                    return out
            # 兜底
            return [
                {'key': 'class', 'name': '类型', 'value': [
                    {'n': '全部', 'v': ''}, {'n': '动作', 'v': '动作'},
                    {'n': '喜剧', 'v': '喜剧'}, {'n': '爱情', 'v': '爱情'},
                    {'n': '科幻', 'v': '科幻'}, {'n': '剧情', 'v': '剧情'},
                    {'n': '犯罪', 'v': '犯罪'}, {'n': '奇幻', 'v': '奇幻'},
                ]},
                {'key': 'area', 'name': '地区', 'value': [
                    {'n': '全部', 'v': ''}, {'n': '大陆', 'v': '大陆'},
                    {'n': '香港', 'v': '香港'}, {'n': '台湾', 'v': '台湾'},
                    {'n': '美国', 'v': '美国'}, {'n': '日本', 'v': '日本'},
                    {'n': '韩国', 'v': '韩国'},
                ]},
                {'key': 'lang', 'name': '语言', 'value': [
                    {'n': '全部', 'v': ''}, {'n': '国语', 'v': '国语'},
                    {'n': '英语', 'v': '英语'}, {'n': '粤语', 'v': '粤语'},
                ]},
                {'key': 'year', 'name': '年份', 'value': [
                    {'n': '全部', 'v': ''}, {'n': '2026', 'v': '2026'},
                    {'n': '2025', 'v': '2025'}, {'n': '2024', 'v': '2024'},
                    {'n': '2023', 'v': '2023'},
                ]},
                {'key': 'sort', 'name': '排序', 'value': [
                    {'n': '全部', 'v': ''}, {'n': '时间', 'v': 'time'},
                    {'n': '人气', 'v': 'hits'}, {'n': '评分', 'v': 'score'},
                ]},
            ]
        except Exception as e:
            print('Error in get_filter_data: %s' % e)
            return []

    # -------------------------------------------------------------- #
    # 分类
    # -------------------------------------------------------------- #
    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = max(1, int(pg or 1))
            params = {'type_id': tid, 'page': page}
            if extend:
                for key in ('class', 'area', 'lang', 'year', 'sort'):
                    val = extend.get(key)
                    if val:
                        params[key] = val

            data = self._api('typeFilterVodList', params)
            if not data:
                return {'list': [], 'page': page, 'pagecount': 1,
                        'limit': 0, 'total': 0}

            rows = data.get('recommend_list') or []
            videos = [self._vod_item(v) for v in rows
                      if v.get('vod_id') and v.get('vod_name')]

            seen, uniq = set(), []
            for v in videos:
                if v['vod_id'] not in seen:
                    seen.add(v['vod_id'])
                    uniq.append(v)

            total = data.get('total', len(uniq))
            pagecount = data.get('page_count', data.get('pagecount', 1))
            try:
                pagecount = max(1, int(pagecount))
            except Exception:
                pagecount = 1

            return {
                'list': uniq,
                'page': page,
                'pagecount': pagecount,
                'limit': len(uniq),
                'total': total,
            }
        except Exception as e:
            print('Error in categoryContent: %s' % e)
            return {'list': [], 'page': 1, 'pagecount': 1, 'limit': 0, 'total': 0}

    # -------------------------------------------------------------- #
    # 搜索
    # -------------------------------------------------------------- #
    def searchContent(self, key, quick, pg="1"):
        try:
            page = max(1, int(pg or 1))
            if not key:
                return {'list': []}
            data = self._api('searchList',
                             {'keywords': key, 'type_id': '0', 'page': page})
            if not data:
                return {'list': []}
            rows = data.get('search_list') or data.get('recommend_list') or []
            videos, seen = [], set()
            for v in rows:
                item = self._vod_item(v)
                if (item['vod_id'] and item['vod_name']
                        and item['vod_id'] not in seen):
                    seen.add(item['vod_id'])
                    videos.append(item)
            return {'list': videos}
        except Exception as e:
            print('Error in searchContent: %s' % e)
            return {'list': []}

    def searchSuggestions(self, keyword):
        try:
            data = self._api('searchSuggestions', {'keyword': keyword})
            if not data:
                return []
            out = []
            for it in data.get('list', []) or []:
                if it.get('vod_name'):
                    out.append(it['vod_name'])
            return out
        except Exception as e:
            print('Error in searchSuggestions: %s' % e)
            return []

    # -------------------------------------------------------------- #
    # 详情（保存影片名/集数名，供弹幕搜索用）
    # -------------------------------------------------------------- #
    def detailContent(self, ids):
        try:
            if not ids or not ids[0]:
                return {'list': []}
            vid = ids[0]
            data = self._api('vodDetail', {'vod_id': vid})
            if not data:
                return {'list': []}

            v = data.get('vod') or {}
            if not isinstance(v, dict):
                return {'list': []}

            # ===== 保存当前影片名 =====
            self._cur_vod = v.get('vod_name', '') or ''

            vod = {
                'vod_id': str(v.get('vod_id', vid)),
                'vod_name': self._cur_vod,
                'vod_pic': self._pic(v.get('vod_pic') or v.get('vod_pic_slide') or ''),
                'vod_remarks': v.get('vod_remarks', '') or '',
                'vod_year': v.get('vod_year', '') or '',
                'vod_area': v.get('vod_area', '') or '',
                'vod_actor': v.get('vod_actor', '') or '',
                'vod_director': v.get('vod_director', '') or '',
                'vod_content': v.get('vod_content', '') or '',
            }

            from_list = data.get('vod_play_from_list') or []
            url_list = data.get('vod_play_url_list') or []
            src_list = data.get('player_source_list') or []
            code2id = {s.get('player_code'): s.get('id')
                       for s in src_list if s.get('player_code')}

            play_from = []
            play_url = []
            for idx, src in enumerate(from_list):
                psid = code2id.get(src, '')
                episodes = []
                if idx < len(url_list):
                    for ep in url_list[idx].get('urls', []):
                        # ===== 集数名编码进 id，供播放时搜弹幕 =====
                        ep_name = ep.get('name', '') or ''
                        episodes.append('%s$%s@%s@%s@%s' % (
                            ep_name, psid,
                            ep.get('episode_index', ''),
                            vid,
                            quote(ep_name, safe=''),
                        ))
                play_from.append(_line_cn(src))
                play_url.append('#'.join(episodes))

            vod['vod_play_from'] = '$$$'.join(play_from)
            vod['vod_play_url'] = '$$$'.join(play_url)
            return {'list': [vod]}
        except Exception as e:
            print('Error in detailContent: %s' % e)
            return {'list': []}

    # -------------------------------------------------------------- #
    # 播放（含弹幕）
    # -------------------------------------------------------------- #
    def playerContent(self, flag, id, vipFlags):
        result = {'parse': 0, 'url': '', 'header': {}, 'playUrl': ''}
        try:
            if not id or id.count('@') < 2:
                return result

            # id 格式：psid@epidx@vid[@集数名(URL编码)]
            parts = str(id).split('@')
            psid = parts[0]
            ep_idx = parts[1]
            vid = parts[2] if len(parts) > 2 else ''
            ep_name = ''
            if len(parts) > 3:
                try:
                    ep_name = unquote(parts[3])
                except Exception:
                    ep_name = ''

            if not ep_name:
                ep_name = '第%s集' % ep_idx
            self._cur_ep = ep_name

            data = self._api('vodParse', {
                'vod_id': vid,
                'player_source_id': psid,
                'episode_index': ep_idx,
            })

            if data and data.get('play_url'):
                result['parse'] = 1 if data['play_url'].startswith('http') else 0
                result['url'] = data['play_url']
                result['header'] = self.play_header

                # ===== 搜索弹幕 =====
                try:
                    dm = search_danmaku(self.danmaku_api,
                                        self._cur_vod, ep_name)
                    if dm:
                        result['danmaku'] = dm
                except Exception as e:
                    print('[danmaku] attach failed: %s' % e)

            return result
        except Exception as e:
            print('Error in playerContent: %s' % e)
            return result

    # -------------------------------------------------------------- #
    # 其他
    # -------------------------------------------------------------- #
    def fetch(self, url):
        try:
            r = requests.get(url, headers=self.header,
                             timeout=self.timeout, verify=False)
            r.encoding = 'utf-8'
            return r.text if r.status_code == 200 else None
        except Exception as e:
            print('Error fetching %s: %s' % (url, e))
            return None

    def get_id_from_href(self, href):
        if not href:
            return href
        m = re.search(r'[?&]id=(\d+)', href)
        if m:
            return m.group(1)
        m = re.search(r'/id/(\d+)', href)
        if m:
            return m.group(1)
        return href


# ------------------------------------------------------------------ #
# 本地测试
# ------------------------------------------------------------------ #
if __name__ == '__main__':
    s = Spider()
    s.init('')
    print('name:', s.getName())
    print('host:', s.host)
    print('danmaku api:', s.danmaku_api)
    # 测试弹幕 API
    dm = search_danmaku(s.danmaku_api, '庆余年', '第1集')
    print('danmaku found:', len(dm))
    if dm:
        print('first:', dm[0])
