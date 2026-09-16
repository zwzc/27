/*
 * title: 独播库
 * author: Spider开发规范
 * host: https://www.duboku.tv/
 * api: https://api.dbokutv.com
 * 说明: FongMi/TV · 影视仓 · TVBox JS Spider（移植自 WexAiDuBoKu）
 * ext 可选: "https://api.dbokutv.com" 或 { "host":"https://api.dbokutv.com", "timeout":10000 }
 */

var PC_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36';
var SITE_HOST = 'https://www.duboku.tv';
var PLAY_HOST = 'https://w.duboku.io';
var DEFAULT_API = 'https://api.dbokutv.com';

var API = DEFAULT_API;
var siteKey = '';
var siteType = 3;
var PlayM3u8Cache = {};
var KParams = {
    headers: {
        'User-Agent': PC_UA,
        Referer: SITE_HOST + '/',
    },
    timeout: 10000,
};

var CLASSES = [
    { type_id: '1', type_name: '电影' },
    { type_id: '2', type_name: '电视剧' },
    { type_id: '3', type_name: '综艺' },
    { type_id: '4', type_name: '动漫' },
    { type_id: '21', type_name: '短剧' },
    { type_id: '20', type_name: '港剧' },
    { type_id: '13', type_name: '陆剧' },
    { type_id: '15', type_name: '日韩剧' },
    { type_id: '14', type_name: '台泰剧' },
];

async function init(cfg) {
    try {
        API = DEFAULT_API;
        var preferred = '';
        var timeout = 0;
        if (cfg) {
            siteKey = cfg.skey || cfg.key || siteKey || '';
            siteType = cfg.stype != null ? cfg.stype : (cfg.type != null ? cfg.type : siteType);
        }
        var ext = cfg && cfg.ext !== undefined ? cfg.ext : cfg;

        if (typeof ext === 'string' && ext.trim()) {
            var s = ext.trim();
            if (s.charAt(0) === '{') {
                try {
                    ext = JSON.parse(s);
                } catch (e) {
                    preferred = s;
                    ext = null;
                }
            } else {
                preferred = s;
                ext = null;
            }
        }

        if (ext && typeof ext === 'object') {
            if (ext.host) preferred = String(ext.host).trim();
            if (ext.timeout) timeout = parseInt(ext.timeout, 10);
        }

        if (preferred && /^https?:\/\//i.test(preferred)) {
            API = preferred.replace(/\/$/, '');
        }
        if (timeout > 0) KParams.timeout = timeout;
        KParams.headers['User-Agent'] = PC_UA;
        KParams.headers['Referer'] = SITE_HOST + '/';
    } catch (e) {
        console.error('初始化失败：', e.message);
        API = DEFAULT_API;
        KParams.headers['Referer'] = SITE_HOST + '/';
    }
}

/** TMDB 国内常被墙，换 CDN；其它图地址原样返回 */
function fixPic(url) {
    if (!url) return '';
    url = String(url).trim();
    if (!url) return '';
    url = url.replace(/^https?:\/\/image\.tmdb\.org/i, 'https://tmdb-image-prod.b-cdn.net');
    url = url.replace(/^https?:\/\/www\.themoviedb\.org\/t\/p\//i, 'https://tmdb-image-prod.b-cdn.net/t/p/');
    return url;
}

function mediaHeaders() {
    return {
        'User-Agent': PC_UA,
        Origin: PLAY_HOST,
        Referer: PLAY_HOST + '/',
    };
}

function mediaOrigin(url) {
    var m = String(url || '').match(/^(https?:\/\/[^\/]+)/i);
    return m ? m[1] : '';
}

function resolveAgainst(line, m3u8Url) {
    line = String(line || '').trim();
    if (!line) return line;
    if (/^https?:\/\//i.test(line)) return line;
    if (line.indexOf('//') === 0) return 'https:' + line;
    var origin = mediaOrigin(m3u8Url);
    if (line.charAt(0) === '/') return origin + line;
    var base = m3u8Url.substring(0, m3u8Url.lastIndexOf('/') + 1);
    return base + line;
}

function rewriteM3u8(body, m3u8Url) {
    var lines = String(body || '').split(/\r?\n/);
    var out = [];
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        var trim = line.trim();
        if (!trim || trim.charAt(0) === '#') {
            // #EXT-X-KEY:URI="..." / #EXT-X-MAP:URI="..."
            if (/URI="/i.test(trim)) {
                line = trim.replace(/URI="([^"]+)"/i, function (m, u) {
                    return 'URI="' + resolveAgainst(u, m3u8Url) + '"';
                });
            }
            out.push(line);
            continue;
        }
        out.push(resolveAgainst(trim, m3u8Url));
    }
    return out.join('\n');
}

