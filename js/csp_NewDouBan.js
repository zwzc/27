/*
 * title: 豆瓣推荐（移植自 jar NewDouBan / NewDouBanGuard）
 * 说明: 仅作发现/换源索引（indexs），点片名会到其它可换源站搜索
 * 对应 Java: com.github.catvod.spider.NewDouBan
 */

var API_KEY = '0ac44ae016490db2204ce0a042db2916';
var HOST = 'https://frodo.douban.com/api/v2';
var FILTER_URL = '';
var FILTERS = null;

var DoubanHeaders = {
    Host: 'frodo.douban.com',
    Connection: 'Keep-Alive',
    Referer: 'https://servicewechat.com/wx2f9b06c1de1ccfca/84/page-frame.html',
    'User-Agent':
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
};

var CLASSES = [
    { type_id: 'hot_gaia', type_name: '热门电影' },
    { type_id: 'tv_hot', type_name: '热播剧集' },
    { type_id: 'show_hot', type_name: '热播综艺' },
    { type_id: 'movie', type_name: '电影筛选' },
    { type_id: 'tv', type_name: '电视筛选' },
    { type_id: 'rank_list_movie', type_name: '电影榜单' },
    { type_id: 'rank_list_tv', type_name: '电视剧榜单' },
];

var DEFAULT_FILTERS = {
    hot_gaia: [
        {
            key: 'sort',
            name: '排序',
            value: [
                { n: '热度', v: 'recommend' },
                { n: '最新', v: 'time' },
                { n: '评分', v: 'rank' },
            ],
        },
        {
            key: 'area',
            name: '地区',
            value: [
                { n: '全部', v: '全部' },
                { n: '华语', v: '华语' },
                { n: '欧美', v: '欧美' },
                { n: '韩国', v: '韩国' },
                { n: '日本', v: '日本' },
            ],
        },
    ],
    tv_hot: [
        {
            key: 'type',
            name: '分类',
            value: [
                { n: '综合', v: 'tv_hot' },
                { n: '国产剧', v: 'tv_domestic' },
                { n: '欧美剧', v: 'tv_american' },
                { n: '日剧', v: 'tv_japanese' },
                { n: '韩剧', v: 'tv_korean' },
                { n: '动画', v: 'tv_animation' },
            ],
        },
    ],
    show_hot: [
        {
            key: 'type',
            name: '分类',
            value: [
                { n: '综合', v: 'show_hot' },
                { n: '国内', v: 'show_domestic' },
                { n: '国外', v: 'show_foreign' },
            ],
        },
    ],
    movie: [
        {
            key: '类型',
            name: '类型',
            value: [
                { n: '全部类型', v: '' },
                { n: '喜剧', v: '喜剧' },
                { n: '爱情', v: '爱情' },
                { n: '动作', v: '动作' },
                { n: '科幻', v: '科幻' },
                { n: '动画', v: '动画' },
                { n: '悬疑', v: '悬疑' },
                { n: '犯罪', v: '犯罪' },
                { n: '惊悚', v: '惊悚' },
                { n: '冒险', v: '冒险' },
                { n: '音乐', v: '音乐' },
                { n: '历史', v: '历史' },
                { n: '奇幻', v: '奇幻' },
                { n: '恐怖', v: '恐怖' },
                { n: '战争', v: '战争' },
                { n: '传记', v: '传记' },
                { n: '歌舞', v: '歌舞' },
                { n: '武侠', v: '武侠' },
                { n: '情色', v: '情色' },
                { n: '灾难', v: '灾难' },
                { n: '西部', v: '西部' },
                { n: '纪录片', v: '纪录片' },
                { n: '短片', v: '短片' },
            ],
        },
        {
            key: '地区',
            name: '地区',
            value: [
                { n: '全部地区', v: '' },
                { n: '华语', v: '华语' },
                { n: '欧美', v: '欧美' },
                { n: '韩国', v: '韩国' },
                { n: '日本', v: '日本' },
                { n: '中国大陆', v: '中国大陆' },
                { n: '美国', v: '美国' },
                { n: '中国香港', v: '中国香港' },
                { n: '中国台湾', v: '中国台湾' },
                { n: '英国', v: '英国' },
                { n: '法国', v: '法国' },
                { n: '德国', v: '德国' },
                { n: '意大利', v: '意大利' },
                { n: '西班牙', v: '西班牙' },
                { n: '印度', v: '印度' },
                { n: '泰国', v: '泰国' },
                { n: '俄罗斯', v: '俄罗斯' },
                { n: '加拿大', v: '加拿大' },
                { n: '澳大利亚', v: '澳大利亚' },
                { n: '爱尔兰', v: '爱尔兰' },
                { n: '瑞典', v: '瑞典' },
                { n: '巴西', v: '巴西' },
                { n: '丹麦', v: '丹麦' },
            ],
        },
        {
            key: 'sort',
            name: '排序',
            value: [
                { n: '近期热度', v: 'T' },
                { n: '首映时间', v: 'R' },
                { n: '高分优先', v: 'S' },
            ],
        },
        {
            key: '年代',
            name: '年代',
            value: [
                { n: '全部年代', v: '' },
                { n: '2026', v: '2026' },
                { n: '2025', v: '2025' },
                { n: '2024', v: '2024' },
                { n: '2023', v: '2023' },
                { n: '2022', v: '2022' },
                { n: '2021', v: '2021' },
                { n: '2020', v: '2020' },
                { n: '2019', v: '2019' },
                { n: '2010年代', v: '2010年代' },
                { n: '2000年代', v: '2000年代' },
                { n: '90年代', v: '90年代' },
                { n: '80年代', v: '80年代' },
                { n: '70年代', v: '70年代' },
                { n: '60年代', v: '60年代' },
                { n: '更早', v: '更早' },
            ],
        },
    ],
    tv: [
        {
            key: '类型',
            name: '类型',
            value: [
                { n: '不限', v: '' },
                { n: '电视剧', v: '电视剧' },
                { n: '综艺', v: '综艺' },
            ],
        },
        {
            key: '电视剧形式',
            name: '电视剧形式',
            value: [
                { n: '不限', v: '' },
                { n: '喜剧', v: '喜剧' },
                { n: '爱情', v: '爱情' },
                { n: '悬疑', v: '悬疑' },
                { n: '动画', v: '动画' },
                { n: '武侠', v: '武侠' },
                { n: '古装', v: '古装' },
                { n: '家庭', v: '家庭' },
                { n: '犯罪', v: '犯罪' },
                { n: '科幻', v: '科幻' },
                { n: '恐怖', v: '恐怖' },
                { n: '历史', v: '历史' },
                { n: '战争', v: '战争' },
                { n: '动作', v: '动作' },
                { n: '冒险', v: '冒险' },
                { n: '传记', v: '传记' },
                { n: '剧情', v: '剧情' },
                { n: '奇幻', v: '奇幻' },
                { n: '惊悚', v: '惊悚' },
                { n: '灾难', v: '灾难' },
                { n: '歌舞', v: '歌舞' },
                { n: '音乐', v: '音乐' },
            ],
        },
        {
            key: '综艺形式',
            name: '综艺形式',
            value: [
                { n: '不限', v: '' },
                { n: '真人秀', v: '真人秀' },
                { n: '脱口秀', v: '脱口秀' },
                { n: '音乐', v: '音乐' },
                { n: '歌舞', v: '歌舞' },
            ],
        },
        {
            key: '地区',
            name: '地区',
            value: [
                { n: '全部地区', v: '' },
                { n: '华语', v: '华语' },
                { n: '欧美', v: '欧美' },
                { n: '国外', v: '国外' },
                { n: '韩国', v: '韩国' },
                { n: '日本', v: '日本' },
                { n: '中国大陆', v: '中国大陆' },
                { n: '中国香港', v: '中国香港' },
                { n: '美国', v: '美国' },
                { n: '英国', v: '英国' },
                { n: '泰国', v: '泰国' },
                { n: '中国台湾', v: '中国台湾' },
                { n: '意大利', v: '意大利' },
                { n: '法国', v: '法国' },
                { n: '德国', v: '德国' },
                { n: '西班牙', v: '西班牙' },
                { n: '俄罗斯', v: '俄罗斯' },
                { n: '瑞典', v: '瑞典' },
                { n: '巴西', v: '巴西' },
                { n: '丹麦', v: '丹麦' },
                { n: '印度', v: '印度' },
                { n: '加拿大', v: '加拿大' },
                { n: '爱尔兰', v: '爱尔兰' },
                { n: '澳大利亚', v: '澳大利亚' },
            ],
        },
        {
            key: 'sort',
            name: '排序',
            value: [
                { n: '近期热度', v: 'T' },
                { n: '首播时间', v: 'R' },
                { n: '高分优先', v: 'S' },
            ],
        },
        {
            key: '年代',
            name: '年代',
            value: [
                { n: '全部', v: '' },
                { n: '2026', v: '2026' },
                { n: '2025', v: '2025' },
                { n: '2024', v: '2024' },
                { n: '2023', v: '2023' },
                { n: '2022', v: '2022' },
                { n: '2021', v: '2021' },
                { n: '2020', v: '2020' },
                { n: '2019', v: '2019' },
                { n: '2010年代', v: '2010年代' },
                { n: '2000年代', v: '2000年代' },
                { n: '90年代', v: '90年代' },
                { n: '80年代', v: '80年代' },
                { n: '70年代', v: '70年代' },
                { n: '60年代', v: '60年代' },
                { n: '更早', v: '更早' },
            ],
        },
        {
            key: '平台',
            name: '平台',
            value: [
                { n: '全部', v: '' },
                { n: '腾讯视频', v: '腾讯视频' },
                { n: '爱奇艺', v: '爱奇艺' },
                { n: '优酷', v: '优酷' },
                { n: '湖南卫视', v: '湖南卫视' },
                { n: 'Netflix', v: 'Netflix' },
                { n: 'HBO', v: 'HBO' },
                { n: 'BBC', v: 'BBC' },
                { n: 'NHK', v: 'NHK' },
                { n: 'CBS', v: 'CBS' },
                { n: 'NBC', v: 'NBC' },
                { n: 'tvN', v: 'tvN' },
            ],
        },
    ],
    rank_list_movie: [
        {
            key: '榜单',
            name: '榜单',
            value: [
                { n: '实时热门电影', v: 'movie_real_time_hotest' },
                { n: '一周口碑电影榜', v: 'movie_weekly_best' },
                { n: '豆瓣电影Top250', v: 'movie_top250' },
            ],
        },
    ],
    rank_list_tv: [
        {
            key: '榜单',
            name: '榜单',
            value: [
                { n: '实时热门电视', v: 'tv_real_time_hotest' },
                { n: '华语口碑剧集榜', v: 'tv_chinese_best_weekly' },
                { n: '全球口碑剧集榜', v: 'tv_global_best_weekly' },
                { n: '国内口碑综艺榜', v: 'show_chinese_best_weekly' },
                { n: '国外口碑综艺榜', v: 'show_global_best_weekly' },
            ],
        },
    ],
};

