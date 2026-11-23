import base64
import json
import gzip
import re
import secrets
import threading
import time
from urllib.parse import urlencode, urlsplit, urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

try:
    from base.spider import Spider as BaseSpider
except ModuleNotFoundError as error:
    if error.name not in ("base", "base.spider"):
        raise
    BaseSpider = object


API_BASE = "http://122.228.193.199:30399"
USER_AGENT = "okhttp/3.12.1"
DEFAULT_EPG = "https://zzf.new.tg/epg.xml"
FALLBACK_LOGOS = {"CCTV-1":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV1.png","CCTV-2":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV2.png","CCTV-3":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV3.png","CCTV-4":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV4.png","CCTV-5":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV5.png","CCTV-6":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV6.png","CCTV-7":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV7.png","CCTV-8":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV8.png","CCTV-9":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV9.png","CCTV-10":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV10.png","CCTV-11":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV11.png","CCTV-12":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV12.png","CCTV-13":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV13.png","CCTV-14":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV14.png","CCTV-15":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV15.png","CCTV-16":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV16.png","CCTV-17":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV17.png","北京卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Beijing.png","东方卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Dongfang.png","湖南卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Hunan.png","浙江卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Zhejiang.png","江苏卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Jiangsu.png","安徽卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Anhui.png","重庆卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Chongqing.png","东南卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Dongnan.png","甘肃卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Gansu.png","广东卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Guangdong.png","广西卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Guangxi.png","贵州卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Guizhou.png","海南卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Hainan.png","河北卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Hebei.png","河南卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Henan.png","黑龙江卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Heilongjiang.png","湖北卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Hubei.png","吉林卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Jilin.png","江西卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Jiangxi.png","辽宁卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Liaoning.png","内蒙古卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Neimeng.png","宁夏卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Ningxia.png","青海卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Qinghai.png","山东卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Shandong.png","山西卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Shanxi_.png","陕西卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Shanxi.png","深圳卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Shenzhen.png","四川卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Sichuan.png","天津卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Tianjin.png","新疆卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Xinjiang.png","西藏卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Xizang.png","云南卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Yunnan.png","海峡卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Haixia.png","兵团卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Bingtuan.png","黄河卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Huanghe.png","安多卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Anduo.png","康巴卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Kangba.png","南方卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Nanfang.png","农林卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Nonglin.png","三沙卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Sansha.png","延边卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Yanbian.png","厦门卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Xiamen.png","山东教育卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Shandongjy.png","澜湄国际卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Meilan.png","福建东南卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Dongfang.png","凤凰卫视":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/Phoenix1.png","民视新闻":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/FTV.png","CCTV-5+":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV5plus.png","CCTV-4K超高清":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV4K.png","CCTV-8K超高清":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTV8K.png","CCTV-电视指南":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVdszn.png","CCTV-第一剧场":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVdyjc.png","CCTV-风云剧场":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVfyjc.png","CCTV-风云音乐":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVfyyy.png","CCTV-风云足球":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVfyzq.png","CCTV-高尔夫网球":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVgefwq.png","CCTV-兵器科技":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVbqkj.png","CCTV-女性时尚":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVnxss.png","CCTV-世界地理":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVsjdl.png","CCTV-怀旧剧场":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVhjjc.png","CCTV-央视台球":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVystq.png","CCTV-央视文化精品":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVyswhjp.png","CCTV-卫生健康":"https://gh-proxy.org/https://raw.githubusercontent.com/wanglindl/TVlogo/main/img/CCTVwsjk.png"}


def _logo_name(name):
    return re.sub(r"[\s_\-]|高清|超清|蓝光|UHD|HD", "", str(name), flags=re.I).upper()


def _epg_logos(address):
    logos = {}
    with urlopen(Request(address, headers={"User-Agent": USER_AGENT}), timeout=4) as response:
        source = gzip.GzipFile(fileobj=response) if response.headers.get("Content-Encoding") == "gzip" or urlsplit(address).path.endswith(".gz") else response
        parser = ET.XMLPullParser(events=("start", "end"))
        total = 0
        while total < 6 * 1024 * 1024:
            block = source.read(16384)
            if not block:
                break
            total += len(block)
            parser.feed(block)
            for event, node in parser.read_events():
                if event == "start" and node.tag == "programme":
                    return logos
                if event == "end" and node.tag == "channel":
                    icon = node.find("icon")
                    if icon is not None and icon.get("src"):
                        image_url = urljoin(response.geturl(), icon.get("src"))
                        if urlsplit(image_url).scheme in ("http", "https"):
                            for name in node.findall("display-name"):
                                if name.text:
                                    logos[_logo_name(name.text)] = image_url
                    node.clear()
    return logos