function toProxyUrl(url) {
    try {
        if (typeof getProxy === 'function') {
            return getProxy(true) + '&url=' + encodeURIComponent(url);
        }
    } catch (e) {}
    try {
        if (typeof js2Proxy === 'function') {
            return js2Proxy(true, siteType, siteKey, '', url);
        }
    } catch (e) {}
    return '';
}

function toDataM3u8(body) {
    return 'data:application/vnd.apple.mpegurl;charset=utf-8,' + encodeURIComponent(body);
}

/* ---------- Java Random（无 BigInt） ---------- */
function mul48(hi, lo, aHi, aLo) {
    var x0 = lo & 0xffff;
    var x1 = (lo >>> 16) & 0xffff;
    var x2 = hi & 0xffff;
    var y0 = aLo & 0xffff;
    var y1 = (aLo >>> 16) & 0xffff;
    var y2 = aHi & 0xffff;
    var p0 = x0 * y0;
    var p1 = x0 * y1 + x1 * y0;
    var p2 = x0 * y2 + x1 * y1 + x2 * y0;
    var p3 = x1 * y2 + x2 * y1;
    var s0 = p0;
    var s1 = p1 + Math.floor(s0 / 0x10000);
    s0 &= 0xffff;
    var s2 = p2 + Math.floor(s1 / 0x10000);
    s1 &= 0xffff;
    s2 &= 0xffff;
    return { hi: s2, lo: (s0 | (s1 << 16)) >>> 0 };
}

function JavaRandom(seed) {
    var s = seed;
    if (s < 0) s = s >>> 0;
    this.lo = ((s >>> 0) ^ 0xDEECE66D) >>> 0;
    this.hi = ((Math.floor(s / 0x100000000) >>> 0) ^ 0x5) & 0xffff;
}

JavaRandom.prototype.next = function (bits) {
    var p = mul48(this.hi, this.lo, 0x5, 0xDEECE66D);
    var t = p.lo + 0xB;
    this.lo = t >>> 0;
    this.hi = (p.hi + Math.floor(t / 0x100000000)) & 0xffff;
    var shift = 48 - bits;
    if (shift >= 32) return this.hi >>> (shift - 32);
    return ((this.hi << (32 - shift)) | (this.lo >>> shift)) >>> 0;
};

JavaRandom.prototype.nextInt = function (bound) {
    if (bound <= 0) return 0;
    if ((bound & -bound) === bound) {
        return Math.floor(this.next(31) * (bound / 0x80000000));
    }
    var bits;
    var val;
    do {
        bits = this.next(31);
        val = bits % bound;
    } while (bits - val + (bound - 1) < 0);
    return val;
};

function randStr(len, offset, charsetMode) {
    var random = new JavaRandom(Math.floor(Date.now() / 1000) + offset);
    var charset;
    if (charsetMode === 33) {
        charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    } else if (charsetMode === 88) {
        charset = 'XYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVW';
    } else {
        charset = '';
        for (var i = charsetMode; i < charsetMode + 62; i++) charset += String.fromCharCode(i);
    }
    var out = '';
    for (var j = 0; j < len; j++) out += charset.charAt(random.nextInt(charset.length));
    return out;
}

function signQuery() {
    var t = Math.floor(Date.now() / 1000);
    var iNextInt = new JavaRandom(t).nextInt(800000000) % 800000001;
    var ms = String(Date.now());
    var mixed = String(100000000 + iNextInt) + String(900000000 - iNextInt);
    var sb = '';
    var n = Math.min(mixed.length, ms.length);
    for (var i = 0; i < n; i++) {
        sb += mixed.charAt(i);
        sb += ms.charAt(i);
    }
    if (mixed.length > n) sb += mixed.substring(n);
    if (ms.length > n) sb += ms.substring(n);
    var ssid = b64encode(sb).replace(/=/g, '.');
    return '?sign=' + randStr(60, 60 + t, 33) + '&ssid=' + ssid + '&token=' + randStr(38, t + 38, 88);
}

/* ---------- Base64 ---------- */
var B64TAB = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

