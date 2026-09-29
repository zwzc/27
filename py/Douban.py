# -*- coding: utf-8 -*-
"""
豆瓣 (Douban) Python Spider
数据来源：豆瓣移动端 (m.douban.com)
功能：首页推荐、分类浏览、搜索、详情展示（无播放源）
"""

import re
import json
import requests
from urllib.parse import quote, urljoin
from base.spider import Spider as BaseSpider

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class Spider(BaseSpider):
    HOST = "https://m.douban.com"
    UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")

    # 图片代理（绕过豆瓣防盗链）
    IMG_PROXY = "https://images.weserv.nl/?url="

    def getName(self):
        return "豆瓣"

    def init(self, extend=""):
        self.timeout = 15
        self.sess = requests.Session()
        self.sess.headers.update({
            "User-Agent": self.UA,
            "Referer": self.HOST + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        return {"status": 0}

    # ---------- 工具 ----------
    def _get(self, url):
        try:
            r = self.sess.get(url, timeout=self.timeout, allow_redirects=True)
            r.encoding = "utf-8"
            return r.text if r.status_code == 200 else ""
        except Exception:
            return ""

    def _pic(self, url):
        if not url:
            return ""
        url = url.strip()
        if url.startswith("//"):
            url = "https:" + url
        return self.IMG_PROXY + quote(url, safe="")

    def _clean(self, text):
        return re.sub(r"\s+", " ", str(text or "")).strip()

    # ---------- 列表解析 ----------
    def _parse_list(self, html):
        """解析豆瓣移动端列表页，返回视频卡片列表"""
        if not html or not BeautifulSoup:
            return []
        soup = BeautifulSoup(html, "html.parser")
        items = []
        seen = set()
        for a in soup.select("a[href*='/movie/subject/']"):
            href = a.get("href", "")
            m = re.search(r"/movie/subject/(\d+)", href)
            if not m:
                continue
            vid = m.group(1)
            if vid in seen:
                continue
            seen.add(vid)

            # 标题
            title_el = a.select_one(".subject-title") or a.select_one("h3") or a
            title = self._clean(title_el.get_text()) if title_el else ""
            if not title:
                continue

            # 图片
            img = a.select_one("img")
            pic = img.get("src") or img.get("data-src") or "" if img else ""

            # 评分 / 备注
            remark = ""
            rate_el = a.select_one(".rating") or a.select_one(".subject-rate")
            if rate_el:
                remark = self._clean(rate_el.get_text())

            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self._pic(pic),
                "vod_remarks": remark,
            })
        return items

    # ---------- 首页 ----------
    def homeContent(self, filter):
        classes = [
            {"type_id": "playing", "type_name": "正在上映"},
            {"type_id": "upcoming", "type_name": "即将上映"},
            {"type_id": "top250", "type_name": "Top 250"},
            {"type_id": "tv", "type_name": "热门剧集"},
        ]
        return {"class": classes, "filters": {}}

    def homeVideoContent(self):
        html = self._get(self.HOST + "/movie/nowplaying")
        return {"list": self._parse_list(html)[:30]}

    # ---------- 分类 ----------
    def categoryContent(self, tid, pg, filter, extend):
        page = max(1, int(pg or 1))
        tid = str(tid or "playing")
        start = (page - 1) * 20

        if tid == "playing":
            url = self.HOST + "/movie/nowplaying"
        elif tid == "upcoming":
            url = self.HOST + "/movie/coming"
        elif tid == "top250":
            url = "https://movie.douban.com/top250?start=%d" % start
        elif tid == "tv":
            url = self.HOST + "/tv/hot"
        else:
            url = self.HOST + "/movie/nowplaying"

        html = self._get(url)
        lst = self._parse_list(html)

        # Top250 分页
        pagecount = page + 1 if len(lst) >= 20 else page
        if tid == "top250":
            pagecount = 13  # Top250 共 13 页

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
        url = ("https://m.douban.com/rexxar/api/v2/search?"
               "q=%s&type=movie&start=%d&count=20" % (quote(key), (page - 1) * 20))
        try:
            r = self.sess.get(url, timeout=self.timeout,
                              headers={"Referer": self.HOST + "/"})
            data = r.json()
            items = []
            for it in (data.get("items") or []):
                target = it.get("target") or {}
                vid = str(target.get("id") or "")
                if not vid:
                    continue
                items.append({
                    "vod_id": vid,
                    "vod_name": target.get("title") or "",
                    "vod_pic": self._pic(target.get("cover_url") or
                                         target.get("pic", {}).get("large", "")),
                    "vod_remarks": str(target.get("rating", {}).get("value", "")) or "",
                })
            return {"list": items, "page": page, "pagecount": page + 1}
        except Exception:
            return {"list": []}

    # ---------- 详情 ----------
    def detailContent(self, ids):
        vid = str(ids[0] if isinstance(ids, list) else ids or "").strip()
        if not vid:
            return {"list": []}
        url = "https://movie.douban.com/subject/%s/" % vid
        html = self._get(url)
        if not html or not BeautifulSoup:
            return {"list": []}

        soup = BeautifulSoup(html, "html.parser")

        # 标题
        title_el = soup.select_one("span[property='v:itemreviewed']")
        title = self._clean(title_el.get_text()) if title_el else vid

        # 图片
        pic_el = soup.select_one("#mainpic img")
        pic = pic_el.get("src") if pic_el else ""

        # 信息
        info = {}
        info_el = soup.select_one("#info")
        if info_el:
            for line in info_el.get_text("\n").split("\n"):
                line = line.strip()
                if ":" in line:
                    k, v = line.split(":", 1)
                    info[k.strip()] = v.strip()

        # 简介
        intro_el = soup.select_one("span[property='v:summary']") or soup.select_one("#link-report span")
        content = self._clean(intro_el.get_text()) if intro_el else ""

        return {"list": [{
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": self._pic(pic),
            "type_name": info.get("类型", ""),
            "vod_year": info.get("上映日期", "")[:4],
            "vod_area": info.get("制片国家/地区", ""),
            "vod_actor": info.get("主演", ""),
            "vod_director": info.get("导演", ""),
            "vod_content": content,
            "vod_play_from": "",  # 豆瓣无播放源
            "vod_play_url": "",
        }]}

    def playerContent(self, flag, vid, vipFlags):
        return {"parse": 0, "url": "", "header": ""}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        return None


