from backend.services.build_word_bank_candidates import (
    categorize,
    clean_phones,
    ends_in_consonant,
    has_consonant_cluster,
    is_physical_noun,
)


def test_clean_phones_strips_digits():
    assert clean_phones(["AA1", "B", "AH2", "notaphone", "3"]) == ["AA", "B", "AH"]


def test_clean_phones_empty():
    assert clean_phones([]) == []


def test_has_consonant_cluster_true():
    assert has_consonant_cluster(["S", "T", "AH"]) is True
    assert has_consonant_cluster(["K", "R"]) is True


def test_has_consonant_cluster_false():
    assert has_consonant_cluster(["AH", "S"]) is False
    assert has_consonant_cluster(["M"]) is False
    assert has_consonant_cluster([]) is False


def test_ends_in_consonant_true():
    assert ends_in_consonant(["AH", "T"]) is True
    assert ends_in_consonant(["K"]) is True


def test_ends_in_consonant_false():
    assert ends_in_consonant(["AH", "AA"]) is False
    assert ends_in_consonant([]) is False


def test_categorize_known_phonemes():
    result = categorize(["S", "T", "AH"])
    assert "s" in result
    assert "clusters" in result


def test_categorize_unknown_phonemes():
    result = categorize(["AH", "AA"])
    assert result == []


def test_is_physical_noun_true():
    assert is_physical_noun("mountain") is True
    assert is_physical_noun("river") is True


def test_is_physical_noun_false():
    assert is_physical_noun("love") is False
    assert is_physical_noun("believe") is False
