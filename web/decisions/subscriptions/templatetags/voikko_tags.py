from django import template

register = template.Library()

import libvoikko

voikot = {}

# https://github.com/voikko/corevoikko/blob/master/libvoikko/doc/morphological-analysis.txt
ACCEPTABLE_WORD_CLASSES = [
    "nimisana",
    "laatusana",
    "nimi",
    "etunimi",
    "paikannimi",
    "sukunimi",
    "teonsana",
    "lyhenne",
]

@register.filter
def voikko_simplify(text, language):
    """Reduces the given text to its base forms using libvoikko.

    This allows the search engine to ignore spelling variation and
    match more things at the cost of exactness.

    """
    if language not in voikot:
        try:
            voikot[language] = libvoikko.Voikko(language)
        except (libvoikko.VoikkoException, OSError):
            # either voikko isn't installed or voikko doesn't have the
            # language we request. never try this language again
            voikot[language] = None
            return text

    v = voikot[language]

    if v is None:
        return text

    new_words = []
    for word in text.split():
        analysis = v.analyze(word)
        if analysis:
            analysis = analysis[0]
            word_class = analysis.get("CLASS", "nimisana")
            if word_class not in ACCEPTABLE_WORD_CLASSES:
                # filter uninteresting word types outright
                continue
            if "BASEFORM" in analysis:
                new_words.append(analysis["BASEFORM"])

    return u" ".join(new_words)