BIZ_KEY = "EWZJSTF0ZJCXQ2VUEDL4VFHOY2Q0PQ=="
PP_KEY = "ed5fdsgucxumegqa"
SIG23_KEY = "OC1A06E197EF10CF3F6058CA7A803B5E"
SEED = "cqpoZ3O="
NONCE = "lrfQ0Ib1uFxatVUL6AG="
RSA_PUB = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCduNEnfxGaLuQRk5ABzXHhPV43zi00sCHjLo8BYc+Wi6xXm2b4v0i28Sq4WlNCKhseft9fz8kO/qLr6/022o1RcuOU7e4GFL3U9WnNODwRBYSYWd+K8nqpI/tAUDmZEBGRWqjrc7x6aMl3A+xpnWkLbPCLsuhbuuUE3tv09oeOpwIDAQAB"
CHANNEL_GROUPS = [["CCTV直播",[["CCTV1综合","zb-cctv1"],["CCTV2财经","zb-cctv2"],["CCTV3综艺","zb-cctv3"],["CCTV4中文国际","zb-cctv4"],["CCTV5体育","zb-cctv5"],["CCTV5+体育赛事","zb-cctv5p"],["CCTV6电影","zb-cctv6"],["CCTV7国防军事","zb-cctv7"],["CCTV8电视剧","zb-cctv8"],["CCTV9纪录","zb-cctv9"],["CCTV10科教","zb-cctv10"],["CCTV11戏曲","zb-cctv11"],["CCTV12社会与法","zb-cctv12"],["CCTV13新闻","zb-cctv13"],["CCTV14少儿","zb-cctv14"],["CCTV15音乐","zb-cctv15"],["CCTV16奥林匹克","zb-cctv16"],["CCTV17农业农村","zb-cctv17"],["CCTV4欧洲","zb-cctv4oz"],["CCTV4美洲","zb-cctv4mz"],["CGTN外语记录","zb-cgtnwyjl"],["CGTN阿拉伯语","zb-cgtnalby"],["CGTN西班牙语","zb-cgtnxbyy"],["CGTN法语","zb-cgtnfy"],["CGTN俄语","zb-cgtney"],["CGTN","zb-cgtn"],["CCTV4K","zb-cctv4k"],["CCTV8K","zb-cctv8k"],["CCTV风云剧场","zb-cctvfyjcpd"],["CCTV第一剧场","zb-cctvdyjcpd"],["CCTV怀旧剧场","zb-cctvhjjcpd"]]],["卫视频道",[["浙江卫视","zb-zjws"],["北京卫视","zb-bjws"],["湖南卫视","zb-hunws"],["江苏卫视","zb-jsws"],["东方卫视","zb-dfws"],["山东卫视","zb-sdws"],["广东卫视","zb-gdws"],["江西卫视","zb-jxws"],["河南卫视","zb-henws"],["湖北卫视","zb-hubws"],["吉林卫视","zb-jlws"],["青海卫视","zb-qhws"],["海南卫视","zb-hainws"],["辽宁卫视","zb-lnws"],["宁夏卫视","zb-nxws"],["重庆卫视","zb-cqws"],["东南卫视","zb-dnws"],["大湾区卫视","zb-dwqws"],["三沙卫视","zb-ssws"],["嘉佳卡通","zb-jjkt"],["优漫卡通","zb-ymkt"],["江苏教育","zb-jsjy"],["山东教育","zb-sdjy"],["兵团卫视","zb-btws"],["河北卫视","zb-hebws"],["黑龙江卫视","zb-hljws"],["延边卫视","zb-ybws"],["西藏卫视","zb-xzws"],["西藏藏语卫视","zb-xzzy"],["山西卫视","zb-sxws"],["陕西卫视","zb-shanxws"],["农林卫视","zb-nlws"],["内蒙古卫视","zb-nmgws"],["海峡卫视","zb-hxws"],["厦门卫视","zb-xmws"],["甘肃卫视","zb-gsws"],["新疆卫视","zb-xjws"],["云南卫视","zb-ynws"],["深圳卫视","zb-szws"],["天津卫视","zb-tjws"],["安徽卫视","zb-ahws"],["广西卫视","zb-gxws"],["四川卫视","zb-scws"],["贵州卫视","zb-gzws"],["青海安多卫视","zb-qhadws"]]],["体育频道",[["CCTV5体育","zb-cctv5"],["CCTV5+体育赛事","zb-cctv5p"]]],["地方卫视",[["浙江钱江","zb-zjqj"],["浙江经济生活","zb-zjjjsh"],["浙江教科影视","zb-zjjkys"],["浙江民生休闲","zb-zjmsxx"],["浙江新闻","zb-zjxw"],["浙江少儿","zb-zjse"],["浙江国际","zb-zjgj"],["浙江好易购","zb-zjhyg"],["浙江之江纪录","zb-zjzjjl"],["湖南经视","zb-hunjs"],["金鹰卡通","zb-jykt"],["金鹰纪实","zb-jyjs"],["快乐垂钓","zb-klcd"],["先锋乒羽","zb-xfpy"],["湖南都市","zb-hunds"],["湖南电视剧","zb-hndsj"],["湖南公共","zb-hungg"],["湖南国际","zb-hungj"],["湖南娱乐","zb-hunyl"],["湖南快乐购","zb-klg"],["湖南茶频道","zb-cpd"],["湖南电影","zb-hndy"],["长沙新闻","zb-csxw"],["长沙政法","zb-cszf"],["长沙女性","zb-csnx"],["CETV1","zb-cetv1"],["CETV2","zb-cetv2"],["CETV4","zb-cetv4"],["上海新闻综合","zb-shxwzh"],["上海新纪实","zb-shxjs"],["上海魔都眼","zb-shmdy"],["上海第一财经","zb-shdycj"],["上海都市频道","zb-shdspd"],["上海五星体育","zb-shwxty"],["东方财经","zb-dfcj"],["上海生活时尚","zb-shss"],["金色学堂","zb-jsxt"],["上海教育","zb-shjy"],["游戏风云","zb-yxfy"],["法治天地","zb-fztd"],["上视东方影视","zb-ssdfys"],["山西经济","zb-sxjj"],["山西影视","zb-sxys"],["山西社会与法治","zb-sxfz"],["山西文体生活","zb-sxwt"],["山西黄河","zb-sxhh"],["太原新闻综合","zb-sxtyxwzh"],["阳泉新闻综合","zb-sxyqxwzh"],["长治新闻综合","zb-sxczxwzh"],["晋城新闻综合","zb-sxjcxwzh"],["朔州新闻综合","zb-sxszxwzh"],["晋中新闻综合","zb-sxjzxwzh"],["运城新闻综合","zb-sxycxwzh"],["忻州新闻综合","zb-sxxzzh"],["临汾新闻综合","zb-sxlfxwzh"],["吕梁新闻综合","zb-sxllxwzh"],["太原经济生活","zb-tyjjsh"],["太原社教法制","zb-tysjfz"],["太原影视","zb-tyyspd"],["太原文体","zb-tywtpd"],["太原佰乐购","zb-tyblg"],["太原城市","zb-tycssh"],["太原教育","zb-tyjypd"],["大同新闻综合","zb-dtxwzh"],["大同公共频道","zb-dtggpd"],["大同都生活","zb-dtmdsh"],["陕西新闻资讯","zb-xwzx"],["陕西都市青春","zb-dsqc"],["银龄频道","zb-ylpd"],["秦腔频道","zb-qqpd"],["乐家购物","zb-ljgw"],["移动电视","zb-ydds"],["陕西银龄频道","zb-sxylpd"],["陕西都市青春频道","zb-sxdsqcpd"],["陕西秦腔频道","zb-sxqkpd"],["陕西新闻资讯频道","zb-sxxwzxpd"],["陕西体育休闲频道","zb-sxtyxxpd"],["甘肃文化影视","zb-gswsys"],["甘肃公共应急","zb-gsggyj"],["甘肃少儿频道","zb-gssepd"],["甘肃科教频道","zb-gskjpd"],["甘肃移动电视","zb-gsydds"],["甘肃证券服务","zb-gszjfw"],["文山综合频道","zb-wszhpd"],["云南娱乐频道","zb-ynylpd"],["巍山综合频道","zb-wszhpd"],["云龙综合频道","zb-ylzhpd"],["红河新闻综合","zb-hhxwzh"],["临沧一套","zb-lc1t"],["临沧二套","zb-lc2t"],["绥江电视台","zb-suijdst"],["迪庆综合频道","zb-dqzhpd"],["迪庆藏语频道","zb-dqzypd"],["河南都市","zb-hnds"],["河南民生","zb-hnms"],["河南法治","zb-hmfz"],["河南电视剧","zb-hndsj"],["河南新闻","zb-hnxw"],["欢腾购物","zb-htgw"],["河南公共","zb-hngg"],["河南乡村","zb-hnxc"],["河南国际","zb-hngj"],["河南梨园","zb-hnly"],["文物宝库","zb-wwbk"],["武术世界","zb-wspd"],["晴彩中原","zb-jczy"],["移动戏曲","zb-ydxj"],["象视界","zb-xsj"],["国学频道","zb-gxpd"],["郑州新闻综合","zb-zzxwzh"],["开封新闻综合","zb-kfxwzh"],["洛阳新闻综合","zb-lyxwzh"],["平顶山新闻综合","zb-pdsxwzh"],["安阳新闻综合","zb-ayxwzh"],["鹤壁新闻综合","zb-hbxwzh"],["新乡新闻综合","zb-xxxwzh"],["焦作新闻综合","zb-jzxwzh"],["濮阳新闻综合","zb-pyxwzh"],["许昌新闻综合","zb-xcxwzh"],["漯河新闻综合","zb-lhxwzh"],["三门峡新闻综合","zb-smxxwzh"],["南阳新闻综合","zb-nyxwzh"],["商丘新闻综合","zb-sqxwzh"],["信阳新闻综合","zb-xyxwzh"],["周口新闻综合","zb-zkxwzh"],["驻马店新闻综合","zb-zmdxwzh"],["济源新闻综合","zb-jyxwzh"],["新疆维语新闻综合","zb-xjwyzh"],["新疆哈语新闻综合","zb-xjhyzh"],["新疆综艺","zb-xjzy"],["新疆维语影视","zb-xjwyys"],["新疆经济生活","zb-xjjjsh"],["新疆哈语综艺","zb-xjhyzy"],["新疆维语经济生活","zb-xjwyjj"],["新疆体育健康","zb-xjty"],["新疆信息服务","zb-xjxxfw"],["新疆少儿频道","zb-xjse"],["吉林都市频道","zb-jldspd"],["吉林生活频道","zb-jlshpd"],["吉林影视频道","zb-jlyspd"],["吉林乡村频道","zb-jlxcpd"],["吉林综艺文化频道","zb-jlzywhpd"],["松原新闻综合","zb-syzh"],["长春综合频道","zb-cczhpd"],["吉林新闻综合频道","zb-jlxwzhpd"],["四平新闻综合频道","zb-spxwzhpd"],["辽源新闻综合频道","zb-lyxwzhpd"],["白城新闻综合频道","zb-bcxwzhpd"],["通化新闻综合频道","zb-thxwzhpd"],["白山新闻综合频道","zb-bsxwzhpd"],["黑龙江文体频道","zb-hljwtpd"],["黑龙江影视频道","zb-hljyspd"],["黑龙江新闻法治频道","zb-hljxwfzpd"],["黑龙江都市频道","zb-hljdspd"],["黑龙江农业・科教频道","zb-hljnykjpd"],["齐齐哈尔新闻综合频道","zb-qqhexwzhpd"],["鹤岗新闻综合频道","zb-hgxwzhpd"],["黑河新闻综合频道","zb-hhxwzhpd"],["大兴安岭新闻综合频道","zb-dxalxwzhpd"],["山东新闻频道","zb-sdxwpd"],["山东齐鲁频道","zb-sdqlpd"],["山东体育休闲频道","zb-sdtyxx"],["山东生活频道","zb-sdshpd"],["山东综艺频道","zb-sdzypd"],["山东文旅频道","zb-sdwlpd"],["山东农科频道","zb-sdnkpd"],["山东少儿频道","zb-sdsepd"],["济南电视台","zb-jndst"],["淄博电视台","zb-zbdst"],["枣庄电视台","zb-zzdst"],["东营电视台","zb-dydst"],["烟台电视台","zb-ytdst"],["潍坊电视台","zb-wfdst"],["泰安电视台","zb-tadst"],["威海电视台","zb-whdst"],["日照电视台","zb-rzdst"],["临沂电视台","zb-lydst"],["德州电视台","zb-dzdst"],["聊城电视台","zb-lcdst"],["滨州电视台","zb-bzdst"],["菏泽电视台","zb-hzdst"],["济南都市","zb-jndspd"],["济南文旅体育","zb-jnwlty"],["济南生活","zb-jnshpd"],["济南少儿","zb-jnsepd"],["济南鲁中","zb-jnlzpd"],["江苏综艺频道","zb-jszy"],["江苏城市频道","zb-jscs"],["江苏国际","zb-jsgj"],["江苏影视频道","zb-jsys"],["江苏公共新闻频道","zb-jsxw"],["江苏财富天下","zb-cftx"],["江苏体育休闲频道","zb-jsxx"],["无锡新闻综合","zb-wxxwzh"],["无锡娱乐","zb-wxyl"],["无锡都市资讯","zb-wxdszx"],["无锡生活","zb-wxsh"],["无锡经济","zb-wxjj"],["盐城新闻综合","zb-ycxwzh"],["淮安新闻综合","zb-haxwzh"],["泰州新闻综合","zb-qzxwzh"],["连云港新闻综合","zb-lygxwzh"],["宿迁新闻综合","zb-sqxwzh"],["徐州新闻综合","zb-xzxwzh"],["江阴新闻综合","zb-jyxwzh"],["南通新闻综合","zb-ntxwzh"],["宜兴新闻综合","zb-yxxwzh"],["溧水新闻综合","zb-lsxwzh"],["南京新闻综合频道","zb-njxwzhpd"],["南京教科频道","zb-njjkpd"],["南京十八频道","zb-nj18pd"],["成都新闻频道","zb-cdtv1"],["成都经济频道","zb-cdtv2"],["成都生活频道","zb-cdtv3"],["成都影视频道","zb-cdtv4"],["成都公共频道","zb-cdtv5"],["成都少儿频道","zb-cdtv6"],["成都蓉城先锋","zb-cdrcxf"],["成华有线电视","zb-chyx"],["大邑电视台","zb-dytv"],["高新电视台","zb-gxtv"],["金牛电视台","zb-jntv"],["金堂电视台","zb-jttv"],["简阳新闻综合","zb-jyxwzh"],["郫都新闻综合","zb-pdxwzh"],["浦江电视台","zb-pjtv"],["彭州电视台","zb-pztv"],["青白江电视台","zb-qbjtv"],["邛崃电视台","zb-qltv"],["青羊电视台","zb-qytv"],["双流综合","zb-slzh"],["武侯电视台","zb-whtv"],["温江电视台","zb-wjtv"],["新都电视台","zb-xdtv"],["绵阳江油新闻综合","zb-myjyxw"],["绵阳北川综合","zb-mybczh"],["绵阳盐亭综合","zb-myytzh"],["绵阳梓潼综合","zb-myztzh"],["阿坝新闻综合","zb-abxwzh"],["阿坝藏语综合","zb-abzyzh"],["阿坝若尔盖综合","zb-abregzh"],["内江东兴新闻","zb-njdxxw"],["内江资中综合","zb-njzzzh"],["德阳广汉综合","zb-dyghzh"],["凉山甘洛综合","zb-lsglzh"],["凉山冕宁电视","zb-lsmnds"],["广安邻水综合","zb-galszh"],["广安武胜综合","zb-gawszh"],["眉山丹棱综合","zb-msdlzh"],["遂宁蓬溪新闻综合","zb-snpxxwzh"],["南充综合","zb-nczh"],["南充科教生活","zb-nckjsh"],["西藏影视文化","zb-xzys"],["察隅电视台","zb-xzcydst"],["日喀则汉语综合","zb-rkzhyzh"],["日喀则藏语综合","zb-rkzzyzh"],["拉萨综合频道","zb-lszhpd"],["拉萨文化旅游","zb-lswhlypd"],["贵州公共频道","zb-gzggpd"],["贵州影视频道","zb-gzyspd"],["贵州生活频道","zb-gzshpd"],["贵州乡村频道","zb-gzxcpd"],["贵州科教频道","zb-gzkjpd"],["贵州家有购物","zb-gzjygwpd"],["贵州移动频道","zb-gzydpd"],["黔西南综合","zb-qxnzh"],["黔西南公共","zb-qxngg"],["辽宁广播电视台公共频道","zb-lngbdstggpd"],["辽宁广播电视台生活频道","zb-lngbdsttshpd"],["大连新闻综合","zb-lldlzh"],["大连生活","zb-lldlsh"],["大连文体","zb-lldlwt"],["大连乐天购物","zb-lldlgw"],["福建综合","zb-fjzh"],["福建新闻","zb-fjxw"],["福建乡村振兴公共","zb-fjxc"],["福建电视剧","zb-fjdsj"],["福建旅游","zb-fjly"],["福建经济","zb-fjjj"],["福建文体","zb-fjwt"],["福建少儿","zb-fjse"],["福州新闻综合","zb-fz1"],["漳州新闻综合","zb-zz1"],["泉州新闻综合","zb-qz1"],["三明综合","zb-sm1"],["莆田综合","zb-pt1"],["南平综合","zb-np1"],["龙岩综合","zb-ly1"],["宁德新闻综合","zb-nd1"],["平潭综合","zb-pttv"],["广州综合","zb-gzzh"],["中山综合","zb-zszh"]]]]
SBOX = [99,124,119,123,242,107,111,197,48,1,103,43,254,215,171,118,202,130,201,125,250,89,71,240,173,212,162,175,156,164,114,192,183,253,147,38,54,63,247,204,52,165,229,241,113,216,49,21,4,199,35,195,24,150,5,154,7,18,128,226,235,39,178,117,9,131,44,26,27,110,90,160,82,59,214,179,41,227,47,132,83,209,0,237,32,252,177,91,106,203,190,57,74,76,88,207,208,239,170,251,67,77,51,133,69,249,2,127,80,60,159,168,81,163,64,143,146,157,56,245,188,182,218,33,16,255,243,210,205,12,19,236,95,151,68,23,196,167,126,61,100,93,25,115,96,129,79,220,34,42,144,136,70,238,184,20,222,94,11,219,224,50,58,10,73,6,36,92,194,211,172,98,145,149,228,121,231,200,55,109,141,213,78,169,108,86,244,234,101,122,174,8,186,120,37,46,28,166,180,198,232,221,116,31,75,189,139,138,112,62,181,102,72,3,246,14,97,53,87,185,134,193,29,158,225,248,152,17,105,217,142,148,155,30,135,233,206,85,40,223,140,161,137,13,191,230,66,104,65,153,45,15,176,84,187,22]