async function init(cfg) {
    try {
        var ext = cfg && cfg.ext !== undefined ? cfg.ext : '';
        if (typeof ext === 'string') FILTER_URL = ext.trim();
        else if (ext && typeof ext === 'object') {
            FILTER_URL = String(ext.filter || ext.url || ext.host || '').trim();
        }
        FILTERS = await loadFilters(FILTER_URL);
    } catch (e) {
        FILTERS = DEFAULT_FILTERS;
        console.error('豆瓣 init:', e.message);
    }
}

async function loadFilters(url) {
    if (!url) return DEFAULT_FILTERS;
    try {
        var res = await req(url, { headers: { 'User-Agent': DoubanHeaders['User-Agent'] }, timeout: 8000 });
        var body = res && res.content;
        if (!body) return DEFAULT_FILTERS;
        var obj = typeof body === 'string' ? JSON.parse(body) : body;
        if (obj && typeof obj === 'object') return obj;
    } catch (e) {}
    return DEFAULT_FILTERS;
}

async function requestJson(url) {
    var res = await req(url, { headers: DoubanHeaders, timeout: 10000 });
    var body = res && res.content;
    if (!body) return null;
    return typeof body === 'string' ? JSON.parse(body) : body;
}

function picWithHeader(url) {
    if (!url) return '';
    return (
        url +
        '@Referer=https://movie.douban.com/@User-Agent=' +
        encodeURIComponent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        )
    );
}

