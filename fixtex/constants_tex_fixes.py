# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import re
import utool as ut
from utool.util_regex import regex_word

COMMON_ERRORS = [
    ('spacial', 'spatial',),
    ('image net', 'Image Net',),
    ('hand crafted', 'hand-crafted',),
]


ACRONYMN_LIST = [
    ('Scale Invariant Feature Transform', 'SIFT'),
    ('Selective Match Kernel', 'SMK'),
    ('bag of words', 'BoW'),
    ('Fisher Vector', 'FV'),
    ('Vector of Locally Aggregated Descriptors', 'VLAD'),
    ('Gaussian mixture model', 'GMM'),
    ('Hamming embedding', 'HE'),
    (r'Local \Naive Bayes Nearest Neighbor', 'LNBNN'),
    (r'\naive Bayes nearest Neighbor', 'LNBNN'),
    ('Fast Library for Approximate Nearest Neighbors', 'FLANN'),

    ('Leaky Rectified Linear Unit', 'LRLU'),
    ('Rectified Linear Unit', 'RLU'),
]


CAPITAL_LIST = [
    'Great Zebra Count',
    'Great Zebra and Giraffe Count',
    'Gauss',
    'Hessian',
    'Poisson',
    'Hamming',
    #'TF-IDF',
    'Bayes',
    'Fisher',
    'Lincoln-Petersen',
]

CAPITAL_TITLE_LIST = CAPITAL_LIST[:]


# for full, acro in ACRONYMN_LIST:
#     capfull = full[0].upper() + full[1:]
#     CAPITAL_TITLE_LIST.append(capfull)


AUTHOR_NAME_MAPS = {
    #u'Perdòch': ['Perdoch', u'Perd\'och'],
    #u'Perd\'och': ['Perdoch', u'Perd\'och'],
    #u'Perd\\mkern-6mu\'och': ['Perdoch', u'Perd\'och'],
    u'Perdoch': ['Perdoch', u'Perd\'och'],
    u'Jégou': [u'Jegou'],
    u'Hervé': [u'Herve'],
    u'Ondřej': [u'Ondrej'],
    u'Jörg': [u'Jorg'],
    u'Schnörr': [u'Schnörr'],
    u'Jiří': ['Jiri'],
    u'Mikulík': ['Mikulik']

    #'Frédéric'
    #'Léon'
    #Sánchez
    # Türetken
    #Ladický
    #Tomás
    #Jiří
}


# Lists confkeys known to be conferences
CONFERENCE_LIST = [
    'ECCV',
    'CVPR',
    'EMMCVPR',
    'NIPS',
    'ICDT',
    'ICCV',
    'WACV',
    'ICML',
    'BMVC',
]


# Lists confkeys known to be journals
JOURNAL_LIST = [
    'IJCV'
    'TPAMI',
    'CVIU',
    'CoRR',
    'Machine Learning',
    'Pattern Recognition Letters',
    'Pattern Recognition',
    'Nature Methods',
]


class Pub(ut.NiceRepr):
    """
    publication
    """
    def __init__(self, abbrev, full=None, patterns=[], type=None, publisher=None):
        self._abbrev = abbrev
        self._full = full
        self._patterns = patterns
        self._publisher = publisher
        if type is None:
            if abbrev in CONFERENCE_LIST:
                type = 'conference'
            elif abbrev in JOURNAL_LIST:
                type = 'journal'
            else:
                if full is not None and 'journal' in full.lower():
                    type = 'journal'
                if full is not None and 'conference' in full.lower():
                    type = 'conference'

        if type is not None:
            assert type in {'conference', 'journal', 'book', 'report'}, type
        self.type = type

    def __nice__(self):
        return self.abbrev()

    def abbrev(self):
        if self._abbrev is None:
            return self._full
        return self._abbrev

    def full(self):
        if self._full is None:
            return self._abbrev
        return self._full

    def matches(self, title):
        if title == self._abbrev:
            return True
        if title == self._full:
            return True
        else:
            return any(re.search(pat, title, flags=re.IGNORECASE)
                       for pat in self._patterns)


