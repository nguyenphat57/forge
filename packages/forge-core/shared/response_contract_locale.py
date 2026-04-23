from __future__ import annotations

import re

from response_contract_text import strip_markdown_code
from text_utils import normalize_text


MOJIBAKE_MARKERS = (
    "Ã",
    "Æ",
    "Ä",
    "áº",
    "á»",
    "Ãƒ",
    "Ã¡Â»",
    "Ã„â€˜",
    "Ã†Â°",
    "Ã¢â‚¬Å“",
    "Ã¢â‚¬",
)

VIETNAMESE_DIACRITIC_CHARACTERS = set(
    "ÄƒÃ¢Ä‘ÃªÃ´Æ¡Æ°"
    "Ã¡Ã áº£Ã£áº¡áº¯áº±áº³áºµáº·áº¥áº§áº©áº«áº­"
    "Ã©Ã¨áº»áº½áº¹áº¿á»á»ƒá»…á»‡"
    "Ã­Ã¬á»‰Ä©á»‹"
    "Ã³Ã²á»Ãµá»á»‘á»“á»•á»—á»™á»›á»á»Ÿá»¡á»£"
    "ÃºÃ¹á»§Å©á»¥á»©á»«á»­á»¯á»±"
    "Ã½á»³á»·á»¹á»µ"
    "Ä‚Ã‚ÄÃŠÃ”Æ Æ¯"
    "ÃÃ€áº¢Ãƒáº áº®áº°áº²áº´áº¶áº¤áº¦áº¨áºªáº¬"
    "Ã‰Ãˆáººáº¼áº¸áº¾á»€á»‚á»„á»†"
    "ÃÃŒá»ˆÄ¨á»Š"
    "Ã“Ã’á»ŽÃ•á»Œá»á»’á»”á»–á»˜á»šá»œá»žá» á»¢"
    "ÃšÃ™á»¦Å¨á»¤á»¨á»ªá»¬á»®á»°"
    "Ãá»²á»¶á»¸á»´"
)

VIETNAMESE_UNACCENTED_TOKENS = {
    "anh",
    "can",
    "chon",
    "chua",
    "dang",
    "da",
    "de",
    "duoc",
    "giai",
    "giu",
    "huong",
    "kiem",
    "khong",
    "lam",
    "loi",
    "luc",
    "neu",
    "ngay",
    "nguoc",
    "nhung",
    "phan",
    "ro",
    "sau",
    "sua",
    "them",
    "thich",
    "thu",
    "tiep",
    "toi",
    "tra",
    "truoc",
    "tuong",
    "va",
    "van",
    "vi",
    "viec",
    "voi",
    "xac",
}


def validate_vietnamese_output(text: str, output_contract: dict[str, object]) -> dict[str, object]:
    language = output_contract.get("language")
    user_facing_language = output_contract.get("user_facing_language")
    orthography = output_contract.get("orthography")
    accent_policy = output_contract.get("accent_policy")

    requires_vietnamese = language == "vi" or user_facing_language == "vietnamese"
    requires_diacritics = orthography == "vietnamese-diacritics" or accent_policy == "required"
    if not requires_vietnamese and not requires_diacritics:
        return {
            "status": "PASS",
            "findings": [],
            "warnings": [],
        }

    findings: list[str] = []
    warnings: list[str] = []
    prose = strip_markdown_code(text)
    normalized_prose = normalize_text(prose)
    word_count = len(re.findall(r"[a-zA-Z]+", normalized_prose))
    has_diacritics = any(char in VIETNAMESE_DIACRITIC_CHARACTERS for char in prose)
    matched_unaccented_tokens = sorted(
        {
            token
            for token in re.findall(r"[a-z]+", normalized_prose)
            if token in VIETNAMESE_UNACCENTED_TOKENS
        }
    )

    if any(marker in prose for marker in MOJIBAKE_MARKERS):
        findings.append("Output appears mojibake; Vietnamese text must stay valid UTF-8.")

    if requires_vietnamese and not has_diacritics:
        if len(matched_unaccented_tokens) >= 2:
            findings.append(
                "Output appears to be accent-stripped Vietnamese while the contract requires full diacritics."
            )
        elif word_count >= 8:
            findings.append("Output does not appear to be Vietnamese prose even though the contract requires it.")
        else:
            warnings.append("Not enough prose to confidently validate Vietnamese orthography.")

    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "warnings": warnings,
        "matched_unaccented_tokens": matched_unaccented_tokens,
    }


def validate_tone_detail_output(text: str, output_contract: dict[str, object]) -> dict[str, object]:
    tone_detail = output_contract.get("tone_detail")
    if not isinstance(tone_detail, str) or not tone_detail.strip():
        return {
            "status": "PASS",
            "findings": [],
            "warnings": [],
        }

    normalized_tone = normalize_text(tone_detail)
    normalized_prose = normalize_text(strip_markdown_code(text))
    findings: list[str] = []
    warnings: list[str] = []

    if "goi sep" in normalized_tone and "xung em" in normalized_tone:
        if not re.search(r"\bsep\b", normalized_prose):
            findings.append("Tone detail requires addressing the user as 'S\u1ebfp'.")
        if re.search(r"\banh\b", normalized_prose):
            findings.append("Tone detail requires x\u01b0ng 'Em'; found 'anh' in the response prose.")
        if not re.search(r"\bem\b", normalized_prose):
            warnings.append("Tone detail prefers explicit self-reference as 'Em'.")

    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "warnings": warnings,
    }
