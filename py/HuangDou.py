# -*- coding: utf-8 -*-
# 黄果短剧 融合优化版
# 修复问题：前面几个分类（精选推荐、最近上新等）出不了内容
# 优化重点：
#   1. 修正 recommend、newest 及各分类的访问路径与参数格式
#   2. 增强卡片选择器容错（支持更多标签结构，避免因 class 微调导致完全匹配失败）
#   3. 为前置空分类增加多模式降级与首页模块提取

import sys
import re
import json
import base64
import threading
import html as htmllib
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.path.append('..')
try:
    from base.spider import Spider
except ImportError:
    class Spider:
        pass

try:
    import requests as rq
    rq.packages.urllib3.disable_warnings()
except Exception:
    pass

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from Crypto.Cipher import AES
except ImportError:
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        AES = None

# ---------- 常量 ----------
HOSTS = [
    "https://huangguoai.com",
    "https://ttvoij.ediayikma.cc",
    "https://thu.ediayikma.cc",
    "https://pku.ediayikma.cc",
    "https://fdu.ediayikma.cc",
    "https://thu.agdkczeyx.cc",
]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
TIMEOUT = 15
PAGE_SIZE = 24
_AES_KEY = b'f5d965df75336270'
_AES_IV = b'97b60394abc2fbe1'
_PLACEHOLDER_GIF = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
_PROXY_PORT = [0]
_TAG_RE = re.compile(r'<[^>]+>')


def _clean(s):
    if not s:
        return ""
    s = htmllib.unescape(str(s))
    s = _TAG_RE.sub(' ', s)
    return re.sub(r'\s+', ' ', s).strip()


# ---------- 本地图片代理服务器 ----------
try:
    from http.server import BaseHTTPRequestHandler, HTTPServer

    def _fetch_img_raw(u, referer):
        headers = {"User-Agent": UA, "Referer": referer, "Accept": "image/*"}
        try:
            rr = rq.get(u, headers=headers, timeout=12, verify=False, allow_redirects=True)
            if rr.status_code == 200 and rr.content and len(rr.content) > 50:
                return rr.content
        except Exception:
            pass
        return b''

    def _decrypt_img(data):
        if not data or AES is None:
            return data
        if data[:3] == b'\xff\xd8\xff' or data[:8] == b'\x89PNG\r\n\x1a\n' \
                or data[:6] in (b'GIF87a', b'GIF89a') \
                or (data[:4] == b'RIFF' and data[8:12] == b'WEBP'):
            return data
        try:
            dec = AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV).decrypt(data)
            pad = dec[-1]
            if 1 <= pad <= 16 and all(b == pad for b in dec[-pad:]):
                dec = dec[:-pad]
            else:
                dec = dec.rstrip(b'\x00')
            return dec
        except Exception:
            return data

    def _detect_mime(data):
        if data[:3] == b'\xff\xd8\xff':
            return 'image/jpeg'
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        if data[:6] in (b'GIF87a', b'GIF89a'):
            return 'image/gif'
        if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return 'image/webp'
        return 'image/jpeg'

    class _ImgHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                pr = urllib.parse.urlparse(self.path)
                if pr.path not in ('/img', '/proxy'):
                    self.send_response(404)
                    self.end_headers()
                    return
                q = urllib.parse.parse_qs(pr.query)
                u = q.get('u', q.get('url', ['']))[0]
                u = urllib.parse.unquote(u)
                if not u.startswith('http'):
                    self.send_response(400)
                    self.end_headers()
                    return
                raw = _fetch_img_raw(u, HOSTS[0] + "/")
                data = _decrypt_img(raw) if raw else b''
                if not data or len(data) < 50:
                    data, ctype = _PLACEHOLDER_GIF, 'image/gif'
                else:
                    ctype = _detect_mime(data)
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'max-age=86400')
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                pass

        def log_message(self, *args):
            pass

    def _start_proxy_server():
        if _PROXY_PORT[0]:
            return _PROXY_PORT[0]
        for port in [9978] + list(range(9979, 10000)):
            try:
                srv = HTTPServer(('127.0.0.1', port), _ImgHandler)
                _PROXY_PORT[0] = port
                threading.Thread(target=srv.serve_forever, daemon=True).start()
                return port
            except Exception:
                continue
        return 0