function utf8Bytes(str) {
    var bytes = [];
    for (var i = 0; i < str.length; i++) {
        var c = str.charCodeAt(i);
        if (c < 0x80) bytes.push(c);
        else if (c < 0x800) bytes.push(0xc0 | (c >> 6), 0x80 | (c & 0x3f));
        else if (c >= 0xd800 && c <= 0xdbff) {
            var c2 = str.charCodeAt(++i);
            var u = 0x10000 + (((c & 0x3ff) << 10) | (c2 & 0x3ff));
            bytes.push(0xf0 | (u >> 18), 0x80 | ((u >> 12) & 0x3f), 0x80 | ((u >> 6) & 0x3f), 0x80 | (u & 0x3f));
        } else {
            bytes.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 0x3f), 0x80 | (c & 0x3f));
        }
    }
    return bytes;
}

function utf8String(bytes) {
    var out = '';
    for (var i = 0; i < bytes.length; ) {
        var c = bytes[i++];
        if (c < 0x80) out += String.fromCharCode(c);
        else if (c < 0xe0) out += String.fromCharCode(((c & 0x1f) << 6) | (bytes[i++] & 0x3f));
        else if (c < 0xf0) {
            out += String.fromCharCode(((c & 0x0f) << 12) | ((bytes[i++] & 0x3f) << 6) | (bytes[i++] & 0x3f));
        } else {
            var u = ((c & 0x07) << 18) | ((bytes[i++] & 0x3f) << 12) | ((bytes[i++] & 0x3f) << 6) | (bytes[i++] & 0x3f);
            u -= 0x10000;
            out += String.fromCharCode(0xd800 + (u >> 10), 0xdc00 + (u & 0x3ff));
        }
    }
    return out;
}

function b64encodeManual(bytes) {
    var out = '';
    for (var i = 0; i < bytes.length; i += 3) {
        var a = bytes[i];
        var b = i + 1 < bytes.length ? bytes[i + 1] : 0;
        var c = i + 2 < bytes.length ? bytes[i + 2] : 0;
        var n = (a << 16) | (b << 8) | c;
        out += B64TAB.charAt((n >> 18) & 63) + B64TAB.charAt((n >> 12) & 63);
        out += i + 1 < bytes.length ? B64TAB.charAt((n >> 6) & 63) : '=';
        out += i + 2 < bytes.length ? B64TAB.charAt(n & 63) : '=';
    }
    return out;
}

function b64decodeManual(b64) {
    b64 = String(b64 || '').replace(/[^A-Za-z0-9+/=]/g, '');
    var bytes = [];
    for (var i = 0; i < b64.length; i += 4) {
        var a = B64TAB.indexOf(b64.charAt(i));
        var b = B64TAB.indexOf(b64.charAt(i + 1));
        var c = B64TAB.indexOf(b64.charAt(i + 2));
        var d = B64TAB.indexOf(b64.charAt(i + 3));
        var n = (a << 18) | (b << 12) | ((c >= 0 ? c : 0) << 6) | (d >= 0 ? d : 0);
        bytes.push((n >> 16) & 255);
        if (b64.charAt(i + 2) !== '=') bytes.push((n >> 8) & 255);
        if (b64.charAt(i + 3) !== '=') bytes.push(n & 255);
    }
    return bytes;
}

function b64encode(str) {
    try {
        if (typeof base64 !== 'undefined' && base64.encode) return base64.encode(str);
    } catch (e) {}
    try {
        if (typeof Buffer !== 'undefined') return Buffer.from(str, 'utf8').toString('base64');
    } catch (e) {}
    try {
        if (typeof btoa === 'function') return btoa(unescape(encodeURIComponent(str)));
    } catch (e) {}
    return b64encodeManual(utf8Bytes(str));
}

function b64decode(b64) {
    try {
        if (typeof base64 !== 'undefined' && base64.decode) return base64.decode(b64);
    } catch (e) {}
    try {
        if (typeof Buffer !== 'undefined') return Buffer.from(b64, 'base64').toString('utf8');
    } catch (e) {}
    try {
        if (typeof atob === 'function') return decodeURIComponent(escape(atob(b64)));
    } catch (e) {}
    return utf8String(b64decodeManual(b64));
}

function reverseStr(s) {
    var o = '';
    for (var i = s.length - 1; i >= 0; i--) o += s.charAt(i);
    return o;
}

