/*
 * title: JRKAN直播
 * host: http://m.jrkan2023.com/
 * 说明: FongMi/OK影视 JS Spider · 体育赛事直播（赛程从 index.js 解析，播放取真实 m3u8）
 */
var HOST = 'http://m.jrkan2023.com';
var HOME = HOST + '/?lan=1';
var IDX  = 'https://im-imgs-bucket.oss-accelerate.aliyuncs.com/index.js';
var UA   = 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36';
var HDRS = {'User-Agent': UA, 'Referer': HOST + '/', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'zh-CN,zh;q=0.9'};

var CLASSES = [
    {type_id: 'all',   type_name: '全部'},
    {type_id: '1',     type_name: '足球'},
    {type_id: '2',     type_name: '篮球'},
    {type_id: 'other', type_name: '其他'}
];
var LINEHOSTS = {'line1': 'http://m.sportsteam53.com', 'line2': 'http://m.jw1104.com', 'line3': 'http://play.sportsteam356.com'};

/* ---------- 工具 ---------- */
function b64d(s) {
    var C = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    var t = String(s || '').replace(/[^A-Za-z0-9+\/=]/g, '');
    var o = '', i, e1, e2, e3, e4, c1, c2, c3;
    for (i = 0; i < t.length; i += 4) {
        e1 = C.indexOf(t.charAt(i)); e2 = C.indexOf(t.charAt(i + 1));
        e3 = C.indexOf(t.charAt(i + 2)); e4 = C.indexOf(t.charAt(i + 3));
        c1 = (e1 << 2) | (e2 >> 4);
        c2 = ((e2 & 15) << 4) | (e3 >> 2);
        c3 = ((e3 & 3) << 6) | e4;
        o += String.fromCharCode(c1);
        if (e3 >= 0 && e3 !== 64) o += String.fromCharCode(c2);
        if (e4 >= 0 && e4 !== 64) o += String.fromCharCode(c3);
    }
    return o;
}
function origin(u) { var m = String(u || '').match(/^https?:\/\/[^\/]+/); return m ? m[0] : HOST; }
function abs(u, base) { u = String(u || '').trim(); if (!u) return ''; if (/^https?:/i.test(u)) return u; if (u.indexOf('//') === 0) return 'http:' + u; return origin(base) + (u.charAt(0) === '/' ? u : '/' + u); }

async function fetchText(url) {
    try {
        var res = await req(url, {headers: HDRS, timeout: 15000, method: 'GET'});
        if (res && res.content != null) return String(res.content);
        if (typeof res === 'string') return res;
    } catch (e) {}
    return '';
}

/* ---------- 解析：播放线路域名 ---------- */
function parseHosts(html) {
    var m, re = /line(\d)\s*:\s*atob\("([^"]+)"\)/g;
    while ((m = re.exec(html)) !== null) { LINEHOSTS['line' + m[1]] = b64d(m[2]); }
}

/* ---------- 解析：赛程列表（index.js） ---------- */
function parseMatches(js) {
    var out = [], seen = {};
    var re = /<ul class="item play d-touch[^"]*"\s+data-lid="([^"]*)"\s+data-stype="[^"]*">([\s\S]*?)<\/ul>/g, m;
    while ((m = re.exec(js)) !== null) {
        var lid = m[1], body = m[2];
        var sport = (lid.split(',')[1] || '').trim();   /* 1=足球 2=篮球 其余=其他 */
        var g = function (p) { var r = body.match(p); return r ? r[1].trim() : ''; };
        var league = g(/<span class="name">([^<]+)<\/span>/);
        var time   = g(/<li class="lab_time">([^<]*)<\/li>/);
        var home   = g(/<li class="lab_team_home"><strong class="name">([^<]*)<\/strong>/);
        var away   = g(/<li class="lab_team_away"><strong class="name">([^<]*)<\/strong>/);
        var pic    = g(/<li class="lab_team_home">[\s\S]*?<img[^>]*src="([^"]+)"/);
        var sm     = body.match(/getPlayUrl\("line\d"\s*,\s*"(\d+)"\)/);
        var sid    = sm ? sm[1] : '';
        if (!home || !away) continue;
        var name = home + ' VS ' + away;
        var key = sid || name;
        if (seen[key]) continue;
        seen[key] = 1;
        var remark = (league ? league : '直播') + (time ? ' ' + time : '');
        /* 开赛时间戳：把北京钟面时间当 UTC 处理，与 nowBj() 同基准 */
        var start = 0;
        var t = time.match(/(\d+)-(\d+)\s+(\d+):(\d+)/);
        if (t) start = Date.UTC(new Date(Date.now() + 8 * 3600000).getUTCFullYear(), +t[1] - 1, +t[2], +t[3], +t[4]);
        out.push({vod_id: key, vod_name: name, vod_pic: pic, vod_remarks: remark, _sport: sport, _start: start});
    }
    return out;
}

