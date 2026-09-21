"""
拼音输入法核心模块
实现拼音到汉字的转换
"""

import os
import math
from pypinyin import lazy_pinyin, Style
from language_model import NGramLanguageModel


class PinyinInputMethod:
    """拼音输入法"""
    
    def __init__(self, model_path=None):
        """
        初始化拼音输入法
        model_path: 语言模型文件路径
        """
        self.model = NGramLanguageModel(n=2)
        
        if model_path and os.path.exists(model_path):
            self.model.load(model_path)
        
        # 拼音到汉字的映射表
        self.pinyin_dict = {}
        
        # 加载拼音字典
        self._load_pinyin_dict()
    
    def _load_pinyin_dict(self):
        """
        加载拼音字典
        从词汇表构建拼音到汉字的映射
        """
        # 常用汉字拼音映射（简化版）
        common_chars = {
            'a': '阿啊呵',
            'ai': '爱挨埃哀',
            'an': '安按案岸',
            'ang': '昂盎',
            'ao': '奥傲熬',
            'ba': '八把爸巴',
            'bai': '白百拜',
            'ban': '班半办般',
            'bang': '帮邦棒',
            'bao': '报保包宝',
            'bei': '北被备背',
            'ben': '本奔笨',
            'beng': '崩绷泵',
            'bi': '比必笔毕',
            'bian': '边变便编',
            'biao': '表标彪',
            'bie': '别憋',
            'bin': '宾滨彬',
            'bing': '并兵冰病',
            'bo': '波博伯播',
            'bu': '不部步布',
            'ca': '擦',
            'cai': '才采财材',
            'can': '参残餐灿',
            'cang': '藏仓苍',
            'cao': '草操曹',
            'ce': '策测侧册',
            'cen': '岑',
            'ceng': '层曾蹭',
            'cha': '查差察茶',
            'chai': '柴拆豺',
            'chan': '产缠禅蝉',
            'chang': '长常场厂',
            'chao': '超朝潮巢',
            'che': '车彻撤',
            'chen': '陈沉晨称',
            'cheng': '成城程承',
            'chi': '吃持尺池',
            'chong': '重冲充崇',
            'chou': '抽愁仇筹',
            'chu': '出处初除',
            'chuai': '揣踹',
            'chuan': '川穿传船',
            'chuang': '床创窗',
            'chui': '吹垂锤',
            'chun': '春纯唇',
            'chuo': '绰戳',
            'ci': '此次词刺',
            'cong': '从匆聪',
            'cou': '凑',
            'cu': '粗促醋',
            'cuan': '窜攒',
            'cui': '催脆翠',
            'cun': '村存寸',
            'cuo': '错措挫',
            'da': '大打达答',
            'dai': '大代带待',
            'dan': '但单担丹',
            'dang': '当党挡',
            'dao': '到道导倒',
            'de': '的得德',
            'dei': '得',
            'deng': '等灯登邓',
            'di': '地第提底',
            'dian': '电点店典',
            'diao': '掉调钓',
            'die': '爹跌叠',
            'ding': '定丁顶订',
            'diu': '丢',
            'dong': '动东冬懂',
            'dou': '都斗抖豆',
            'du': '都读度独',
            'duan': '段断端短',
            'dui': '对队堆',
            'dun': '顿吨蹲',
            'duo': '多夺朵躲',
            'e': '饿恶额俄',
            'ei': '诶',
            'en': '恩',
            'er': '而二儿耳',
            'fa': '发法罚',
            'fan': '反饭翻犯',
            'fang': '方放房访',
            'fei': '非飞费肥',
            'fen': '分份纷奋',
            'feng': '风封丰峰',
            'fo': '佛',
            'fou': '否',
            'fu': '夫服复父',
            'ga': '咖嘎',
            'gai': '改该概盖',
            'gan': '干感敢赶',
            'gang': '刚港钢岗',
            'gao': '高告搞稿',
            'ge': '个合各革',
            'gei': '给',
            'gen': '根跟',
            'geng': '更耕耿',
            'gong': '工公共功',
            'gou': '够构狗购',
            'gu': '古故股骨',
            'gua': '瓜刮挂寡',
            'guai': '怪拐',
            'guan': '关观管官',
            'guang': '光广逛',
            'gui': '规贵归鬼',
            'gun': '滚棍',
            'guo': '国过果锅',
            'ha': '哈',
            'hai': '还海孩害',
            'han': '汉喊含寒',
            'hang': '行航杭',
            'hao': '好号毫豪',
            'he': '和何合河',
            'hei': '黑嘿',
            'hen': '很恨狠',
            'heng': '横恒哼',
            'hong': '红宏洪轰',
            'hou': '后候厚猴',
            'hu': '乎呼胡护',
            'hua': '化话花华',
            'huai': '坏怀淮',
            'huan': '还欢换环',
            'huang': '黄皇荒慌',
            'hui': '会回挥汇',
            'hun': '婚混魂浑',
            'huo': '或活火获',
            'ji': '几及己机',
            'jia': '家加假价',
            'jian': '见间件建',
            'jiang': '将讲江降',
            'jiao': '叫教交角',
            'jie': '接结节姐',
            'jin': '进今金近',
            'jing': '经京惊精',
            'jiong': '窘',
            'jiu': '就九久酒',
            'ju': '据举居局',
            'juan': '卷捐倦',
            'jue': '决觉绝角',
            'jun': '军君均俊',
            'ka': '卡咖',
            'kai': '开凯慨',
            'kan': '看刊砍',
            'kang': '康抗炕',
            'kao': '考靠烤',
            'ke': '可科克客',
            'ken': '肯垦恳',
            'keng': '坑吭',
            'kong': '空孔恐控',
            'kou': '口扣寇',
            'ku': '哭苦库裤',
            'kua': '夸跨垮',
            'kuai': '快块会',
            'kuan': '宽款',
            'kuang': '况狂矿框',
            'kui': '亏愧葵',
            'kun': '困昆捆',
            'kuo': '扩括阔',
            'la': '拉啦辣腊',
            'lai': '来赖',
            'lan': '兰蓝览烂',
            'lang': '浪郎朗狼',
            'lao': '老劳牢姥',
            'le': '了乐勒',
            'lei': '类累雷泪',
            'leng': '冷愣',
            'li': '里理力利',
            'lia': '俩',
            'lian': '连联练脸',
            'liang': '两量亮良',
            'liao': '了料聊辽',
            'lie': '列烈劣裂',
            'lin': '林临淋邻',
            'ling': '领令另灵',
            'liu': '六留流刘',
            'long': '龙隆笼聋',
            'lou': '楼露漏陋',
            'lu': '路陆录鲁',
            'luan': '乱卵峦',
            'lun': '论轮伦仑',
            'luo': '落罗络洛',
            'ma': '吗妈马麻',
            'mai': '买卖麦埋',
            'man': '满慢漫曼',
            'mang': '忙盲茫芒',
            'mao': '毛冒帽貌',
            'me': '么',
            'mei': '没美每妹',
            'men': '们门闷',
            'meng': '梦蒙猛孟',
            'mi': '米密迷秘',
            'mian': '面免棉眠',
            'miao': '妙描苗秒',
            'mie': '灭蔑',
            'min': '民敏皿',
            'ming': '名明命鸣',
            'miu': '谬',
            'mo': '么没模末',
            'mou': '某谋牟',
            'mu': '目母木幕',
            'na': '那拿哪纳',
            'nai': '奶耐奈',
            'nan': '南难男',
            'nang': '囊',
            'nao': '脑闹恼',
            'ne': '呢哪',
            'nei': '内那',
            'nen': '嫩',
            'neng': '能',
            'ni': '你尼泥逆',
            'nian': '年念粘',
            'niang': '娘酿',
            'niao': '鸟尿',
            'nie': '捏聂孽',
            'nin': '您',
            'ning': '宁凝拧',
            'niu': '牛扭纽',
            'nong': '农浓弄',
            'nu': '努怒奴',
            'nv': '女',
            'nuan': '暖',
            'nue': '虐',
            'o': '哦喔',
            'ou': '欧偶殴',
            'pa': '怕爬帕',
            'pai': '排派拍牌',
            'pan': '判盘盼攀',
            'pang': '旁胖庞',
            'pao': '跑炮抛泡',
            'pei': '配培陪佩',
            'pen': '盆喷',
            'peng': '朋鹏碰捧',
            'pi': '批皮匹疲',
            'pian': '片偏篇骗',
            'piao': '票漂飘',
            'pie': '撇瞥',
            'pin': '品贫拼',
            'ping': '平评凭瓶',
            'po': '破婆坡迫',
            'pou': '剖',
            'pu': '普扑铺仆',
            'qi': '起其气七',
            'qia': '恰洽掐',
            'qian': '前钱千签',
            'qiang': '强枪墙腔',
            'qiao': '桥巧悄瞧',
            'qie': '且切窃茄',
            'qin': '亲秦琴勤',
            'qing': '情请青清',
            'qiong': '穷琼',
            'qiu': '求球秋丘',
            'qu': '去取区曲',
            'quan': '全权圈泉',
            'que': '却确缺雀',
            'qun': '群裙',
            'ran': '然燃染',
            'rang': '让壤',
            'rao': '绕饶扰',
            're': '热惹',
            'ren': '人任认仁',
            'reng': '仍扔',
            'ri': '日',
            'rong': '容荣融溶',
            'rou': '肉柔揉',
            'ru': '如入儒乳',
            'ruan': '软阮',
            'rui': '瑞锐',
            'run': '润闰',
            'ruo': '若弱',
            'sa': '撒洒萨',
            'sai': '赛塞腮',
            'san': '三散伞',
            'sang': '丧桑',
            'sao': '扫嫂骚',
            'se': '色塞涩',
            'sen': '森',
            'seng': '僧',
            'sha': '杀沙傻纱',
            'shai': '晒筛',
            'shan': '山善扇闪',
            'shang': '上商伤尚',
            'shao': '少绍烧稍',
            'she': '社设舍射',
            'shei': '谁',
            'shen': '身深神什',
            'sheng': '生声省升',
            'shi': '是时事十',
            'shou': '手受收首',
            'shu': '书数术树',
            'shua': '刷耍',
            'shuai': '率摔甩帅',
            'shuan': '拴栓',
            'shuang': '双爽',
            'shui': '水谁税',
            'shun': '顺瞬',
            'shuo': '说数硕',
            'si': '死四思司',
            'song': '送松宋颂',
            'sou': '搜艘擞',
            'su': '速素苏诉',
            'suan': '算酸蒜',
            'sui': '岁随虽碎',
            'sun': '孙损笋',
            'suo': '所索缩锁',
            'ta': '他她它踏',
            'tai': '太台态泰',
            'tan': '谈探坦叹',
            'tang': '堂唐糖汤',
            'tao': '讨套逃桃',
            'te': '特忑',
            'teng': '疼腾藤',
            'ti': '体提题替',
            'tian': '天田填甜',
            'tiao': '条调跳挑',
            'tie': '铁贴帖',
            'ting': '听停庭厅',
            'tong': '同通统童',
            'tou': '头投透偷',
            'tu': '图土突徒',
            'tuan': '团',
            'tui': '推退腿',
            'tun': '吞屯',
            'tuo': '托脱拖拓',
            'wa': '瓦娃挖',
            'wai': '外歪',
            'wan': '万完晚玩',
            'wang': '王往望网',
            'wei': '为位委未',
            'wen': '文问闻温',
            'weng': '翁瓮',
            'wo': '我握窝卧',
            'wu': '无五物务',
            'xi': '西息希习',
            'xia': '下夏吓峡',
            'xian': '先现线县',
            'xiang': '相向想象',
            'xiao': '小笑校效',
            'xie': '写些谢协',
            'xin': '心新信辛',
            'xing': '行性形兴',
            'xiong': '兄雄胸凶',
            'xiu': '修休秀袖',
            'xu': '许须需虚',
            'xuan': '选宣玄悬',
            'xue': '学血雪穴',
            'xun': '寻训迅讯',
            'ya': '亚压呀牙',
            'yan': '眼言研严',
            'yang': '样阳养洋',
            'yao': '要药摇遥',
            'ye': '也业夜叶',
            'yi': '一以意义',
            'yin': '因音引银',
            'ying': '应英影营',
            'yo': '哟',
            'yong': '用永勇涌',
            'you': '有又由友',
            'yu': '与于雨余',
            'yuan': '元原员园',
            'yue': '月越约乐',
            'yun': '运云允匀',
            'za': '杂砸咋',
            'zai': '在再载灾',
            'zan': '赞咱暂',
            'zang': '脏葬',
            'zao': '早造遭糟',
            'ze': '则责择泽',
            'zei': '贼',
            'zen': '怎',
            'zeng': '增曾赠',
            'zha': '查扎炸诈',
            'zhai': '摘宅债窄',
            'zhan': '战展站占',
            'zhang': '长张章掌',
            'zhao': '着找召照',
            'zhe': '着者这哲',
            'zhei': '这',
            'zhen': '真镇阵振',
            'zheng': '正政整证',
            'zhi': '之只知直',
            'zhong': '中种重众',
            'zhou': '州周洲舟',
            'zhu': '主住注著',
            'zhua': '抓',
            'zhuai': '拽',
            'zhuan': '转专传砖',
            'zhuang': '状装庄壮',
            'zhui': '追准缀',
            'zhun': '准谆',
            'zhuo': '着卓捉桌',
            'zi': '子字自资',
            'zong': '总宗综纵',
            'zou': '走奏邹',
            'zu': '组足族祖',
            'zuan': '钻赚',
            'zui': '最罪嘴',
            'zun': '尊遵',
            'zuo': '做作坐左',
        }
        
        self.pinyin_dict = common_chars
        print("拼音字典加载完成，共 {} 个拼音".format(len(self.pinyin_dict)))
    
    def pinyin_to_chars(self, pinyin):
        """
        获取拼音对应的所有可能汉字
        """
        pinyin = pinyin.lower()
        chars = self.pinyin_dict.get(pinyin, '')
        return list(chars)
    
    def segment_pinyin(self, pinyin_str):
        """
        将连续拼音字符串切分为单个拼音
        例如: "zhongwen" -> ["zhong", "wen"]
        """
        # 简化版：按空格切分
        if ' ' in pinyin_str:
            return pinyin_str.lower().split()
        
        # 复杂版：需要实现拼音切分算法
        # 这里使用简单的贪心算法
        result = []
        i = 0
        s = pinyin_str.lower()
        
        while i < len(s):
            # 尝试匹配最长的拼音
            matched = False
            for length in range(min(6, len(s) - i), 0, -1):
                substr = s[i:i+length]
                if substr in self.pinyin_dict:
                    result.append(substr)
                    i += length
                    matched = True
                    break
            
            if not matched:
                # 如果没有匹配到，按单个字符处理
                result.append(s[i])
                i += 1
        
        return result
    
    def convert(self, pinyin_str, top_k=5):
        """
        将拼音字符串转换为汉字
        使用Viterbi算法或贪心算法
        """
        # 切分拼音
        pinyins = self.segment_pinyin(pinyin_str)
        
        # 获取每个拼音对应的候选汉字
        candidates = []
        for py in pinyins:
            chars = self.pinyin_to_chars(py)
            if chars:
                candidates.append(chars)
            else:
                # 如果没有对应的汉字，保留原拼音
                candidates.append([py])
        
        if not candidates:
            return []
        
        # 使用语言模型选择最优路径
        results = self._beam_search(candidates, top_k)
        
        return results
    
    def _beam_search(self, candidates, beam_size=5):
        """
        使用束搜索(Beam Search)找到最优的汉字序列
        """
        if not candidates:
            return []
        
        # 初始化：第一个拼音的候选
        beams = []
        for char in candidates[0][:10]:  # 限制初始候选数
            beams.append(([char], 0.0))  # (路径, 分数)
        
        # 逐个处理后续拼音
        for i in range(1, len(candidates)):
            new_beams = []
            
            for path, score in beams:
                context = path[-1:] if len(path) > 0 else []
                
                for char in candidates[i][:10]:
                    # 计算条件概率
                    prob = self.model.get_probability(char, context)
                    new_score = score + math.log(prob)
                    new_path = path + [char]
                    new_beams.append((new_path, new_score))
            
            # 保留top-k
            new_beams.sort(key=lambda x: x[1], reverse=True)
            beams = new_beams[:beam_size]
        
        # 返回结果
        results = []
        for path, score in beams:
            results.append({
                'text': ''.join(path),
                'score': score
            })
        
        return results


if __name__ == '__main__':
    # 测试代码
    ime = PinyinInputMethod()
    
    # 测试拼音切分
    test_pinyin = "zhongwen"
    segments = ime.segment_pinyin(test_pinyin)
    print("拼音 '{}' 切分结果: {}".format(test_pinyin, segments))
    
    # 测试拼音转汉字
    test_cases = [
        "zhongwen",
        "pinyin",
        "shurufa",
        "beijing"
    ]
    
    print("\n拼音输入法测试:")
    for pinyin in test_cases:
        results = ime.convert(pinyin, top_k=3)
        print("\n{}:".format(pinyin))
        for i, result in enumerate(results, 1):
            print("  {}. {} (score: {:.4f})".format(i, result['text'], result['score']))