function mapItems(arr) {
    var list = [];
    if (!arr || !arr.length) return list;
    for (var i = 0; i < arr.length; i++) {
        var it = arr[i];
        if (!it) continue;
        var title = it.title || '';
        if (!title) continue;
        var pic = '';
        try {
            pic = (it.pic && (it.pic.normal || it.pic.large)) || '';
        } catch (e) {}
        if (!pic) continue;
        var score = '';
        try {
            score = it.rating && it.rating.value != null ? String(it.rating.value) : '';
        } catch (e2) {}
        // msearch: 供影视仓按片名到其它 changeable 源换源搜索
        list.push({
            vod_id: 'msearch:' + (it.id || ''),
            vod_name: title,
            vod_pic: picWithHeader(pic),
            vod_remarks: score ? '评分：' + score : '',
        });
    }
    return list;
}

function joinTags(extend) {
    if (!extend || typeof extend !== 'object') return '';
    var parts = [];
    for (var k in extend) {
        if (!Object.prototype.hasOwnProperty.call(extend, k)) continue;
        if (k === 'sort' || k === 'area' || k === 'type' || k === '榜单') continue;
        var v = extend[k];
        if (v == null || v === '') continue;
        parts.push(String(v));
    }
    return parts.join(',');
}

async function home(filter) {
    try {
        var out = { class: CLASSES };
        if (filter) out.filters = FILTERS || DEFAULT_FILTERS;
        return JSON.stringify(out);
    } catch (e) {
        return JSON.stringify({ class: CLASSES, filters: {} });
    }
}

