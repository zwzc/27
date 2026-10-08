# -*- coding: utf-8 -*-
"""
TVB云播 (https://fjcgs.cc/) 采集脚本
适用: 安卓影视+ / ok影视 等支持 T4/PY 采集规范的影视壳子 App

接口规范 (T4 Python Spider):
    homeContent(filter)       -> {"class": [...], "filters": {...}}
    categoryContent(tid, pg, filter, extend) -> {"page":.., "pagecount":.., "limit":.., "total":.., "list":[...]}
    detailContent(ids)        -> {"list": [...详情...]}
    searchContent(key, quick) -> {"list": [...]}
    playerContent(flag, ids, vipFlags) -> {"parse":0, "playUrl":"", "url":"..."}

站点要点:
    1. 站点为苹果CMS定制版, 桌面UA会触发滑块WAF, 移动端UA/蜘蛛UA不受限,
       因此所有请求统一使用移动端 Chrome UA。
    2. 分类: 电影1 / 电视剧2 / 综艺3 / 动漫4 / 短视频9 / 即将上映51
       路由  /fjcgcctype/{tid}.html             第1页
             /fjcgcctype/{tid}-{pg}.html        第2页起
    3. 详情  /fjcgcc/{id}.html         含线路名(name17)与集数(list-number1)
    4. 播放  /fjcgccplay/{id}-{sid}-{nid}.html  页面内 player_aaaa.url 即真实地址
    5. 搜索  /search/-------------.html?wd={kw}  分页 &page=N
"""
import re
import json
import urllib.parse

_HAS_REQUESTS = False
_req = None
try:
    import requests as _req
    _HAS_REQUESTS = True
except Exception:
    pass

SITE = "https://fjcgs.cc"
UA = ("Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")

# 需要走解析站的播放源(from), 其余视为直链
_PARSE_FROM = {"fjyg", "leduo", "qpdz", "qq", "dbyun", "wolong", "ffm3u8", "dbm3u8", "mp4", "link"}
_PARSE_GATE = "https://m3u8.nmghytd.com/index.php?url="


# ---------------------------------------------------------------- http 基础

def _get(url, timeout=15):
    headers = {
        "User-Agent": UA,
        "Referer": SITE + "/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    text = ""
    if _HAS_REQUESTS and _req is not None:
        resp = _req.get(url, headers=headers, timeout=timeout,
                        allow_redirects=True, verify=False)
        resp.encoding = resp.apparent_encoding or "utf-8"
        text = resp.text
    else:
        import ssl
        import urllib.request
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            data = r.read()
            enc = r.headers.get_content_charset() or "utf-8"
            text = data.decode(enc, errors="ignore")
    return text


def _abs(u):
    if not u:
        return u
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return SITE + u
    if u.startswith("http"):
        return u
    return SITE + "/" + u


# ---------------------------------------------------------------- 首页分类

def homeContent(filter):
    classes = [
        {"type_id": "1", "type_name": "电影"},
        {"type_id": "2", "type_name": "电视剧"},
        {"type_id": "3", "type_name": "综艺"},
        {"type_id": "4", "type_name": "动漫"},
        {"type_id": "9", "type_name": "短视频"},
        {"type_id": "51", "type_name": "即将上映"},
    ]
    return {"class": classes, "filters": {}}


# ---------------------------------------------------------------- 列表解析

def _parse_vod_list(html):
    items = []
    # 条目: <a href="/fjcgcc/ID.html"><img ... data-src="PIC" alt="NAME" ...><div class="ys-name6">NAME</div></a>
    pat = re.compile(
        r'<a[^>]+href="(/fjcgcc/(\d+)\.html)"[^>]*>\s*'
        r'<img[^>]+(?:data-src|src)="([^"]*)"[^>]*alt="([^"]*)"[^>]*>.*?'
        r'<div class="ys-name6">(.*?)</div>',
        re.S,
    )
    for m in pat.finditer(html):
        href, vid, pic, alt, name = m.groups()
        name = (name or alt or "").strip()
        if not name:
            continue
        items.append({
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": _abs(pic),
            "vod_remarks": "",
        })
    # 去重
    seen, uniq = set(), []
    for it in items:
        if it["vod_id"] in seen:
            continue
        seen.add(it["vod_id"])
        uniq.append(it)
    return uniq


def _fetch_pages(html, tid):
    """从列表页解析最大页码"""
    nums = set()
    # 形如 /fjcgcctype/1-1843.html
    for m in re.finditer(r'/fjcgcctype/%s-(\d+)\.html' % re.escape(tid), html):
        try:
            nums.add(int(m.group(1)))
        except Exception:
            pass
    return max(nums) if nums else 1


def categoryContent(tid, pg, filter, extend):
    pg = int(pg) if str(pg).isdigit() else 1
    page = 1 if pg <= 1 else pg
    url = "%s/fjcgcctype/%s.html" % (SITE, tid) if page == 1 else \
        "%s/fjcgcctype/%s-%d.html" % (SITE, tid, page)
    try:
        html = _get(url)
    except Exception:
        return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}
    items = _parse_vod_list(html)
    pagecount = _fetch_pages(html, str(tid)) if items else 1
    return {
        "page": page,
        "pagecount": pagecount,
        "limit": len(items) or 20,
        "total": (pagecount or 1) * (len(items) or 20),
        "list": items,
    }


