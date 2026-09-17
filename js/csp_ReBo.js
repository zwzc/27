/*
 * title: 热播影视
 * 说明: FongMi/TV · 影视仓 · TVBox JS Spider（移植自 WexAiReBo）
 * 对应 Java: com.github.catvod.spider.WexAiReBo
 * ext 可选: { "host":"http://v.rbotv.cn", "timeout":10000, "danmaku":"http://..." }
 */

var MOBILE_UA = 'Mozilla/5.0 (Linux; Android 12; V2055A Build/SP1A.210812.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36';
var API_UA = 'okhttp-okgo/jeasonlzy';
var DEFAULT_HOST = 'http://v.rbotv.cn';
var SIGN_SALT = '7gp0bnd2sr85ydii2j32pcypscoc4w6c7g5spl';
var HOST = DEFAULT_HOST;
var siteKey = '';
var siteType = 3;
var TIMEOUT = 10000;

var md5Pure = (function () {
    function d(n, t) { var r = (65535 & n) + (65535 & t); return (n >> 16) + (t >> 16) + (r >> 16) << 16 | 65535 & r; }
    function f(n, t, r, e, o, u) { return d((u = d(d(t, n), d(e, u))) << o | u >>> 32 - o, r); }
    function l(n, t, r, e, o, u, c) { return f(t & r | ~t & e, n, t, o, u, c); }
    function g(n, t, r, e, o, u, c) { return f(t & e | r & ~e, n, t, o, u, c); }
    function v(n, t, r, e, o, u, c) { return f(t ^ r ^ e, n, t, o, u, c); }
    function m(n, t, r, e, o, u, c) { return f(r ^ (t | ~e), n, t, o, u, c); }
    function c(n, t) {
        var r, e, o, u; n[t >> 5] |= 128 << t % 32; n[14 + (t + 64 >>> 9 << 4)] = t;
        for (var c = 1732584193, f = -271733879, i = -1732584194, a = 271733878, h = 0; h < n.length; h += 16)
            c = l(r = c, e = f, o = i, u = a, n[h], 7, -680876936), a = l(a, c, f, i, n[h + 1], 12, -389564586), i = l(i, a, c, f, n[h + 2], 17, 606105819), f = l(f, i, a, c, n[h + 3], 22, -1044525330),
            c = l(c, f, i, a, n[h + 4], 7, -176418897), a = l(a, c, f, i, n[h + 5], 12, 1200080426), i = l(i, a, c, f, n[h + 6], 17, -1473231341), f = l(f, i, a, c, n[h + 7], 22, -45705983),
            c = l(c, f, i, a, n[h + 8], 7, 1770035416), a = l(a, c, f, i, n[h + 9], 12, -1958414417), i = l(i, a, c, f, n[h + 10], 17, -42063), f = l(f, i, a, c, n[h + 11], 22, -1990404162),
            c = l(c, f, i, a, n[h + 12], 7, 1804603682), a = l(a, c, f, i, n[h + 13], 12, -40341101), i = l(i, a, c, f, n[h + 14], 17, -1502002290),
            c = g(c, f = l(f, i, a, c, n[h + 15], 22, 1236535329), i, a, n[h + 1], 5, -165796510), a = g(a, c, f, i, n[h + 6], 9, -1069501632), i = g(i, a, c, f, n[h + 11], 14, 643717713), f = g(f, i, a, c, n[h], 20, -373897302),
            c = g(c, f, i, a, n[h + 5], 5, -701558691), a = g(a, c, f, i, n[h + 10], 9, 38016083), i = g(i, a, c, f, n[h + 15], 14, -660478335), f = g(f, i, a, c, n[h + 4], 20, -405537848),
            c = g(c, f, i, a, n[h + 9], 5, 568446438), a = g(a, c, f, i, n[h + 14], 9, -1019803690), i = g(i, a, c, f, n[h + 3], 14, -187363961), f = g(f, i, a, c, n[h + 8], 20, 1163531501),
            c = g(c, f, i, a, n[h + 13], 5, -1444681467), a = g(a, c, f, i, n[h + 2], 9, -51403784), i = g(i, a, c, f, n[h + 7], 14, 1735328473),
            c = v(c, f = g(f, i, a, c, n[h + 12], 20, -1926607734), i, a, n[h + 5], 4, -378558), a = v(a, c, f, i, n[h + 8], 11, -2022574463), i = v(i, a, c, f, n[h + 11], 16, 1839030562), f = v(f, i, a, c, n[h + 14], 23, -35309556),
            c = v(c, f, i, a, n[h + 1], 4, -1530992060), a = v(a, c, f, i, n[h + 4], 11, 1272893353), i = v(i, a, c, f, n[h + 7], 16, -155497632), f = v(f, i, a, c, n[h + 10], 23, -1094730640),
            c = v(c, f, i, a, n[h + 13], 4, 681279174), a = v(a, c, f, i, n[h], 11, -358537222), i = v(i, a, c, f, n[h + 3], 16, -722521979), f = v(f, i, a, c, n[h + 6], 23, 76029189),
            c = v(c, f, i, a, n[h + 9], 4, -640364487), a = v(a, c, f, i, n[h + 12], 11, -421815835), i = v(i, a, c, f, n[h + 15], 16, 530742520),
            c = m(c, f = v(f, i, a, c, n[h + 2], 23, -995338651), i, a, n[h], 6, -198630844), a = m(a, c, f, i, n[h + 7], 10, 1126891415), i = m(i, a, c, f, n[h + 14], 15, -1416354905), f = m(f, i, a, c, n[h + 5], 21, -57434055),
            c = m(c, f, i, a, n[h + 12], 6, 1700485571), a = m(a, c, f, i, n[h + 3], 10, -1894986606), i = m(i, a, c, f, n[h + 10], 15, -1051523), f = m(f, i, a, c, n[h + 1], 21, -2054922799),
            c = m(c, f, i, a, n[h + 8], 6, 1873313359), a = m(a, c, f, i, n[h + 15], 10, -30611744), i = m(i, a, c, f, n[h + 6], 15, -1560198380), f = m(f, i, a, c, n[h + 13], 21, 1309151649),
            c = m(c, f, i, a, n[h + 4], 6, -145523070), a = m(a, c, f, i, n[h + 11], 10, -1120210379), i = m(i, a, c, f, n[h + 2], 15, 718787259), f = m(f, i, a, c, n[h + 9], 21, -343485551),
            c = d(c, r), f = d(f, e), i = d(i, o), a = d(a, u);
        return [c, f, i, a];
    }
    function i(n) { for (var t = '', r = 32 * n.length, e = 0; e < r; e += 8) t += String.fromCharCode(n[e >> 5] >>> e % 32 & 255); return t; }
    function a(n) { var t = []; for (t[(n.length >> 2) - 1] = void 0, e = 0; e < t.length; e += 1) t[e] = 0; for (var r = 8 * n.length, e = 0; e < r; e += 8) t[e >> 5] |= (255 & n.charCodeAt(e / 8)) << e % 32; return t; }
    function e(n) { for (var t, r = '0123456789abcdef', e = '', o = 0; o < n.length; o += 1) t = n.charCodeAt(o), e += r.charAt(t >>> 4 & 15) + r.charAt(15 & t); return e; }
    function r(n) { return unescape(encodeURIComponent(n)); }
    function o(n) { return i(c(a(n = r(n)), 8 * n.length)); }
    return function (n) { return e(o(n)); };
})();

