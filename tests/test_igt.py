import unittest
from src.glossing import IGT

class TestIGT(unittest.TestCase):
    def test_glosses(self):
        """Test that we can create IGT objects and access the right properties"""
        example = IGT(transcription='los gatos corren',
                      translation='the cats run',
                      glosses='DET.PL cat.PL run.3PL')
        
        self.assertEqual(example.glosses_list, ['DET', 'PL', '[SEP]', 'cat', 'PL', '[SEP]', 'run', '3PL'])