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

    exclude_words_timeline = [
        "参考文献",
    ]

    # 汎用的なキーのリスト
    GENERAL_KEYS = [
        "氏名",
        "生年月日",
        "没年月日",
        "出生地",
        "国籍",
        "民族",
        "最終学歴",
        "職歴",
        "所属",
        "配偶者",
        "子供",
        "親",
        "分野",
        "主な業績",
        "受賞歴",
        "活動期間",
        "称号",
        "宗教",
        "思想"
    ]

    # キーのマッピング
    key_map = {
        "氏名": ["name", "名前"],
        "生年月日": ["生誕", "誕生日", "生年月日"],
        "没年月日": ["死没", "死亡日", "没年月日"],
        "出生地": ["birth_place", "出身地", "生誕"],
        "国籍": ["nationality", "国", "国籍"],
        "民族": ["ethnicity"],
        "最終学歴": ["education", "学歴", "出身校"],
        "職歴": ["occupation", "職業"],
        "所属": ["affiliation"],
        "配偶者": ["spouse", "夫", "妻"],
        "子供": ["children", "子女"],
        "親": ["parents"],
        "分野": ["field", "研究分野", "専門"],
        "主な業績": ["notable_works", "代表作"],
        "受賞歴": ["awards", "受賞", "表彰", "主な受賞歴"],
        "活動期間": ["active_periods", "活動期間"],
        "称号": ["honorific_title", "肩書", "役職"],
        "宗教": ["religion"],
        "思想": ["ideology"]
    }

    key_type = {
        "生年月日": ["年", "月", "日"],  # 誕生日 (年、月、日)
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

    IGNORE_CLASSES = [
        'toccolours',
    ]

    BASE_URL = "https://ja.wikipedia.org/w/api.php"