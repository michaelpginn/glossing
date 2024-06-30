"""Defines IGT model and convenience functions"""
from typing import Optional, List
import re 
from functools import reduce

class IGTLine:
    """A single line of IGT"""

    def __init__(self, 
                 transcription: str, 
                 segmentation: Optional[str], 
                 glosses: Optional[str],
                 translation: Optional[str]):
        self.transcription = transcription
        self.segmentation = segmentation
        self.glosses = glosses
        self.translation = translation
        self.should_segment = True

    def __repr__(self):
        return f"Trnsc:\t{self.transcription}\nSegm:\t{self.segmentation}\nGloss:\t{self.glosses}\nTrnsl:\t{self.translation}\n\n"

    def gloss_list(self, segmented=False) -> Optional[List[str]]:
        """Returns the gloss line of the IGT as a list.
        :param segmented: If True, will return each morpheme gloss as a separate item.
        """
        if self.glosses is None:
            return []
        if not segmented:
            return self.glosses.split()
        else:
            words = re.split("\s+", self.glosses)
            glosses = [re.split("-", word) for word in words]
            glosses = [[gloss.replace('.', '') for gloss in word_glosses if gloss != ''] for word_glosses in
                       glosses]  # Remove empty glosses introduced by faulty segmentation
            glosses = [word_glosses for word_glosses in glosses if word_glosses != []]
            glosses = reduce(lambda a, b: a + ['[SEP]'] + b, glosses)  # Add separator for word boundaries
            return glosses

    def morphemes(self) -> Optional[List[str]]:
        """Returns the segmented list of morphemes, if possible"""
        if self.segmentation is None:
            return None
        return _tokenize_morpheme(self.segmentation)

    def __dict__(self):
        d = {'transcription': self.transcription, 'translation': self.translation}
        if self.glosses is not None:
            d['glosses'] = self.gloss_list(segmented=self.should_segment)
        if self.segmentation is not None:
            d['segmentation'] = self.segmentation
            d['morphemes'] = self.morphemes()
        return d
    

def _tokenize_morpheme(str: str):
    """Splits a string of morphemes by 

    Args:
        str (str): _description_

    Returns:
        _type_: _description_
    """
    word_regex = r"(?:[^.,!?;¿\s]|\?\?\?)+" # Matches any string not containing punctuation or whitespace

    words = re.findall(word_regex, str)
    words = [word.split('-') for word in words]
    words = [[morpheme for morpheme in word if morpheme != ''] for word in words]  # Remove empty morphemes introduced by faulty segmentation
    words = [word for word in words if word != []]
    morphemes = reduce(lambda a,b: a + ['[SEP]'] + b, words)
    return morphemes