function decodeField(str) {
    try {
        if (!str) return '';
        var sb = '';
        for (var i = 0; i < str.length; i += 10) {
            sb += reverseStr(str.substring(i, Math.min(i + 10, str.length)));
        }
        return b64decode(sb.replace(/\./g, '='));
    } catch (e) {
        return '';
    }
}

/* ---------- 筛选 ---------- */
function nv(n, v) {
    return { n: n, v: v };
}

function filterGroup(key, name, values) {
    return { key: key, name: name, value: values };
}

function tags() {
    var arr = [nv('全部', '')];
    for (var i = 0; i < arguments.length; i++) arr.push(nv(arguments[i], arguments[i]));
    return arr;
}

function buildFilters() {
    var movie = [
        filterGroup('class', '类型', tags('喜剧', '爱情', '恐怖', '动作', '科幻', '剧情', '警匪', '战争', '犯罪', '动画', '奇幻', '武侠', '冒险', '悬疑', '惊悚', '古装', '同性')),
        filterGroup('area', '地区', tags('大陆', '香港', '台湾', '韩国', '英国', '法国', '加拿大', '澳大利亚')),
        filterGroup('year', '年份', tags('2026', '2025', '2024', '2023', '2022', '2021', '2020', '2019')),
        filterGroup('lang', '语言', tags('国语', '粤语', '韩语', '英语', '法语')),
        filterGroup('by', '排序', [nv('时间', ''), nv('人气', '人气'), nv('评分', '评分')]),
    ];
    var drama = [
        filterGroup('class', '类型', tags('悬疑', '武侠', '科幻', '都市', '爱情', '古装', '战争', '青春', '偶像', '喜剧', '家庭', '奇幻', '剧情', '乡村', '年代', '警匪', '谍战', '历险', '罪案', '宫廷', '经典', '动作', '惊悚', '历史', '穿越', '同性')),
        filterGroup('area', '地区', tags('大陆', '香港', '台湾', '韩国', '日本', '新加坡', '泰国')),
        filterGroup('year', '年份', tags('2026', '2025', '2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017', '更早')),
        filterGroup('lang', '语言', tags('国语', '粤语', '韩语', '泰语', '日语')),
        filterGroup('by', '排序', [nv('时间', ''), nv('人气', '人气'), nv('评分', '评分')]),
    ];
    var show = [
        filterGroup('class', '类型', tags('真人秀', '选秀', '竞演', '情感', '旅游', '音乐', '美食', '纪实', '生活', '游戏互动', '竞技', '搞笑', '脱口秀')),
        filterGroup('area', '地区', tags('大陆', '韩国')),
        filterGroup('year', '年份', tags('2026', '2025', '2024', '2023', '2022', '2021', '2020', '2019', '更早')),
        filterGroup('lang', '语言', tags('国语', '韩语')),
        filterGroup('by', '排序', [nv('时间', ''), nv('人气', '人气'), nv('评分', '评分')]),
    ];
    return {
        '1': movie,
        '2': drama,
        '3': show,
        '4': drama,
        '13': drama,
        '14': drama,
        '15': drama,
        '20': drama,
        '21': drama,
    };
}

function parseVodList(arr) {
    var list = [];
    if (!arr || !arr.length) return list;
    for (var i = 0; i < arr.length; i++) {
        var item = arr[i];
        if (!item || !item.Name) continue;
        var id = normalizeVodId(decodeField(item.DId));
        if (!id) continue;
        var remarks = '';
        if (item.Tag) remarks = String(item.Tag);
        else if (item.Rating != null && item.Rating !== '') remarks = item.Rating + '分';
        list.push({
            vod_id: id,
            vod_name: item.Name,
            vod_pic: fixPic(decodeField(item.TnId)),
            vod_remarks: remarks,
        });
    }
    return list;
}

/** 去掉前导 /，避免客户端把 vod_id 当路径导致进不去详情并换源 */
function normalizeVodId(id) {
    id = String(id || '').trim();
    try {
        if (/%2f/i.test(id) || /%2F/.test(id)) id = decodeURIComponent(id);
    } catch (e) {}
    while (id.charAt(0) === '/') id = id.substring(1);
    return id;
}