except Exception:
    def _start_proxy_server():
        return 0
    def _decrypt_img(data):
        return data
    def _detect_mime(data):
        return 'image/jpeg'


class Spider(Spider):

    def getName(self):
        return "黄果短剧"

    def init(self, extend=""):
        self.host = HOSTS[0].rstrip('/')
        try:
            self.host = self._pick_host()
        except Exception:
            pass
        try:
            self.s = rq.Session()
            self.s.verify = False
            self.s.headers.update({
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": self.host + "/",
            })
        except Exception:
            self.s = None
        try:
            _start_proxy_server()
        except Exception:
            pass

    def _pick_host(self):
        """并发快速探测主站可用性"""
        def check(h):
            try:
                r = rq.get(h, headers={"User-Agent": UA}, timeout=3, verify=False)
                if r.status_code == 200 and ('黄果' in r.text or 'huangguo' in r.text.lower() or len(r.text) > 1500):
                    return h.rstrip('/')
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=len(HOSTS)) as executor:
            results = executor.map(check, HOSTS)
            for res in results:
                if res:
                    return res
        return HOSTS[0].rstrip('/')

    def _safe_host(self):
        h = getattr(self, 'host', None)
        if h and isinstance(h, str) and h.startswith('http'):
            return h.rstrip('/')
        return HOSTS[0].rstrip('/')

    def _wrap_pic(self, url):
        if not url or not str(url).startswith('http'):
            return url or ""
        if not _PROXY_PORT[0]:
            _start_proxy_server()
        if _PROXY_PORT[0]:
            return f"http://127.0.0.1:{_PROXY_PORT[0]}/proxy?url={urllib.parse.quote(url, safe='')}"
        try:
            b = base64.b64encode(url.encode('utf-8')).decode('ascii')
            return f"proxy://type=pic&url={b}"
        except Exception:
            return url

    def _get(self, path, ref="/"):
        host = self._safe_host()
        url = host + path if path.startswith('/') else path
        try:
            headers = {"User-Agent": UA, "Referer": host + (ref if ref.startswith('/') else '/' + ref)}
            if getattr(self, 's', None) is not None:
                r = self.s.get(url, timeout=TIMEOUT, allow_redirects=True, headers=headers)
            else:
                r = rq.get(url, timeout=TIMEOUT, verify=False, headers=headers)
            if r.status_code == 200 and r.text:
                r.encoding = 'utf-8'
                return r.text
        except Exception:
            pass
        return ""

    def isVideoFormat(self, url):
        return any(x in (url or '') for x in ['.m3u8', '.mp4', '.flv', '.mkv', '.avi'])

    def manualVideoCheck(self):
        return False

    # ---------- 首页 ----------
    def homeContent(self, filter=False):
        result = {
            "class": [
                {"type_id": "recommend", "type_name": "精选推荐"},
                {"type_id": "newest", "type_name": "最近上新"},
                {"type_id": "ai-duanju", "type_name": "AI成人短剧"},
                {"type_id": "ai-manju", "type_name": "AI成人漫剧"},
                {"type_id": "ai-huanlian", "type_name": "AI换脸"},
                {"type_id": "ai-mogai", "type_name": "AI魔改"},
                {"type_id": "topic", "type_name": "📌专题"},
                {"type_id": "ranks", "type_name": "排行榜"},
                {"type_id": "chigua", "type_name": "黄果吃瓜"},
                {"type_id": "author", "type_name": "黄果官方"},
            ],
            "list": [],
            "filters": {
                "ranks": [{"key": "类型", "name": "类型", "value": [
                    {"n": "热播榜", "v": "hot"},
                    {"n": "推荐榜", "v": "recommend"},
                    {"n": "潜力榜", "v": "potential"},
                ]}],
                "chigua": [{"key": "类型", "name": "类型", "value": [
                    {"n": "全部", "v": "page"},
                    {"n": "热门吃瓜", "v": "remen"},
                    {"n": "AI原创", "v": "yuanchuang"},
                ]}],
                "author": [{"key": "类型", "name": "类型", "value": [
                    {"n": "黄果官方", "v": "156291"},
                    {"n": "黄果ai大师", "v": "156305"},
                ]}],
            }
        }
        try:
            html = self._get("/")
            if html:
                result["list"] = self._parse_list(html)[:PAGE_SIZE]
        except Exception:
            pass
        return result

    def homeVideoContent(self):
        try:
            html = self._get("/")
            return {"list": self._parse_list(html)[:PAGE_SIZE]}
        except Exception:
            return {"list": []}

    # ---------- 分类核心修复 ----------
    def categoryContent(self, tid, pg=1, filter=False, extend=""):
        try:
            pg = int(str(pg or 1))
        except Exception:
            pg = 1
        if pg < 1:
            pg = 1
        cid = str(tid or "").strip().strip("/")
        ext = extend if isinstance(extend, dict) else {}
        rc = ext.get("类型", cid)

        videos, pages, total = [], 9999, 0
        try:
            # 1. 专题
            if cid.startswith("dir_topic_"):
                slug = cid.replace("dir_topic_", "")
                html = self._get(f"/topics/{slug}/?page={pg}")
                videos = self._parse_list(html, mode="drama")
                return self._result(videos, pg, 9999)

            # 2. 精选推荐（首个出不来：优先尝试 API，再尝试多重 URL 结构）
            if cid == "recommend":
                videos, pages, total = self._category_api("recommend", pg)
                if not videos:
                    # 尝试多种站点常见路由
                    urls = [f"/recommend/{pg}/", f"/recommend/?page={pg}", f"/hot/{pg}/", "/"]
                    for u in urls:
                        html = self._get(u)
                        videos = self._parse_list(html)
                        if videos:
                            break

            # 3. 最近上新（第二位出不来：同样 API 优先 + 兜底）
            elif cid == "newest":
                videos, pages, total = self._category_api("newest", pg)
                if not videos:
                    urls = [f"/newest/{pg}/", f"/newest/?page={pg}", f"/latest/{pg}/"]
                    for u in urls:
                        html = self._get(u)
                        videos = self._parse_list(html)
                        if videos:
                            break

            # 4. AI 四大核心分类（优先 JSON API）
            elif cid in ("ai-duanju", "ai-manju", "ai-huanlian", "ai-mogai"):
                videos, pages, total = self._category_api(cid, pg)
                if not videos:
                    path = f"/{cid}/" if pg <= 1 else f"/{cid}/{pg}/"
                    html = self._get(path)
                    videos = self._parse_list(html)
                    ps = [int(x) for x in re.findall(r'/' + re.escape(cid) + r'/(\d+)/', html or "")]
                    if ps:
                        pages = max(ps)

            # 5. 专题列表
            elif cid == "topic":
                html = self._get("/topics/")
                videos = self._parse_list(html, mode="topic")
                pages = 1

            # 6. 排行榜
            elif cid == "ranks":
                rtype = rc if rc in ("hot", "recommend", "potential") else "hot"
                html = self._get(f"/ranks/{rtype}/")
                videos = self._parse_list(html, mode="rank")
                pages = 1

            # 7. 吃瓜
            elif cid == "chigua":
                ctype = rc if rc in ("page", "remen", "yuanchuang") else "page"
                html = self._get(f"/chigua/{ctype}/{pg}/")
                videos = self._parse_list(html, mode="post")

            # 8. 官方作者
            elif cid == "author":
                aid = rc if str(rc).isdigit() else "156291"
                html = self._get(f"/author/{aid}/video/{pg}/")
                videos = self._parse_list(html)

            # 9. 兜底通用请求
            else:
                path = f"/{cid}/" if pg <= 1 else f"/{cid}/{pg}/"
                html = self._get(path)
                videos = self._parse_list(html)

            # 若前几个分类仍为空且请求的是第一页，从首页匹配对应标题模块作为降级兜底
            if not videos and pg == 1:
                html = self._get("/")
                videos = self._parse_list(html)

        except Exception:
            videos = []

        if len(videos) > PAGE_SIZE:
            videos = videos[:PAGE_SIZE]
        return self._result(videos, pg, pages, total)

    def _category_api(self, slug, pg):
        """同时兼容 /api/videos/category/{slug} 与 /api/videos/list/{slug}"""
        apis = [
            f"/api/videos/category/{urllib.parse.quote(slug)}?sort=hot&page={pg}&size={PAGE_SIZE}",
            f"/api/videos/list?type={urllib.parse.quote(slug)}&page={pg}&size={PAGE_SIZE}",
        ]
        for url in apis:
            text = self._get(url, ref=f"/{slug}/")
            if not text:
                continue
            try:
                data = json.loads(text)
                d = data.get("data") or {}
                items = d.get("items") or d.get("list") or []
                if items:
                    pag = d.get("pagination") or {}
                    videos = [self._api_item(it) for it in items if self._api_item(it)]
                    pages = int(pag.get("pages") or 0) if str(pag.get("pages") or "").isdigit() else 0
                    total = int(pag.get("total") or 0) if str(pag.get("total") or "").isdigit() else 0
                    return videos, pages, total
            except Exception:
                continue
        return [], 0, 0

    def _api_item(self, it):
        vid = it.get("id")
        if vid is None:
            return None
        title = _clean(it.get("title"))
        if not title:
            return None
        pic = (it.get("cover") or "").strip()
        epc = it.get("episode_count")
        finished = it.get("is_finished")
        if finished:
            remark = f"全{epc}集" if epc else "全剧"
        else:
            remark = f"更新至{epc}集" if epc else "连载中"
        score = it.get("score")
        if score:
            remark = f"{score}分 " + remark
        return {
            "vod_id": str(vid),
            "vod_name": title,
            "vod_pic": self._wrap_pic(pic),
            "vod_remarks": remark or "在线观看",
        }

    def _result(self, videos, pg, pagecount=9999, total=0):
        n = len(videos)
        if total < 1:
            total = pagecount * max(n, 1) if pagecount > 1 else n
        return {
            "list": videos,
            "page": pg,
            "pagecount": pagecount,
            "limit": PAGE_SIZE,
            "total": total,
        }

    # ---------- 搜索 ----------
    def searchContent(self, key, quick=False, pg="1"):
        return self.searchContentPage(key, quick, pg)

    def searchContentPage(self, key, quick, page):
        kw = urllib.parse.quote(str(key or "").strip())
        if not kw:
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}
        try:
            pg = int(page) if page else 1
        except Exception:
            pg = 1
        html = self._get(f"/search/video/{kw}/{pg}/")
        videos = self._parse_list(html, mode="search")
        has_more = len(videos) >= 18
        return {
            "page": pg,
            "pagecount": pg + 1 if has_more else pg,
            "limit": 20,
            "total": 0,
            "list": videos,
        }

    # ---------- 详情 ----------
    def detailContent(self, ids):
        try:
            raw = ids[0] if isinstance(ids, (list, tuple)) else ids
            did = str(raw).strip()
        except Exception:
            return {"list": []}
        if not did:
            return {"list": []}

        if "/archives/" in did or (did.startswith("http") and "archives" in did):
            return self._detail_chigua(did)

        m = re.search(r'(?:detail/|/)?(\d+)/?$', did)
        vid = m.group(1) if m else (did if did.isdigit() else None)
        html = self._get(f"/detail/{vid}/") if vid else self._get(did if did.startswith("/") else "/" + did)

        if not html:
            return {"list": []}

        title = ""
        m = re.search(r'<h1[^>]*>([^<]+)</h1>', html) or re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if m:
            title = _clean(m.group(1))
        if not title:
            m = re.search(r'<title>(.*?)</title>', html)
            if m:
                title = _clean(m.group(1).split('|')[0])
        if not title:
            return {"list": []}

        pic = ""
        m = re.search(r'<img[^>]*data-src="([^"]+)"[^>]*>', html) or re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if m:
            pic = htmllib.unescape(m.group(1)).strip()

        desc = ""
        m = re.search(r'<p class="[^"]*hg-web-detail__desc[^"]*"[^>]*>(.*?)</p>', html, re.S) or re.search(r'<meta name="description" content="([^"]+)"', html)
        if m:
            desc = _clean(m.group(1))

        meta = ""
        m = re.search(r'class="[^"]*hg-web-detail__meta[^"]*"[^>]*>(.*?)</div>', html, re.S)
        if m:
            meta = _clean(m.group(1))
        tags = [_clean(m.group(2)) for m in re.finditer(r'class="hg-tag"[^>]*href="(/tag/[^"]+)"[^>]*>([^<]+)<', html)]

        eps = []
        seen = set()
        if vid:
            for m in re.finditer(r'href="(/video/' + re.escape(vid) + r'(?:/ep-(\d+))?/)"', html):
                path = m.group(1)
                if path in seen:
                    continue
                seen.add(path)
                epn = m.group(2)
                eps.append((f"{int(epn):02d}" if epn else "01", path))

            if not eps:
                vhtml = self._get(f"/video/{vid}/")
                if vhtml:
                    for m in re.finditer(r'<a class="hg-play__ep-item[^"]*" href="([^"]*)"[^>]*data-ep-id="([^"]*)"[^>]*>([^<]*)</a>', vhtml):
                        path = m.group(1) if m.group(1).startswith("/") else "/" + m.group(1)
                        if path in seen:
                            continue
                        seen.add(path)
                        label = _clean(m.group(3)) or f"第{m.group(2)}集"
                        eps.append((label, path))

        eps = sorted(eps, key=lambda x: self._ep_sort(x[1]))
        if not eps and vid:
            eps = [("01", f"/video/{vid}/")]

        return {"list": [{
            "vod_id": vid or did,
            "vod_name": title,
            "vod_pic": self._wrap_pic(pic),
            "type_name": ",".join(tags) or "黄果短剧",
            "vod_remarks": meta or "在线观看",
            "vod_content": desc,
            "vod_play_from": "正片",
            "vod_play_url": "#".join(f"{l}${p}" for l, p in eps),
            "vod_year": "", "vod_area": "", "vod_actor": "", "vod_director": "",
        }]}

    def _detail_chigua(self, url):
        if not url.startswith("http"):
            url = self.host.rstrip('/') + (url if url.startswith('/') else '/' + url)
        try:
            html = self._get(url.replace(self.host, "")) if url.startswith(self.host) else ""
            if not html:
                r = rq.get(url, headers={"User-Agent": UA, "Referer": self.host + "/"}, timeout=TIMEOUT, verify=False)
                html = r.text if r.status_code == 200 else ""
        except Exception:
            return {"list": []}
        if not html:
            return {"list": []}

        title = ""
        m = re.search(r'<title>(.*?)</title>', html)
        if m:
            title = _clean(m.group(1).split('|')[0])

        players = re.findall(r'<div class="post-video-player"[^>]*data-player-key="([^"]*)"[^>]*data-src="([^"]*)"', html)
        if not players:
            players = [(f"线路{i+1}", u) for i, u in enumerate(re.findall(r'data-src="(https?://[^"]+\.m3u8[^"]*)"', html))]

        play = "#".join([f"{k}${v.replace('&amp;', '&')}" for k, v in players]) if players else ""
        return {"list": [{
            "vod_id": url,
            "vod_name": title or "吃瓜",
            "vod_pic": "",
            "vod_remarks": "",
            "vod_content": title,
            "type_name": "黄果吃瓜",
            "vod_play_from": "黄果吃瓜",
            "vod_play_url": play or f"正片${url}",
            "vod_year": "", "vod_area": "", "vod_actor": "", "vod_director": "",
        }]}

    @staticmethod
    def _ep_sort(path):
        m = re.search(r'/ep-(\d+)/', path or "")
        if m:
            return int(m.group(1))
        m2 = re.search(r'/(\d+)/?$', path or "")
        return 1 if not m2 else int(m2.group(1))

    # ---------- 播放解析 ----------
    def playerContent(self, flag, id, vipFlags=None, vipIds=None):
        key = str(id or "").strip()
        if not key:
            return {"url": ""}

        if key.startswith("http"):
            return {"parse": 0, "url": key.replace("&amp;", "&").replace("\\u0026", "&"), "header": {"User-Agent": UA}}

        if key.isdigit():
            key = f"/video/{key}/"
        elif not key.startswith("/"):
            key = "/" + key

        html = self._get(key, ref="/")
        if not html or "videoInitialData" not in html:
            for h in HOSTS:
                try:
                    u = h.rstrip('/') + key
                    r = rq.get(u, headers={"User-Agent": UA, "Referer": h.rstrip('/') + "/"}, timeout=TIMEOUT, verify=False, allow_redirects=True)
                    if r.status_code == 200 and r.text and "videoInitialData" in r.text:
                        html = r.text
                        break
                except Exception:
                    continue

        if not html:
            return {"url": ""}

        m = re.search(r'<script id="videoInitialData" type="application/json">(.*?)</script>', html, re.S)
        if not m:
            m2 = re.search(r'data-play-src="(https?://[^"]+)"', html)
            if m2:
                return {"parse": 0, "url": m2.group(1).replace("&amp;", "&"), "header": {"User-Agent": UA}}
            return {"url": ""}

        try:
            data = json.loads(m.group(1))
        except Exception:
            return {"url": ""}

        url = data.get("videoSrc") or ""
        if not url:
            eps = data.get("epPlaySrcs") or {}
            pm = re.search(r'/ep-(\d+)/', key)
            ep_from_path = pm.group(1) if pm else None
            ep = data.get("ep")
            if ep_from_path and str(ep_from_path) in eps:
                url = eps[str(ep_from_path)]
            elif ep is not None and str(ep) in eps:
                url = eps[str(ep)]
            else:
                for v in eps.values():
                    if v:
                        url = v
                        break

        url = str(url or "").replace("\\u0026", "&").replace("&amp;", "&").strip()
        if url.startswith("http"):
            return {"parse": 0, "url": url, "header": {"User-Agent": UA}}
        return {"url": ""}

    # ---------- 本地代理 ----------
    def localProxy(self, param):
        try:
            if isinstance(param, dict):
                if param.get("type") == "pic":
                    return self._proxy_pic(param)
                url = param.get("url") or param.get("u") or ""
            else:
                url = self._resolve_img_param(param)
            if not url:
                return None
            host = self._safe_host()
            headers = {"User-Agent": UA, "Referer": host + "/", "Accept": "image/*"}
            rr = rq.get(url, headers=headers, timeout=12, verify=False, allow_redirects=True)
            if rr.status_code == 200 and rr.content and len(rr.content) > 50:
                data = _decrypt_img(rr.content)
                return [200, _detect_mime(data), data]
        except Exception:
            pass
        return None

    def _proxy_pic(self, params):
        try:
            raw = params.get("url") or ""
            if not raw.startswith("http"):
                try:
                    raw = base64.b64decode(raw + "==").decode("utf-8", "ignore")
                except Exception:
                    pass
            if not raw.startswith("http"):
                return None
            headers = {"User-Agent": UA, "Referer": self._safe_host() + "/"}
            data = rq.get(raw, headers=headers, timeout=12, verify=False).content
            data = _decrypt_img(data)
            return [200, _detect_mime(data), data]
        except Exception:
            return None

    @staticmethod
    def _resolve_img_param(param):
        if not param:
            return ""
        p = str(param).strip()
        p = re.sub(r'^https?://127\.0\.0\.1:\d+/proxy\?', '', p)
        p = re.sub(r'^proxy\?', '', p)
        if "url=" in p:
            q = urllib.parse.parse_qs(p)
            cand = q.get("url", [""])[0]
            if cand:
                p = cand
        try:
            p = urllib.parse.unquote(p)
        except Exception:
            pass
        if not p.startswith("http"):
            try:
                dec = base64.b64decode(p + "==").decode("utf-8", "ignore")
                if dec.startswith("http"):
                    p = dec
            except Exception:
                pass
        return p if p.startswith("http") else ""

    # ---------- 容错列表解析 ----------
    def _parse_list(self, html, mode="drama"):
        if not html or len(html) < 150:
            return []
        if BeautifulSoup is not None:
            try:
                try:
                    doc = BeautifulSoup(html, "lxml")
                except Exception:
                    doc = BeautifulSoup(html, "html.parser")
                res = self._parse_bs4(doc, mode)
                if res:
                    return res
            except Exception:
                pass
        return self._parse_regex(html)

    def _parse_bs4(self, doc, mode):
        videos, seen = [], set()

        if mode in ("drama", "search"):
            # 1. 尝试专有卡片类名
            cards = doc.select("div.hg-drama-card, div.video-card, div.drama-item, div.post-item")
            
            # 2. 若没有专有类名，全文档智能扫包含 /detail/\d+ 的超链接容器
            if not cards:
                cards = doc.find_all("a", href=re.compile(r"/detail/\d+"))

            for card in cards:
                a = card if card.name == "a" else card.find("a", href=True)
                if not a:
                    continue
                href = a.get("href", "")
                m = re.search(r"/detail/(\d+)", href)
                if not m:
                    continue
                vid = m.group(1)
                if vid in seen:
                    continue
                seen.add(vid)

                img = card.find("img")
                pic = (img.get("data-src") or img.get("src") or "") if img else ""
                title = (img.get("alt") if img else "") or ""
                if not title:
                    t = card.select_one(".hg-drama-card__title a, .hg-drama-card__title, h2, h3, .title")
                    title = t.get_text(strip=True) if t else (card.get("title") or "")
                
                parts = [el.get_text(strip=True) for sel in [
                    ".hg-drama-card__score", ".hg-drama-card__episode", 
                    ".hg-drama-card__badge", ".score", ".episode"
                ] if (el := card.select_one(sel))]
                
                if title:
                    videos.append({
                        "vod_id": vid,
                        "vod_name": _clean(title),
                        "vod_pic": self._wrap_pic(pic),
                        "vod_remarks": " ".join(parts).strip() or "在线观看",
                    })

        elif mode == "rank":
            for item in doc.select("div.hg-rank-item"):
                a = item.find("a", href=True, class_=re.compile("cover")) or item.find("a", href=True)
                if not a:
                    continue
                m = re.search(r"/detail/(\d+)", a.get("href", ""))
                vid = m.group(1) if m else a.get("href", "")
                if vid in seen:
                    continue
                seen.add(vid)
                img = item.find("img")
                pic = (img.get("data-src") or img.get("src") or "") if img else ""
                title = item.get("data-track-title") or (img.get("alt") if img else "") or ""
                if not title:
                    t = item.select_one(".hg-rank-item__title, h2")
                    title = t.get_text(strip=True) if t else ""
                heat = item.select_one(".hg-rank-item__heat-value")
                remark = ("🔥" + heat.get_text(strip=True)) if heat else ""
                if title:
                    videos.append({
                        "vod_id": vid,
                        "vod_name": _clean(title),
                        "vod_pic": self._wrap_pic(pic),
                        "vod_remarks": remark,
                    })

        elif mode == "topic":
            for card in doc.select("a.hg-topic-card"):
                href = card.get("href", "")
                slug = href.strip("/").split("/")[-1]
                img = card.find("img")
                pic = (img.get("data-src") or img.get("src") or "") if img else ""
                t = card.select_one(".hg-topic-card__title, h2")
                title = t.get_text(strip=True) if t else (img.get("alt") if img else "")
                meta = card.select_one(".hg-topic-card__meta")
                if title:
                    videos.append({
                        "vod_id": "dir_topic_" + slug,
                        "vod_name": _clean(title),
                        "vod_pic": self._wrap_pic(pic),
                        "vod_remarks": meta.get_text(strip=True) if meta else "",
                        "vod_tag": "folder",
                    })

        elif mode == "post":
            for card in doc.select("a.hg-post-card"):
                href = card.get("href", "")
                if not href:
                    continue
                img = card.find("img")
                pic = (img.get("data-src") or img.get("src") or "") if img else ""
                h3 = card.find("h3")
                title = h3.get_text(strip=True) if h3 else ""
                parts = [s.get_text(strip=True) for s in (card.select_one(".hg-post-card__date"), card.select_one(".hg-post-card__cat")) if s]
                videos.append({
                    "vod_id": href if href.startswith("http") else self.host + href,
                    "vod_name": _clean(title),
                    "vod_pic": self._wrap_pic(pic),
                    "vod_remarks": " | ".join(parts),
                })
        return videos

    def _parse_regex(self, html):
        """宽松正则匹配：只要含 /detail/(\d+) 即视作有效卡片"""
        result, seen = [], set()
        blocks = re.findall(r'<a[^>]+href="[^"]*/detail/(\d+)[^"]*"[^>]*>(.*?)</a>', html, re.S)
        for vid, inner in blocks:
            if vid in seen:
                continue
            seen.add(vid)
            
            pic = ""
            pm = re.search(r'data-src="([^"]+)"', inner) or re.search(r'src="([^"]+)"', inner)
            if pm:
                pic = htmllib.unescape(pm.group(1)).strip()

            title = ""
            tm = re.search(r'alt="([^"]+)"', inner) or re.search(r'title="([^"]+)"', inner)
            if tm:
                title = _clean(tm.group(1))
            if not title:
                title = _clean(inner)
            
            if not title or len(title) > 60:
                continue

            result.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self._wrap_pic(pic),
                "vod_remarks": "在线观看",
            })
        return result
