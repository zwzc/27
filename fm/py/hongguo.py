class Spider(_BaseSpider):
    def __init__(self):
        self.device_id = str(random.randint(10**17, 10**18 - 1))
        self.install_id = str(random.randint(10**17, 10**18 - 1))

    def _adopt_working_pair(self):
        pair = _working_device_pair()
        if pair is not None:
            self.device_id = pair["device_id"]
            self.install_id = pair["install_id"]

    def isVideoFormat(self, url):
        u = str(url or "").lower()
        return (
            ".mp4" in u
            or "video_mp4" in u
            or "m3u8" in u
            or "mime_type=video" in u
            or "qznovelvod" in u
        )

    def manualVideoCheck(self):
        return False

    def getDependence(self):
        return []

    def download(self, path, url):
        return ""

    def isVPAYard(self, flag):
        return False

    def action(self, action):
        return {}

    def init(self, extend=""):
        try:
            _hg_cache_cleanup(False)
        except Exception:
            pass

    def destroy(self):
        try:
            _hg_cache_cleanup(False)
        except Exception:
            pass

    def liveContent(self, url=""):
        return {}

    def danmaku(self, id, emit):
        """红果官方无公开弹幕接口；保留入口以兼容壳调用，返回可调用的停止函数。"""
        return lambda: None

    def homeContent(self, filter):
        class_list = [{"type_id": k, "type_name": n} for k, n, _ in _HG_CONTENT_TYPES]
        filters = {}
        for k, _n, cats in _HG_CONTENT_TYPES:
            if len(cats) > 1:
                filters[k] = [{
                    "key": "cat",
                    "name": "分类",
                    "value": [{"n": nm, "v": v} for v, nm in cats],
                }]
        return {"class": class_list, "filters": filters}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = max(1, int(pg))
        except (TypeError, ValueError):
            page = 1
        route = _hg_route_of(tid)
        ext = dict(extend) if isinstance(extend, dict) else {}
        cat = str(ext.get("cat") or ext.get("分类") or "").strip()
        if isinstance(filter, dict):
            f2 = str(filter.get("cat") or filter.get("分类") or "").strip()
            if f2 and not cat:
                cat = f2
        if cat in ("all", "全部", "0", "all_cat"):
            cat = ""
        try:
            p = _hg_category_page(route, cat, page)
        except Exception:
            p = _hg_category_page("real-drama", cat, page)
        rows = p.get("recommendList") or []
        page_data = p.get("pagination") or {}
        return {
            "page": page,
            "pagecount": int(page_data.get("totalPages") or 1),
            "limit": len(rows),
            "total": int(page_data.get("total") or len(rows)),
            "list": [_cat_item(x) for x in rows],
        }

    def searchContent(self, key, quick, pg="1"):
        try:
            page = max(1, int(pg))
        except (TypeError, ValueError):
            page = 1
        key = str(key or "").strip() or "短剧"
        low = key.lower()
        if key in ("AI漫剧", "ai漫剧") or "ai漫" in low:
            return _search_by_keywords(_AI_MANJU_KEYWORDS, page)
        if key in ("漫剧", "动漫短剧"):
            return _search_by_keywords(_MANJU_KEYWORDS, page)
        p = _search_loader(key, page)
        rows = p.get("searchList") or []
        if not rows:
            scanned = _hg_search_scan(key, page)
            if scanned.get("list"):
                return scanned
        try:
            total = int(p.get("totalCount") or 0)
        except Exception:
            total = 0
        try:
            total_pages = int(p.get("totalPages") or 1)
        except Exception:
            total_pages = 1
        out = []
        seen = set()
        for x in rows:
            it = _item(x)
            vid = str(it.get("vod_id") or "")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            out.append(it)
        if not total:
            total = len(out)
        return {
            "page": page,
            "pagecount": max(1, min(50, total_pages if total_pages else 1)),
            "limit": len(out),
            "total": total,
            "list": out,
        }

    def _detail(self, sid):
        sid = str(sid).replace("hg-series-v1:", "")
        p = (
            (_data(SITE + "/detail?series_id=" + quote(sid, safe="")).get("loaderData") or {})
            .get("detail_page") or {}
        )
        s = p.get("seriesDetail") or {}
        vids = s.get("vid_list") or []
        actors = [
            str(x.get("nickname"))
            for x in (s.get("celebrities") or [])
            if isinstance(x, dict) and x.get("nickname")
        ]
        play_from = []
        play_url = []
        for q, line_name in _HG_QUALITY_LINES:
            eps = "#".join(
                "第%d集%s%s%s%s" % (i + 1, "$", EPISODE_PREFIX, q + ":", str(v))
                for i, v in enumerate(vids)
            )
            play_from.append(line_name)
            play_url.append(eps)
        return {
            "list": [{
                "vod_id": sid,
                "vod_name": str(s.get("series_name") or ""),
                "vod_pic": str(s.get("series_cover") or ""),
                "vod_year": "",
                "vod_area": "",
                "vod_director": "",
                "vod_actor": ",".join(actors),
                "vod_content": str(s.get("series_intro") or ""),
                "vod_remarks": str(s.get("episode_right_text") or ""),
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url),
            }]
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        responses = [self._detail(video_id) for video_id in ids]
        return {
            **responses[0],
            "list": [item for response in responses for item in response["list"]],
        }

    def playerContent(self, flag, id, vipFlags):
        self._adopt_working_pair()
        vip_flags = list(vipFlags or [])
        token_q, vid = _split_episode_token(id)
        line_q = "1080"
        for name_key, candidate_q in _QUALITY_LINE_NAME_TO_Q.items():
            if name_key in str(flag or ""):
                line_q = candidate_q
                break
        q = line_q if token_q == "1080" and str(flag) else token_q
        q = q if q in _QUALITY_LINE_NAME_TO_Q else "1080"
        if not str(vid).isdigit():
            return {
                "parse": 1,
                "jx": 0,
                "playUrl": "",
                "url": SITE + "/",
                "header": {"User-Agent": UA},
            }

        def _warm_session():
            try:
                _stream_session(vid, {
                    "device_id": self.device_id or "",
                    "install_id": self.install_id or "",
                }, q)
            except Exception:
                pass

        try:
            threading.Thread(target=_warm_session, daemon=True).start()
        except Exception:
            pass
        try:
            port = _start_stream_server()
        except Exception:
            port = 0
        if port:
            query = urlencode(
                {
                    "vid": vid,
                    "q": q,
                    "did": self.device_id or "",
                    "iid": self.install_id or "",
                }
            )
            return {
                "parse": 0,
                "jx": 0,
                "playUrl": "",
                "url": "http://127.0.0.1:%d/hg.mp4?%s" % (port, query),
                "header": {"User-Agent": UA},
            }
        proxy = ""
        try:
            getter = getattr(self, "proxyUrl", None) or getattr(self, "getProxyUrl", None)
            if getter is not None:
                proxy = (getter() or "").strip()
        except Exception:
            proxy = ""
        if proxy:
            sep = "&" if "?" in proxy else "?"
            url = proxy + sep + urlencode(
                {
                    "vid": vid,
                    "q": q,
                    "hg": "cenc",
                    "did": self.device_id or "",
                    "iid": self.install_id or "",
                }
            )
            return {
                "parse": 0,
                "jx": 0,
                "playUrl": "",
                "url": url,
                "header": {
                    "User-Agent": MEDIA_UA,
                    "Referer": "https://novel.snssdk.com/",
                },
            }
        return {
            "parse": 1,
            "jx": 0,
            "playUrl": "",
            "url": SITE + "/",
            "header": {"User-Agent": UA},
        }

    def proxy(self, params):
        import traceback
        params = params or {}
        self._adopt_working_pair()
        vid = str(
            params.get("vid")
            or params.get("id")
            or params.get("mediaId")
            or ""
        ).strip()
        if not vid or not str(vid).isdigit():
            for _key, value in params.items():
                text = str(value or "").strip()
                if text.isdigit() and len(text) >= 10:
                    vid = text
                    break
        if not vid:
            return [400, "text/plain; charset=utf-8", b"missing vid"]
        try:
            cfg = {
                "device_id": str(params.get("did") or self.device_id or ""),
                "install_id": str(params.get("iid") or self.install_id or ""),
            }
            user_q = str(params.get("q") or params.get("quality") or "").strip()
            if user_q:
                order = [user_q, "1080", "720", "480", "360"]
            elif _aes_is_fast():
                order = ["1080", "720", "480", "360"]
            else:
                order = ["720", "480", "1080", "360"]
            seen_q = set()
            quals = []
            for q in order:
                if q and q not in seen_q:
                    seen_q.add(q)
                    quals.append(q)
            primary = [user_q] if user_q else quals
            for q in primary:
                cached = _hg_cache_get(vid, q)
                if cached:
                    return [200, "video/mp4", cached]
            model = None
            rows = None
            for _round in range(4):
                try:
                    model = _video_model(vid, cfg)
                except Exception as err:
                    if not _is_empty_model_error(err) or _round >= 3:
                        raise
                    pair = _rotate_stream_device()
                    cfg = {"device_id": pair["device_id"], "install_id": pair["install_id"]}
                    self.device_id = pair["device_id"]
                    self.install_id = pair["install_id"]
                    continue
                rows = _video_list_from_model(model)
                if rows:
                    break
                if _round >= 3:
                    break
                pair = _rotate_stream_device()
                cfg = {"device_id": pair["device_id"], "install_id": pair["install_id"]}
                self.device_id = pair["device_id"]
                self.install_id = pair["install_id"]
            if not rows:
                return [500, "text/plain; charset=utf-8", b"empty video list"]
            last_err = None
            for wanted in quals:
                try:
                    cached = _hg_cache_get(vid, wanted)
                    if cached:
                        return [200, "video/mp4", cached]
                    _, item = _select_quality(rows, wanted)
                    url = _media_url(item)
                    spade = _spade_value(item)
                    if not url or not spade:
                        last_err = "missing url/spade q=%s" % wanted
                        continue
                    try:
                        key_seed = _key_seed_from_model(model)
                        if key_seed:
                            url = _decrypt_spade_url(url, key_seed)
                    except Exception:
                        pass
                    dl_timeout = 150 if _aes_is_fast() else 90
                    media_headers = {
                        "User-Agent": MEDIA_UA,
                        "Referer": "https://novel.snssdk.com/",
                    }
                    try:
                        body = _multi_download(
                            url,
                            headers=media_headers,
                            timeout=dl_timeout,
                            workers=4 if _aes_is_fast() else 3,
                        )
                    except Exception as dl_err:
                        last_err = "download failed q=%s err=%s" % (wanted, dl_err)
                        continue
                    if not body:
                        last_err = "empty body q=%s" % wanted
                        continue
                    if (not _aes_is_fast()) and wanted in ("1080", "4k") and len(body) > 45 * 1024 * 1024:
                        last_err = "skip large %s without native AES size=%s" % (wanted, len(body))
                        continue
                    plain = decrypt_mp4_cenc(body, derive_content_key(spade))
                    if len(plain) < 64 or (b"ftyp" not in plain[:64] and b"moov" not in plain[:4096]):
                        last_err = "bad mp4 after decrypt q=%s" % wanted
                        continue
                    try:
                        _hg_cache_put(vid, wanted, plain)
                    except Exception:
                        pass
                    return [200, "video/mp4", plain]
                except Exception as one_err:
                    last_err = "%s q=%s" % (one_err, wanted)
                    continue
            msg = "hg proxy failed: %s" % last_err
            return [500, "text/plain; charset=utf-8", msg.encode("utf-8")]
        except Exception as exc:
            msg = "hg proxy failed: %s\n%s" % (exc, traceback.format_exc())
            return [500, "text/plain; charset=utf-8", msg.encode("utf-8")]
