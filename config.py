import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEFAULT_LOG_LEVEL = os.environ.get("DEFAULT_LOG_LEVEL", "DEBUG")
    LOG_DIRECTORY = os.environ.get("LOG_DIRECTORY", "logs")
    LOG_FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name} | {message}"
    CONSOLE_LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>"
    LOG_ROTATION = "10 MB"
    LOG_RETENTION = 5
    LOG_COMPRESSION = "zip"

    EXCLUDE_WORDS = ["Null"]

    EXCLUDED_SECTION_KEYWORDS = [
        "著作",
        "参考文献",
        "関連文献",
        "作品",
        "書誌情報",
        "参考文献",
        "選集",
        "全集",
        "共著",
        "脚注",
        "注釈",
        "出典",
        "関連項目",
    ]

    regex_patterns = {
        "timeline_year_month_day": [
            "(\\d{4})年(\\d{1,2})月(\\d{1,2})日?(?:[\\s、]{1,2})?(.+?)(?=(?:\\d{4}年|$))",
            "(\\d{4})/(\\d{1,2})/(\\d{1,2})(?:[\\s、]{1,2})?(.+?)(?=(?:\\d{4}年|$))",
            "(\\d{4})-(\\d{1,2})-(\\d{1,2})(?:[\\s、]{1,2})?(.+?)(?=(?:\\d{4}年|$))"
        ],
        "timeline_year_only": [
            "(\\d{4})年(?:[\\s、]{1,2})?(.+?)(?=(?:\\d{4}年|$))"
        ],
        "rule_based_ner": [
            "([一-龯]{1,})\\s([一-龯]{1,})",
            "([一-龯]{1,})先生",
            "([一-龯]{1,})氏",
            "([A-Z][a-z]+)\\s([A-Z][a-z]+)"
        ],
        "name": [
            r"(.[ァ-ヶー・]+)"
        ],
        "real_name": [
            r"[A-Za-z\s]+"
        ],
        "birth_date": [
            r"(\d{4})年\s*(\d{1,2})月(\d{1,2})日|(\d{4})-(\d{1,2})-(\d{1,2})"
        ],
        "death_date": [
            r"(\d{4})年\s*(\d{1,2})月(\d{1,2})日|(\d{4})-(\d{1,2})-(\d{1,2})"
        ],
        "residence": [
            r"(.+)"
        ],
        "birth_place": [
            r"(.+?)、\s*(.+)",
            r"(.+?)\s*,\s*(.+)"
        ],
        "death_place": [
            r"(.+?)、\s*(.+)",
            r"(.+?)\s*,\s*(.+)"
        ],
        "alma_mater": [
            r"(.+?)\((.+?)\)"
        ],
        "spouse": [
            r"(.+?)(\d{4}-\d{4}|\d{4}-\d{2,4}|\d{4}-\d{1,2}|\d{4}-\d{1}|\d{4}-|\d{4,4})",
            r"(.+)"
        ],
        "children": [
            r"(.+?)(\d{4}-\d{4}|\d{4}-\d{2,4}|\d{4}-\d{1,2}|\d{4}-\d{1}|\d{4}-|\d{4,4})",
            r"(.+)"
        ],
        "nationality": [
            r"(.+?)\s+(\d{4}-\d{4}|\d{4}-\d{2,4}|\d{4}-\d{1,2}|\d{4}-\d{1}|\d{4}-|\d{4,4})",
            r"(.+)"
        ],
        "affiliation": [
            r"(.+?)\s+(\d{4}-\d{4}|\d{4}-\d{2,4}|\d{4}-\d{1,2}|\d{4}-\d{1}|\d{4}-|\d{4,4})",
            r"(.+)"
        ],
        "occupation": [
            r"(.+)"
        ],

    }

    exclude_words_timeline = [
        "参考文献",
    ]

    key_map = {
        "名前": "name",
        "本名": "real_name",
        "別名": "alias",
        "生誕": "birth_date",
        "誕生日": "birth_date",
        "生年月日": "birth_date",
        "死没": "death_date",
        "死亡日": "death_date",
        "没年月日": "death_date",
        "出生地": "birth_place",
        "出身地": "birth_place",
        "生地": "birth_place",
        "死没地": "death_place",
        "死亡地": "death_place",
        "没地": "death_place",
        "国": "country",
        "国籍": "nationality",
        "居住": "residence",
        "活動拠点": "active_base",
        "居住地": "residence",

        "出身校": "alma_mater",
        "学歴": "education",
        "学位": "degree",
        "研究分野": "field",
        "研究機関": "institutions",
        "指導教員": "advisor",
        "博士課程指導教員": "doctoral_advisor",
        "他の指導教員": "other_advisors",
        "卒業": "graduated",
        "最終学歴": "final_education",
        "卒業年": "graduated_year",
        "修了年": "graduated_year",
        "修了": "graduated",

        "主な業績": "notable_works",
        "博士論文": "doctoral_dissertation",
        "代表作": "notable_works",
        "主な受賞歴": "awards",
        "受賞歴": "awards",
        "受賞": "awards",
        "表彰": "awards",
        "称号": "honorific_title",

        "配偶者": "spouse",
        "夫": "spouse",
        "妻": "spouse",
        "子供": "children",
        "子女": "children",
        "親": "parents",
        "影響を与えた人物": "influenced",
        "影響を受けた人物": "influenced_by",
        "師": "mentor",
        "弟子": "disciple",

        "署名": "signature",
        "ウェブサイト": "website",
        "公式サイト": "website",
        "活動": "active_periods",
        "活動期間": "active_periods",
        "肩書": "position",
        "役職": "position",
        "民族": "ethnicity",
        "宗教": "religion",
        "分野": "occupation",
        "職業": "occupation",
        "所属": "affiliation",
        "専門": "expertise",

        "作品": "works",
        "映画": "films",
        "出演": "appeared",
        "脚注": "footnote"
    }

    key_type = {
        "birth_date": ["birth_year", "birth_month", "birth_day"],  # 誕生日 (年、月、日)
        "death_date": ["death_year", "death_month", "death_day", "death_age"],  # 死亡日 (年、月、日、享年)
        "birth_place": ["birth_country", "birth_kingdom", "birth_city"],  # 出生地 (国、旧国名、都市)
        "death_place": ["death_country", "death_state", "death_city"],  # 死亡地 (国、州/県、都市)
        "residence": ["residence_country", "residence_city"],  # 居住地 (国、都市)
        "active_base": ["active_base_country", "active_base_city"],  # 活動拠点 (国、都市)
        "education": ["school", "major", "graduated_year"],  # 学歴 (学校、専攻、卒業年)
        "alma_mater": ["alma_mater_university", "alma_mater_faculty"],  # 出身校 (大学、学部)
        "spouse": ["spouse_name", "spouse_start_year", "spouse_end_year"],  # 配偶者 (名前、結婚年、離婚年)
        "children": ["children_name", "children_birth_year", "children_death_year"],  # 子供 (名前、出生年、死亡年)
        "nationality": ["nationality_country", "nationality_start_year", "nationality_end_year"],  # 国籍 (国名、開始年、終了年)
        "degree": ["degree_name", "degree_major"],  # 学位 (学位名、専攻)
        "affiliation": ["affiliation_name", "affiliation_start_year", "affiliation_end_year", "affiliation_position"], # 所属 (所属名、開始年、終了年、役職)
        "occupation": ["occupation_name"],  # 職業 (職業名)
        "awards": ["award_name", "award_year"],  # 受賞歴 (賞名、受賞年)
        "notable_works": ["notable_work_name"],  # 主な業績/代表作 (作品名)
        "advisor": ["advisor_name"],  # 指導教員 (指導教員名)
        "doctoral_advisor": ["doctoral_advisor_name"],  # 博士課程指導教員 (博士課程指導教員名)
        "influenced": ["influenced_name"],  # 影響を与えた人物（名前）
        "influenced_by": ["influenced_by_name"],  # 影響を受けた人物（名前）
    }

    _FETCH_PAGE_DATA_ERROR_MESSAGE = "HTML コンテンツがありません。fetch_page_data() を先に実行してください。"
    FULL_WIDTH_SPACE = r"\u3000"

    HEADING_LEVELS = ['mw-heading2', 'mw-heading3', 'mw-heading4']

    UNNECESSARY_TAGS = [
        "sup",
        "style",
        "scope",
        "typeof",
        "strong",
        "script",
        "noscript",
        "form",
        "input",
    ]

    BASE_URL = "https://ja.wikipedia.org/w/api.php"