def _xtime(value):
    return ((value << 1) ^ (0x11B if value & 128 else 0)) & 255


class AES:
    def __init__(self, key):
        if len(key) not in (16, 32):
            raise ValueError("Invalid AES key length")
        self.rounds = len(key) // 4 + 6
        self.keys = list(key)
        rcon = 1
        while len(self.keys) < 16 * (self.rounds + 1):
            word = self.keys[-4:]
            if len(self.keys) % len(key) == 0:
                word = [SBOX[value] for value in word[1:] + word[:1]]
                word[0] ^= rcon
                rcon = _xtime(rcon)
            elif len(key) == 32 and len(self.keys) % 32 == 16:
                word = [SBOX[value] for value in word]
            start = len(self.keys) - len(key)
            self.keys.extend(self.keys[start + offset] ^ word[offset] for offset in range(4))

    def encrypt_block(self, block):
        if len(block) != 16:
            raise ValueError("Invalid AES block length")
        state = [value ^ self.keys[index] for index, value in enumerate(block)]
        for round_number in range(1, self.rounds + 1):
            state = [SBOX[value] for value in state]
            state = [state[row + 4 * ((column + row) % 4)] for column in range(4) for row in range(4)]
            if round_number != self.rounds:
                for column in range(4):
                    offset = column * 4
                    first, second, third, fourth = state[offset:offset + 4]
                    total = first ^ second ^ third ^ fourth
                    state[offset:offset + 4] = [
                        first ^ total ^ _xtime(first ^ second),
                        second ^ total ^ _xtime(second ^ third),
                        third ^ total ^ _xtime(third ^ fourth),
                        fourth ^ total ^ _xtime(fourth ^ first),
                    ]
            state = [value ^ self.keys[round_number * 16 + index] for index, value in enumerate(state)]
        return bytes(state)


