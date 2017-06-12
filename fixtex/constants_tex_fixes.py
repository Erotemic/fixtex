# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import re
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
    'ICML',
    'BMVC',
]


# Lists confkeys known to be journals
JOURNAL_LIST = [
    'IJCV'
    'TPAMI',
    'CVIU',
    'Nature Methods',
]


class Conf(object):
    def __init__(self, abbrev, full=None, patterns=[]):
        self._abbrev = abbrev
        self._full = full
        self._patterns = patterns

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


CONFERENCES = [
    Conf(None, 'Nature Methods'),
    Conf('CVPR', 'Computer Vision and Pattern Recognition', [
        regex_word('CVPR'),
        '^Computer Vision and Pattern Recognition',
        r'Computer Vision, \d* IEEE \d*th International Conference on',
        'Computer Vision, 2003. Proceedings. Ninth IEEE International Conference on',
        'Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition',
    ]),

    Conf('IJCV', 'International Journal of Computer Vision', [
        regex_word('IJCV'),
        'International Journal of Computer Vision',
    ]),

    Conf('ICCV', 'International Conference on Computer Vision', [
        regex_word('ICCV'),
        'International Conference on Computer Vision',
    ]),

    Conf('TPAMI', 'Transactions on Pattern Analysis and Machine Intelligence', [
        regex_word('TPAMI'),
        'Transactions on Pattern Analysis and Machine Intelligence',
        'Pattern Analysis and Machine Intelligence, IEEE Transactions on',
    ]),

    Conf('ECCV', 'European Conference on Computer Vision', [
        regex_word('ECCV'),
        'Computer VisionECCV',
        'European Conference on Computer Vision',
    ]),

    Conf('NIPS', 'Advances in Neural Information Processing Systems', [
        regex_word('NIPS'),
        'Advances in Neural Information Processing Systems',
    ]),

    Conf(None, 'Science', [
    ]),

    Conf(None, 'Nature', [
    ]),

    Conf('ICML', 'International Conference on Machine Learning', [
        regex_word('ICML'),
        '{International} {Conference} on {Machine} {Learning}',
    ]),

    Conf('WACV', 'Winter Applications of Computer Vision', [
        regex_word('WACV'),
    ]),

    Conf('WACVW', 'Winter Applications of Computer Vision Workshops', [
        regex_word('WACVW'),
        'Winter Applications of Computer Vision Workshops',
    ]),

    Conf('CVIU', None, []),

    Conf('ICPR', 'International Conference on Pattern Recognition', [
        regex_word('ICPR'),
    ]),

    Conf('BMVC', 'British Machine Vision Conference', [
        regex_word('BMVC'),
        'BMVC92',
    ]),

    Conf('NN', 'Transactions on Neural Networks', [
        'Transactions on Neural Networks',
        '^Neural Networks$',
    ]),

    Conf('TIP', 'Transactions on Image Processing', [
        'Transactions on Image Processing',
    ]),

    Conf('ICIP', None, []),

    Conf('BMVA', 'British Machine Vision Association', [
        'Alvey vision conference',
    ]),

    Conf('IT', 'Transactions on Information Theory', [
        'Transactions on Information Theory',
    ]),

    Conf('ACCV', None, [
        regex_word('ACCV'),
    ]),
    Conf('CoRR', None, []),
    Conf('AMIDA', None, []),

    Conf('IJCNN', 'International Joint Conference on Neural Networks', ['International Joint Conference on Neural Networks']),

    Conf('AAAI', None, []),

    Conf('JMLR', 'Journal of Machine Learning Research', [
        re.escape('J. Mach. Learn. Res.'),
    ]),

    Conf('SP', 'Transactions on Signal Processing', [
        'Transactions on Signal Processing',
    ]),

    Conf('CSUR', 'ACM Computing Surveys', ['ACM Comput. Surv.', 'ACM Computing Surveys']),

    Conf('ICASSP', 'International Conference on Acoustics, Speech and Signal Processing', [
        regex_word('ICASSP'),
    ]),

    Conf('STOC', 'ACM symposium on Theory of computing', [
        'ACM symposium on Theory of computing',
    ]),

    Conf(None, 'Pattern Recognition', [
        '^Pattern Recognition$',
    ]),

    Conf(None, 'Pattern Recognition Letters', [
        '^Pattern Recognition Letters$',
    ]),

    Conf('VISAPP', 'International Conference on Computer Vision Theory and Applications', [
        'International Conference on Computer Vision Theory and Applications',
    ]),

    Conf('ICOMIV', 'ACM International Conference on Multimedia', [
        'ACM International Conference on Multimedia',
    ]),

    Conf('CiSE', 'Computing in Science Engineering', [
        'Computing in Science Engineering',
    ]),

    Conf(None, 'Journal of Cognitive Neuroscience', []),

    Conf('IJCPR', 'International Joint Conference on Pattern Recognition', [
        'International Joint Conference on Pattern Recognition',
    ]),

    Conf(None, 'Image and Vision Computing', [
        '^Image and Vision Computing$',
    ]),

    Conf('PAA', 'Pattern Analysis and Applications', ['Pattern Analysis and Applications']),

    Conf('Siggraph', None, [
        'ACM Siggraph Computer Graphics',
    ]),

    Conf('ICLR', 'International Conference on Learning Representations', []),

    Conf(None, 'Oecologia', []),

    Conf(None, 'Machine Learning', []),

    Conf(None, 'Journal of Algorithms', []),

    Conf('PLOS ONE', 'PLOS ONE', ['PLoS ONE']),

    Conf('TOMS', 'ACM Transactions on Mathematical Software', ['ACM Transactions on Mathematical Software']),

    Conf('IJDAR', 'International Conference on Document Analysis and Recognition', ['International Conference on Document Analysis and Recognition']),

    Conf('CIVR', 'International Conference on Image and Video Retrieval', ['International Conference on Image and Video Retrieval']),

    Conf('SoCG', 'Symposium on Computational Geometry', ['Twentieth Annual Symposium on Computational Geometry']),

    Conf(None, 'Advances in the Study of Behavior', []),

    Conf('TOG', 'ACM Transactions on Graphics', [r'\bACM TOG\b']),

    Conf('PCM', None, ['Multimedia Information Processing']),

    Conf(None, 'The Computer Journal', []),

    Conf(None, 'Biometrics', []),

    Conf('BTAS', 'Biometrics: Theory, Applications and Systems', [
        r'Biometrics: Theory, Applications and Systems .*, 2013 IEEE Sixth International Conference on',
    ]),

    Conf(None, 'Python in Science', ['Python in Science']),

    Conf(None, 'INRIA Research Report', [r'Rapport de recherche RR-[0-9]*, INRIA']),

    Conf(None, 'Proceedings of the IEEE', []),

    Conf(None, 'Foundations and Trends in Computer Graphics and Vision', ['Foundations and Trends. in Computer Graphics and Vision']),

    Conf('CVGIP', 'Graphical Models and Image Processing', ['Computer Vision, Graphics, and Image Processing']),

    Conf(None, 'Foundations and Trends in Machine Learning', [u'Foundations and Trends® in Machine Learning']),

    Conf(None, 'Wiley StatsRef: Statistics Reference Online', []),

    Conf(None, 'Communications ACM', ['Commun\. ACM']),

    Conf(None, 'Biometrika', []),
    Conf(None, 'Algorithmica', []),

    Conf(None, 'Bird Study', []),

    Conf(None, 'SIAM Journal on Computing', []),
    Conf(None, 'The Journal of Machine Learning Research', []),
    Conf(None, 'Wildlife Monographs', []),
    Conf(None, 'Journal of the Institution of Electrical Engineers', ['Journal of the Institution of Electrical Engineers']),

    Conf('ICDT', 'Database Theory', ['Database Theory — ICDT’99']),

    Conf('EMMCVPR', None, [
        regex_word('EMMCVPR'),
        'Energy Minimization Methods in Computer Vision and Pattern Recognition'
    ]),
]