# ---------------------------------------------------------------- 搜索

def searchContent(key, quick):
    kw = urllib.parse.quote(str(key).strip())
    items = []
    pagecount = 1
    try:
        html = _get("%s/search/-------------.html?wd=%s" % (SITE, kw))
        items = _parse_vod_list(html)
        # 搜索分页
        pagecount = _fetch_pages(html, "search") or 1
        for m in re.finditer(r'/search/[-]+(\d+)\.html', html):
            try:
                pagecount = max(pagecount, int(m.group(1)))
            except Exception:
                pass
    except Exception:
        pass
    return {"list": items, "page": 1, "pagecount": pagecount,
            "limit": len(items) or 20, "total": len(items)}


# ---------------------------------------------------------------- 详情

def _extract_lines(html):
    """按 HTML 顺序解析 线路名(name17) 与 集数(list-number1), 一一配对"""
    lines = []
    n17s = re.findall(r'<div class="name17">(.*?)</div>', html, re.S)
    lns = re.findall(
        r'<div class="list-number1">(.*?)(?=<div class="list-name23">|<!--|\Z)',
        html, re.S)
    # 只保留"线路"开头的线路名
    line_names = [n.strip() for n in n17s if n.strip().startswith("线路")]
    for idx, seg in enumerate(lns):
        eps = re.findall(r'href="/fjcgccplay/(\d+)-(\d+)-(\d+)\.html"><div>(.*?)</div>', seg, re.S)
        if not eps:
            continue
        sid = eps[0][1]
        name = line_names[idx] if idx < len(line_names) else ("线路" + str(sid))
        urls = []
        for _, s, n, ename in eps:
            urls.append("%s$%s/fjcgccplay/%s-%s-%s.html" % (
                ename.strip() or ("第%s集" % n), SITE, eps[0][0], s, n))
        lines.append((name, "#".join(urls)))
    return lines


