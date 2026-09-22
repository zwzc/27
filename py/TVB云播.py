# -*- coding: utf-8 -*-
# by @Qist
"""
TVB云播 / HKTV影视
含广告过滤（线路名 / 集数名 / 标题 / m3u8 内插）
"""
import re
import json
import base64
import zlib
import random
import requests
import urllib.parse
from Crypto.Cipher import AES
from base.spider import Spider  # 继承基础Spider类

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass


# ------------------------------------------------------------------ #
# 响应解密（AES-128-CBC + gzip），key/iv 来自 libnmmp.so
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


# 线路名 -> 中文显示名（源站返回的是英文/拼音缩写）
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
    """线路名转中文显示；未知线路保留原名。"""
    return _LINE_CN.get(name, name)


# ------------------------------------------------------------------ #
# 广告过滤
# ------------------------------------------------------------------ #
# 广告关键词（赌场 + 色情 + 常见推广）
_AD_PATTERN = re.compile(
    r'澳门|澳門|新葡京|葡京|威尼斯人|银河|金沙|皇冠|赌场|賭場|博彩|六合彩'
    r'|时时彩|时时彩|彩票|棋牌|美女荷官|裸聊|成人|AV在线|福利'
    r'|哥哥快来|新片首发|UUE29|约炮|上门|包养|外围|在线看片'
    r'|免费观看|点击进入|加微信|加QQ|复制链接|下载APP',
    re.I
)


def _is_ad(text):
    """判断文本是否含广告关键词。"""
    return bool(_AD_PATTERN.search(str(text or '')))


