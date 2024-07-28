"""Defines IGT model and convenience functions"""
from typing import Optional, List
import re 
from functools import reduce

DEFAULT_WORD_REGEX = r"(?<=\W|^)[\w?]+(?:[-=.])*[\w?]+(?=\W|$)"

class IGT:
    """A single line of IGT"""

    def __init__(self, 
                 transcription: str, 
                 segmentation: Optional[str] = None, 
                 glosses: Optional[str] = None,
                 translation: Optional[str] = None):
        self.transcription = transcription
        self.segmentation = segmentation
        self.glosses = glosses
        self.translation = translation
        self.should_segment = True

    def __repr__(self):
        return f"Trnsc:\t{self.transcription}\nSegm:\t{self.segmentation}\nGloss:\t{self.glosses}\nTrnsl:\t{self.translation}\n\n"

    @property
    def word_glosses_list(self) -> List[str]:
        """Returns a list of the glosses, split by words"""
        if self.glosses is None:
            raise ValueError("`glosses` not set on example!")
        return re.findall(DEFAULT_WORD_REGEX, self.glosses)
    
    @property
    def glosses_list(self)  -> List[str]:
        """Returns a list of the glosses, split by morphemes and including word boundaries"""
        glosses = [re.split("-", word) for word in self.word_glosses_list]
        glosses = [[gloss.replace('.', '') for gloss in word_glosses if gloss != ''] for word_glosses in
                    glosses]  # Remove empty glosses introduced by faulty segmentation
        glosses = [word_glosses for word_glosses in glosses if word_glosses != []]
        glosses = reduce(lambda a, b: a + ['[SEP]'] + b, glosses)  # Add separator for word boundaries
        return glosses

    def morphemes_list(self) -> List[str]:
        """Returns the segmented list of morphemes, if possible"""
        if self.segmentation is None:
            raise ValueError("Cannot provide morphemes for non-segmented IGT!")
        words = re.findall(DEFAULT_WORD_REGEX, self.segmentation)
        words = [word.split('-') for word in words]
        words = [[morpheme for morpheme in word if morpheme != ''] for word in words] 
        words = [word for word in words if word != []]
        morphemes = reduce(lambda a,b: a + ['[SEP]'] + b, words)
        return morphemes

    def __dict__(self):
        d = {'transcription': self.transcription, 'translation': self.translation}
        if self.glosses is not None:
            d['glosses'] = self.glosses_list
        if self.segmentation is not None:
            d['segmentation'] = self.segmentation
            d['morphemes'] = self.morphemes_list
        return d
    