"""Devanagari text hygiene: normalisation, PDF-artefact repair, sentence splitting."""
import re
import unicodedata

_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"), None)
_DEV = r"\u0900-\u097F"
_ARTEFACT_PAIRS = [
    ("इं जी", "इंजी"), ("इं ज", "इंज"), ("इं स्ट", "इंस्ट"), ("इं दिरा", "इंदिरा"),
    ("रिं ग", "रिंग"), ("कु छ", "कुछ"), ("कु रान", "कुरान"), ("किं तु", "किंतु"),
    ("अक्टू बर", "अक्टूबर"), ("हिं दी", "हिंदी"), ("हिं दु", "हिंदु"), ("हिं दू", "हिंदू"),
    ("कें द्र", "केंद्र"), ("कें डरी", "केंडरी"), ("चिं तन", "चिंतन"), ("फें के", "फेंके"),
    ("रॉके ट", "रॉकेट"), ("कै से", "कैसे"), ("सके ?", "सके?"), ("स्कू ", "स्कू"),
    ("दू र", "दूर"), ("दू स", "दूस"), ("के वल", "केवल"), ("ऊँ च", "ऊँच"),
    ("इं ड् स", "इंड्स"),
]
_AFTER_RI = re.compile(r"ृ (?=[\u0915-\u0939])")
_SPLIT_YON = re.compile(r"ि यों")
_LONE_TA = re.compile(rf"(?<=[\u0915-\u0939]ि) त(?![{_DEV}])")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(_INVISIBLE)
    text = text.replace("\u00a0", " ").replace("\f", "\n").replace("\r", "\n")
    text = _AFTER_RI.sub("ृ", text)
    text = _LONE_TA.sub("त", text)
    text = _SPLIT_YON.sub("ियों", text)
    for bad, good in _ARTEFACT_PAIRS:
        text = text.replace(bad, good)
    return text


def clean_inline(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

_SENTENCE = re.compile(r"[^।?!]+[।?!]+[\"”’)]*|[^।?!]+$")


def split_sentences(text: str) -> list[str]:

    text = clean_inline(text)
    return [s.strip() for s in _SENTENCE.findall(text) if s.strip()]