def _clean_ad_text(text):
    """清洗标题/简介里的广告词。"""
    if not text:
        return ''
    s = str(text)
    s = re.sub(r'澳门.{0,10}(赌场|博彩|皇冠|新葡京|葡京|威尼斯人|银河|金沙)', '', s, flags=re.I)
    s = re.sub(r'(赌场|博彩|六合彩|时时彩|美女荷官|裸聊|成人|AV在线|约炮|外围|包养).{0,10}', '', s, flags=re.I)
    s = re.sub(r'【[^】]*广告[^】]*】', '', s)
    s = re.sub(r'\[[^\]]*广告[^\]]*\]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _strip_ad_blocks(m3u8_text):
    """
    去掉 m3u8 里被 #EXT-X-DISCONTINUITY 包裹的短广告段。
    判定条件（满足任一即视为广告）：
      1. 段内 ts 分片 <= 3
      2. 段内有 METHOD=NONE 突变
      3. 段内总时长 < 30 秒
    """
    if not m3u8_text or '#EXTM3U' not in m3u8_text:
        return m3u8_text
    lines = m3u8_text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('#EXT-X-DISCONTINUITY'):
            # 找到下一个 DISCONTINUITY 或结尾
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('#EXT-X-DISCONTINUITY'):
                j += 1
            # 分析这段
            seg_count = 0
            total_dur = 0.0
            has_none = False
            for k in range(i + 1, j):
                l = lines[k].strip()
                if l.startswith('#EXT-X-KEY:METHOD=NONE'):
                    has_none = True
                m = re.match(r'^#EXTINF:([\d.]+)', l)
                if m:
                    try:
                        total_dur += float(m.group(1))
                    except Exception:
                        pass
                if l and not l.startswith('#') and '.ts' in l:
                    seg_count += 1
            # 判定为广告则跳过整段
            if seg_count == 0:
                i = j
                continue
            if seg_count <= 3 or has_none or total_dur < 30:
                i = j
                continue
        out.append(line)
        i += 1
    return '\n'.join(out)


# 随机机型池：观看端一般是电视盒 / 手机，混合使用以模拟真实 UA。
_DEVICE_MODELS = [
    # 电视盒
    'ZXV10S100V7', 'MIBOX4', 'MIBOX3', 'ADT-2', 'ADT-3',
    'HWVTR-H', 'EC6108V9', 'Q21A', 'B860H', 'S905X3',
    'FiberHome-HG680', 'ZTE-B860AV2.1', 'Skyworth-E900V21E',
    # 手机
    'SM-S918B', 'SM-G998B', 'SM-S901B', 'Pixel-7', 'Pixel-8-Pro',
    '2201123G', 'M2012K11AG', 'PHK110', 'PAHM00', 'RMX3370',
]


def _rand_device_model():
    """随机选一个机型，模拟电视盒 / 手机观看端。"""
    return random.choice(_DEVICE_MODELS)


class Spider(Spider):
    def getName(self):
        return 'HKTV影视'

    def init(self, extend=""):
        if extend and extend.strip():
            self.host = extend.strip().rstrip('/')
        return self.host

    def __init__(self):
        self.name = 'HKTV影视'
        self.host = 'http://app.tuxianimg.com'
        self.timeout = 25
        # 随机机型（电视盒 / 手机混合），每台实例固定一次，模拟真实观看端 UA。
        self.device_model = _rand_device_model()
        # 注：Host / Content-Length 由 requests 按 URL 与 body 自动生成，不在此手动设置。
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
        # 由 playerContent 作为“全局播放 header”返回，框架会透传到所有直链请求。
        # 注：host 字段由 requests/框架按 URL 自动生成，不在此手动设置（否则跨域名会错）。
        self.play_header = {
            'User-Agent': f'Dalvik/2.1.0 (Linux; U; Android 15; {self.device_model} Build/b5cc949.1)',
            'accept-encoding': 'gzip',
            'allowcrossprotocolredirects': 'true',
            'connection': 'Keep-Alive',
        }
        # 运行时由 init 接口填充
        self.class_names = []
        self.class_urls = []
        self.type_extend = {}   # type_id -> {class/area/lang/year/sort 选项}

    # ------------------------------------------------------------------ #
    # 内部：统一 API 请求 + 解密
    # ------------------------------------------------------------------ #
    def _api(self, endpoint, params=None):
        url = f"{self.host}/api/vod/{endpoint}"
        try:
            resp = requests.post(url, data=params or {}, headers=self.header,
                                 timeout=self.timeout, verify=False)
            resp.encoding = 'utf-8'
            if resp.status_code != 200:
                print(f"[hktv] {endpoint} HTTP {resp.status_code}")
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
            print(f"[hktv] request {endpoint} failed: {e}")
            return None

    @staticmethod
    def _pic(pic):
        if not pic:
            return ''
        return pic if pic.startswith('http') else pic

    @staticmethod
    def _vod_item(v):
        pic = v.get('vod_pic') or v.get('vod_pic_slide') or ''
        return {
            'vod_id': str(v.get('vod_id', '') or ''),
            'vod_name': _clean_ad_text(v.get('vod_name', '') or ''),
            'vod_pic': Spider._pic(pic),
            'vod_remarks': _clean_ad_text(v.get('vod_remarks', '') or ''),
        }

    # ------------------------------------------------------------------ #
    # 框架接口
    # ------------------------------------------------------------------ #
    def homeContent(self, filter):
        try:
            result = {'class': [], 'list': []}
            init = self._api('init')
            if init:
                # 分类
                for c in init.get('type_list', []):
                    tid = str(c.get('type_id', ''))
                    tname = c.get('type_name', '')
                    if not tid or not tname:
                        continue
                    if tid == '0' and tname == '全部':
                        continue  # 跳过“全部”虚拟项
                    self.class_names.append(tname)
                    self.class_urls.append(tid)
                    # 解析筛选维度
                    ext = c.get('type_extend', '')
                    if ext:
                        try:
                            self.type_extend[tid] = json.loads(ext)
                        except Exception:
                            pass
                # 首页推荐
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
            print(f"Error in homeContent: {e}")
            import traceback
            traceback.print_exc()
            return {'class': [], 'list': []}

    def get_filter_data(self, tid):
        """
        筛选维度来自 init 的 type_extend（真实数据）；无则用预定义兜底。
        维度：class(类型)/area(地区)/lang(语言)/year(年份)/sort(排序)
        """
        try:
            ext = self.type_extend.get(str(tid))
            if ext:
                out = []
                label_map = {'class': '类型', 'area': '地区', 'lang': '语言',
                             'year': '年份', 'sort': '排序', 'star': '明星',
                             'director': '导演', 'state': '状态', 'version': '版本'}
                for key, label in label_map.items():
                    vals = ext.get(key)
                    if not vals:
                        continue
                    items = [{'n': '全部', 'v': ''}]
                    for v in vals.split(','):
                        v = v.strip()
                        if v:
                            items.append({'n': v, 'v': v})
                    out.append({'key': key, 'name': label, 'value': items})
                if out:
                    return out
            # 兜底
            return [
                {'key': 'class', 'name': '类型', 'value': [{'n': '全部', 'v': ''}, {'n': '动作', 'v': '动作'}, {'n': '喜剧', 'v': '喜剧'}, {'n': '爱情', 'v': '爱情'}, {'n': '科幻', 'v': '科幻'}, {'n': '剧情', 'v': '剧情'}, {'n': '犯罪', 'v': '犯罪'}, {'n': '奇幻', 'v': '奇幻'}]},
                {'key': 'area', 'name': '地区', 'value': [{'n': '全部', 'v': ''}, {'n': '大陆', 'v': '大陆'}, {'n': '香港', 'v': '香港'}, {'n': '台湾', 'v': '台湾'}, {'n': '美国', 'v': '美国'}, {'n': '日本', 'v': '日本'}, {'n': '韩国', 'v': '韩国'}]},
                {'key': 'lang', 'name': '语言', 'value': [{'n': '全部', 'v': ''}, {'n': '国语', 'v': '国语'}, {'n': '英语', 'v': '英语'}, {'n': '粤语', 'v': '粤语'}]},
                {'key': 'year', 'name': '年份', 'value': [{'n': '全部', 'v': ''}, {'n': '2026', 'v': '2026'}, {'n': '2025', 'v': '2025'}, {'n': '2024', 'v': '2024'}, {'n': '2023', 'v': '2023'}]},
                {'key': 'sort', 'name': '排序', 'value': [{'n': '全部', 'v': ''}, {'n': '时间', 'v': 'time'}, {'n': '人气', 'v': 'hits'}, {'n': '评分', 'v': 'score'}]},
            ]
        except Exception as e:
            print(f"Error in get_filter_data: {e}")
            return []

    def categoryContent(self, tid, pg, filter, extend):
        try:
            params = {'type_id': tid, 'page': pg}
            if extend:
                for key in ('class', 'area', 'lang', 'year', 'sort'):
                    val = extend.get(key)
                    if val:
                        params[key] = val

            data = self._api('typeFilterVodList', params)
            if not data:
                return {'list': [], 'page': int(pg), 'pagecount': 0,
                        'limit': 0, 'total': 0}

            rows = data.get('recommend_list') or []
            videos = [self._vod_item(v) for v in rows
                      if v.get('vod_id') and v.get('vod_name')]

            seen = set()
            uniq = []
            for v in videos:
                if v['vod_id'] not in seen:
                    seen.add(v['vod_id'])
                    uniq.append(v)

            total = data.get('total', len(uniq))
            pagecount = data.get('page_count', data.get('pagecount', 999))
            return {
                'list': uniq,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': len(uniq),
                'total': total,
            }
        except Exception as e:
            print(f"Error in categoryContent: {e}")
            import traceback
            traceback.print_exc()
            return {'list': [], 'page': int(pg), 'pagecount': 0,
                    'limit': 0, 'total': 0}

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

            vod = {
                'vod_id': str(v.get('vod_id', vid)),
                'vod_name': _clean_ad_text(v.get('vod_name', '') or ''),
                'vod_pic': self._pic(v.get('vod_pic') or v.get('vod_pic_slide') or ''),
                'vod_remarks': _clean_ad_text(v.get('vod_remarks', '') or ''),
                'vod_year': v.get('vod_year', '') or '',
                'vod_area': v.get('vod_area', '') or '',
                'vod_actor': _clean_ad_text(v.get('vod_actor', '') or ''),
                'vod_director': _clean_ad_text(v.get('vod_director', '') or ''),
                'vod_content': _clean_ad_text(v.get('vod_content', '') or ''),
            }

            # 线路：from_list 名 + url_list 集（url 在 vodParse 中解密）
            from_list = data.get('vod_play_from_list') or []
            url_list = data.get('vod_play_url_list') or []
            src_list = data.get('player_source_list') or []
            # player_code -> player_source_id
            code2id = {s.get('player_code'): s.get('id') for s in src_list if s.get('player_code')}

            play_from = []
            play_url = []
            for idx, src in enumerate(from_list):
                line_name = _line_cn(src)
                # ===== 过滤广告线路名 =====
                if _is_ad(line_name) or _is_ad(src):
                    continue
                psid = code2id.get(src, '')
                episodes = []
                if idx < len(url_list):
                    for ep in url_list[idx].get('urls', []):
                        ep_name = ep.get('name', '')
                        # ===== 过滤广告集数名 =====
                        if _is_ad(ep_name):
                            continue
                        # 编码: 名称$player_source_id@episode_index@vod_id
                        episodes.append(f"{ep_name}${psid}@{ep.get('episode_index','')}@{vid}")
                if not episodes:
                    continue
                play_from.append(line_name)
                play_url.append('#'.join(episodes))

            vod['vod_play_from'] = '$$$'.join(play_from)
            vod['vod_play_url'] = '$$$'.join(play_url)
            return {'list': [vod]}
        except Exception as e:
            print(f"Error in detailContent: {e}")
            import traceback
            traceback.print_exc()
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            # 真实搜索接口：searchList，参数 keywords / type_id / page
            data = self._api('searchList', {'keywords': key, 'type_id': '0', 'page': pg})
            if not data:
                return {'list': []}
            rows = data.get('search_list') or data.get('recommend_list') or []
            videos = []
            seen = set()
            for v in rows:
                item = self._vod_item(v)
                if item['vod_id'] and item['vod_name'] and item['vod_id'] not in seen:
                    seen.add(item['vod_id'])
                    videos.append(item)
            return {'list': videos}
        except Exception as e:
            print(f"Error in searchContent: {e}")
            import traceback
            traceback.print_exc()
            return {'list': []}

    def searchSuggestions(self, keyword):
        """
        搜索联想（实时补全）。参数 keyword。
        与 searchContent 共用同一套解密；返回建议名称列表。
        """
        try:
            data = self._api('searchSuggestions', {'keyword': keyword})
            if not data:
                return []
            out = []
            for it in data.get('list', []) or []:
                name = it.get('vod_name')
                if name and not _is_ad(name):
                    out.append(name)
            return out
        except Exception as e:
            print(f"Error in searchSuggestions: {e}")
            return []

    def playerContent(self, flag, id, vipFlags):
        """
        detailContent 中每集被编码为 "name$psid@epidx@vodid"，
        框架传入的 id 形态为 "psid@epidx@vodid"（不含名称）。
        经 vodParse 接口用 (vod_id, player_source_id, episode_index) 换取真实 play_url。
        拿到 m3u8 后先做广告段过滤，再返回。
        """
        try:
            if not id or id.count('@') < 2:
                return {'parse': 0, 'url': '', 'header': {}, 'playUrl': ''}
            psid, ep_idx, vid = id.split('@', 2)
            data = self._api('vodParse', {
                'vod_id': vid,
                'player_source_id': psid,
                'episode_index': ep_idx,
            })
            if not data or not data.get('play_url'):
                return {'parse': 0, 'url': '', 'header': {}, 'playUrl': ''}

            url = data['play_url']

            # ===== m3u8 广告段过滤 =====
            if url and '.m3u8' in url.lower():
                try:
                    raw = self.fetch(url)
                    if raw and '#EXTM3U' in raw:
                        fixed = _strip_ad_blocks(raw)
                        if fixed and fixed != raw:
                            # 用 data URI 返回过滤后的 m3u8，避免相对路径问题
                            url = ('data:application/vnd.apple.mpegurl;charset=utf-8,'
                                   + urllib.parse.quote(fixed, safe=''))
                except Exception as ee:
                    print(f"[hktv] m3u8 filter fail: {ee}")

            return {
                'parse': 1 if url.startswith('http') else 0,
                'url': url,
                'header': self.play_header,
                'playUrl': '',
            }
        except Exception as e:
            print(f"Error in playerContent: {e}")
            return {'parse': 0, 'url': '', 'header': {}, 'playUrl': ''}

    def fetch(self, url):
        try:
            response = requests.get(url, headers=self.play_header, timeout=self.timeout,
                                    verify=False)
            response.encoding = 'utf-8'
            return response.text if response.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
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
