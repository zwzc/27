# coding=utf-8
"""
title: 瓜子影视
author: 对照 spider_source/WexAiGuaZi（Java 最快路径）
说明: FongMi/TV · 影视仓 · TVBox Python Spider
Java 快的关键点已对齐:
  1) token/device_key 落盘，下次 refresh 而不是每次 signUp
  2) 多主机并行竞速，谁先通就用谁（o()）
  3) 首页走 /App/IndexList/index，一次出推荐列表
  4) 分类带 sub 默认值（动作片/国产剧等）
ext 可选: { "host": "https://sdapi.e2wu4ht.com", "timeout": 5000 }
"""

import os
import sys
import json
import time
import base64
import hashlib
import random
import string
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Util.Padding import pad, unpad
from Crypto.PublicKey import RSA

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    # 与 WexAiGuaZi 分类 id 一致
    TYPE_MAP = {
        '1': '电影', '2': '电视剧', '3': '动漫', '4': '综艺',
        '64': '短剧', '72': '音乐', '74': 'AI漫剧', '73': '电影解说',
        '71': '体育解说', '70': '电竞解说',
    }
    SUB_DEFAULT = {'1': '5', '2': '12', '3': '30', '4': '22'}
    RESOLUTIONS = ['3840', '2160', '1080', '720', '480', '360', '240']
    DEFAULT_HOSTS = [
        'https://sdapi.e2wu4ht.com',
        'https://apinew.uozvr.com',
        'https://api.w32z7vtd.com',
        'https://api.6a7nnf7.com',
        'https://api.umygrx3.com',
    ]
    PUB_B64 = (
        'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDUM5+/y8sPsWkd1/RQS64X259EUwxFXFE5HlA65Mqr'
        'xnPs0JqoSRojSDy5QhwvROlaD6TwRQHKMY2OAZ6SnQeUJsChTEFIR9qUkwrs3/MVUMxjsv6JS6Oe/juc'
        'lyJGTgVmDhB55EafXsD0SQYVj/QXXsxR6ewR5E2kL52yAAD4yQIDAQAB'
    )
    PRIV_PEM = '''-----BEGIN PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGAe6hKrWLi1zQmjTT1
ozbE4QdFeJGNxubxld6GrFGximxfMsMB6BpJhpcTouAqywAFppiKetUBBbXwYsYU
1wNr648XVmPmCMCy4rY8vdliFnbMUj086DU6Z+/oXBdWU3/b1G0DN3E9wULRSwcK
ZT3wj/cCI1vsCm3gj2R5SqkA9Y0CAwEAAQKBgAJH+4CxV0/zBVcLiBCHvSANm0l7
HetybTh/j2p0Y1sTXro4ALwAaCTUeqdBjWiLSo9lNwDHFyq8zX90+gNxa7c5EqcW
V9FmlVXr8VhfBzcZo1nXeNdXFT7tQ2yah/odtdcx+vRMSGJd1t/5k5bDd9wAvYdI
DblMAg+wiKKZ5KcdAkEA1cCakEN4NexkF5tHPRrR6XOY/XHfkqXxEhMqmNbB9U34
saTJnLWIHC8IXys6Qmzz30TtzCjuOqKRRy+FMM4TdwJBAJQZFPjsGC+RqcG5UvVM
iMPhnwe/bXEehShK86yJK/g/UiKrO87h3aEu5gcJqBygTq3BBBoH2md3pr/W+hUM
WBsCQQChfhTIrdDinKi6lRxrdBnn0Ohjg2cwuqK5zzU9p/N+S9x7Ck8wUI53DKm8
jUJE8WAG7WLj/oCOWEh+ic6NIwTdAkEAj0X8nhx6AXsgCYRql1klbqtVmL8+95KZ
K7PnLWG/IfjQUy3pPGoSaZ7fdquG8bq8oyf5+dzjE/oTXcByS+6XRQJAP/5ciy1b
L3NhUhsaOVy55MHXnPjdcTX0FaLi+ybXZIfIQ2P4rb19mVq1feMbCXhz+L1rG8oa
t5lYKfpe8k83ZA==
-----END PRIVATE KEY-----'''
    DEVICE_OLD_KEY = 'aLFBMWpxBrIDAD1Si/KVvm41'
    SIGN_SUFFIX = '*&zvdvdvddbfikkkumtmdwqppp?|4Y!s!2br'
    AES_REQ_KEY = 'mvXBSW7ekreItNsT'
    AES_REQ_IV = '2U3IrJL8szAKp0Fj'
    STATIC_KEYS = (
        'Qmxi5ciWXbQzkr7o+SUNiUuQxQEf8/AVyUWY4T/BGhcXBIUz4nOyHBGf9A4KbM0iKF3yp9M7WAY0rrs5PzdTAOB45plcS2zZ0w'
        'UibcXuGJ29VVGRWKGwE9zu2vLwhfgjTaaDpXo4rby+7GxXTktzJmxvneOUdYeHi+PZsThlvPI='
    )

    def __init__(self):
        self.name = '瓜子影视'
        self.hosts = list(self.DEFAULT_HOSTS)
        self.host = self.hosts[0]
        self.timeout = 5000
        self.token = ''
        self.token_id = ''
        self.device_key = ''.join(random.choices('0123456789ABCDEF', k=40))
        self.device_id = str(864150060000000 + random.randint(0, 9999))
        self.play_ref = 'http://WJiZxLXA2.com/'
        self._cache = {}
        self._cache_ttl = 180
        self._home_list = []
        self._rsa_pub = RSA.import_key(base64.b64decode(self.PUB_B64))
        self._rsa_priv = RSA.import_key(self.PRIV_PEM)
        self._ready = False
        self._auth_lock = threading.Lock()
        self._auth_file = self._resolve_auth_file()

    def getName(self):
        return self.name

    def init(self, extend=''):
        try:
            preferred = ''
            timeout = 0
            if isinstance(extend, str) and extend.strip():
                txt = extend.strip()
                if txt.startswith('{'):
                    obj = json.loads(txt)
                    preferred = str(obj.get('host') or '').strip()
                    timeout = int(obj.get('timeout') or 0)
                elif txt.startswith('http'):
                    preferred = txt
            elif isinstance(extend, dict):
                preferred = str(extend.get('host') or '').strip()
                timeout = int(extend.get('timeout') or 0)
            if timeout > 0:
                self.timeout = timeout
            if preferred:
                preferred = preferred.rstrip('/')
                if preferred in self.hosts:
                    self.hosts.remove(preferred)
                self.hosts.insert(0, preferred)
                self.host = preferred
            self._load_auth()
            # 对齐 Java init：并行竞速拿到最快主机 + 有效 token
            self._race_auth()
        except Exception as e:
            print('瓜子 init 失败:', e)

    def homeContent(self, filter):
        classes = [
            {'type_name': '电影', 'type_id': '1'},
            {'type_name': '电视剧', 'type_id': '2'},
            {'type_name': '动漫', 'type_id': '3'},
            {'type_name': '综艺', 'type_id': '4'},
            {'type_name': '短剧', 'type_id': '64'},
        ]
        filters = {
            '1': [self._filter('sub', '类型', '动作片:5,悬疑片:29,喜剧片:6,爱情片:7,科幻片:8,恐怖片:9,剧情片:10,战争片:11,动画片:36,纪录片:20,灾难片:38,犯罪片:61')],
            '2': [self._filter('sub', '类型', '国产剧:12,香港剧:13,台湾剧:14,欧美剧:15,日本剧:16,韩国剧:17,海外剧:18,泰国剧:19,新加坡剧:69')],
            '3': [self._filter('sub', '类型', '中国动漫:30,日本动漫:31,欧美动漫:33')],
            '4': [self._filter('sub', '类型', '大陆综艺:22,港台综艺:23,日韩综艺:24,欧美综艺:25')],
        }
        for tid in ('1', '2', '3', '4', '64'):
            extra = [
                self._filter('area', '地区', '全部:0,大陆:大陆,香港:香港,台湾:台湾,美国:美国,韩国:韩国,日本:日本,英国:英国,法国:法国,泰国:泰国,印度:印度,其他:其他'),
                self._filter('year', '年份', '全部:0,' + ','.join('%s:%s' % (y, y) for y in range(2026, 2004, -1)) + ',更早:2004'),
                self._filter('sort', '排序', '最新:d_id,最热:d_hits,推荐:d_score'),
            ]
            filters.setdefault(tid, [])
            filters[tid].extend(extra)

        videos = []
        try:
            self._ensure_auth()
            data = self.get_data(
                {'ns': '', 'nt': str(int(time.time())), 'pid': '1'},
                '/App/IndexList/index',
                use_cache=True,
            )
            videos = self._map_index(data)
            self._home_list = videos
        except Exception as e:
            print('瓜子首页推荐失败:', e)
            videos = list(self._home_list)

        return {'class': classes, 'filters': filters, 'list': videos}

    def homeVideoContent(self):
        if self._home_list:
            return {'list': self._home_list}
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        extend = self._parse_extend(extend)
        try:
            tid = str(tid)
            sub = extend.get('sub') or self.SUB_DEFAULT.get(tid, '')
            body = {
                'area': extend.get('area', '0') or '0',
                'sub': sub,
                'year': extend.get('year', '0') or '0',
                'pageSize': '30',
                'sort': extend.get('sort', 'd_id') or 'd_id',
                'page': str(pg or 1),
                'tid': tid,
            }
            data = self.get_data(body, '/App/IndexList/indexList')
            videos = self._map_list(data)
        except Exception as e:
            print('瓜子分类失败:', e)
            videos = []
        page = int(pg or 1)
        return {
            'list': videos,
            'page': page,
            'pagecount': page + 1 if len(videos) >= 30 else page,
            'limit': 30,
            'total': 999999,
        }

    def detailContent(self, ids):
        try:
            self._ensure_auth()
            vod_id = str(ids[0]).split('/')[0]
            t = str(int(time.time()))
            body_info = {
                'token_id': str(self.token_id or ''),
                'vod_id': vod_id,
                'mobile_time': t,
                'token': self.token,
            }
            body_vurl = {'vurl_cloud_id': '2', 'vod_d_id': vod_id}
            with ThreadPoolExecutor(max_workers=2) as pool:
                f1 = pool.submit(self.get_data, body_info, '/App/IndexPlay/playInfo', False)
                f2 = pool.submit(self.get_data, body_vurl, '/App/Resource/Vurl/show', False)
                qdata = f1.result()
                jdata = f2.result()
            if not qdata or 'vodInfo' not in qdata:
                return {'list': []}
            vod = qdata['vodInfo']
            play_list = []
            for index, item in enumerate((jdata or {}).get('list') or []):
                play = item.get('play') or {}
                names = []
                param = ''
                for res in self.RESOLUTIONS:
                    node = play.get(res) or {}
                    if str(node.get('show_type')) == '2':
                        continue
                    p = (node.get('param') or '').strip()
                    if not p:
                        continue
                    names.append(res)
                    if not param:
                        param = p
                if not param:
                    continue
                title = (item.get('title') or '').strip() or ('第%s集' % (index + 1))
                play_list.append('%s$%s||%s' % (title, param, '@'.join(names)))

            tid = str(vod.get('t_id') or vod.get('vod_category') or '')
            year = str(vod.get('vod_year') or '')
            if len(year) > 4 and year[:4].isdigit():
                year = year[:4]
            score = str(vod.get('vod_scroe') or vod.get('vod_score') or '').strip()
            remarks = score if score and score != '0' else str(vod.get('vod_continu') or '')
            return {
                'list': [{
                    'vod_id': vod_id,
                    'vod_name': vod.get('vod_name', ''),
                    'vod_pic': vod.get('vod_pic', ''),
                    'vod_year': year,
                    'vod_area': vod.get('vod_area', ''),
                    'type_name': self.TYPE_MAP.get(tid, ''),
                    'vod_remarks': remarks,
                    'vod_actor': vod.get('vod_actor', ''),
                    'vod_director': vod.get('vod_director', ''),
                    'vod_content': (vod.get('vod_use_content') or '').strip(),
                    'vod_play_from': '瓜子',
                    'vod_play_url': '#'.join(play_list),
                }]
            }
        except Exception as e:
            print('瓜子详情失败:', e)
            return {'list': []}

    def searchContent(self, key, quick, pg=1):
        try:
            data = self.get_data(
                {'keywords': key, 'order_val': '1', 'page': str(pg or 1)},
                '/App/Index/findMoreVod',
                use_cache=False,
            )
            return {'list': self._map_list(data), 'page': int(pg or 1), 'limit': 30, 'total': 999999}
        except Exception as e:
            print('瓜子搜索失败:', e)
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            parts = str(id).split('||')
            param_str = parts[0]
            resolutions = parts[1].split('@') if len(parts) > 1 and parts[1] else []
            params = {}
            for pair in param_str.split('&'):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    params[k] = v
            if 'vod_d_id' in params:
                params['vod_id'] = params.pop('vod_d_id')
            if resolutions:
                resolutions = sorted(
                    [r for r in resolutions if str(r).isdigit()],
                    key=lambda x: int(x), reverse=True,
                )
                if resolutions:
                    params['resolution'] = resolutions[0]
            if not params.get('resolution'):
                params['resolution'] = '1080'
            params['type'] = 'play'
            params['_client_ts'] = str(time.time_ns())
            params['mobile_time'] = str(int(time.time()))
            params['rand'] = str(abs(random.randint(0, 10 ** 9)))

            data = self.get_data(params, '/App/Resource/VurlDetail/showOne', use_cache=False)
            url = (data or {}).get('url') or ''
            if url and ('wanglaoshi' in url or 'xn--fiqs8s' in url):
                self._race_auth(force=True)
                params['_client_ts'] = str(time.time_ns())
                params['mobile_time'] = str(int(time.time()))
                params['rand'] = str(abs(random.randint(0, 10 ** 9)))
                data = self.get_data(params, '/App/Resource/VurlDetail/showOne', use_cache=False)
                url = (data or {}).get('url') or url
            return {
                'parse': 0,
                'jx': 0,
                'url': url,
                'header': {'User-Agent': 'Lavf/57.83.100', 'Referer': self.play_ref},
            }
        except Exception as e:
            print('瓜子播放失败:', e)
            return {'parse': 0, 'jx': 0, 'url': ''}

    def isVideoFormat(self, url):
        u = (url or '').lower()
        return any(x in u for x in ['.m3u8', '.mp4', '.flv', '.ts'])

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        return None

    # ---------- Java 对齐：鉴权 / 竞速 / 持久化 ----------

    def _resolve_auth_file(self):
        candidates = []
        try:
            candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.csp_gzys_auth.json'))
        except Exception:
            pass
        for d in ('/sdcard/tvbox', '/sdcard/Download', '/data/data/com.fongmi.android.tv/cache', os.path.expanduser('~')):
            candidates.append(os.path.join(d, '.csp_gzys_auth.json'))
        for p in candidates:
            try:
                folder = os.path.dirname(p)
                if folder and not os.path.isdir(folder):
                    continue
                # 可写探测
                with open(p, 'a', encoding='utf-8'):
                    pass
                return p
            except Exception:
                continue
        return candidates[0] if candidates else '.csp_gzys_auth.json'

    def _load_auth(self):
        try:
            if not self._auth_file or not os.path.isfile(self._auth_file):
                return
            with open(self._auth_file, 'r', encoding='utf-8') as f:
                obj = json.load(f)
            self.token = obj.get('token') or ''
            self.token_id = str(obj.get('token_id') or '')
            dk = obj.get('device_key') or ''
            if dk:
                self.device_key = dk
            host = obj.get('host') or ''
            if host:
                self.host = host.rstrip('/')
                if self.host in self.hosts:
                    self.hosts.remove(self.host)
                self.hosts.insert(0, self.host)
            if self.token:
                self._ready = True
        except Exception:
            pass

    def _save_auth(self):
        try:
            obj = {
                'token': self.token,
                'token_id': self.token_id,
                'device_key': self.device_key,
                'host': self.host,
                'ts': int(time.time()),
            }
            folder = os.path.dirname(self._auth_file)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
            with open(self._auth_file, 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False)
        except Exception as e:
            print('瓜子保存鉴权失败:', e)

    def _apply_auth(self, result, host=None):
        if not result:
            raise Exception('认证空响应')
        token = result.get('token') or ''
        if not token:
            raise Exception('认证无 token')
        self.token = token
        tid = result.get('app_user_id') or result.get('token_id') or ''
        if tid:
            self.token_id = str(tid)
        if host:
            self.host = host
            if host in self.hosts:
                self.hosts.remove(host)
            self.hosts.insert(0, host)
        self._ready = True
        self._save_auth()

    def _auth_once(self, host):
        """单主机：有 token 先 refresh，失败再 signIn/signUp（同 Java o()）。"""
        t0 = time.time()
        if self.token:
            try:
                data = self._post_raw(
                    '/App/Authentication/Authenticator/refresh',
                    self._build_body({}, token=self.token, dynamic=True),
                    host,
                )
                return host, data, int((time.time() - t0) * 1000)
            except Exception:
                pass
            try:
                data = self._post_raw(
                    '/App/Authentication/Device/signIn',
                    self._build_body(
                        {'new_key': self.device_key, 'old_key': self.DEVICE_OLD_KEY},
                        token='', dynamic=True,
                    ),
                    host,
                )
                return host, data, int((time.time() - t0) * 1000)
            except Exception:
                pass
        data = self._post_raw(
            '/App/Authentication/Device/signUp',
            self._build_body(
                {
                    'new_key': self.device_key,
                    'old_key': self.DEVICE_OLD_KEY,
                    'phone_type': 1,
                    'code': '',
                },
                token='', dynamic=True,
            ),
            host,
        )
        return host, data, int((time.time() - t0) * 1000)

    def _race_auth(self, force=False):
        """对齐 Java o()：最多 4 路并行，先通先用，其余取消。"""
        with self._auth_lock:
            if self.token and self._ready and not force:
                # 已有落盘 token：只对当前主机 refresh 一次，失败再竞速
                try:
                    host, data, ms = self._auth_once(self.host)
                    self._apply_auth(data, host)
                    print('瓜子鉴权(快路径)', host, ms, 'ms')
                    return
                except Exception:
                    self._ready = False

            hosts = list(dict.fromkeys(self.hosts))[:4]
            last = None
            with ThreadPoolExecutor(max_workers=len(hosts) or 1) as pool:
                futs = [pool.submit(self._auth_once, h) for h in hosts]
                try:
                    done, not_done = wait(futs, timeout=max(3.0, self.timeout / 1000.0), return_when=FIRST_COMPLETED)
                    # 继续等到第一个真正成功
                    pending = set(futs)
                    deadline = time.time() + max(3.0, self.timeout / 1000.0)
                    while pending and time.time() < deadline:
                        done, pending = wait(pending, timeout=max(0.05, deadline - time.time()), return_when=FIRST_COMPLETED)
                        for fut in done:
                            try:
                                host, data, ms = fut.result()
                                if data and data.get('token'):
                                    self._apply_auth(data, host)
                                    for x in pending:
                                        x.cancel()
                                    print('瓜子鉴权(竞速)', host, ms, 'ms')
                                    return
                            except Exception as e:
                                last = e
                finally:
                    for fut in futs:
                        if not fut.done():
                            fut.cancel()
            if last:
                raise last
            raise Exception('瓜子鉴权失败')

    def _ensure_auth(self, force=False):
        if self.token and self._ready and not force:
            return
        self._race_auth(force=force)

    # ---------- 请求 / 加解密 ----------

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            txt = extend.strip()
            if not txt:
                return {}
            try:
                obj = json.loads(txt)
                return obj if isinstance(obj, dict) else {}
            except Exception:
                return {}
        return {}

    def _filter(self, key, name, pairs):
        values = []
        for part in pairs.split(','):
            if ':' not in part:
                continue
            n, v = part.split(':', 1)
            values.append({'n': n, 'v': v})
        return {'key': key, 'name': name, 'value': values}

    def _map_list(self, data):
        videos = []
        for item in (data or {}).get('list') or []:
            if not isinstance(item, dict):
                continue
            if not item.get('vod_id'):
                continue
            cont = item.get('vod_continu', 0)
            try:
                cont_n = int(cont)
            except Exception:
                cont_n = 0
            score = str(item.get('vod_scroe') or item.get('vod_score') or '').strip()
            if score and score not in ('0', '0.0'):
                remarks = score
            else:
                remarks = '电影' if cont_n == 0 else ('更新至%s集' % cont)
            videos.append({
                'vod_id': str(item.get('vod_id', '')),
                'vod_name': item.get('vod_name', ''),
                'vod_pic': item.get('vod_pic', ''),
                'vod_remarks': remarks,
            })
        return videos

    def _map_index(self, data):
        # 对齐 Java：从 list[1..] 汇总各分区影片
        videos = []
        sections = (data or {}).get('list') or []
        for i, sec in enumerate(sections):
            if i == 0 or not isinstance(sec, dict):
                continue
            videos.extend(self._map_list({'list': sec.get('list') or []}))
        return videos

    def _rand16(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def aes_encrypt(self, text, key, iv):
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        return cipher.encrypt(pad(text.encode('utf-8'), AES.block_size)).hex().upper()

    def aes_decrypt(self, text, key, iv):
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        return unpad(cipher.decrypt(bytes.fromhex(text)), AES.block_size).decode('utf-8')

    def rsa_encrypt(self, text):
        cipher = PKCS1_v1_5.new(self._rsa_pub)
        return base64.b64encode(cipher.encrypt(text.encode('utf-8'))).decode('utf-8')

    def rsa_decrypt(self, encrypted_data):
        cipher = PKCS1_v1_5.new(self._rsa_priv)
        raw = base64.b64decode(encrypted_data)
        out = b''
        for i in range(0, len(raw), 128):
            chunk = cipher.decrypt(raw[i:i + 128], None)
            if chunk is None:
                return ''
            out += chunk
        return out.decode('utf-8')

    def _build_body(self, data_obj, token=None, dynamic=False):
        if token is None:
            token = self.token or ''
        if dynamic:
            aesk, aesiv = self._rand16(), self._rand16()
            request_key = self.aes_encrypt(
                json.dumps(data_obj, ensure_ascii=False, separators=(',', ':')),
                aesk, aesiv,
            )
            keys = self.rsa_encrypt(json.dumps({'iv': aesiv, 'key': aesk}, separators=(',', ':')))
            sig_upper = True
        else:
            request_key = self.aes_encrypt(
                json.dumps(data_obj, ensure_ascii=False, separators=(',', ':')),
                self.AES_REQ_KEY, self.AES_REQ_IV,
            )
            keys = self.STATIC_KEYS
            sig_upper = False
        t = str(int(time.time()))
        sign_str = (
            'token_id=,token=%s,phone_type=1,request_key=%s,app_id=1,time=%s,keys=%s%s'
            % (token, request_key, t, keys, self.SIGN_SUFFIX)
        )
        signature = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        if sig_upper:
            signature = signature.upper()
        return {
            'token': token,
            'token_id': '',
            'phone_type': '1',
            'time': t,
            'phone_model': 'xiaomi-22081212c',
            'keys': keys,
            'request_key': request_key,
            'signature': signature,
            'app_id': '1',
            'ad_version': '1',
        }

    def _headers(self, host=None):
        host = host or self.host
        return {
            'User-Agent': 'okhttp/3.12.0',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Ver': '3.0.4.8',
            'Version': '2606029',
            'api-ver': '3.0.4.8',
            'PackageName': 'com.v54f07a912.t4ee50f184.dbb1e7669f20260721',
            'code': 'GZ0313',
            'deviceId': self.device_id,
            'lang': 'zh_cn',
            'Cache-Control': 'no-cache',
            'Referer': host,
        }

    def get_data(self, data, path, use_cache=True):
        cache_key = '%s_%s' % (path, json.dumps(data, ensure_ascii=False, sort_keys=True))
        now = time.time()
        if use_cache and cache_key in self._cache:
            cached, ts = self._cache[cache_key]
            if now - ts < self._cache_ttl:
                return cached

        self._ensure_auth()
        last_err = None
        for host in list(dict.fromkeys([self.host] + self.hosts))[:2]:
            try:
                body = self._build_body(data, token=self.token, dynamic=False)
                result = self._post_raw(path, body, host)
                self.host = host
                if use_cache:
                    self._cache[cache_key] = (result, time.time())
                return result
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if 'token' in msg or '401' in msg or '403' in msg or '业务错误' in msg:
                    try:
                        self._race_auth(force=True)
                    except Exception:
                        pass
                continue
        if last_err:
            raise last_err
        return None

    def _post_raw(self, path, body, host=None):
        host = host or self.host
        url = host + path
        headers = self._headers(host)
        timeout_s = max(2.5, min(5.0, self.timeout / 1000.0))
        req = urllib.request.Request(
            url,
            data=urllib.parse.urlencode(body).encode('utf-8'),
            headers=headers,
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        if isinstance(raw, dict) and raw.get('code', 200) not in (200, '200', None):
            raise Exception('业务错误 code=%s path=%s' % (raw.get('code'), path))
        data_response = (raw or {}).get('data')
        if not data_response:
            raise Exception('无 data')
        bodyki = json.loads(self.rsa_decrypt(data_response['keys']))
        decrypted = self.aes_decrypt(data_response['response_key'], bodyki['key'], bodyki['iv'])
        return json.loads(decrypted)