/* ---------- 解析：播放页线路（data-play） ---------- */
function parseLines(html, base) {
    var out = [], seen = {}, re = /data-play="([^"]+)"[^>]*>[\s\S]{0,200}?<strong>([^<]*)<\/strong>/g, m;
    while ((m = re.exec(html)) !== null) {
        var p = m[1], n = (m[2] || '').trim();
        if (!p || p.indexOf('/play') !== 0) continue;
        if (p.indexOf('=&') >= 0) continue;
        var u = abs(p, base);
        if (seen[u]) continue;
        seen[u] = 1;
        out.push({n: n || ('线路' + (out.length + 1)), u: u});
    }
    return out;
}

/* ---------- 站点把主域名倒序混淆: remmuszs → szsummer ---------- */
function deobf(u) {
    var m = String(u || '').match(/^(https?:)?\/\/([^\/]+)([\s\S]*)$/);
    if (!m) return u;
    var proto = m[1] || 'http:';
    var hp = m[2].split(':');
    var parts = hp[0].split('.');
    if (parts.length >= 2) {
        var i = parts.length - 2;
        parts[i] = parts[i].split('').reverse().join('');
    }
    hp[0] = parts.join('.');
    return proto + '//' + hp.join(':') + m[3];
}

/* ---------- 解析：真实播放地址 ---------- */
function pickUrl(html) {
    var h = String(html || '').replace(/\\\//g, '/');
    /* 形如 xxx/msss.html?id=//real.com/live/1.m3u8?auth_key=...  →
       提取内层直链；该域名被站点倒序混淆，需还原 */
    var w = h.match(/[?&](?:id|url)=((?:https?:)?\/\/[^"'\s<>\\]+\.m3u8[^"'\s<>\\]*)/);
    if (w) {
        var r = w[1];
        if (r.indexOf('//') === 0) r = 'http:' + r;
        return deobf(r);
    }
    var m = h.match(/https?:\/\/[^"'\s<>\\]+\.m3u8[^"'\s<>\\]*/);
    if (m) return m[0].trim();
    m = h.match(/["'](\/\/[^"'\s<>\\]+\.m3u8[^"'\s<>\\]*)/);
    if (m) return ('http:' + m[1]).trim();
    m = h.match(/https?:\/\/[^"'\s<>\\]+\.(mp4|flv)[^"'\s<>\\]*/);
    if (m) return m[0].trim();
    return '';
}

/* ---------- 解析：首页赛程（含线路域名） ---------- */
async function loadMatches() {
    var home = await fetchText(HOME);
    if (home) parseHosts(home);
    var js = await fetchText(IDX + '?t=' + Date.now());
    if (!js) js = await fetchText(IDX);
    return parseMatches(js);
}

/* 北京时间毫秒戳（把北京钟面当 UTC，与 _start 同基准） */
function nowBj() { return Date.now() + 8 * 3600000; }

/* 只显示"正在直播"的：开赛前15分钟 ~ 开赛后3.5小时内可播 */
var LIVE_ONLY = true;          /* 想显示全部赛程改成 false */
var BEFORE_MS = 15 * 60000;    /* 提前15分钟放出来，方便蹲守 */
var AFTER_MS  = 150 * 60000;   /* 开赛后2.5小时仍显示（覆盖足球加时/篮球全场） */

function onlyLive(list) {
    if (!LIVE_ONLY) return list;
    var n = nowBj();
    return list.filter(function (v) {
        if (!v._start) return false;
        return n >= v._start - BEFORE_MS && n <= v._start + AFTER_MS;
    });
}

/* 剥离内部字段后返回给客户端 */
function clean(list) {
    return list.map(function (v) {
        return {vod_id: v.vod_id, vod_name: v.vod_name, vod_pic: v.vod_pic, vod_remarks: v.vod_remarks};
    });
}
function filterByTid(list, tid) {
    tid = String(tid || 'all').toLowerCase();
    var l = onlyLive(list);
    if (tid === 'all' || tid === '' || tid === 'live') return l;
    return l.filter(function (v) {
        var s = String(v._sport || '');
        if (tid === '1') return s === '1';
        if (tid === '2') return s === '2';
        if (tid === 'other') return s !== '1' && s !== '2';
        return true;
    });
}

/* ---------- 接口 ---------- */
async function init(cfg) { return ''; }

async function home(filter) {
    try { return JSON.stringify({class: CLASSES, filters: {}}); }
    catch (e) { return JSON.stringify({class: [], filters: {}}); }
}

async function homeVod() {
    try { return JSON.stringify({list: clean(onlyLive(await loadMatches()))}); }
    catch (e) { return JSON.stringify({list: []}); }
}

async function category(tid, pg, filter, extend) {
    try {
        var l = filterByTid(await loadMatches(), tid);
        return JSON.stringify({page: 1, pagecount: 1, limit: l.length || 30, total: l.length, list: clean(l)});
    }
    catch (e) { return JSON.stringify({page: 1, pagecount: 1, limit: 30, total: 0, list: []}); }
}

async function search(wd, quick, pg) { return JSON.stringify({list: []}); }

async function detail(ids) {
    try {
        var sid = String(Object.prototype.toString.call(ids) === '[object Array]' ? (ids[0] || '') : (ids || '')).trim();
        if (!sid) return JSON.stringify({list: []});
        var name = sid, league = '', pic = '';
        try {
            var all = await loadMatches(), i;
            for (i = 0; i < all.length; i++) { if (all[i].vod_id === sid) { name = all[i].vod_name; league = all[i].vod_remarks; pic = all[i].vod_pic; break; } }
        } catch (e) {}
        var keys = ['line1', 'line2', 'line3'], k, steam = '', html = '';
        for (k = 0; k < keys.length; k++) {
            var base = LINEHOSTS[keys[k]];
            if (!base || base.indexOf('http') !== 0) continue;
            var tryUrl = base + '/play/steam' + sid + '.html';
            html = await fetchText(tryUrl);
            if (html && html.indexOf('data-play') >= 0) { steam = tryUrl; break; }
        }
        var lines = steam ? parseLines(html, steam) : [];
        var from = ['JRKAN直播'], url = [];
        if (lines.length) url.push(lines.map(function (x) { return x.n + '$' + x.u; }).join('#'));
        else url.push('默认线路$' + HOST + '/');
        return JSON.stringify({list: [{
            vod_id: sid,
            vod_name: name,
            vod_pic: pic,
            vod_remarks: league,
            vod_content: (league ? league + '  ' : '') + name,
            vod_play_from: from.join('$$$'),
            vod_play_url: url.join('$$$')
        }]});
    } catch (e) { return JSON.stringify({list: [], msg: String(e && e.message || e)}); }
}

async function play(flag, ids, flags) {
    try {
        var pid = String(Object.prototype.toString.call(ids) === '[object Array]' ? (ids[0] || '') : (ids || '')).trim();
        if (pid.indexOf('$') >= 0) pid = pid.split('$').pop();
        pid = pid.trim();
        if (!pid) return JSON.stringify({parse: 0, jx: 0, url: ''});
        if (!/^https?:/i.test(pid)) pid = HOST + pid;
        var html = await fetchText(pid);
        var url = pickUrl(html);
        /* sm.html?=N 是套壳页，真实播放页为 /play/N.html */
        if (!url) {
            var qm = pid.match(/[?&]id=(\d+)/);
            if (qm) {
                var real = origin(pid) + '/play/' + qm[1] + '.html';
                var h2 = await fetchText(real);
                url = pickUrl(h2);
                if (!url) {
                    var fm = String(h2).match(/<iframe[^>]*src="([^"]+)"/);
                    if (fm) url = pickUrl(await fetchText(abs(fm[1], real)));
                }
            }
        }
        /* 兜底：页面内第一个 iframe */
        if (!url) {
            var m = String(html).match(/<iframe[^>]*src="([^"]+)"/);
            if (m) { var u = abs(m[1], pid); url = u.indexOf('m3u8') >= 0 ? u : pickUrl(await fetchText(u)); }
        }
        return JSON.stringify({parse: 0, jx: 0, url: url, header: HDRS});
    } catch (e) { return JSON.stringify({parse: 0, jx: 0, url: '', msg: String(e && e.message || e)}); }
}

export default {init, home, homeVod, category, search, detail, play};