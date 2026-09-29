# -*- coding: utf-8 -*-
"""
豆瓣 (Douban) Python Spider —— 无第三方依赖版
只用 requests，不依赖 bs4 / lxml。
数据源：豆瓣 rexxar JSON API（优先）+ HTML 正则（回退）
"""
import re
import json
import requests
from urllib.parse import quote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    HOST = "https://m.douban.com"
    UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")
    IMG_PROXY = "https://images.weserv.nl/?url="

    def getName(self):
        return "豆瓣"

    def init(self, extend=""):
        self.timeout = 15
        self.sess = requests.Session()
        self.sess.trust_env = False
        self.sess.verify = False
        self.sess.headers.update({
            "User-Agent": self.UA,
            "Referer": self.HOST + "/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        print("[douban] init done")
        return {"status": 0}

    # ---------- 工具 ----------
    def _get_text(self, url, headers=None):
        try:
            h = dict(self.sess.headers)
            if headers:
                h.update(headers)
            r = self.sess.get(url, headers=h, timeout=self.timeout)
            r.encoding = "utf-8"
            return r.text if r.status_code == 200 else ""
        except Exception as e:
            print("[douban] GET fail %s : %s" % (url[:60], e))
            return ""

    def _get_json(self, url, headers=None):
        t = self._get_text(url, headers)
        if not t:
            return None
        try:
            return json.loads(t)
        except Exception as e:
            print("[douban] JSON fail %s : %s" % (url[:60], e))
            return None

    def _pic(self, url):
        if not url:
            return ""
        url = url.strip()
        if url.startswith("//"):
            url = "https:" + url
        return self.IMG_PROXY + quote(url, safe="")

    @staticmethod
    def _clean(text):
        return re.sub(r"\s+", " ", str(text or "")).strip()

    # ---------- 解析列表（JSON 优先） ----------
    def _parse_items(self, data):
        """从 rexxar JSON 里提取影片列表"""
        out = []
        seen = set()
        if not data:
            return out
        # 不同接口的字段名可能不同
        items = (data.get("items") or data.get("subjects")
                 or data.get("list") or [])
        for it in items:
            if not isinstance(it, dict):
                continue
            # 有些接口包了一层 target
            target = it.get("target") if isinstance(it.get("target"), dict) else it
            vid = str(target.get("id") or target.get("subject_id") or "").strip()
            title = str(target.get("title") or target.get("name") or "").strip()
            if not vid or not title or vid in seen:
                continue
            seen.add(vid)
            # 图片
            pic = ""
            pic_obj = target.get("pic") or target.get("cover") or {}
            if isinstance(pic_obj, dict):
                pic = (pic_obj.get("large") or pic_obj.get("normal")
                       or pic_obj.get("small") or "")
            elif isinstance(pic_obj, str):
                pic = pic_obj
            # 评分
            rating = ""
            rt = target.get("rating")
            if isinstance(rt, dict):
                rating = str(rt.get("value") or rt.get("average") or "")
            elif rt:
                rating = str(rt)
            out.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self._pic(pic),
                "vod_remarks": rating,
            })
        return out

    # ---------- 解析列表（HTML 正则回退） ----------
    def _parse_html_items(self, html):
        out = []
        seen = set()
        if not html:
            return out
        # 匹配 <a href="/movie/subject/123/"> ... </a>
        pattern = re.compile(
            r'<a[^>]+href="[^"]*?/subject/(\d+)/?[^"]*"[^>]*>(.*?)</a>',
            re.S)
        for m in pattern.finditer(html):
            vid = m.group(1)
            if vid in seen:
                continue
            body = m.group(2)
            # 标题：优先 class=subject-title，其次 <h3>，其次 img alt
            t = re.search(r'class="[^"]*subject-title[^"]*"[^>]*>([^<]+)<', body)
            if not t:
                t = re.search(r'<h3[^>]*>([^<]+)</h3>', body)
            if not t:
                t = re.search(r'alt="([^"]+)"', body)
            if not t:
                continue
            title = self._clean(t.group(1))
            if not title:
                continue
            # 图片
            p = re.search(r'data-src="([^"]+)"', body) or re.search(r'src="([^"]+)"', body)
            pic = p.group(1) if p else ""
            seen.add(vid)
            out.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self._pic(pic),
                "vod_remarks": "",
            })
        return out

    # ---------- 首页 ----------
    def homeContent(self, filter):
        classes = [
            {"type_id": "playing", "type_name": "正在上映"},
            {"type_id": "coming", "type_name": "即将上映"},
            {"type_id": "top250", "type_name": "Top 250"},
            {"type_id": "tv", "type_name": "热门剧集"},
        ]
        return {"class": classes, "filters": {}}

    def homeVideoContent(self):
        # 优先 JSON API
        data = self._get_json(self.HOST + "/rexxar/api/v2/movie/nowplaying?count=20")
        lst = self._parse_items(data)
        if not lst:
            # 回退 HTML
            html = self._get_text(self.HOST + "/movie/nowplaying")
            lst = self._parse_html_items(html)
        print("[douban] homeVideoContent: %d" % len(lst))
        return {"list": lst[:30]}

    # ---------- 分类 ----------
    def categoryContent(self, tid, pg, filter, extend):
        page = max(1, int(pg or 1))
        tid = str(tid or "playing")
        start = (page - 1) * 20
        lst = []

        if tid == "playing":
            data = self._get_json(
                self.HOST + "/rexxar/api/v2/movie/nowplaying?count=20")
            lst = self._parse_items(data)
        elif tid == "coming":
            data = self._get_json(
                self.HOST + "/rexxar/api/v2/movie/coming_soon?count=20")
            lst = self._parse_items(data)
        elif tid == "top250":
            url = "https://movie.douban.com/top250?start=%d" % start
            html = self._get_text(url)
            lst = self._parse_html_items(html)
        elif tid == "tv":
            data = self._get_json(
                self.HOST + "/rexxar/api/v2/tv/recommend?count=20")
            lst = self._parse_items(data)
            if not lst:
                html = self._get_text(self.HOST + "/tv/hot")
                lst = self._parse_html_items(html)

        pagecount = page + 1 if len(lst) >= 20 else page
        if tid == "top250":
            pagecount = 13
        return {
            "list": lst,
            "page": page,
            "pagecount": pagecount,
            "limit": 20,
            "total": 999,
        }

    # ---------- 搜索 ----------
    def searchContent(self, key, quick, pg="1"):
        page = max(1, int(pg or 1))
        if not key:
            return {"list": []}
        start = (page - 1) * 20
        url = ("%s/rexxar/api/v2/search?q=%s&type=movie&start=%d&count=20"
               % (self.HOST, quote(str(key)), start))
        data = self._get_json(url, headers={"Referer": self.HOST + "/"})
        lst = self._parse_items(data)
        return {"list": lst, "page": page,
                "pagecount": page + 1 if len(lst) >= 20 else page}

    # ---------- 详情 ----------
    def detailContent(self, ids):
        vid = str(ids[0] if isinstance(ids, list) else ids or "").strip()
        if not vid:
            return {"list": []}

        # 优先 JSON API
        data = self._get_json(
            self.HOST + "/rexxar/api/v2/movie/%s" % vid,
            headers={"Referer": self.HOST + "/"})

        title = ""
        pic = ""
        content = ""
        type_name = ""
        year = ""
        area = ""
        actors = ""
        director = ""

        if isinstance(data, dict):
            title = str(data.get("title") or "")
            pic_obj = data.get("pic") or {}
            if isinstance(pic_obj, dict):
                pic = pic_obj.get("large") or pic_obj.get("normal") or ""
            elif isinstance(pic_obj, str):
                pic = pic_obj
            content = str(data.get("intro") or data.get("summary") or "")
            # 年份
            year = str(data.get("year") or "")
            # 类型
            genres = data.get("genres") or []
            if isinstance(genres, list):
                type_name = " ".join(str(x) for x in genres[:3])
            # 地区
            countries = data.get("countries") or []
            if isinstance(countries, list):
                area = " ".join(str(x) for x in countries[:2])
            # 演员
            casts = data.get("casts") or []
            if isinstance(casts, list):
                actors = "/".join(
                    str(c.get("name") or "") for c in casts[:8]
                    if isinstance(c, dict))
            # 导演
            dirs = data.get("directors") or []
            if isinstance(dirs, list):
                director = "/".join(
                    str(d.get("name") or "") for d in dirs[:3]
                    if isinstance(d, dict))

        # JSON 失败，回退 HTML
        if not title:
            html = self._get_text("https://movie.douban.com/subject/%s/" % vid)
            m = re.search(r'<span[^>]*property="v:itemreviewed"[^>]*>([^<]+)</span>', html)
            if m:
                title = self._clean(m.group(1))
            m = re.search(r'id="mainpic"[^>]*>\s*<img[^>]+src="([^"]+)"', html)
            if m:
                pic = m.group(1)
            m = re.search(r'<span[^>]*property="v:summary"[^>]*>([\s\S]*?)</span>', html)
            if m:
                content = self._clean(re.sub(r"<[^>]+>", " ", m.group(1)))

        if not title:
            title = vid

        return {"list": [{
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": self._pic(pic),
            "type_name": type_name,
            "vod_year": year,
            "vod_area": area,
            "vod_actor": actors,
            "vod_director": director,
            "vod_content": content,
            "vod_play_from": "",
            "vod_play_url": "",
        }]}

    # ---------- 播放（豆瓣无播放源） ----------
    def playerContent(self, flag, vid, vipFlags):
        return {"parse": 0, "url": "", "header": ""}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        return None