def detailContent(ids):
    vid = str(ids).strip()
    # 兼容 "vod_id-sid-nid" 或纯 id
    vid = re.sub(r'-\d+$', '', vid)
    try:
        html = _get("%s/fjcgcc/%s.html" % (SITE, vid))
    except Exception:
        return {"list": []}

    vod = {"vod_id": vid}

    # 片名
    m = re.search(r'<div class="ys-name18">(.*?)</div>', html, re.S)
    if not m:
        m = re.search(r'<title>(.*?)</title>', html, re.S)
        if m:
            t = m.group(1).strip()
            t = re.sub(r'^《|》.*$', '', t)
            vod["vod_name"] = t
        else:
            vod["vod_name"] = vid
    else:
        vod["vod_name"] = m.group(1).strip()

    # 海报
    m = re.search(r'<img[^>]+data-src="(https?://[^"]+)"', html, re.S)
    vod["vod_pic"] = _abs(m.group(1)) if m else ""

    # 导演 / 主演
    def _links(label):
        i = html.find(label)
        if i < 0:
            return ""
        seg = html[i:i + 800]
        names = re.findall(r'<a[^>]+>([^<]+)</a>', seg)
        out = []
        for n in names:
            n = n.strip().replace("\u00a0", "").replace("&nbsp;", "")
            if n:
                out.append(n)
        return " ".join(out)

    vod["vod_director"] = _links("导演")
    vod["vod_actor"] = _links("主演")

    # 类型 / 地区
    def _kv(label):
        i = html.find(label)
        if i < 0:
            return ""
        seg = html[i:i + 300]
        m = re.search(r'<a[^>]*>(.*?)</a>', seg, re.S)
        v = m.group(1) if m else ""
        return v.strip().replace("\u00a0", "").replace("&nbsp;", "")

    vod["type_name"] = _kv("类型")
    vod["vod_area"] = _kv("地区")
    vod["vod_year"] = ""
    vod["vod_remarks"] = ""

    # 简介
    m = re.search(r'<div class="vod-descri1"(.*?)>((?:(?!</div>).)*)</div>', html, re.S)
    if not m:
        m = re.search(r'<div class="Synopsis-word"[^>]*>(.*?)</div>', html, re.S)
    vod["vod_content"] = re.sub(r'<[^>]+>|&nbsp;|\u00a0|\s+', ' ',
                                 m.group(2 or 1)).strip() if m else ""

    # 线路 -> vod_play_from / vod_play_url
    lines = _extract_lines(html)
    vod["vod_play_from"] = "$$$".join(nm for nm, _ in lines)
    vod["vod_play_url"] = "$$$".join(u for _, u in lines)

    return {"list": [vod]}


# ---------------------------------------------------------------- 播放

def playerContent(flag, ids, vipFlags):
    # ids 可能是完整 URL、站内相对路径、或 "vid-sid-nid"
    u = str(ids).strip()
    if not u.startswith("http"):
        if u.startswith("/"):
            u = SITE + u
        else:
            # 兼容 "vid-sid-nid" 或纯 vid
            parts = u.split("-")
            if len(parts) >= 3 and parts[-2].isdigit() and parts[-1].isdigit():
                u = "%s/fjcgccplay/%s.html" % (SITE, u)
            else:
                u = "%s/fjcgccplay/%s-1-1.html" % (SITE, u)
    try:
        html = _get(u)
    except Exception:
        return {"parse": 0, "playUrl": "", "url": ""}

    # 提取 player_aaaa JSON
    m = re.search(r'var player_aaaa=(\{.*?\});', html, re.S)
    url, src_from = "", ""
    if m:
        try:
            data = json.loads(m.group(1))
            url = data.get("url", "")
            src_from = data.get("from", "")
        except Exception:
            mm = re.search(r'"url"\s*:\s*"([^"]*)"', m.group(1))
            if mm:
                url = mm.group(1).replace("\\/", "/") if mm else ""
    if not url:
        return {"parse": 0, "playUrl": "", "url": ""}

    url = url.replace("\\/", "/")
    # 需要解析站的线路, 且当前不是解析地址时套接解析器
    if src_from in _PARSE_FROM and not url.startswith(_PARSE_GATE):
        url = _PARSE_GATE + urllib.parse.quote(url, safe="")
    return {"parse": 0, "playUrl": "", "url": url}


# ---------------------------------------------------------------- 本地调试

if __name__ == "__main__":
    import sys
    def p(obj):
        print(json.dumps(obj, ensure_ascii=False, indent=2)[:1500])
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "home":
        p(homeContent(False))
    elif arg == "movie":
        p(categoryContent("1", "1", False, ""))
    elif arg.startswith("detail:"):
        p(detailContent(arg.split(":", 1)[1]))
    elif arg.startswith("search:"):
        p(searchContent(arg.split(":", 1)[1], False))
    elif arg.startswith("play:"):
        p(playerContent("", arg.split(":", 1)[1], ""))
    else:
        print("usage: python fjcgs_tvb.py home|movie|detail:id|search:key|play:url")