# ============ 弹幕补丁（追加到文件末尾） ============
import re as _dm_re
import json as _dm_json
from urllib.parse import quote as _dm_quote

_DM_API = "http://47.103.92.65:9321/DMQlCpHvSpxj4uQofGTafer8y_aL1XDa/api/v2/fongmi/danmaku"
_DM_CACHE = {}


def _dm_clean(name):
    s = str(name or "")
    s = _dm_re.sub(r'正在播放\s*[:：]?', ' ', s)
    s = _dm_re.sub(r'\[.*?\]', ' ', s)
    s = _dm_re.sub(r'【.*?】', ' ', s)
    s = _dm_re.sub(r'\([^)]*\)', ' ', s)
    s = _dm_re.sub(r'(1080p|720p|480p|2160p|4k|8k|hd|sd|uhd|fhd)', ' ', s, flags=_dm_re.I)
    s = _dm_re.sub(r'(国语|粤语|中字|中英|繁体|简体|完整版|未删减|蓝光|高清|超清)', ' ', s)
    s = _dm_re.sub(r'第\s*\d+\s*[集期话].*$', '', s)
    s = _dm_re.sub(r'\s+', ' ', s).strip()
    return s or str(name or '')


def _dm_search(api, name, episode):
    if not api or not name:
        return []
    cname = _dm_clean(name)
    ep = str(episode or '第1集').strip() or '第1集'
    key = cname + '||' + ep
    if key in _DM_CACHE:
        return _DM_CACHE[key]
    try:
        import requests
        url = '%s?name=%s&episode=%s' % (
            api.rstrip('/'),
            _dm_quote(cname, safe=''),
            _dm_quote(ep, safe=''),
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
            if isinstance(it, dict) and it.get('url'):
                out.append({
                    'name': str(it.get('name') or '弹幕')[:80],
                    'url': str(it['url']),
                })
        if len(_DM_CACHE) > 50:
            _DM_CACHE.clear()
        _DM_CACHE[key] = out
        return out
    except Exception as e:
        print('[dm] search failed: %s' % e)
        return []


_orig_init = Spider.init
_orig_detailContent = Spider.detailContent
_orig_playerContent = Spider.playerContent


def _patched_init(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    self._cur_vod = ''
    self.danmaku_api = _DM_API
    ext = getattr(self, 'extend', '') or ''
    if ext:
        try:
            obj = _dm_json.loads(ext) if isinstance(ext, str) else {}
            if isinstance(obj, dict) and obj.get('danmu'):
                self.danmaku_api = str(obj['danmu']).strip()
        except Exception:
            pass


def _patched_detailContent(self, *args, **kwargs):
    result = _orig_detailContent(self, *args, **kwargs)
    try:
        if result and isinstance(result, dict) and result.get('list'):
            first = result['list'][0]
            if isinstance(first, dict):
                self._cur_vod = first.get('vod_name', '') or ''
    except Exception:
        pass
    return result


def _patched_playerContent(self, *args, **kwargs):
    result = _orig_playerContent(self, *args, **kwargs)
    try:
        if isinstance(result, dict) and result.get('danmaku'):
            return result
        if not getattr(self, '_cur_vod', ''):
            return result
        dm = _dm_search(self.danmaku_api, self._cur_vod, '第1集')
        if dm:
            result['danmaku'] = dm
    except Exception as e:
        print('[dm] attach failed: %s' % e)
    return result


Spider.init = _patched_init
Spider.detailContent = _patched_detailContent
Spider.playerContent = _patched_playerContent
# ============ 弹幕补丁结束 ============
