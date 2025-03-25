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

    EXCLUDE_WORDS = ["英語版", "Emc", "(英語版)"]

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
        "出身地",
        "国籍",
        "民族",
        "最終学歴",
        "職歴",
        "所属",
        "家族構成",
        "配偶者",
        "子供",
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
        "没年月日": ["死亡", "死亡日", "没年月日", "死没"],
        "出身地": ["birth_place", "出身地", "生誕"],
        "国籍": ["nationality", "国", "国籍"],
        "民族": ["ethnicity"],
        "最終学歴": ["education", "学歴", "出身校"],
        "職歴": ["occupation", "職業"],
        "家族構成": ["父", "母"],
        "所属": ["affiliation"],
        "配偶者": ["spouse", "夫", "妻", "配偶者"],
        "子供": ["children", "子女", "子供"],
        "分野": ["field", "研究分野", "専門"],
        "主な業績": ["notable_works", "代表作", "主な業績", "著名な実績"],
        "受賞歴": ["awards", "受賞", "表彰", "主な受賞歴"],
        "活動期間": ["active_periods", "活動期間"],
        "称号": ["honorific_title", "肩書", "役職"],
        "宗教": ["religion"],
        "思想": ["ideology"]
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