def _encrypt(data, key, iv=None):
    key_bytes = key.encode("utf-8")
    if len(key_bytes) not in (16, 32):
        key_bytes = key_bytes[:32].ljust(32, b"\0")
    cipher = AES(key_bytes)
    padding = 16 - len(data) % 16
    data += bytes([padding]) * padding
    result = bytearray()
    previous = iv
    for offset in range(0, len(data), 16):
        block = data[offset:offset + 16]
        if previous is not None:
            block = bytes(left ^ right for left, right in zip(block, previous))
        encrypted = cipher.encrypt_block(block)
        result.extend(encrypted)
        if previous is not None:
            previous = encrypted
    return bytes(result)


def _der_value(data, offset=0):
    tag = data[offset]
    size = data[offset + 1]
    start = offset + 2
    if size & 128:
        count = size & 127
        size = int.from_bytes(data[start:start + count], "big")
        start += count
    return tag, data[start:start + size], start + size


def _rsa_encrypt(message):
    _, outer, _ = _der_value(base64.b64decode(RSA_PUB))
    _, _, offset = _der_value(outer)
    _, bits, _ = _der_value(outer, offset)
    _, public_key, _ = _der_value(bits[1:])
    _, modulus_bytes, offset = _der_value(public_key)
    _, exponent_bytes, _ = _der_value(public_key, offset)
    modulus = int.from_bytes(modulus_bytes, "big")
    exponent = int.from_bytes(exponent_bytes, "big")
    size = (modulus.bit_length() + 7) // 8
    padding_size = size - len(message) - 3
    if padding_size < 8:
        raise ValueError("RSA message too long")
    padding = bytes(secrets.randbelow(255) + 1 for _ in range(padding_size))
    padded = b"\0\2" + padding + b"\0" + message
    return base64.b64encode(pow(int.from_bytes(padded, "big"), exponent, modulus).to_bytes(size, "big")).decode("ascii")


