#!/usr/bin/env python3
"""
Build a comprehensive Buddhist translation glossary from all translation files.
Reads all T*_translation.md files, extracts Buddhist terms (names, places,
titles, doctrinal concepts, monastic items, etc.), and outputs glossary_data.json.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

TRANSLATIONS_DIR = Path(os.path.expanduser("~/taisho-translation/translations"))
OUTPUT_FILE = Path(os.path.expanduser("~/taisho-translation/glossary_data.json"))


def get_t_number(filename):
    """Extract T-number from filename like T0002_translation.md -> T0002"""
    m = re.match(r'(T\d+)', filename)
    return m.group(1) if m else None


def read_all_translations():
    """Read all translation files and return dict of {t_number: text}."""
    texts = {}
    for f in sorted(TRANSLATIONS_DIR.glob("T*_translation.md")):
        t_num = get_t_number(f.name)
        if t_num:
            try:
                texts[t_num] = f.read_text(encoding='utf-8')
            except Exception as e:
                print(f"Warning: could not read {f}: {e}")
    return texts


# ============================================================
# MASTER GLOSSARY: Manually curated entries with known correspondences
# Each entry: (english, chinese, sanskrit, category)
# ============================================================

MASTER_GLOSSARY = [
    # === TITLES / EPITHETS ===
    ("World-Honored One", "世尊", "Bhagavān", "title"),
    ("Blessed One", "世尊", "Bhagavān", "title"),
    ("Tathāgata", "如來", "Tathāgata", "title"),
    ("Tathagata", "如來", "Tathāgata", "title"),
    ("Worthy One", "應供", "Arhat", "title"),
    ("Perfectly Enlightened", "正等覺", "Samyaksaṃbuddha", "title"),
    ("Well-Gone", "善逝", "Sugata", "title"),
    ("Well-Gone One", "善逝", "Sugata", "title"),
    ("Knower of the World", "世間解", "Lokavid", "title"),
    ("Unsurpassed", "無上士", "Anuttara", "title"),
    ("Tamer of Men", "調御丈夫", "Puruṣadamyasārathi", "title"),
    ("Teacher of Gods and Humans", "天人師", "Śāstā devamanuṣyāṇām", "title"),
    ("bhikṣu", "比丘", "bhikṣu", "title"),
    ("bhikṣus", "比丘", "bhikṣu", "title"),
    ("bhiksus", "比丘", "bhikṣu", "title"),
    ("bhiksu", "比丘", "bhikṣu", "title"),
    ("bhikṣuṇī", "比丘尼", "bhikṣuṇī", "title"),
    ("bhikṣuṇīs", "比丘尼", "bhikṣuṇī", "title"),
    ("bhiksunis", "比丘尼", "bhikṣuṇī", "title"),
    ("upāsaka", "優婆塞", "upāsaka", "title"),
    ("upāsakas", "優婆塞", "upāsaka", "title"),
    ("upasakas", "優婆塞", "upāsaka", "title"),
    ("upāsikā", "優婆夷", "upāsikā", "title"),
    ("upāsikās", "優婆夷", "upāsikā", "title"),
    ("upasikas", "優婆夷", "upāsikā", "title"),
    ("bodhisattva", "菩薩", "bodhisattva", "title"),
    ("bodhisattva-mahāsattva", "菩薩摩訶薩", "bodhisattva-mahāsattva", "title"),
    ("bodhisattvas", "菩薩", "bodhisattva", "title"),
    ("bodhisattva-mahāsattvas", "菩薩摩訶薩", "bodhisattva-mahāsattva", "title"),
    ("arhat", "阿羅漢", "arhat", "title"),
    ("arhats", "阿羅漢", "arhat", "title"),
    ("arahant", "阿羅漢", "arhat", "title"),
    ("arahants", "阿羅漢", "arhat", "title"),
    ("arhatship", "阿羅漢果", "arhat", "title"),
    ("arahantship", "阿羅漢果", "arhat", "title"),
    ("pratyekabuddha", "辟支佛", "pratyekabuddha", "title"),
    ("pratyekabuddhas", "辟支佛", "pratyekabuddha", "title"),
    ("śramaṇa", "沙門", "śramaṇa", "title"),
    ("śramaṇas", "沙門", "śramaṇa", "title"),
    ("sramana", "沙門", "śramaṇa", "title"),
    ("śrāvaka", "聲聞", "śrāvaka", "title"),
    ("śrāvakas", "聲聞", "śrāvaka", "title"),
    ("wheel-turning king", "轉輪王", "cakravartin", "title"),
    ("cakravartin", "轉輪王", "cakravartin", "title"),
    ("universal monarch", "轉輪王", "cakravartin", "title"),
    ("ācārya", "阿闍梨", "ācārya", "title"),
    ("dharma king", "法王", "dharmarāja", "title"),
    ("Dharma King", "法王", "dharmarāja", "title"),
    ("Great Vajra-Holder", "大金剛手", "Mahāvajradhara", "title"),
    ("Tripiṭaka Master", "三藏法師", "Tripiṭaka", "title"),

    # === PERSONS (Historical/Mythological) ===
    ("Buddha", "佛", "Buddha", "person"),
    ("Śākyamuni", "釋迦牟尼", "Śākyamuni", "person"),
    ("Śākyamuni Buddha", "釋迦牟尼佛", "Śākyamuni Buddha", "person"),
    ("Vipaśyin", "毘婆尸", "Vipaśyin", "person"),
    ("Śikhin", "尸棄", "Śikhin", "person"),
    ("Viśvabhū", "毘舍浮", "Viśvabhū", "person"),
    ("Krakucchanda", "拘留孫", "Krakucchanda", "person"),
    ("Kanakamuni", "拘那含牟尼", "Kanakamuni", "person"),
    ("Kāśyapa", "迦葉", "Kāśyapa", "person"),
    ("Kāśyapa Buddha", "迦葉佛", "Kāśyapa", "person"),
    ("Vipassin", "毘婆尸", "Vipaśyin", "person"),
    ("Sikhin", "尸棄", "Śikhin", "person"),
    ("Vessabhu", "毘舍浮", "Viśvabhū", "person"),
    ("Ānanda", "阿難", "Ānanda", "person"),
    ("Ananda", "阿難", "Ānanda", "person"),
    ("Śāriputra", "舍利弗", "Śāriputra", "person"),
    ("Sariputra", "舍利弗", "Śāriputra", "person"),
    ("Mahāmaudgalyāyana", "大目犍連", "Mahāmaudgalyāyana", "person"),
    ("Maudgalyāyana", "目犍連", "Maudgalyāyana", "person"),
    ("Maudgalyayana", "目犍連", "Maudgalyāyana", "person"),
    ("Mahāmaudgalyāyana", "大目犍連", "Mahāmaudgalyāyana", "person"),
    ("Nāgārjuna", "龍樹", "Nāgārjuna", "person"),
    ("Bhāviveka", "清辯", "Bhāviveka", "person"),
    ("Asaṅga", "無著", "Asaṅga", "person"),
    ("Vasubandhu", "世親", "Vasubandhu", "person"),
    ("Kumārajīva", "鳩摩羅什", "Kumārajīva", "person"),
    ("Xuánzàng", "玄奘", "Xuanzang", "person"),
    ("Xuanzang", "玄奘", "", "person"),
    ("Dharmarakṣa", "竺法護", "Dharmarakṣa", "person"),
    ("Prabhākaramitra", "波羅頗蜜多羅", "Prabhākaramitra", "person"),
    ("Guṇabhadra", "求那跋陀羅", "Guṇabhadra", "person"),
    ("Buddhajiva", "佛陀什", "Buddhajīva", "person"),
    ("Fātian", "法天", "", "person"),
    ("Rāhula", "羅睺羅", "Rāhula", "person"),
    ("Śuddhodana", "淨飯王", "Śuddhodana", "person"),
    ("Mahāmāyā", "摩耶夫人", "Mahāmāyā", "person"),
    ("Vajrapāṇi", "金剛手", "Vajrapāṇi", "person"),
    ("Samantabhadra", "普賢", "Samantabhadra", "person"),
    ("Avalokiteśvara", "觀自在", "Avalokiteśvara", "person"),
    ("Mañjuśrī", "文殊師利", "Mañjuśrī", "person"),
    ("Maitreya", "彌勒", "Maitreya", "person"),
    ("Vajrasattva", "金剛薩埵", "Vajrasattva", "person"),
    ("Mahāvairocana", "大毘盧遮那", "Mahāvairocana", "person"),
    ("Ākāśagarbha", "虛空藏", "Ākāśagarbha", "person"),
    ("Bhadrapāla", "跋陀和", "Bhadrapāla", "person"),
    ("Ratnākara", "寶積", "Ratnākara", "person"),
    ("Ajātaśatru", "阿闍世", "Ajātaśatru", "person"),
    ("Prasenajit", "波斯匿王", "Prasenajit", "person"),
    ("Māra", "魔", "Māra", "person"),
    ("Māra Pāpīyas", "魔波旬", "Māra Pāpīyas", "person"),
    ("Mara Papiyan", "魔波旬", "Māra Pāpīyas", "person"),
    ("Śakra", "帝釋", "Śakra", "person"),
    ("Indra", "帝釋", "Indra", "person"),
    ("Śakra Devānām-Indra", "帝釋天", "Śakra Devānām Indra", "person"),
    ("Brahmā", "梵天", "Brahmā", "person"),
    ("Vasubhadra", "婆素跋陀", "Vasubhadra", "person"),
    ("Sudinna", "須提那", "Sudinna", "person"),
    ("Varṣakāra", "禹舍", "Varṣakāra", "person"),
    ("Bandhumat", "般頭摩", "Bandhumat", "person"),
    ("Bandhumā", "般頭摩", "Bandhumat", "person"),
    ("Bandhumatī", "般頭摩底", "Bandhumatī", "person"),
    ("Anāthapiṇḍada", "給孤獨", "Anāthapiṇḍada", "person"),
    ("Āmrapālī", "菴婆女", "Āmrapālī", "person"),
    ("Ambapālī", "菴婆女", "Āmrapālī", "person"),
    ("Kauṇḍinya", "憍陳如", "Kauṇḍinya", "person"),
    ("Gautama", "瞿曇", "Gautama", "person"),
    ("Sudāna", "須達拏", "Sudāna", "person"),
    ("Sarvadatta", "薩婆達", "Sarvadatta", "person"),
    ("Aruṇa", "阿樓那", "Aruṇa", "person"),
    ("Supratīta", "善淨", "Supratīta", "person"),
    ("Prabhāvatī", "光明", "Prabhāvatī", "person"),
    ("Viśākhā", "毘舍佉", "Viśākhā", "person"),
    ("Uttarā", "優多羅", "Uttarā", "person"),
    ("Kṛkī", "汲毘", "Kṛkī", "person"),
    ("Piṇḍola-bhāradvāja", "賓頭盧跋羅墮闍", "Piṇḍola Bhāradvāja", "person"),
    ("Subhūti", "須菩提", "Subhūti", "person"),
    ("Mahāsubhūti", "大須菩提", "Mahāsubhūti", "person"),
    ("Nārada", "那羅陀", "Nārada", "person"),
    ("Kang Senghui", "康僧會", "", "person"),
    ("Saṃghabhūti", "僧伽跋澄", "Saṃghabhūti", "person"),

    # === PLACES ===
    ("Śrāvastī", "舍衛", "Śrāvastī", "place"),
    ("Rājagṛha", "王舍城", "Rājagṛha", "place"),
    ("Rajagriha", "王舍城", "Rājagṛha", "place"),
    ("Jetavana", "祇園", "Jetavana", "place"),
    ("Jeta's Grove", "祇樹", "Jetavana", "place"),
    ("Vulture Peak", "靈鷲山", "Gṛdhrakūṭa", "place"),
    ("Mount Gṛdhrakūṭa", "靈鷲山", "Gṛdhrakūṭa", "place"),
    ("Gṛdhrakūṭa", "耆闍崛山", "Gṛdhrakūṭa", "place"),
    ("Kapilavastu", "迦毘羅衛", "Kapilavastu", "place"),
    ("Vaiśālī", "毘舍離", "Vaiśālī", "place"),
    ("Vaisali", "毘舍離", "Vaiśālī", "place"),
    ("Vārāṇasī", "波羅奈", "Vārāṇasī", "place"),
    ("Magadha", "摩揭陀", "Magadha", "place"),
    ("Pāṭaliputra", "華氏城", "Pāṭaliputra", "place"),
    ("Pāṭaligāma", "巴吒釐村", "Pāṭaligāma", "place"),
    ("Nādikā", "那提迦", "Nādikā", "place"),
    ("Kuśinagara", "拘尸那", "Kuśinagara", "place"),
    ("Jambudvīpa", "閻浮提", "Jambudvīpa", "place"),
    ("Mount Sumeru", "須彌山", "Sumeru", "place"),
    ("Sahā world", "娑婆世界", "Sahā", "place"),
    ("Sahā", "娑婆", "Sahā", "place"),
    ("Koṭigāma", "拘利村", "Koṭigāma", "place"),
    ("Uttarakuru", "北俱盧洲", "Uttarakuru", "place"),
    ("Aruṇavatī", "阿樓那跋提", "Aruṇavatī", "place"),
    ("Hiraṇyavatī", "希連禪河", "Hiraṇyavatī", "place"),
    ("Ganges", "恒河", "Gaṅgā", "place"),

    # === COSMOLOGICAL ===
    ("Trāyastriṃśa", "忉利天", "Trāyastriṃśa", "cosmological"),
    ("Trāyastriṃśa Heaven", "忉利天", "Trāyastriṃśa", "cosmological"),
    ("Tuṣita", "兜率天", "Tuṣita", "cosmological"),
    ("Tuṣita Heaven", "兜率天", "Tuṣita", "cosmological"),
    ("Tusita heaven", "兜率天", "Tuṣita", "cosmological"),
    ("Paranirmitavaśavartin", "他化自在天", "Paranirmitavaśavartin", "cosmological"),
    ("Paranirmitavaśavartin Heaven", "他化自在天", "Paranirmitavaśavartin", "cosmological"),
    ("Nirmāṇarati", "化樂天", "Nirmāṇarati", "cosmological"),
    ("Yāma", "夜摩天", "Yāma", "cosmological"),
    ("Akaniṣṭha", "色究竟天", "Akaniṣṭha", "cosmological"),
    ("four great kings", "四大天王", "Caturmahārāja", "cosmological"),
    ("Four Great Kings", "四大天王", "Caturmahārāja", "cosmological"),
    ("Brahmā heaven", "梵天", "Brahmaloka", "cosmological"),
    ("three realms", "三界", "trailokya", "cosmological"),
    ("trichiliocosm", "三千大千世界", "trisāhasramahāsāhasralokadhātu", "cosmological"),
    ("great trichiliocosm", "三千大千世界", "trisāhasramahāsāhasralokadhātu", "cosmological"),
    ("hell", "地獄", "naraka", "cosmological"),
    ("hungry ghost", "餓鬼", "preta", "cosmological"),
    ("hungry ghosts", "餓鬼", "preta", "cosmological"),
    ("animal realm", "畜生", "tiryagyoni", "cosmological"),
    ("three evil paths", "三惡道", "trayo durgati", "cosmological"),
    ("five turbidities", "五濁", "pañcakaṣāya", "cosmological"),
    ("kalpa", "劫", "kalpa", "cosmological"),
    ("kalpas", "劫", "kalpa", "cosmological"),
    ("Fortunate Kalpa", "賢劫", "bhadrakalpa", "cosmological"),
    ("Bhadra kalpa", "賢劫", "bhadrakalpa", "cosmological"),
    ("koṭi", "億", "koṭi", "cosmological"),
    ("koṭis", "億", "koṭi", "cosmological"),
    ("maṇḍala", "曼荼羅", "maṇḍala", "cosmological"),
    ("saṃsāra", "輪迴", "saṃsāra", "cosmological"),
    ("Mount Meru", "須彌山", "Sumeru", "cosmological"),

    # === DOCTRINAL ===
    ("nirvāṇa", "涅槃", "nirvāṇa", "doctrinal"),
    ("nirvana", "涅槃", "nirvāṇa", "doctrinal"),
    ("parinirvāṇa", "般涅槃", "parinirvāṇa", "doctrinal"),
    ("bodhi", "菩提", "bodhi", "doctrinal"),
    ("anuttarā-samyak-saṃbodhi", "阿耨多羅三藐三菩提", "anuttarā-samyak-saṃbodhi", "doctrinal"),
    ("prajñāpāramitā", "般若波羅蜜多", "prajñāpāramitā", "doctrinal"),
    ("prajñā", "般若", "prajñā", "doctrinal"),
    ("dharma", "法", "dharma", "doctrinal"),
    ("Dharma", "法", "dharma", "doctrinal"),
    ("saṃgha", "僧伽", "saṃgha", "doctrinal"),
    ("Saṃgha", "僧伽", "saṃgha", "doctrinal"),
    ("Samgha", "僧伽", "saṃgha", "doctrinal"),
    ("Three Jewels", "三寶", "triratna", "doctrinal"),
    ("three refuges", "三歸依", "triśaraṇa", "doctrinal"),
    ("five aggregates", "五蘊", "pañcaskandha", "doctrinal"),
    ("five aggregates of clinging", "五取蘊", "pañcopādānaskandha", "doctrinal"),
    ("form", "色", "rūpa", "doctrinal"),
    ("feeling", "受", "vedanā", "doctrinal"),
    ("perception", "想", "saṃjñā", "doctrinal"),
    ("formations", "行", "saṃskāra", "doctrinal"),
    ("volitional formations", "行", "saṃskāra", "doctrinal"),
    ("consciousness", "識", "vijñāna", "doctrinal"),
    ("dependent origination", "緣起", "pratītyasamutpāda", "doctrinal"),
    ("dependent arising", "緣起", "pratītyasamutpāda", "doctrinal"),
    ("twelve links", "十二因緣", "dvādaśāṅga-pratītyasamutpāda", "doctrinal"),
    ("ignorance", "無明", "avidyā", "doctrinal"),
    ("name-and-form", "名色", "nāmarūpa", "doctrinal"),
    ("six sense bases", "六入", "ṣaḍāyatana", "doctrinal"),
    ("contact", "觸", "sparśa", "doctrinal"),
    ("craving", "愛", "tṛṣṇā", "doctrinal"),
    ("grasping", "取", "upādāna", "doctrinal"),
    ("becoming", "有", "bhava", "doctrinal"),
    ("birth", "生", "jāti", "doctrinal"),
    ("aging and death", "老死", "jarāmaraṇa", "doctrinal"),
    ("four noble truths", "四聖諦", "catvāri āryasatyāni", "doctrinal"),
    ("truth of suffering", "苦諦", "duḥkha-satya", "doctrinal"),
    ("truth of the origin", "集諦", "samudaya-satya", "doctrinal"),
    ("truth of cessation", "滅諦", "nirodha-satya", "doctrinal"),
    ("truth of the path", "道諦", "mārga-satya", "doctrinal"),
    ("impermanence", "無常", "anitya", "doctrinal"),
    ("suffering", "苦", "duḥkha", "doctrinal"),
    ("emptiness", "空", "śūnyatā", "doctrinal"),
    ("not-self", "無我", "anātman", "doctrinal"),
    ("non-self", "無我", "anātman", "doctrinal"),
    ("three marks", "三法印", "trilakṣaṇa", "doctrinal"),
    ("liberation", "解脫", "vimukti", "doctrinal"),
    ("liberation of mind", "心解脫", "cetovimutti", "doctrinal"),
    ("stream-entry", "須陀洹", "srotāpatti", "doctrinal"),
    ("stream-enterer", "須陀洹", "srotāpanna", "doctrinal"),
    ("srotāpanna", "須陀洹", "srotāpanna", "doctrinal"),
    ("srotāpatti", "須陀洹果", "srotāpatti", "doctrinal"),
    ("once-return", "斯陀含", "sakṛdāgāmin", "doctrinal"),
    ("once-returner", "斯陀含", "sakṛdāgāmin", "doctrinal"),
    ("non-return", "阿那含", "anāgāmin", "doctrinal"),
    ("non-returner", "阿那含", "anāgāmin", "doctrinal"),
    ("anāgāmin", "阿那含", "anāgāmin", "doctrinal"),
    ("Middle Way", "中道", "madhyamā-pratipad", "doctrinal"),
    ("conceptual proliferation", "戲論", "prapañca", "doctrinal"),
    ("conceptual proliferations", "戲論", "prapañca", "doctrinal"),
    ("conventional truth", "世俗諦", "saṃvṛti-satya", "doctrinal"),
    ("ultimate truth", "勝義諦", "paramārtha-satya", "doctrinal"),
    ("two truths", "二諦", "dvisatya", "doctrinal"),
    ("buddha-nature", "佛性", "buddhadhātu", "doctrinal"),
    ("tathāgatagarbha", "如來藏", "tathāgatagarbha", "doctrinal"),
    ("ālaya-vijñāna", "阿賴耶識", "ālaya-vijñāna", "doctrinal"),
    ("storehouse consciousness", "阿賴耶識", "ālaya-vijñāna", "doctrinal"),
    ("afflicted mentation", "末那識", "kliṣṭa-manas", "doctrinal"),
    ("mentation", "意", "manas", "doctrinal"),
    ("self-view", "我見", "ātma-dṛṣṭi", "doctrinal"),
    ("self-conceit", "我慢", "ātma-māna", "doctrinal"),
    ("karma", "業", "karma", "doctrinal"),
    ("karmic consequences", "業報", "karmavipāka", "doctrinal"),
    ("defilements", "煩惱", "kleśa", "doctrinal"),
    ("afflictions", "煩惱", "kleśa", "doctrinal"),
    ("outflows", "漏", "āsrava", "doctrinal"),
    ("three poisons", "三毒", "triviṣa", "doctrinal"),
    ("greed", "貪", "rāga", "doctrinal"),
    ("anger", "瞋", "dveṣa", "doctrinal"),
    ("delusion", "癡", "moha", "doctrinal"),
    ("right view", "正見", "samyag-dṛṣṭi", "doctrinal"),
    ("wrong view", "邪見", "mithyā-dṛṣṭi", "doctrinal"),
    ("signlessness", "無相", "animitta", "doctrinal"),
    ("wishlessness", "無願", "apraṇihita", "doctrinal"),
    ("three doors of liberation", "三解脫門", "trīṇi vimokṣamukhāni", "doctrinal"),
    ("twelve divisions of scripture", "十二部經", "dvādaśāṅga-pravacana", "doctrinal"),
    ("sūtra", "經", "sūtra", "doctrinal"),
    ("sūtras", "經", "sūtra", "doctrinal"),
    ("geyā", "應頌", "geya", "doctrinal"),
    ("geyas", "應頌", "geya", "doctrinal"),
    ("gāthā", "偈", "gāthā", "doctrinal"),
    ("gāthās", "偈", "gāthā", "doctrinal"),
    ("gathas", "偈", "gāthā", "doctrinal"),
    ("udāna", "自說", "udāna", "doctrinal"),
    ("udānas", "自說", "udāna", "doctrinal"),
    ("nidāna", "因緣", "nidāna", "doctrinal"),
    ("nidānas", "因緣", "nidāna", "doctrinal"),
    ("jātaka", "本生", "jātaka", "doctrinal"),
    ("jātakas", "本生", "jātaka", "doctrinal"),
    ("vaipulya", "方廣", "vaipulya", "doctrinal"),
    ("vaipulyas", "方廣", "vaipulya", "doctrinal"),
    ("avadāna", "譬喻", "avadāna", "doctrinal"),
    ("avadānas", "譬喻", "avadāna", "doctrinal"),
    ("upadeśa", "論議", "upadeśa", "doctrinal"),
    ("upadeshas", "論議", "upadeśa", "doctrinal"),
    ("Tripiṭaka", "三藏", "Tripiṭaka", "doctrinal"),
    ("Vinaya", "律", "vinaya", "doctrinal"),
    ("Abhidharma", "阿毘達磨", "Abhidharma", "doctrinal"),
    ("Āgama", "阿含", "Āgama", "doctrinal"),
    ("Āgamas", "阿含", "Āgama", "doctrinal"),
    ("Great Vehicle", "大乘", "Mahāyāna", "doctrinal"),
    ("Mahāyāna", "大乘", "Mahāyāna", "doctrinal"),
    ("Hīnayāna", "小乘", "Hīnayāna", "doctrinal"),
    ("Madhyamaka", "中觀", "Madhyamaka", "doctrinal"),
    ("ten powers", "十力", "daśabala", "doctrinal"),
    ("four fearlessnesses", "四無畏", "catvāri vaiśāradyāni", "doctrinal"),
    ("eighteen unique dharmas", "十八不共法", "aṣṭādaśa āveṇika-buddhadharma", "doctrinal"),
    ("five eyes", "五眼", "pañcacakṣus", "doctrinal"),
    ("divine eye", "天眼", "divyacakṣus", "doctrinal"),
    ("wisdom eye", "慧眼", "prajñācakṣus", "doctrinal"),
    ("dharma eye", "法眼", "dharmacakṣus", "doctrinal"),
    ("buddha eye", "佛眼", "buddhacakṣus", "doctrinal"),
    ("six supernatural powers", "六神通", "ṣaḍabhijñā", "doctrinal"),
    ("supernatural powers", "神通", "abhijñā", "doctrinal"),

    # === PRACTICE ===
    ("samādhi", "三摩地", "samādhi", "practice"),
    ("dhyāna", "禪", "dhyāna", "practice"),
    ("four dhyānas", "四禪", "catvāri dhyānāni", "practice"),
    ("jhāna", "禪", "dhyāna", "practice"),
    ("meditation", "禪定", "dhyāna", "practice"),
    ("concentration", "定", "samādhi", "practice"),
    ("mindfulness", "念", "smṛti", "practice"),
    ("right mindfulness", "正念", "samyak-smṛti", "practice"),
    ("four foundations of mindfulness", "四念處", "catvāri smṛtyupasthānāni", "practice"),
    ("four right efforts", "四正勤", "catvāri samyakpradhānāni", "practice"),
    ("four bases of supernatural power", "四如意足", "catvāra ṛddhipādāḥ", "practice"),
    ("five faculties", "五根", "pañcendriyāṇi", "practice"),
    ("five powers", "五力", "pañcabalāni", "practice"),
    ("seven factors of awakening", "七覺支", "saptabodhyaṅga", "practice"),
    ("eightfold path", "八正道", "aṣṭāṅgika-mārga", "practice"),
    ("noble eightfold path", "八正道", "āryāṣṭāṅgika-mārga", "practice"),
    ("thirty-seven factors of awakening", "三十七道品", "saptatriṃśad bodhipakṣyadharmāḥ", "practice"),
    ("six pāramitās", "六波羅蜜", "ṣaṭpāramitā", "practice"),
    ("six perfections", "六度", "ṣaṭpāramitā", "practice"),
    ("dāna-pāramitā", "布施波羅蜜", "dāna-pāramitā", "practice"),
    ("dāna", "布施", "dāna", "practice"),
    ("giving", "布施", "dāna", "practice"),
    ("śīla-pāramitā", "持戒波羅蜜", "śīla-pāramitā", "practice"),
    ("śīla", "戒", "śīla", "practice"),
    ("morality", "戒", "śīla", "practice"),
    ("kṣānti-pāramitā", "忍辱波羅蜜", "kṣānti-pāramitā", "practice"),
    ("kṣānti", "忍辱", "kṣānti", "practice"),
    ("patience", "忍辱", "kṣānti", "practice"),
    ("vīrya-pāramitā", "精進波羅蜜", "vīrya-pāramitā", "practice"),
    ("vīrya", "精進", "vīrya", "practice"),
    ("diligence", "精進", "vīrya", "practice"),
    ("dhyāna-pāramitā", "禪定波羅蜜", "dhyāna-pāramitā", "practice"),
    ("loving-kindness", "慈", "maitrī", "practice"),
    ("compassion", "悲", "karuṇā", "practice"),
    ("great compassion", "大悲", "mahākaruṇā", "practice"),
    ("four immeasurables", "四無量心", "catvāry apramāṇāni", "practice"),
    ("four formless absorptions", "四無色定", "caturārūpyadhyāna", "practice"),
    ("eight liberations", "八解脫", "aṣṭavimokṣa", "practice"),
    ("brahmacarya", "梵行", "brahmacarya", "practice"),
    ("pure conduct", "梵行", "brahmacarya", "practice"),
    ("almsround", "乞食", "piṇḍapāta", "practice"),
    ("dhāraṇī", "陀羅尼", "dhāraṇī", "practice"),
    ("mantra", "真言", "mantra", "practice"),
    ("emptiness samādhi", "空三昧", "śūnyatā-samādhi", "practice"),
    ("signless samādhi", "無相三昧", "animitta-samādhi", "practice"),
    ("wishless samādhi", "無願三昧", "apraṇihita-samādhi", "practice"),
    ("patient endurance", "忍", "kṣānti", "practice"),
    ("non-retrogression", "不退轉", "avaivartika", "practice"),
    ("disenchantment", "厭離", "nirveda", "practice"),
    ("recollection", "念", "smṛti", "practice"),
    ("equanimity", "捨", "upekṣā", "practice"),
    ("faith", "信", "śraddhā", "practice"),
    ("tranquility", "輕安", "praśrabdhi", "practice"),
    ("heedfulness", "不放逸", "apramāda", "practice"),
    ("aspiration", "欲", "chanda", "practice"),
    ("volition", "思", "cetanā", "practice"),
    ("attention", "作意", "manaskāra", "practice"),
    ("resolve", "勝解", "adhimokṣa", "practice"),
    ("wisdom", "慧", "prajñā", "practice"),
    ("mindfulness of the Buddha", "念佛", "buddhānusmṛti", "practice"),
    ("mindfulness of the Dharma", "念法", "dharmānusmṛti", "practice"),
    ("mindfulness of the Saṅgha", "念僧", "saṃghānusmṛti", "practice"),
    ("vajra", "金剛", "vajra", "practice"),
    ("consecration", "灌頂", "abhiṣeka", "practice"),

    # === MONASTIC ITEMS / VINAYA ===
    ("kāṣāya", "袈裟", "kāṣāya", "monastic_item"),
    ("kasaya", "袈裟", "kāṣāya", "monastic_item"),
    ("kāṣāya robe", "袈裟", "kāṣāya", "monastic_item"),
    ("uttarāsaṅga", "鬱多羅僧", "uttarāsaṅga", "monastic_item"),
    ("saṃghāṭī", "僧伽梨", "saṃghāṭī", "monastic_item"),
    ("antarvāsa", "安陀會", "antarvāsa", "monastic_item"),
    ("alms bowl", "鉢", "pātra", "monastic_item"),
    ("Prātimokṣa", "波羅提木叉", "Prātimokṣa", "monastic_item"),
    ("Pratimoksa", "波羅提木叉", "Prātimokṣa", "monastic_item"),
    ("pārājika", "波羅夷", "pārājika", "monastic_item"),
    ("parajika", "波羅夷", "pārājika", "monastic_item"),
    ("rains retreat", "安居", "varṣā", "monastic_item"),
    ("five precepts", "五戒", "pañcaśīla", "monastic_item"),
    ("precepts", "戒", "śīla", "monastic_item"),
    ("ordination", "受具足戒", "upasampadā", "monastic_item"),
    ("full ordination", "受具足戒", "upasampadā", "monastic_item"),
    ("stūpa", "塔", "stūpa", "monastic_item"),

    # === OTHER ===
    ("kṣatriya", "剎帝利", "kṣatriya", "other"),
    ("brāhmaṇa", "婆羅門", "brāhmaṇa", "other"),
    ("brahmin", "婆羅門", "brāhmaṇa", "other"),
    ("brahmins", "婆羅門", "brāhmaṇa", "other"),
    ("Licchavī", "離車", "Licchavī", "other"),
    ("Licchavis", "離車", "Licchavī", "other"),
    ("Vṛjji", "跋耆", "Vṛjji", "other"),
    ("Vṛjjis", "跋耆", "Vṛjji", "other"),
    ("maṇi", "摩尼", "maṇi", "other"),
    ("cintāmaṇi", "如意寶珠", "cintāmaṇi", "other"),
    ("four elements", "四大", "catvāri mahābhūtāni", "other"),
    ("four great elements", "四大", "catvāri mahābhūtāni", "other"),
    ("Dharmaguptaka", "法藏部", "Dharmaguptaka", "other"),
    ("Mahisasaka", "彌沙塞部", "Mahīśāsaka", "other"),
    ("Mahīśāsaka", "彌沙塞部", "Mahīśāsaka", "other"),

    # More doctrinal terms
    ("three fetters", "三結", "trīṇi saṃyojanāni", "doctrinal"),
    ("five precepts", "五戒", "pañcaśīla", "doctrinal"),
    ("ten wholesome deeds", "十善業", "daśakuśalakarmapatha", "doctrinal"),
    ("five hindrances", "五蓋", "pañcanīvaraṇa", "doctrinal"),
    ("three characteristics", "三法印", "trilakṣaṇa", "doctrinal"),
    ("conditioned phenomena", "有為法", "saṃskṛta-dharma", "doctrinal"),
    ("unconditioned", "無為", "asaṃskṛta", "doctrinal"),
    ("conventional designation", "假名", "prajñapti", "doctrinal"),
    ("self-nature", "自性", "svabhāva", "doctrinal"),

    # More practices
    ("seven factors of awakening", "七覺支", "saptabodhyaṅga", "practice"),
    ("mindfulness awakening-factor", "念覺支", "smṛti-saṃbodhyaṅga", "practice"),
    ("investigation awakening-factor", "擇法覺支", "dharmavicaya-saṃbodhyaṅga", "practice"),
    ("energy awakening-factor", "精進覺支", "vīrya-saṃbodhyaṅga", "practice"),
    ("joy awakening-factor", "喜覺支", "prīti-saṃbodhyaṅga", "practice"),
    ("tranquility awakening-factor", "輕安覺支", "praśrabdhi-saṃbodhyaṅga", "practice"),
    ("concentration awakening-factor", "定覺支", "samādhi-saṃbodhyaṅga", "practice"),
    ("equanimity awakening-factor", "捨覺支", "upekṣā-saṃbodhyaṅga", "practice"),

    # More secondary afflictions from T1602
    ("wrath", "忿", "krodha", "doctrinal"),
    ("enmity", "恨", "upanāha", "doctrinal"),
    ("dissimulation", "覆", "mrakṣa", "doctrinal"),
    ("vexation", "惱", "pradāśa", "doctrinal"),
    ("jealousy", "嫉", "īrṣyā", "doctrinal"),
    ("miserliness", "慳", "mātsarya", "doctrinal"),
    ("deceit", "誑", "māyā", "doctrinal"),
    ("guile", "諂", "śāṭhya", "doctrinal"),
    ("arrogance", "憍", "mada", "doctrinal"),
    ("harmfulness", "害", "vihiṃsā", "doctrinal"),
    ("torpor", "惛沉", "styāna", "doctrinal"),
    ("restlessness", "掉舉", "auddhatya", "doctrinal"),
    ("laziness", "懈怠", "kausīdya", "doctrinal"),
    ("forgetfulness", "失念", "muṣita-smṛtitā", "doctrinal"),
    ("distraction", "散亂", "vikṣepa", "doctrinal"),
    ("regret", "惡作", "kaukṛtya", "doctrinal"),
    ("drowsiness", "睡眠", "middha", "doctrinal"),
    ("applied thought", "尋", "vitarka", "doctrinal"),
    ("sustained thought", "伺", "vicāra", "doctrinal"),
    ("conceit", "慢", "māna", "doctrinal"),
    ("doubt", "疑", "vicikitsā", "doctrinal"),
    ("non-harmfulness", "不害", "ahiṃsā", "doctrinal"),
    ("shame", "慚", "hrī", "doctrinal"),
    ("decorum", "愧", "apatrāpya", "doctrinal"),

    # Cosmological trees/locations
    ("Pāṭalī tree", "波吒釐樹", "Pāṭalī", "other"),
    ("Puṇḍarīka tree", "芬陀利樹", "Puṇḍarīka", "other"),
    ("Śāla tree", "娑羅樹", "śāla", "other"),
    ("Śirīṣa tree", "尸利沙樹", "śirīṣa", "other"),
    ("Udumbara tree", "優曇婆羅樹", "udumbara", "other"),
    ("Nyagrodha tree", "尼拘陀樹", "nyagrodha", "other"),
    ("Aśvattha tree", "阿說他樹", "aśvattha", "other"),
    ("Bodhi tree", "菩提樹", "bodhivṛkṣa", "other"),

    # === ADDITIONAL PERSONS ===
    ("Bimbisāra", "頻婆娑羅", "Bimbisāra", "person"),
    ("King Bimbisāra", "頻婆娑羅王", "Bimbisāra", "person"),
    ("Vaiśravaṇa", "毘沙門", "Vaiśravaṇa", "person"),
    ("Dhṛtarāṣṭra", "持國天王", "Dhṛtarāṣṭra", "person"),
    ("Virūḍhaka", "增長天王", "Virūḍhaka", "person"),
    ("Virūpākṣa", "廣目天王", "Virūpākṣa", "person"),
    ("Kauśika", "憍尸迦", "Kauśika", "person"),
    ("Anīkṣipta", "阿泥翅", "Anīkṣipta", "person"),
    ("Sudāna", "須達拏", "Sudāna", "person"),
    ("Reṇu", "大典尊", "Reṇu", "person"),
    ("Mahādṛḍha", "大堅固", "Mahādṛḍha", "person"),
    ("Nigrodha", "尼拘陀", "Nigrodha", "person"),
    ("Vajramuṣṭi", "金剛拳", "Vajramuṣṭi", "person"),
    ("Ākāśasaṃbhava", "虛空生", "Ākāśasaṃbhava", "person"),
    ("Māravimardaka", "摧魔", "Māravimardaka", "person"),
    ("Sūryaprabha", "日光", "Sūryaprabha", "person"),
    ("Amoghadarśin", "不空見", "Amoghadarśin", "person"),
    ("Varuṇadatta", "水天授", "Varuṇadatta", "person"),
    ("Nandika", "難提迦", "Nandika", "person"),
    ("Sudinna", "須提那", "Sudinna", "person"),

    # === ADDITIONAL PLACES ===
    ("Kalandaka Bamboo Grove", "迦蘭陀竹園", "Kalandakanivāpa Veṇuvana", "place"),
    ("Bamboo Grove", "竹林精舍", "Veṇuvana", "place"),
    ("Kuśinagara", "拘尸那", "Kuśinagara", "place"),
    ("Kāśī", "迦尸", "Kāśī", "place"),
    ("Kosala", "拘薩羅", "Kosala", "place"),
    ("Mallā", "末羅", "Mallā", "place"),
    ("Campā", "瞻波", "Campā", "place"),
    ("Mithilā", "彌稀羅", "Mithilā", "place"),
    ("Kuru", "拘樓", "Kuru", "place"),
    ("Pañcāla", "般闍羅", "Pañcāla", "place"),
    ("Avanti", "阿盤提", "Avanti", "place"),
    ("Videha", "毘提訶", "Videha", "place"),
    ("Kamboja", "劍浮沙", "Kamboja", "place"),
    ("Aṅga", "鴦伽", "Aṅga", "place"),
    ("Pāṭalī", "波吒釐", "Pāṭalī", "place"),
    ("Vaiśālī", "毘舍離", "Vaiśālī", "place"),
    ("Sārandada Shrine", "沙然陀", "Sārandada", "place"),

    # === ADDITIONAL COSMOLOGICAL ===
    ("asura", "阿修羅", "asura", "cosmological"),
    ("asuras", "阿修羅", "asura", "cosmological"),
    ("gandharva", "乾闥婆", "gandharva", "cosmological"),
    ("devaputra", "天子", "devaputra", "cosmological"),
    ("devaputras", "天子", "devaputra", "cosmological"),
    ("Cāturmahārājakāyika", "四大王眾天", "Cāturmahārājakāyika", "cosmological"),
    ("desire realm", "欲界", "kāmadhātu", "cosmological"),
    ("form realm", "色界", "rūpadhātu", "cosmological"),
    ("formless realm", "無色界", "ārūpyadhātu", "cosmological"),
    ("five Pure Abodes", "五淨居天", "pañca śuddhāvāsa", "cosmological"),
    ("Avṛha", "無煩天", "Avṛha", "cosmological"),
    ("Atapa", "無熱天", "Atapa", "cosmological"),
    ("Sudṛśa", "善見天", "Sudṛśa", "cosmological"),
    ("Sudarśana", "善現天", "Sudarśana", "cosmological"),
    ("nāga", "龍", "nāga", "cosmological"),
    ("yakṣa", "夜叉", "yakṣa", "cosmological"),

    # === ADDITIONAL DOCTRINAL ===
    ("five hindrances", "五蓋", "pañcanīvaraṇa", "doctrinal"),
    ("sensual desire", "欲貪", "kāmacchanda", "doctrinal"),
    ("ill will", "瞋恚", "vyāpāda", "doctrinal"),
    ("sloth-and-torpor", "昏沉睡眠", "styāna-middha", "doctrinal"),
    ("restlessness-and-remorse", "掉舉惡作", "auddhatya-kaukṛtya", "doctrinal"),
    ("six sense bases", "六入", "ṣaḍāyatana", "doctrinal"),
    ("āyatana", "處", "āyatana", "doctrinal"),
    ("six contacts", "六觸", "ṣaṭ sparśa", "doctrinal"),
    ("six consciousnesses", "六識", "ṣaḍ vijñāna", "doctrinal"),
    ("eye-consciousness", "眼識", "cakṣur-vijñāna", "doctrinal"),
    ("ear-consciousness", "耳識", "śrotra-vijñāna", "doctrinal"),
    ("nose-consciousness", "鼻識", "ghrāṇa-vijñāna", "doctrinal"),
    ("tongue-consciousness", "舌識", "jihvā-vijñāna", "doctrinal"),
    ("body-consciousness", "身識", "kāya-vijñāna", "doctrinal"),
    ("mental consciousness", "意識", "mano-vijñāna", "doctrinal"),
    ("eight worldly conditions", "八風", "aṣṭalokadharma", "doctrinal"),
    ("view of the self-collection", "身見", "satkāya-dṛṣṭi", "doctrinal"),
    ("extreme view", "邊見", "antagrāha-dṛṣṭi", "doctrinal"),
    ("clinging to views", "見取", "dṛṣṭi-parāmarśa", "doctrinal"),
    ("clinging to rules and observances", "戒禁取", "śīla-vrata-parāmarśa", "doctrinal"),
    ("selflessness of persons", "人無我", "pudgala-nairātmya", "doctrinal"),
    ("selflessness of dharmas", "法無我", "dharma-nairātmya", "doctrinal"),
    ("twofold selflessness", "二無我", "dvi-nairātmya", "doctrinal"),
    ("cessation of perception and feeling", "滅盡定", "nirodha-samāpatti", "doctrinal"),
    ("seven stations of consciousness", "七識住", "saptavijñānasthiti", "doctrinal"),
    ("nine abodes of beings", "九有情居", "navasattāvāsa", "doctrinal"),
    ("sphere of boundless space", "空無邊處", "ākāśānantyāyatana", "doctrinal"),
    ("sphere of boundless consciousness", "識無邊處", "vijñānānantyāyatana", "doctrinal"),
    ("sphere of nothingness", "無所有處", "ākiñcanyāyatana", "doctrinal"),
    ("sphere of neither-perception-nor-non-perception", "非想非非想處", "naivasaṃjñānāsaṃjñāyatana", "doctrinal"),
    ("conceptual proliferation", "戲論", "prapañca", "doctrinal"),
    ("āsrava", "漏", "āsrava", "doctrinal"),
    ("seeds", "種子", "bīja", "doctrinal"),

    # === ADDITIONAL PRACTICE ===
    ("right view", "正見", "samyag-dṛṣṭi", "practice"),
    ("right intention", "正思惟", "samyak-saṃkalpa", "practice"),
    ("right speech", "正語", "samyag-vāc", "practice"),
    ("right action", "正業", "samyak-karmānta", "practice"),
    ("right livelihood", "正命", "samyag-ājīva", "practice"),
    ("right effort", "正精進", "samyag-vyāyāma", "practice"),
    ("right concentration", "正定", "samyak-samādhi", "practice"),
    ("sympathetic joy", "喜", "muditā", "practice"),
    ("lion's roar", "獅子吼", "siṃhanāda", "practice"),
    ("Poṣadha", "布薩", "poṣadha", "practice"),

    # === ADDITIONAL MONASTIC ===
    ("four assemblies", "四眾", "catuḥpariṣad", "monastic_item"),
    ("saṃgha", "僧伽", "saṃgha", "monastic_item"),
    ("Saṅgha", "僧伽", "saṃgha", "monastic_item"),

    # === ADDITIONAL OTHER ===
    ("amṛta", "甘露", "amṛta", "other"),
    ("Vedas", "吠陀", "Veda", "other"),
    ("Vedic", "吠陀", "Veda", "other"),
]


def normalize_for_search(term):
    """Create a search-friendly version of a term."""
    return term


def find_term_in_text(term, text):
    """Check if a term appears in text, with word-boundary awareness."""
    # For short common words, require word boundaries
    if len(term) <= 3:
        pattern = r'\b' + re.escape(term) + r'\b'
        return bool(re.search(pattern, text))
    # For italicized terms in markdown
    if re.search(re.escape(term), text):
        return True
    # Also check with markdown italics wrapping
    if re.search(r'\*' + re.escape(term) + r'\*', text):
        return True
    return False


def build_glossary(texts):
    """Build glossary from master list, checking which texts contain each term."""
    # Consolidate entries: merge duplicates by (english_lower, category)
    # to handle variant spellings mapping to same concept
    consolidated = {}  # key -> {english, chinese, sanskrit, category, search_terms}

    for english, chinese, sanskrit, category in MASTER_GLOSSARY:
        # Use canonical form as key (prefer diacritical form)
        key = (english.lower().rstrip('s'), category)
        if key not in consolidated:
            consolidated[key] = {
                'english': english,
                'chinese': chinese,
                'sanskrit': sanskrit,
                'category': category,
                'search_terms': set(),
            }
        consolidated[key]['search_terms'].add(english)
        # Keep the longest/most diacritical form as the canonical english
        if len(english) > len(consolidated[key]['english']):
            consolidated[key]['english'] = english

    # Now scan texts for each consolidated entry
    glossary_entries = []
    seen_keys = set()

    for (english, chinese, sanskrit, category) in MASTER_GLOSSARY:
        # Deduplicate: use (canonical_english_lower, category) as dedup key
        dedup_key = (english.lower(), category)
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        sources = []
        for t_num, text in texts.items():
            if find_term_in_text(english, text):
                sources.append(t_num)

        if sources:
            glossary_entries.append({
                'english': english,
                'chinese': chinese,
                'sanskrit': sanskrit,
                'category': category,
                'sources': sorted(sources),
            })

    return glossary_entries


def has_diacritics(s):
    """Check if string contains IAST diacritical marks."""
    diacriticals = set('āīūṛṝḷḹṃḥṅñṭḍṇśṣĀĪŪṚṜḶḸṂḤṄÑṬḌṆŚṢ')
    return any(c in diacriticals for c in s)


def deduplicate_glossary(entries):
    """Remove duplicate entries by merging on (chinese, category).

    For entries sharing the same Chinese + category:
    - Merge all sources
    - Prefer the form with IAST diacritics as canonical English
    - Among diacritical forms, prefer shorter (singular) forms
    """
    # First pass: group by (chinese, category) where chinese is non-empty
    by_chinese = defaultdict(list)
    no_chinese = []
    for e in entries:
        if e['chinese']:
            key = (e['chinese'], e['category'])
            by_chinese[key].append(e)
        else:
            no_chinese.append(e)

    result = []
    for key, group in by_chinese.items():
        # Merge all sources
        all_sources = set()
        for g in group:
            all_sources.update(g['sources'])

        # Pick canonical English: prefer diacritical, then shortest
        # Sort: diacritical first, then by length (shorter=singular preferred), then alphabetical
        group.sort(key=lambda x: (
            not has_diacritics(x['english']),  # diacritical first
            len(x['english']),                  # shorter first
            x['english']
        ))
        best = group[0].copy()
        best['sources'] = sorted(all_sources)
        result.append(best)

    # Second pass for no-chinese entries: group by (english_normalized, category)
    by_english = defaultdict(list)
    for e in no_chinese:
        norm = e['english'].lower().rstrip('s')
        key = (norm, e['category'])
        by_english[key].append(e)

    for key, group in by_english.items():
        all_sources = set()
        for g in group:
            all_sources.update(g['sources'])
        group.sort(key=lambda x: (-len(x['sources']), len(x['english'])))
        best = group[0].copy()
        best['sources'] = sorted(all_sources)
        result.append(best)

    return result


def sort_glossary(entries):
    """Sort glossary: by category, then alphabetically by English."""
    category_order = [
        'person', 'place', 'title', 'doctrinal', 'practice',
        'cosmological', 'monastic_item', 'other'
    ]
    def sort_key(e):
        cat_idx = category_order.index(e['category']) if e['category'] in category_order else 99
        return (cat_idx, e['english'].lower())
    return sorted(entries, key=sort_key)


def main():
    print("Reading translation files...")
    texts = read_all_translations()
    print(f"  Read {len(texts)} files")

    print("Building glossary...")
    entries = build_glossary(texts)
    print(f"  Found {len(entries)} raw entries")

    print("Deduplicating...")
    entries = deduplicate_glossary(entries)
    print(f"  {len(entries)} entries after dedup")

    # Final cross-category dedup: merge entries with same english (case-insensitive)
    from collections import defaultdict as dd2
    by_eng = dd2(list)
    for e in entries:
        by_eng[e['english'].lower()].append(e)
    deduped = []
    for eng, group in by_eng.items():
        if len(group) == 1:
            deduped.append(group[0])
        else:
            # Merge sources, keep preferred category
            all_sources = set()
            for g in group:
                all_sources.update(g['sources'])
            best = group[0].copy()
            best['sources'] = sorted(all_sources)
            deduped.append(best)
    entries = deduped
    print(f"  {len(entries)} entries after cross-category dedup")

    print("Sorting...")
    entries = sort_glossary(entries)

    print(f"Writing {len(entries)} entries to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    # Print summary
    from collections import Counter
    cat_counts = Counter(e['category'] for e in entries)
    print("\nGlossary summary:")
    for cat in ['person', 'place', 'title', 'doctrinal', 'practice',
                'cosmological', 'monastic_item', 'other']:
        print(f"  {cat}: {cat_counts.get(cat, 0)} entries")
    print(f"  TOTAL: {len(entries)} entries")

    # Show most widely-attested terms
    print("\nMost widely-attested terms (appearing in 20+ texts):")
    for e in sorted(entries, key=lambda x: -len(x['sources'])):
        if len(e['sources']) >= 20:
            print(f"  {e['english']} ({e['category']}): {len(e['sources'])} texts")


if __name__ == '__main__':
    main()