async function homeVod() {
    try {
        var url =
            'https://frodo.douban.com/api/v2/subject_collection/subject_real_time_hotest/items?apikey=' +
            API_KEY;
        // 兼容旧接口域名
        var data = await requestJson(url);
        if (!data || !data.subject_collection_items) {
            data = await requestJson(
                'http://api.douban.com/api/v2/subject_collection/subject_real_time_hotest/items?apikey=' +
                    API_KEY
            );
        }
        var list = mapItems((data && data.subject_collection_items) || []);
        return JSON.stringify({ list: list });
    } catch (e) {
        console.error('豆瓣首页推荐失败:', e.message);
        return JSON.stringify({ list: [] });
    }
}

async function category(tid, pg, filter, extend) {
    try {
        var page = Math.max(parseInt(pg || '1', 10) || 1, 1);
        var start = (page - 1) * 20;
        extend = extend || {};
        if (typeof extend === 'string' && extend) {
            try {
                extend = JSON.parse(extend);
            } catch (e) {
                extend = {};
            }
        }
        var sort = extend.sort || 'T';
        var tags = encodeURIComponent(joinTags(extend));
        var url = '';
        var listKey = 'items';

        if (tid === 'rank_list_movie') {
            var mid = extend['榜单'] || 'movie_real_time_hotest';
            url =
                HOST +
                '/subject_collection/' +
                mid +
                '/items?apikey=' +
                API_KEY +
                '&start=' +
                start +
                '&count=20';
            listKey = 'subject_collection_items';
        } else if (tid === 'rank_list_tv') {
            var tidRank = extend['榜单'] || 'tv_real_time_hotest';
            url =
                HOST +
                '/subject_collection/' +
                tidRank +
                '/items?apikey=' +
                API_KEY +
                '&start=' +
                start +
                '&count=20';
            listKey = 'subject_collection_items';
        } else if (tid === 'tv_hot' || tid === 'show_hot') {
            var col = extend.type || tid;
            url =
                HOST +
                '/subject_collection/' +
                col +
                '/items?apikey=' +
                API_KEY +
                '&start=' +
                start +
                '&count=20';
            listKey = 'subject_collection_items';
        } else if (tid === 'hot_gaia') {
            var hs = extend.sort || 'recommend';
            var area = encodeURIComponent(extend.area || '全部');
            url =
                HOST +
                '/movie/hot_gaia?apikey=' +
                API_KEY +
                '&sort=' +
                hs +
                '&area=' +
                area +
                '&start=' +
                start +
                '&count=20';
            listKey = 'items';
        } else if (tid === 'tv') {
            url =
                HOST +
                '/tv/recommend?apikey=' +
                API_KEY +
                '&sort=' +
                sort +
                '&tags=' +
                tags +
                '&start=' +
                start +
                '&count=20';
            listKey = 'items';
        } else {
            // movie 筛选
            url =
                HOST +
                '/movie/recommend?apikey=' +
                API_KEY +
                '&sort=' +
                sort +
                '&tags=' +
                tags +
                '&start=' +
                start +
                '&count=20';
            listKey = 'items';
        }

        var data = await requestJson(url);
        var arr = (data && data[listKey]) || [];
        var list = mapItems(arr);
        return JSON.stringify({
            list: list,
            page: page,
            pagecount: 9999,
            limit: 20,
            total: 999999,
        });
    } catch (e) {
        console.error('豆瓣分类失败:', e.message);
        return JSON.stringify({ list: [], page: 1, pagecount: 1, limit: 20, total: 0 });
    }
}

async function detail(ids) {
    // 索引站：无详情，靠换源搜片名
    return JSON.stringify({ list: [] });
}

async function play(flag, ids, flags) {
    return JSON.stringify({ parse: 0, url: '' });
}

async function search(wd, quick, pg) {
    return JSON.stringify({ list: [] });
}

export function __jsEvalReturn() {
    return {
        init: init,
        home: home,
        homeVod: homeVod,
        category: category,
        detail: detail,
        play: play,
        search: search,
    };
}