﻿/* ===== 弹幕模块（独立维护：danmaku_logvar.js） ===== */
/*
 * LogVar 弹幕模块（独立文件，不改厂长片源逻辑）
 * 供 csp_CzzyDM.js 使用；纯厂长请用 csp_Czzy.js
 */
var DANMAKU_API = '';
var LastVodName = '';
var LastVodYear = '';
var DanmakuCache = {};
var DanmakuCacheKeys = [];
var DanmakuIndex = {};
var DanmakuPending = {};
var DANMAKU_TIMEOUT = 4000;

function dmEnabled() {
    return !!(DANMAKU_API && String(DANMAKU_API).trim());
}

function cleanSearchName(name) {
    return String(name || '')
        .replace(/正在播放\s*[:：]?/g, ' ')
        .replace(/\[.*?\]/g, ' ')
        .replace(/【.*?】/g, ' ')
        .replace(/[\(（][^)）]*[\)）]/g, ' ')
        .replace(/\b(?:\d{3,4}[pi]|4k|8k|uhd|fhd|qhd|hd|sd|2160p|1440p|1080p|720p|480p|360p)\b/ig, ' ')
        .replace(/\b(?:x264|x265|h\.?264|h\.?265|hevc|av1|vp9|mpeg[- ]?4)\b/ig, ' ')
        .replace(/\b(?:8bit|10bit|12bit|hdr10?\+?|dolby(?:\s*vision)?|atmos|dts|ddp|aac|ac3|eac3|truehd)\b/ig, ' ')
        .replace(/\b(?:web-?dl|blu-?ray|bdrip|hdrip|dvdrip|brrip|hdtv|remux|webrip)\b/ig, ' ')
        .replace(/(蓝光|原盘|超清|高清|标清|国语|粤语|中字|中英|英字|繁体|简体|完整版|未删减|加长版|双语|特效|内嵌|软字幕)/g, ' ')
        .replace(/[\(（]\s*((?:19|20)\d{2})\s*[\)）]/g, ' ')
        .replace(/((?:19|20)\d{2})\s*$/g, '')
        .replace(/[._\-]+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function cnEpisodeNum(text) {
    let s = String(text || '').trim();
    if (!s) return -1;
    if (/^\d+$/.test(s)) return parseInt(s, 10);
    let table = { '零': 0, '〇': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10 };
    if (s === '十') return 10;
    if (s.indexOf('十') === 0) return 10 + (table[s.slice(1)] || 0);
    if (s.indexOf('十') > 0) {
        let parts = s.split('十');
        return (table[parts[0]] || 0) * 10 + (parts[1] ? (table[parts[1]] || 0) : 0);
    }
    return (table[s] !== undefined) ? table[s] : -1;
}

function titleSimilarity(a, b) {
    a = String(a || '').replace(/\s+/g, '');
    b = String(b || '').replace(/\s+/g, '');
    if (!a || !b) return 0;
    if (a === b) return 100;
    if (a.indexOf(b) >= 0 || b.indexOf(a) >= 0) {
        return 100 * Math.min(a.length, b.length) / Math.max(a.length, b.length);
    }
    function grams(s) {
        let g = [];
        for (let i = 0; i < s.length - 1; i++) g.push(s.slice(i, i + 2));
        if (!g.length && s) g.push(s);
        return g;
    }
    let ga = grams(a), gb = grams(b);
    let map = {};
    for (let i = 0; i < ga.length; i++) map[ga[i]] = (map[ga[i]] || 0) + 1;
    let inter = 0;
    for (let i = 0; i < gb.length; i++) {
        if (map[gb[i]]) { inter++; map[gb[i]]--; }
    }
    return 100 * (2 * inter) / ((ga.length + gb.length) || 1);
}

function danmakuTitleCore(name) {
    return cleanSearchName(name)
        .replace(/from\s*\w+/ig, ' ')
        .replace(/第\s*\d+\s*[集期话].*$/g, ' ')
        .replace(/第\s*[零〇一二三四五六七八九十百两]+\s*[集期话].*$/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function normalizeEpisode(episode) {
    let s = String(episode || '').replace(/正在播放\s*[:：]?/g, '').trim();
    if (!s) return '第1集';
    let m = s.match(/[\[【]\s*0*(\d{1,4})\s*[\]】]/);
    if (m) {
        let n = parseInt(m[1], 10);
        if (n < 1900 || n > 2100) return '第' + n + '集';
    }
    m = s.match(/s\d{1,2}\s*e\s*(\d{1,4})/i);
    if (m) return '第' + parseInt(m[1], 10) + '集';
    m = s.match(/第\s*(\d{1,4})\s*([集期话])/);
    if (m) {
        let n = parseInt(m[1], 10);
        if (n >= 1900 && n <= 2100) return '第1集';
        return '第' + n + m[2];
    }
    m = s.match(/第\s*([零〇一二三四五六七八九十百两]+)\s*([集期话])/);
    if (m) {
        let n = cnEpisodeNum(m[1]);
        if (n > 0) return '第' + n + m[2];
    }
    if (/^(EP|E|第)?\s*\d{1,4}\s*(集|期|话)?$/i.test(s)) {
        let num = s.match(/\d+/);
        if (num) {
            let n = parseInt(num[0], 10);
            if (n >= 1900 && n <= 2100) return '第1集';
            return '第' + n + '集';
        }
    }
    if (/(1080|720|480|2160|4k|HD|蓝光|原画|正片|高清|超清|中字|国语|粤语|中英)/i.test(s)) return '第1集';
    m = s.match(/^0*(\d{1,4})$/);
    if (m) {
        let n = parseInt(m[1], 10);
        if (n < 1900 || n > 2100) return '第' + n + '集';
    }
    return s;
}

function parseDanmakuList(body) {
    if (!body) return [];
    let data = typeof body === 'string' ? JSON.parse(body) : body;
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.list)) return data.list;
    if (Array.isArray(data.data)) return data.data;
    if (Array.isArray(data.danmaku)) return data.danmaku;
    return [];
}

function pickDanmakuItems(arr, episode, title, year, limit) {
    if (!Array.isArray(arr) || !arr.length) return [];
    let want = cleanSearchName(title) || '';
    let wantC = want.replace(/\s+/g, '');
    let y = String(year || '').match(/(19|20)\d{2}/);
    y = y ? y[0] : '';
    episode = normalizeEpisode(episode);
    let pref = ['iqiyi', 'qiyi', 'youku', 'qq', 'mgtv', 'bilibili', '优酷', '爱奇艺', '腾讯', '芒果'];
    let scored = [];
    for (let i = 0; i < arr.length; i++) {
        let it = arr[i];
        if (!it) continue;
        let n = String(it.name || '');
        let nl = n.toLowerCase();
        let core = danmakuTitleCore(n);
        let coreC = core.replace(/\s+/g, '');
        let score = 0;
        let exact = false;
        let sim = want ? titleSimilarity(core, want) : 100;
        if (want) {
            if (core === want || coreC === wantC) { score += 220; exact = true; }
            else if (sim >= 80) { score += 160; exact = true; }
            else if (core.indexOf(want) >= 0 || want.indexOf(core) >= 0) {
                score += (Math.min(coreC.length, wantC.length) >= 2) ? 120 : 10;
                exact = Math.abs(coreC.length - wantC.length) <= 4;
            } else if (core.indexOf(want) === 0 || want.indexOf(core) === 0) {
                score += 80; exact = true;
            } else if (sim >= 55) {
                score += Math.floor(sim);
            } else {
                score -= 100;
            }
        }
        if (y) {
            if (n.indexOf(y) >= 0) score += 100;
            else if (/(19|20)\d{2}/.test(n)) score -= exact ? 20 : 80;
        }
        for (let j = 0; j < pref.length; j++) {
            if (nl.indexOf(pref[j].toLowerCase()) >= 0) {
                score += (pref.length - j);
                break;
            }
        }
        if (episode && n.indexOf(episode) >= 0) score += 30;
        let nums = String(episode || '').match(/\d+/);
        if (nums) {
            let re = new RegExp('(^|[^0-9])0*' + parseInt(nums[0], 10) + '([^0-9]|$)');
            if (re.test(n)) score += 25;
        }
        if ((episode === '第1集' || episode === '第1期' || episode === '第1话') && !/第\s*\d+\s*[集期话]/.test(n)) {
            score += 15;
        }
        if (want && !exact && sim < 50 && score < 180) continue;
        scored.push({ it: it, score: score, sim: sim });
    }
    scored.sort((a, b) => (b.score - a.score) || (b.sim - a.sim));
    let out = [];
    let seen = {};
    for (let i = 0; i < scored.length; i++) {
        if (scored[i].score < 80) continue;
        if (want && scored[i].sim < 55 && scored[i].score < 180) continue;
        let url = String((scored[i].it && scored[i].it.url) || '');
        if (!url || seen[url]) continue;
        seen[url] = 1;
        out.push(scored[i].it);
        if (out.length >= (limit || 3)) break;
    }
    return out;
}

function danmakuCacheKey(name, episode, year) {
    let y = String(year || '').match(/(19|20)\d{2}/);
    y = y ? y[0] : '';
    return (cleanSearchName(name) || name) + '\t' + (normalizeEpisode(episode) || '第1集') + '\t' + y;
}

function rememberDanmaku(key, value) {
    DanmakuCache[key] = value;
    let i = DanmakuCacheKeys.indexOf(key);
    if (i >= 0) DanmakuCacheKeys.splice(i, 1);
    DanmakuCacheKeys.push(key);
    while (DanmakuCacheKeys.length > 80) {
        let old = DanmakuCacheKeys.shift();
        delete DanmakuCache[old];
    }
}

function danmakuOrigin() {
    let api = String(DANMAKU_API || '');
    let m = api.match(/^(https?:\/\/[^/]+\/[^/?#]+)/);
    if (m) return m[1];
    return api.replace(/\/api\/.*$/, '').replace(/\/$/, '');
}

async function reqJson(url, timeout) {
    const res = await req(url, {
        headers: { 'User-Agent': MOBILE_UA },
        timeout: timeout || DANMAKU_TIMEOUT,
    });
    let body = res && res.content;
    if (!body) return null;
    return typeof body === 'string' ? JSON.parse(body) : body;
}

async function searchDanmakuEpisodes(name) {
    let origin = danmakuOrigin();
    if (!origin || !name) return [];
    let data = await reqJson(origin + '/api/v2/search/episodes?anime=' + encodeURIComponent(name));
    let animes = (data && data.animes) || [];
    let arr = [];
    for (let i = 0; i < animes.length; i++) {
        let a = animes[i] || {};
        let eps = a.episodes || [];
        for (let j = 0; j < eps.length; j++) {
            let e = eps[j] || {};
            if (!e.episodeId) continue;
            arr.push({
                name: String((a.animeTitle || '') + ' ' + (e.episodeTitle || '') + ' ' + (a.source || '')),
                url: origin + '/api/v2/comment/' + e.episodeId + '?format=xml',
            });
        }
    }
    return arr;
}

async function searchDanmakuFongmi(name, episode) {
    let api = DANMAKU_API;
    let ep = episode || '第1集';
    if (api.indexOf('{name}') >= 0) {
        api = api.replace('{name}', encodeURIComponent(name)).replace('{episode}', encodeURIComponent(ep));
    } else {
        api += (api.indexOf('?') >= 0 ? '&' : '?') + 'name=' + encodeURIComponent(name) + '&episode=' + encodeURIComponent(ep);
    }
    return parseDanmakuList(await reqJson(api));
}

async function searchDanmaku(name, episode) {
    try {
        let arr = await searchDanmakuEpisodes(name);
        if (arr.length) return arr;
    } catch (e) {}
    try {
        return await searchDanmakuFongmi(name, episode);
    } catch (e) {
        return [];
    }
}

async function loadDanmakuIndex(name) {
    let t = cleanSearchName(name) || name;
    if (!t || !dmEnabled()) return [];
    if (DanmakuIndex[t]) return DanmakuIndex[t];
    if (DanmakuPending[t]) return DanmakuPending[t];
    DanmakuPending[t] = (async function () {
        try {
            DanmakuIndex[t] = (await searchDanmaku(t, '第1集')) || [];
            return DanmakuIndex[t];
        } catch (e) {
            return [];
        } finally {
            delete DanmakuPending[t];
        }
    })();
    return DanmakuPending[t];
}

function packDanmakuList(title, episode, items) {
    if (!items || !items.length) return [];
    let out = [];
    for (let i = 0; i < items.length; i++) {
        let it = items[i];
        if (!it || !it.url) continue;
        out.push({
            name: String(it.name || (title + ' ' + episode)).slice(0, 80),
            url: String(it.url),
        });
    }
    return out;
}

function collectEpisodeNames(kurls, ktabs) {
    let names = [];
    for (let i = 0; i < kurls.length; i++) {
        if (/磁力|网盘/.test(ktabs[i] || '')) continue;
        let parts = String(kurls[i] || '').split('#');
        for (let j = 0; j < parts.length; j++) {
            let cut = parts[j].lastIndexOf('$');
            if (cut <= 0) continue;
            let n = parts[j].slice(0, cut);
            if (n && names.indexOf(n) < 0) names.push(n);
        }
    }
    return names;
}

function applyDanmakuCache(title, episodeNames, year) {
    let t = cleanSearchName(title) || title;
    let arr = DanmakuIndex[t];
    if (!arr || !arr.length) return;
    let eps = (episodeNames && episodeNames.length) ? episodeNames : ['第1集'];
    for (let i = 0; i < eps.length && i < 40; i++) {
        let packed = packDanmakuList(t, eps[i], pickDanmakuItems(arr, eps[i], t, year, 3));
        if (packed.length) rememberDanmaku(danmakuCacheKey(t, eps[i], year), packed);
    }
}

function pickCachedDanmaku(name, episode, year) {
    let key = danmakuCacheKey(name, episode, year);
    if (DanmakuCache[key]) return DanmakuCache[key];
    let t = cleanSearchName(name) || name;
    let arr = t && DanmakuIndex[t];
    if (!arr || !arr.length) return [];
    episode = normalizeEpisode(episode);
    return packDanmakuList(t, episode || '第1集', pickDanmakuItems(arr, episode || '第1集', t, year, 3));
}

function parsePlayMeta(ids) {
    let raw = Array.isArray(ids) ? String(ids[0] || '') : String(ids || '');
    let playId = raw;
    let name = LastVodName || '';
    let episode = '';
    let year = LastVodYear || '';
    if (raw.indexOf('||') >= 0) {
        let bits = raw.split('||');
        playId = bits[0];
        try { name = decodeURIComponent(bits[1] || '') || name; } catch (e) { name = bits[1] || name; }
        try { episode = decodeURIComponent(bits[2] || ''); } catch (e) { episode = bits[2] || ''; }
        try { year = decodeURIComponent(bits[3] || '') || year; } catch (e) { year = bits[3] || year; }
    }
    if (!episode) episode = '第1集';
    return { playId, name, episode, year };
}

function shortDanmakuLabel(name) {
    let s = String(name || '').replace(/\s+/g, ' ').replace(/from\s+/ig, '').trim();
    if (s.length > 36) s = s.slice(0, 36) + '…';
    return s || '弹幕';
}

function attachPlayMeta(kurls, title, year) {
    if (!title || !kurls || !kurls.length) return kurls;
    return kurls.map(line => line.split('#').map(ep => {
        let i = ep.lastIndexOf('$');
        if (i < 0) return ep;
        let epName = ep.slice(0, i);
        let playId = ep.slice(i + 1);
        if (!playId || playId.indexOf('||') >= 0) return ep;
        return epName + '$' + playId + '||' + encodeURIComponent(title) + '||' + encodeURIComponent(epName) + '||' + encodeURIComponent(year || '');
    }).join('#'));
}


async function pushDanmaku(url) {
    if (!url) return;
    let path = encodeURIComponent(String(url));
    let ports = [9978, 9979, 9980, 9981, 9982];
    for (let i = 0; i < ports.length; i++) {
        try {
            await req('http://127.0.0.1:' + ports[i] + '/action?do=refresh&type=danmaku&path=' + path, {
                headers: { 'User-Agent': 'okhttp/3.12.11' },
                timeout: 600,
            });
            return;
        } catch (e) {}
    }
}

/* ===== 弹幕模块结束 ===== */


function makeSign(ts) {
    return md5Pure(SIGN_SALT + String(ts));
}

function formBody(obj) {
    if (!obj) return '';
    if (typeof obj === 'string') return obj;
    var parts = [];
    for (var k in obj) {
        if (!Object.prototype.hasOwnProperty.call(obj, k)) continue;
        parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(obj[k] == null ? '' : String(obj[k])));
    }
    return parts.join('&');
}

function pickReqText(res) {
    if (res == null) return '';
    if (typeof res === 'string') return res;
    if (res.content != null) return String(res.content);
    if (res.body != null) return String(res.body);
    if (res.data != null && typeof res.data === 'string') return res.data;
    return '';
}

async function request(reqUrl, options) {
    options = options || {};
    var method = (options.method || 'GET').toUpperCase();
    var headers = (options.headers && typeof options.headers === 'object') ? options.headers : { 'User-Agent': MOBILE_UA };
    var timeout = parseInt(options.timeout, 10) > 0 ? parseInt(options.timeout, 10) : TIMEOUT;
    var opt = { headers: headers, timeout: timeout, method: method };
    if (method === 'POST') {
        opt.body = typeof options.body === 'string' ? options.body : formBody(options.body || {});
        opt.postType = 'form';
    }
    try {
        var text = pickReqText(await req(reqUrl, opt));
        if (text) return text;
    } catch (e) {}
    if (method === 'POST' && typeof post === 'function') {
        try {
            return pickReqText(post(reqUrl, opt.body, { headers: headers })) || '';
        } catch (e2) {}
    }
    return '';
}

async function apiPost(path, fields) {
    var ts = String(Math.floor(Date.now() / 1000));
    var body = Object.assign({}, fields || {}, {
        sign: makeSign(ts),
        timestamp: ts,
    });
    var raw = await request(HOST + path, {
        method: 'POST',
        headers: {
            'User-Agent': API_UA,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body,
        timeout: TIMEOUT,
    });
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (e) {
        console.error('热播 JSON 解析失败：', e.message);
        return null;
    }
}

function parseExtend(extend) {
    if (!extend) return {};
    if (typeof extend === 'string') {
        try { return JSON.parse(extend) || {}; } catch (e) { return {}; }
    }
    return typeof extend === 'object' ? extend : {};
}

function pickFirstId(ids) {
    if (ids == null) return '';
    if (Array.isArray(ids)) return String(ids[0] || '');
    return String(ids);
}

function asList(v) {
    if (!v) return [];
    if (Array.isArray(v)) return v;
    if (typeof v === 'object') return Object.keys(v).map(function (k) { return v[k]; });
    return [];
}

function filterValues(arr, allName) {
    var out = [{ n: allName, v: '' }];
    var list = asList(arr);
    for (var i = 0; i < list.length; i++) {
        var item = list[i];
        var name = '';
        if (item == null) continue;
        if (typeof item === 'string' || typeof item === 'number') name = String(item);
        else name = String(item.n || item.name || item.v || item.value || '');
        if (!name || name === '全部') continue;
        out.push({ n: name, v: name });
    }
    return out;
}

function vodItem(it) {
    if (!it) return null;
    return {
        vod_id: String(it.vod_id || ''),
        vod_name: it.vod_name || '',
        vod_pic: it.vod_pic || it.vod_pic_thumb || '',
        vod_remarks: it.vod_remarks || '',
    };
}

function parseVodList(list) {
    var out = [];
    var arr = asList(list);
    for (var i = 0; i < arr.length; i++) {
        var v = vodItem(arr[i]);
        if (v && v.vod_id) out.push(v);
    }
    return out;
}

function isDirectMedia(url) {
    var s = String(url || '');
    if (!s) return false;
    if (/\.(m3u8|mp4|mkv|flv|ts|iso|mpd)(\?|$)/i.test(s)) return true;
    if (/^https?:\/\//i.test(s) && s.indexOf('=') < 0) return true;
    return false;
}

function playHeader(extraUa) {
    return {
        'User-Agent': extraUa || MOBILE_UA,
    };
}

function playResult(url, extraUa, danmaku) {
    var out = {
        jx: 0,
        parse: 0,
        url: url || '',
        header: playHeader(extraUa),
    };
    if (danmaku) out.danmaku = String(danmaku);
    return JSON.stringify(out);
}

async function init(cfg) {
    try {
        HOST = DEFAULT_HOST;
        TIMEOUT = 10000;
        if (cfg) {
            siteKey = cfg.skey || cfg.key || siteKey || '';
            siteType = cfg.stype != null ? cfg.stype : (cfg.type != null ? cfg.type : siteType);
        }
        var ext = cfg && cfg.ext !== undefined ? cfg.ext : cfg;
        if (typeof ext === 'string' && ext.trim()) {
            var s = ext.trim();
            if (s.charAt(0) === '{') {
                try { ext = JSON.parse(s); } catch (e) { HOST = s.replace(/\/$/, ''); ext = null; }
            } else {
                HOST = s.replace(/\/$/, '');
                ext = null;
            }
        }
        if (ext && typeof ext === 'object') {
            if (ext.host) HOST = String(ext.host).replace(/\/$/, '');
            if (ext.timeout) TIMEOUT = parseInt(ext.timeout, 10) || TIMEOUT;
            if (ext.danmaku) DANMAKU_API = String(ext.danmaku).trim();
        }
        if (!DANMAKU_API) {
            DANMAKU_API = 'http://47.103.92.65:9321/DMQlCpHvSpxj4uQofGTafer8y_aL1XDa/api/v2/fongmi/danmaku';
        }
    } catch (e) {
        HOST = DEFAULT_HOST;
    }
}

async function home(filter) {
    try {
        var data = await apiPost('/v3/type/top_type', {});
        var list = data && data.data && data.data.list ? data.data.list : [];
        var classes = [];
        var filters = {};
        for (var i = 0; i < list.length; i++) {
            var t = list[i] || {};
            var tid = String(t.type_id || '');
            if (!tid) continue;
            classes.push({ type_id: tid, type_name: t.type_name || tid });
            filters[tid] = [
                { key: 'class', name: '剧情', value: filterValues(t.extend, '全部剧情') },
                { key: 'area', name: '地区', value: filterValues(t.area, '全部地区') },
                { key: 'lang', name: '语言', value: filterValues(t.lang, '全部语言') },
                { key: 'year', name: '时间', value: filterValues(t.year, '全部时间') },
            ];
        }
        return JSON.stringify({ class: classes, filters: filters, jx: 0, parse: 0 });
    } catch (e) {
        console.error('热播分类失败：', e.message);
        return JSON.stringify({ class: [], filters: {} });
    }
}

async function homeVod() {
    try {
        var data = await apiPost('/v3/home/type_search', {
            area: '',
            year: '',
            type_id: '10',
            page: '1',
            lang: '',
            class: '',
        });
        return JSON.stringify({ list: parseVodList(data && data.data && data.data.list) });
    } catch (e) {
        return JSON.stringify({ list: [] });
    }
}

async function category(tid, pg, filter, extend) {
    try {
        pg = parseInt(pg, 10);
        pg = pg > 0 ? pg : 1;
        var fl = parseExtend(extend);
        var data = await apiPost('/v3/home/type_search', {
            area: fl.area || '',
            year: fl.year || '',
            type_id: tid || '',
            page: String(pg),
            lang: fl.lang || '',
            class: fl['class'] || '',
        });
        var list = parseVodList(data && data.data && data.data.list);
        return JSON.stringify({
            page: pg,
            pagecount: 999999,
            limit: list.length,
            total: 999999,
            list: list,
        });
    } catch (e) {
        console.error('热播分类页失败：', e.message);
        return JSON.stringify({ page: 1, pagecount: 1, limit: 0, total: 0, list: [] });
    }
}

async function search(wd, quick, pg) {
    try {
        if (!wd) return JSON.stringify({ list: [] });
        var data = await apiPost('/v3/home/search', { keyword: String(wd) });
        return JSON.stringify({ list: parseVodList(data && data.data && data.data.list) });
    } catch (e) {
        console.error('热播搜索失败：', e.message);
        return JSON.stringify({ list: [] });
    }
}

async function detail(ids) {
    try {
        var id = pickFirstId(ids);
        if (!id) return JSON.stringify({ list: [] });
        var data = await apiPost('/v3/home/vod_details', { vod_id: id });
        var vod = data && data.data ? data.data : null;
        if (!vod) return JSON.stringify({ list: [] });

        var tabs = [];
        var kurls = [];
        var playList = asList(vod.vod_play_list);
        for (var i = 0; i < playList.length; i++) {
            var pl = playList[i] || {};
            var title = pl.title || pl.name || ('线路' + (i + 1));
            var parses = asList(pl.parse_urls);
            var parseUrl = parses.length ? String(parses[0] || '') : '';
            var urls = asList(pl.urls);
            var eps = [];
            for (var j = 0; j < urls.length; j++) {
                var ep = urls[j] || {};
                var n = String(ep.name || '').replace(/\$/g, '_');
                var u = String(ep.url || '');
                if (!n || !u) continue;
                if (parseUrl) eps.push(n + '$' + parseUrl + encodeURIComponent(u));
                else eps.push(n + '$' + u);
            }
            if (!eps.length) continue;
            tabs.push(title);
            kurls.push(eps.join('#'));
        }

        var titleName = vod.vod_name || '';
        var year = String(vod.vod_year || '');
        LastVodName = titleName;
        LastVodYear = year;
        var danmakuTask = null;
        if (dmEnabled() && titleName) {
            danmakuTask = loadDanmakuIndex(titleName);
            kurls = attachPlayMeta(kurls, titleName, year);
        }

        var out = JSON.stringify({
            list: [{
                vod_id: id,
                vod_name: titleName,
                vod_pic: vod.vod_pic || '',
                vod_year: year,
                vod_area: vod.vod_area || '',
                vod_class: vod.vod_class || '',
                vod_content: String(vod.vod_content || '').replace(/<[^>]*>/g, ''),
                vod_actor: vod.vod_actor || '',
                vod_director: vod.vod_director || '',
                vod_play_from: tabs.join('$$$'),
                vod_play_url: kurls.join('$$$'),
            }],
        });
        if (danmakuTask) {
            try {
                await danmakuTask;
                applyDanmakuCache(titleName, collectEpisodeNames(kurls, tabs), year);
            } catch (e) {}
        }
        return out;
    } catch (e) {
        console.error('热播详情失败：', e.message);
        return JSON.stringify({ list: [] });
    }
}

function queryParam(url, key) {
    var m = String(url || '').match(new RegExp('[?&]' + key + '=([^&]*)'));
    if (!m) return '';
    try { return decodeURIComponent(m[1]); } catch (e) { return m[1]; }
}

async function resolvePlayUrl(id) {
    var url = String(id || '').trim();
    if (!url) return { url: '', ua: '' };
    if (isDirectMedia(url)) return { url: url, ua: '' };
    var raw = await request(url, {
        method: 'GET',
        headers: { 'User-Agent': MOBILE_UA },
        timeout: TIMEOUT,
    });
    if (raw) {
        try {
            var j = JSON.parse(raw);
            var msg = String(j.msg || '');
            if (!msg || msg.indexOf('错误') < 0) {
                var play = j.url || j.data || '';
                if (typeof play === 'object') play = play.url || '';
                if (play) return { url: String(play), ua: j.UA || j.ua || '' };
            }
        } catch (e) {}
    }
    var fallback = queryParam(url, 'url');
    return { url: fallback || url, ua: '' };
}

async function play(flag, ids, flags) {
    try {
        var meta = parsePlayMeta(ids);
        var playId = meta.playId || pickFirstId(ids);
        if (playId.indexOf('$') >= 0) playId = playId.split('$').pop();
        playId = String(playId || '').split('||')[0].trim();
        if (!playId) return playResult('', '', '');

        var dmWait = (dmEnabled() && meta.name) ? loadDanmakuIndex(meta.name) : null;
        var resolved = await resolvePlayUrl(playId);
        var danmaku = '';
        if (meta && dmEnabled()) {
            if (dmWait) {
                try { await dmWait; } catch (e) {}
            }
            var items = pickCachedDanmaku(meta.name, meta.episode, meta.year);
            if (items.length && items[0] && items[0].url) {
                danmaku = String(items[0].url);
                try { await pushDanmaku(danmaku); } catch (e) {}
            }
        }
        return playResult(resolved.url, resolved.ua, danmaku);
    } catch (e) {
        console.error('热播播放失败：', e.message);
        return JSON.stringify({ jx: 0, parse: 0, url: '', msg: e.message });
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
    };
}