def _public_params():
    timestamp = int(time.time() * 1000)
    random_text = "".join(secrets.choice("1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz") for _ in range(15)) + "="
    signature = base64.b64encode(_encrypt((str(timestamp) + random_text).encode(), SIG23_KEY)).decode("ascii")
    params = {
        "country": "CN", "vName": "8.0.2.0", "cpuId": "", "young": 0,
        "facturer": "Xiaomi", "pkg": "com.wlxxcl.xcydzkj",
        "uuid": "500334441C1E00EF23936D90ADFCB9D5",
        "resolution": "1220x2441", "mac": "02%3A00%3A00%3A00%3A00%3A00",
        "sig": _rsa_encrypt((str(timestamp) + random_text + "8020").encode()),
        "abid": "258", "model": "25098PN5AC", "plat": "android",
        "udid": "500334441C1E00EF23936D90ADFCB9D5", "dpi": "520", "net": "0",
        "lang": "zh", "random_str": random_text,
        "brand": "Xiaomi", "timestamp": timestamp, "density": "3.25",
        "appName": "%E7%94%B5%E5%BD%B1%E5%A4%A9%E5%A0%82", "cpu": "arm64-v8a",
        "chid": "10000", "carrier": "%E6%9C%AA%E7%9F%A5-%E4%B8%AD%E5%9B%BD%E5%B9%BF%E7%94%B5",
        "sig2": signature[:8], "v": 1, "sig3": signature[8:],
        "tenantId": "default", "_vOsCode": "37", "vOs": "17", "vApp": "8020",
        "device": 0, "androidID": "a1ba5c5b309a8420",
    }
    body = json.dumps(params, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encrypted = _encrypt(body, PP_KEY, PP_KEY.encode())
    return json.dumps({"paramsData": encrypted.hex()}, separators=(",", ":"))


def _varint(value):
    result = bytearray()
    while value > 127:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def _field(number, data):
    data = data.encode() if isinstance(data, str) else data
    return _varint((number << 3) | 2) + _varint(len(data)) + data


def _read_varint(data, offset):
    result = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise ValueError("Truncated protobuf")
        value = data[offset]
        offset += 1
        result |= (value & 127) << shift
        if not value & 128:
            return result, offset
    raise ValueError("Invalid protobuf integer")


def _protobuf(data):
    fields = {}
    offset = 0
    while offset < len(data):
        tag, offset = _read_varint(data, offset)
        number, wire = tag >> 3, tag & 7
        if number == 0:
            raise ValueError("Invalid protobuf field")
        if wire == 0:
            value, offset = _read_varint(data, offset)
        elif wire in (1, 2, 5):
            size = 8 if wire == 1 else 4
            if wire == 2:
                size, offset = _read_varint(data, offset)
            if offset + size > len(data):
                raise ValueError("Truncated protobuf field")
            value = data[offset:offset + size]
            offset += size
        else:
            raise ValueError("Unsupported protobuf wire type")
        fields.setdefault(number, []).append(value)
    return fields


def _fetch_address(code, timeout):
    timestamp = int(time.time() * 1000)
    params = urlencode({"vodPlayFrom": "cctv", "playUrl": code})
    encrypted = base64.b64encode(_encrypt((params + str(timestamp)).encode(), BIZ_KEY)).decode("ascii")
    body = (_field(1, SEED + encrypted[:12]) + _field(2, encrypted[12:]) + _field(3, NONCE)
            + _varint(4 << 3) + _varint(timestamp) + _field(5, SEED))
    request = Request(API_BASE + "/api/proto/v5/videoUsableUrl", data=body, headers={
        "User-Agent": USER_AGENT, "Content-Type": "application/x-protobuf",
        "Accept": "application/x-protobuf", "publicParams": _public_params(),
    })
    with urlopen(request, timeout=timeout) as response:
        data = response.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError("取址响应过大")
    envelope = _protobuf(data)
    payload = envelope.get(3, [None])[0]
    if not isinstance(payload, bytes):
        raise ValueError("取址接口未返回播放信息")
    address = _protobuf(payload).get(1, [b""])[0].decode("utf-8")
    if urlsplit(address).scheme not in ("http", "https"):
        raise ValueError("取址接口未返回有效 HTTP 地址")
    return address


def _resolve_address(address, timeout):
    request = Request(address, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        body = response.read(262145)
    if len(body) > 262144:
        raise ValueError("播放清单过大")
    if not body.lstrip(b"\xef\xbb\xbf \r\n\t").startswith(b"#EXTM3U"):
        raise ValueError("未取得有效 HLS 清单，可能令牌过期或接口不可用")
    return final_url


class Spider(BaseSpider):
    def __init__(self):
        self.timeout = 15
        self.cache = {}
        self.lock = threading.Lock()
        self.logo_lock = threading.Lock()
        self.epg_url = DEFAULT_EPG
        self.epg_logos = {}
        self.logo_refresh_at = 0
        self.fallback_logos = {_logo_name(name): address for name, address in FALLBACK_LOGOS.items()}
        self.groups = {name: channels for name, channels in CHANNEL_GROUPS}
        self.channels = {code: (name, group) for group, channels in CHANNEL_GROUPS for name, code in channels}

    def getName(self):
        return "设备直连直播"

    def init(self, extend=""):
        if isinstance(extend, str) and extend.strip():
            extend = json.loads(extend)
        if isinstance(extend, dict):
            self.timeout = max(5, min(30, int(extend.get("timeout", 15))))
            self.epg_url = str(extend.get("epg", DEFAULT_EPG)).strip()
            self.epg_logos = {}
            self.logo_refresh_at = 0

    def _logo(self, code, name):
        with self.logo_lock:
            if self.epg_url and time.monotonic() >= self.logo_refresh_at:
                self.logo_refresh_at = time.monotonic() + 600
                try:
                    self.epg_logos = _epg_logos(self.epg_url)
                    self.logo_refresh_at = time.monotonic() + 6 * 3600
                except Exception:
                    pass
        names = [_logo_name(name)]
        canonical = {"zb-cctv5p": "CCTV5+", "zb-cctv4k": "CCTV4K超高清", "zb-cctv8k": "CCTV8K超高清"}.get(code)
        if not canonical and re.fullmatch(r"zb-cctv\d+", code):
            canonical = code[3:]
        if canonical:
            names.append(_logo_name(canonical))
        for mapping in (self.epg_logos, self.fallback_logos):
            for candidate in names:
                if candidate in mapping:
                    return mapping[candidate]
        return ""

    def _item(self, code):
        name, group = self.channels[code]
        return {"vod_id": code, "vod_name": name, "vod_pic": self._logo(code, name),
                "vod_remarks": group, "land": 1, "ratio": 16 / 9}

    def homeContent(self, filter):
        return {"class": [{"type_id": group, "type_name": group} for group in self.groups],
                "list": self.homeVideoContent()["list"]}

    def homeVideoContent(self):
        codes = list(self.channels)[:30]
        return {"list": [self._item(code) for code in codes]}

    def categoryContent(self, tid, pg, filter, extend):
        channels = self.groups.get(tid, [])
        page = max(1, int(pg))
        items = [self._item(code) for _, code in channels[(page - 1) * 60:page * 60]]
        return {"list": items, "page": page, "pagecount": max(1, (len(channels) + 59) // 60),
                "limit": 60, "total": len(channels)}

    def searchContent(self, key, quick=False, pg="1"):
        matches = [code for code, (name, _) in self.channels.items() if str(key).casefold() in name.casefold()]
        page = max(1, int(pg))
        return {"list": [self._item(code) for code in matches[(page - 1) * 60:page * 60]],
                "page": page, "pagecount": max(1, (len(matches) + 59) // 60), "limit": 60, "total": len(matches)}

    def detailContent(self, ids):
        code = ids[0] if isinstance(ids, (list, tuple)) and ids else ids
        if code not in self.channels:
            return {"list": []}
        item = self._item(code)
        item.update({"vod_play_from": "CDN直连", "vod_play_url": "直播$" + code,
                     "vod_content": "由播放设备直接取址，播放器直连上游CDN，不使用PHP中转。"})
        return {"list": [item]}

    def playerContent(self, flag, id, vipFlags=None):
        if id not in self.channels:
            raise ValueError("未知频道编号")
        with self.lock:
            cached = self.cache.get(id)
            if cached and time.monotonic() - cached[0] < 45:
                address = cached[1]
            else:
                self.cache.pop(id, None)
                address = _resolve_address(_fetch_address(id, self.timeout), self.timeout)
                self.cache[id] = (time.monotonic(), address)
        return {"parse": 0, "jx": 0, "playUrl": "", "url": address,
                "header": {"User-Agent": USER_AGENT}}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        return [404, "text/plain", b"Direct playback only"]

    def destroy(self):
        self.cache.clear()