PUBLICATIONS = [
    Pub(None, 'Nature Methods'),
    Pub('CVPR', 'Computer Vision and Pattern Recognition', [
        regex_word('CVPR'),
        '^Computer Vision and Pattern Recognition',
        r'Computer Vision, \d* IEEE \d*th International Conference on',
        'Computer Vision, 2003. Proceedings. Ninth IEEE International Conference on',
        'Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition',
        'Proceedings of the {IEEE} Conference on Computer Vision and Pattern Recognition',
        'IEEE Conference on Computer Vision and Pattern Recognition',
    ]),

    Pub('IJCV', 'International Journal of Computer Vision', [
        regex_word('IJCV'),
        'International Journal of Computer Vision',
    ]),

    Pub('JMLT', 'Journal of Machine Learning Technologies', []),

    Pub('ICCV', 'International Conference on Computer Vision', [
        regex_word('ICCV'),
        'International Conference on Computer Vision$',
    ]),

    Pub('TPAMI', 'IEEE Transactions on Pattern Analysis and Machine Intelligence', [
        regex_word('TPAMI'),
        'Transactions on Pattern Analysis and Machine Intelligence',
        'Pattern Analysis and Machine Intelligence, IEEE Transactions on',
    ], type='journal'),

    Pub('ECCV', 'European Conference on Computer Vision', [
        regex_word('ECCV'),
        'Computer VisionECCV',
        'European Conference on Computer Vision',
    ]),

    Pub('NIPS', 'Advances in Neural Information Processing Systems', [
        regex_word('NIPS'),
        'Advances in Neural Information Processing Systems',
    ]),

    Pub('ICONIP', 'International Conference on Neural Information Processing', [
        regex_word('ICONIP'),
        'International Conference on Neural Information Processing',
    ]),

    Pub('Science', 'Science', [], type='journal'),

    Pub('Nature', 'Nature', [], type='journal'),

    Pub('ICML', 'International Conference on Machine Learning', [
        regex_word('ICML'),
        '{International} {Conference} on {Machine} {Learning}',
    ]),

    Pub('WACV', 'Winter Applications of Computer Vision', [
        regex_word('WACV'),
    ]),

    Pub('WACVW', 'Winter Applications of Computer Vision Workshops', [
        regex_word('WACVW'),
        'Winter Applications of Computer Vision Workshops',
    ], type='conference'),

    Pub('CVIU', 'Computer Vision and Image Understanding', [], type='journal'),

    Pub('ICPR', 'International Conference on Pattern Recognition', [regex_word('ICPR')], type='conference'),

    Pub('BMVC', 'British Machine Vision Conference', [
        regex_word('BMVC'),
        'BMVC92',
    ], type='conference'),

    Pub('TNN', 'IEEE Transactions on Neural Networks', [
        'Transactions on Neural Networks',
        '^Neural Networks$',
    ], type='journal', publisher='IEEE'),

    Pub('TIP', 'IEEE Transactions on Image Processing', [
        'Transactions on Image Processing',
    ], type='journal', publisher='IEEE'),

    Pub('ICIP', 'International Conference on Image Processing', [], type='conference'),

    Pub('BMVA', 'British Machine Vision Association', [
        'Alvey vision conference',
    ], type='conference'),

    Pub('IT', 'IEEE Transactions on Information Theory', [
        'Transactions on Information Theory',
    ], type='journal', publisher='IEEE'),

    Pub('ACCV', 'Asian Conference on Computer Vision', [
        'Asian Conference on Computer Vision',
        regex_word('ACCV'),
    ]),
    Pub('CoRR', 'Computing Research Repository', []),
    Pub('AMIDA', None, []),

    Pub('IJCNN', 'International Joint Conference on Neural Networks', ['International Joint Conference on Neural Networks']),

    Pub('AAAI', 'Association for the Advancement of Artificial Intelligence', []),

    Pub('JMLR', 'Journal of Machine Learning Research', [
        re.escape('J. Mach. Learn. Res.'),
        'The Journal of Machine Learning Research',
    ]),

    Pub('SP', 'IEEE Transactions on Signal Processing', [
        'Transactions on Signal Processing',
    ], type='journal', publisher='IEEE'),

    Pub('CSUR', 'ACM Computing Surveys', ['ACM Comput. Surv.', 'ACM Computing Surveys'], type='journal'),

    Pub('ICASSP', 'International Conference on Acoustics, Speech and Signal Processing', [
        regex_word('ICASSP'),
    ], type='conference', publisher='IEEE',),

    Pub('STOC', 'ACM symposium on Theory of computing', [
        'ACM symposium on Theory of computing',
    ], type='conference', publisher='ACM'),

    Pub(None, 'Pattern Recognition', [
        '^Pattern Recognition$',
    ], type='journal'),

    Pub(None, 'Pattern Recognition Letters', [
        '^Pattern Recognition Letters$',
    ], type='journal'),

    Pub('VISAPP', 'International Conference on Computer Vision Theory and Applications', [
        'International Conference on Computer Vision Theory and Applications',
    ]),

    Pub('ICOMIV', 'ACM International Conference on Multimedia, Internet, and Video Technologies', [
        'ACM International Conference on Multimedia, Internet, and Video Technologies',
    ]),

    Pub('ICMR', 'ACM International Conference on Multimedia Retrieval', [
        'International conference on multimedia retrieval',
    ]),

    Pub('ACMMM', 'ACM International Conference on Multimedia', [
        'ACM International Conference on Multimedia$',
    ]),

    Pub('CiSE', 'Computing in Science Engineering', [
        'Computing in Science Engineering',
    ]),

    Pub(None, 'Journal of Cognitive Neuroscience', []),

    Pub('IJCPR', 'International Joint Conference on Pattern Recognition', [
        'International Joint Conference on Pattern Recognition',
    ]),

    Pub(None, 'Image and Vision Computing', [
        '^Image and Vision Computing$',
    ], type='journal'),

    Pub('PAA', 'Pattern Analysis and Applications', ['Pattern Analysis and Applications'], type='journal', publisher='Springer'),

    Pub('Siggraph', None, [
        'ACM Siggraph Computer Graphics',
    ]),

    Pub('ICLR', 'International Conference on Learning Representations', type='conference'),

    Pub(None, 'Oecologia', [], type='journal', publisher='Springer'),

    Pub(None, 'Machine Learning', [], type='journal'),

    Pub(None, 'Journal of Algorithms', []),

    Pub('PLOS ONE', 'PLOS ONE', ['PLoS ONE'], type='journal'),

    Pub('TOMS', 'ACM Transactions on Mathematical Software', ['ACM Transactions on Mathematical Software'], type='journal'),

    Pub('IJDAR', 'International Conference on Document Analysis and Recognition', ['International Conference on Document Analysis and Recognition']),

    Pub('CIVR', 'International Conference on Image and Video Retrieval', ['International Conference on Image and Video Retrieval']),

    Pub('SoCG', 'Symposium on Computational Geometry', ['Twentieth Annual Symposium on Computational Geometry'], type='conference'),

    Pub(None, 'Advances in the Study of Behavior', [], type='book'),

    Pub('TOG', 'ACM Transactions on Graphics', [r'\bACM TOG\b'], type='journal'),

    Pub('PCM', None, ['Multimedia Information Processing']),

    Pub('Comput. J.', 'The Computer Journal', []),

    Pub(None, 'Biometrics', [], type='journal', publisher='Wiley'),

    Pub('BTAS', 'Biometrics: Theory, Applications and Systems', [
        r'Biometrics: Theory, Applications and Systems .*, 2013 IEEE Sixth International Conference on',
    ], publisher='IEEE', type='conference'),

    Pub(None, 'Python in Science', ['Python in Science']),

    Pub(None, 'INRIA Research Report', [r'Rapport de recherche RR-[0-9]*, INRIA'], type='report'),

    Pub(None, 'Proceedings of the IEEE', []),

    Pub('GCPR', 'German Conference on Pattern Recognition ', [regex_word('DGAM')], type='conference'),

    Pub(None, 'Foundations and Trends in Computer Graphics and Vision',
        ['Foundations and Trends. in Computer Graphics and Vision'],
        type='journal', publisher='World Scientific Publishing Co'),

    Pub('CVGIP', 'Graphical Models and Image Processing', ['Computer Vision, Graphics, and Image Processing'], type='journal'),

    Pub(None, 'Foundations and Trends in Machine Learning', [u'Foundations and Trends® in Machine Learning']),

    Pub(None, 'Wiley StatsRef: Statistics Reference Online', []),

    Pub(None, 'Communications ACM', ['Commun\. ACM'], type='journal'),

    Pub('JACM', 'Journal of the ACM', []),

    Pub(None, 'Behavioral ecology and conservation policy', [], type='book'),

    Pub(None, 'Biometrika', [], type='journal', publisher='Oxford University Press'),
    Pub(None, 'Algorithmica', [], type='journal', publisher='Springer'),

    Pub(None, 'Bird Study', [], type='journal'),

    Pub('AIStats', 'International Conference on Artificial Intelligence and Statistics', []),

    Pub(None, 'SIAM Journal on Computing', []),
    Pub(None, 'Wildlife Monographs', [], type='journal'),
    Pub(None, 'Journal of the Institution of Electrical Engineers', ['Journal of the Institution of Electrical Engineers']),

    Pub('ICDT', 'Database Theory', ['Database Theory — ICDT’99']),

    Pub('EMMCVPR', None, [
        regex_word('EMMCVPR'),
        'Energy Minimization Methods in Computer Vision and Pattern Recognition'
    ]),
]