function toApiPath(id) {
    id = normalizeVodId(id);
    if (!id) return '';
    if (/^https?:\/\//i.test(id)) return id;
    return '/' + id;
}

function pickFirstId(ids) {
    if (ids == null) return '';
    if (Object.prototype.toString.call(ids) === '[object Array]') {
        return ids.length ? String(ids[0] || '') : '';
    }
    var s = String(ids);
    if (s.charAt(0) === '[') {
        try {
            var arr = JSON.parse(s);
            if (arr && arr.length) return String(arr[0] || '');
        } catch (e) {}
    }
    return s;
}

function parseExtend(extend) {
    if (!extend) return {};
    if (typeof extend === 'object') return extend;
    if (typeof extend === 'string') {
        try {
            return JSON.parse(extend || '{}');
        } catch (e) {
            return {};
        }
    }
    return {};
}

async function apiGet(path) {
    var base = API || DEFAULT_API;
    var url = base + path + (path.indexOf('?') >= 0 ? signQuery().replace('?', '&') : signQuery());
    var text = await request(url);
    if (!text) return null;
    try {
        return JSON.parse(text);
    } catch (e) {
        console.error('JSON解析失败：', e.message);
        return null;
    }
}

async function home(filter) {
    try {
        return JSON.stringify({
            class: CLASSES,
            filters: buildFilters(),
        });
    } catch (e) {
        console.error('获取分类失败：', e.message);
        return JSON.stringify({ class: [], filters: {} });
    }
}

async function homeVod() {
    try {
        var data = await apiGet('/home');
        var list = [];
        if (data && data.length) {
            for (var i = 0; i < data.length; i++) {
                var part = parseVodList(data[i] && data[i].VodList);
                for (var j = 0; j < part.length; j++) list.push(part[j]);
            }
        }
        return JSON.stringify({ list: list });
    } catch (e) {
        console.error('推荐页获取失败：', e.message);
        return JSON.stringify({ list: [] });
    }
}

async function category(tid, pg, filter, extend) {
    try {
        pg = parseInt(pg, 10);
        pg = pg > 0 ? pg : 1;
        var fl = parseExtend(extend);
        var cateId = fl.cateId || tid || '1';
        var area = fl.area || '';
        var year = fl.year || '';
        var by = fl.by || '';
        var klass = fl['class'] || '';
        var lang = fl.lang || '';
        var path = '/vodshow/' + cateId + '-' + area + '-' + by + '-' + klass + '-' + lang + '----' + pg + '---' + year;
        var data = await apiGet(path);
        var list = parseVodList(data && data.VodList);
        return JSON.stringify({
            page: pg,
            pagecount: list.length >= 48 ? pg + 1 : pg,
            limit: 48,
            total: 999999,
            list: list,
        });
    } catch (e) {
        console.error('分类页获取失败：', e.message);
        return JSON.stringify({ page: 1, pagecount: 1, limit: 48, total: 0, list: [] });
    }
}

async function search(wd, quick, pg) {
    try {
        if (!wd) return JSON.stringify({ list: [] });
        var data = await apiGet('/vodsearch?wd=' + encodeURIComponent(wd));
        var list = Object.prototype.toString.call(data) === '[object Array]'
            ? parseVodList(data)
            : parseVodList(data && data.VodList);
        return JSON.stringify({ list: list });
    } catch (e) {
        console.error('搜索失败：', e.message);
        return JSON.stringify({ list: [] });
    }
}

async function detail(ids) {
    try {
        var id = normalizeVodId(pickFirstId(ids));
        if (!id) return JSON.stringify({ list: [] });
        var data = await apiGet(toApiPath(id));
        if (!data || !data.Name) return JSON.stringify({ list: [] });

        var actors = '';
        if (data.Actor && typeof data.Actor !== 'string' && data.Actor.length !== undefined) {
            var tmp = [];
            for (var a = 0; a < data.Actor.length; a++) if (data.Actor[a]) tmp.push(data.Actor[a]);
            actors = tmp.join(',');
        } else {
            actors = data.Actor || '';
        }

        var eps = [];
        var playlist = data.Playlist || [];
        for (var i = 0; i < playlist.length; i++) {
            var ep = playlist[i];
            if (!ep) continue;
            var name = ep.EpisodeName || ('第' + (i + 1) + '集');
            name = String(name).replace(/\$/g, '_');
            var vid = normalizeVodId(decodeField(ep.VId));
            if (!vid) continue;
            eps.push(name + '$' + vid);
        }

        return JSON.stringify({
            list: [{
                vod_id: id,
                vod_name: data.Name || '',
                vod_pic: fixPic(decodeField(data.TnId)),
                vod_year: data.ReleaseYear || '',
                vod_content: data.Description || '',
                vod_director: data.Director || '',
                vod_actor: actors,
                type_name: data.Genre || data.Class || '',
                vod_play_from: eps.length ? '独播库' : '',
                vod_play_url: eps.length ? eps.join('#') : '',
            }],
        });
    } catch (e) {
        console.error('详情获取失败：', e.message);
        return JSON.stringify({ list: [] });
    }
}

async function play(flag, ids, flags) {
    try {
        var playId = normalizeVodId(pickFirstId(ids));
        if (playId.indexOf('$') >= 0) playId = normalizeVodId(playId.split('$').pop());
        playId = playId.split('||')[0].trim();
        if (!playId) return JSON.stringify({ jx: 0, parse: 0, url: '', header: {} });

        var data = await apiGet(toApiPath(playId));
        var url = decodeField(data && data.HId);
        if (!url) return JSON.stringify({ jx: 0, parse: 0, url: '', msg: '独播库播放地址为空' });

        var hdr = mediaHeaders();
        var outUrl = url;

        // 分片是 /xxx.ts 根路径，IJK 常解析错；先拉清单改成绝对地址再播
        if (/\.m3u8(\?|$)/i.test(url)) {
            var raw = await request(url, { headers: hdr, timeout: KParams.timeout });
            if (raw && raw.indexOf('#EXTM3U') >= 0) {
                var fixed = rewriteM3u8(raw, url);
                PlayM3u8Cache[url] = fixed;
                var proxy = toProxyUrl(url);
                if (proxy) {
                    outUrl = proxy;
                } else {
                    // 无本地代理时用 data URI，避免相对路径
                    outUrl = toDataM3u8(fixed);
                }
            }
        }

        return JSON.stringify({
            jx: 0,
            parse: 0,
            url: outUrl,
            header: hdr,
        });
    } catch (e) {
        console.error('播放失败：', e.message);
        return JSON.stringify({ jx: 0, parse: 0, url: '', msg: e.message });
    }
}

async function proxy(params) {
    try {
        var url = '';
        if (params) {
            url = params.url || params.ou || params.link || '';
        }
        if (!url) return [400, 'text/plain', 'empty url'];
        try {
            // 只解一层，避免把签名路径解坏
            if (/%3A%2F%2F/i.test(url) || /^https?%3A/i.test(url)) {
                url = decodeURIComponent(url);
            }
        } catch (e) {}

        if (PlayM3u8Cache[url]) {
            return [200, 'application/vnd.apple.mpegurl', PlayM3u8Cache[url]];
        }

        var headers = mediaHeaders();
        var res = await req(url, { headers: headers, timeout: KParams.timeout, buffer: 2 });
        var content = res && res.content != null ? res.content : '';
        var text = typeof content === 'string' ? content : '';

        if (/\.m3u8(\?|$)/i.test(url) || text.indexOf('#EXTM3U') === 0) {
            var fixed = rewriteM3u8(text, url);
            PlayM3u8Cache[url] = fixed;
            return [200, 'application/vnd.apple.mpegurl', fixed];
        }

        var code = (res && res.code) || 200;
        var ct = '';
        if (res && res.headers) {
            ct = res.headers['content-type'] || res.headers['Content-Type'] || '';
        }
        return [code, ct || 'application/octet-stream', content];
    } catch (e) {
        return [500, 'text/plain', 'proxy error: ' + e.message];
    }
}

async function request(reqUrl, options) {
    try {
        options = options || {};
        if (typeof reqUrl !== 'string' || !reqUrl.trim()) throw new Error('reqUrl无效');
        var method = (options.method || 'GET').toUpperCase();
        var headers = (options.headers && typeof options.headers === 'object') ? options.headers : KParams.headers;
        var timeout = parseInt(options.timeout, 10) > 0 ? parseInt(options.timeout, 10) : KParams.timeout;
        var res = await req(reqUrl, {
            headers: headers,
            timeout: timeout,
            method: method,
        });
        if (res && res.content != null) return res.content;
        return '';
    } catch (e) {
        console.error(reqUrl + ' 请求失败：', e.message);
        return '';
    }
}

export function __jsEvalReturn() {
    return {
        init: init,
        home: home,
        homeVod: homeVod,
        category: category,
        search: search,
        detail: detail,
        play: play,
        proxy: proxy,
    };
}
