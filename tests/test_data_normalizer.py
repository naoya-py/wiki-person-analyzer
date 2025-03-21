import pytest
from core.data_normalizer import DataNormalizer

class TestDataNormalizer:

    @pytest.mark.parametrize("input_date, expected", [
        ("令和3年5月1日", "2021-05-01"),
        ("平成30年12月31日", "2018-12-31"),
        ("2021/05/01", "2021-05-01"),
        ("2021-05-01", "2021-05-01"),
        ("不明", "不明"),
        ("", "不明"),
    ])
    def test_normalize_date(self, input_date, expected):
        assert DataNormalizer.normalize_date(input_date) == expected

    @pytest.mark.parametrize("input_location, expected", [
        ("東京", "東京都"),
        ("大阪", "大阪府"),
        ("不明な地名", "不明な地名"),
    ])
    def test_standardize_location(self, input_location, expected):
        assert DataNormalizer.standardize_location(input_location) == expected

    @pytest.mark.parametrize("input_field, expected", [
        ("物理学", "科学"),
        ("文学", "人文科学"),
        ("未知の分野", "未知の分野"),
    ])
    def test_standardize_field(self, input_field, expected):
        assert DataNormalizer.standardize_field(input_field) == expected

    @pytest.mark.parametrize("input_value, expected", [
        ("存在する値", "存在する値"),
        (None, "不明"),
        ("", "不明"),
    ])
    def test_handle_missing_value(self, input_value, expected):
        assert DataNormalizer.handle_missing_value(input_value) == expected

if __name__ == '__main__':
    pytest.main()