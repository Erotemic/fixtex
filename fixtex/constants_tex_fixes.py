# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import re
import utool as ut
from utool.util_regex import regex_word


class Pub(ut.NiceRepr):
    """
    publication
    """
    def __init__(self, accro=None, full=None, patterns=[], type=None,
                 publisher=None, isonline=False, registered=True, places=None):
        self._accro = accro
        self._full = full
        self._patterns = patterns
        self._publisher = publisher
        self._abbrev = None
        self.isonline = isonline
        self.registered = registered
        self.places = places
        if type is None:
            type = self._infer_type(accro, full)
        if type is not None:
            if type == 'inproceedings':
                type = 'conference'
            if type == 'techreport':
                type = 'report'
            if type == 'article':
                type = 'journal'
            if type == 'mastersthesis':
                type = 'thesis'
            if type == 'phdthesis':
                type = 'thesis'
            valid_types = {
                'conference', 'journal', 'book', 'report', 'online', 'thesis',
                'incollection', 'misc', 'patent'
            }
            assert type in valid_types, type
        self.type = type

    def published_online(self):
        if self.type == 'online':
            return True
        return self.isonline

    def _infer_type(self, accro, full):
        type = None
        if accro in CONFERENCE_LIST or full in CONFERENCE_LIST:
            type = 'conference'
        elif accro in JOURNAL_LIST or full in JOURNAL_LIST:
            type = 'journal'
        else:
            if full is not None and 'journal' in full.lower():
                type = 'journal'
            if full is not None and 'conference' in full.lower():
                type = 'conference'
        return type

    def __nice__(self):
        if self.type == 'online':
            return 'online'
        return self.accro()

    def as_dict(self):
        return ut.odict([
            ('type', self.type),
            ('accro', self._accro),
            ('full', self._full),
            ('abbrev', self.abbrev()),
            ('publisher', self._publisher),
        ])

    def accro(self):
        if self._accro is None:
            return self._full
        return self._accro

    def abbrev(self):
        if self._abbrev is None:
            if self._full is not None:
                abbrev = self._full
                for s, r in IEEE_COMMON_ABBREV.items():
                    abbrev = re.sub(regex_word(s), r, abbrev)
                self._abbrev = abbrev
        return self._abbrev

    def full(self):
        if self._full is None:
            return self._accro
        return self._full

    def matches(self, title):
        if title == self._accro:
            return True
        if title == self._full:
            return True
        if title == self.abbrev():
            return True
        else:
            return any(re.search(pat, title, flags=re.IGNORECASE)
                       for pat in self._patterns)


class PubManager(object):
    """
    pubman = PubManager()
    """
    def __init__(pubman):
        pubman.pub_list = PUBLICATIONS

    def as_pandas(pubman):
        """
        for type, sub in df.groupby('type'):
            print('\nTYPE = {!r}'.format(type))
            print(sub)
        """
        import pandas as pd
        df = pd.DataFrame([pub.as_dict() for pub in pubman.pub_list])
        return df

    def types(pubman, want):
        want = set(ut.ensure_iterable(want))
        for pub in pubman.pub_list:
            if pub.type in want:
                yield pub

    def rectify(pubman, pubval):
        if pubval.startswith('arXiv'):
            pubval = 'CoRR'
        return pubval

    def find(pubman, pubval):
        candidates = pubman.findall(pubval)
        if len(candidates) == 0:
            return None
        return candidates[0]

    def findall(pubman, pubval):
        pubval = pubman.rectify(pubval)
        candidates = []
        # Check if the publication name matches any standard patterns
        for pub in pubman.pub_list:
            if pub.matches(pubval):
                candidates.append(pub)
        return candidates

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


# https://www.ieee.org/documents/style_manual.pdf
IEEE_COMMON_ABBREV = dict([
    ('Systems', 'Syst.'), ('Digest', 'Dig.'), ('Record', 'Rec.'),
    ('Conference', 'Conf.'), ('Technical', 'Tech.'), ('Nuclear', 'Nucl.'),
    ('Convention', 'Conv.'), ('Engineering', 'Eng.'), ('Congress', 'Congr.'),
    ('Chinese', 'Chin.'), ('Magazine', 'Mag.'), ('Electronic', 'Electron.'),
    ('Statistics', 'Statist.'), ('International', 'Int.'), ('Review', 'Rev.'),
    ('Magnetics', 'Magn.'), ('Journal', 'J.'), ('Association', 'Assoc.'),
    ('Department', 'Dept.'), ('Royal', 'Roy.'), ('Working', 'Work.'),
    ('Science', 'Sci.'), ('Optical', 'Opt.'), ('National', 'Nat.'),
    ('Transactions', 'Trans.'), ('Correspondence', 'Corresp.'),
    ('Electric', 'Elect.'), ('Technology', 'Technol.'),
    ('Quarterly', 'Quart.'), ('Letter', 'Lett.'),
    ('Institute', 'Inst.'), ('Ergonomics', 'Ergonom.'),
    ('Administration', 'Admin.'),
    ('Apparatus', 'App.'), ('Occupation', 'Occupat.'), ('Symposium', 'Symp.'),
    ('Processing', 'Process.'), ('Sociological', 'Sociol.'),
    ('Productivity', 'Productiv.'),
    ('Annual', 'Annu.'), ('Optics', 'Opt.'), ('Development', 'Develop.'),
    ('Automatic', 'Automat.'), ('Computer', 'Comput.'), ('Express', 'Express'),
    ('Economics', 'Econ.'), ('British', 'Brit.'), ('Japan', 'Jpn.'),
    ('Geoscience', 'Geosci.'), ('Philosophical', 'Philosoph.'),
    ('Research', 'Res.'), ('Vehicular', 'Veh.'),
    ('Administrative', 'Administ.'), ('Intelligence', 'Intell.'),
    ('Annals', 'Ann.'), ('Graphics', 'Graph.'), ('Newsletter', 'Newslett.'),
    ('Operational', 'Oper.'), ('Communications', 'Commun.'),
    ('Economic', 'Econ.'), ('Electrical', 'Elect.'), ('Computers', 'Comput.'),
    ('Supplement', 'Suppl.'), ('Meeting', 'Meeting'),
    ('Cybernetics', 'Cybern.'), ('Analysis', 'Anal.'),
    ('Organization', 'Org.'), ('Managing', 'Manag.'),
    ('Applied', 'Appl.'), ('Reliability', 'Rel.'), ('Design', 'Des.'),
    ('Society', 'Soc.'), ('Acoustics', 'Acoust.'), ('Applications', 'Appl.'),
    ('European', 'Eur.'), ('Studies', 'Stud.'), ('Mathematical', 'Math.'),
    ('Production', 'Prod.'), ('Proceedings', 'Proc.'), ('American', 'Amer.'),
    ('Foundation', 'Found.'), ('Report', 'Rep.'), ('Machine', 'Mach.'),
    ('Telecommunications', 'Telecommun.'), ('Education', 'Edu.'),
    ('Management', 'Manage.'), ('Mechanical', 'Mech.'), ('Business', 'Bus.'),
    ('Techniques', 'Techn.'), ('Letters', 'Lett.'), ('Canadian', 'Can.'),
    ('Electronics', 'Electron.'), ('Evolutionary', 'Evol.'),
    ('Industrial', 'Ind.'), ('Information', 'Inform.'), ('Selected', 'Select.'),
    ('Broadcasting', 'Broadcast.')
])


def parse_abbrev():
    ref_text = 'Acoustics Acoust.\nAdministration Admin.\nAdministrative Administ.\nAmerican Amer.\nAnalysis Anal.\nAnnals Ann.\nAnnual Annu.\nApparatus App.\nApplications Appl.\nApplied Appl.\nAssociation Assoc.\nAutomatic Automat.\nBritish Brit.\nBroadcasting Broadcast.\nBusiness Bus.\nCanadian Can.\nChinese Chin.\nCommunications Commun.\nComputer(s) Comput.\nConference Conf.\nCongress Congr.\nConvention Conv.\nCorrespondence Corresp.\nCybernetics Cybern.\nDepartment Dept.\nDesign Des.\nDevelopment Develop.\nDigest Dig.\nEconomic(s) Econ.\nEducation Edu.\nElectric Elect.\nElectrical Elect.\nElectronic Electron.\nElectronics Electron.\nEngineering Eng.\nErgonomics Ergonom.\nEuropean Eur.\nEvolutionary Evol.\nExpress Express\nFoundation Found.\nGeoscience Geosci.\nGraphics Graph.\nIndustrial Ind.\nInformation Inform.\nInstitute Inst.\nIntelligence Intell.\nInternational Int.\nJapan Jpn.\nJournal J.\nLetter(s) Lett.\nMachine Mach.\nMagazine Mag.\nMagnetics Magn.\nManagement Manage.\nManaging Manag.\nMathematical Math.\nMechanical Mech.\nMeeting Meeting\nNational Nat.\nNewsletter Newslett.\nNuclear Nucl.\nOccupation Occupat.\nOperational Oper.\nOptical Opt.\nOptics Opt.\nOrganization Org.\nPhilosophical Philosoph.\nProceedings Proc.\nProcessing Process.\nProduction Prod.\nProductivity Productiv.\nQuarterly Quart.\nRecord Rec.\nReliability Rel.\nReport Rep.\nResearch Res.\nReview Rev.\nRoyal Roy.\nScience Sci.\nSelected Select.\nSociety Soc.\nSociological Sociol.\nStatistics Statist.\nStudies Stud.\nSupplement Suppl.\nSymposium Symp.\nSystems Syst.\nTechnical Tech.\nTechniques Techn.\nTechnology Technol.\nTelecommunications Telecommun.\nTransactions Trans.\nVehicular Veh.\nWorking Work.'
    abbrev_map = {}
    for line in ref_text.split('\n'):
        full, accro = line.split(' ')
        if full.endswith('(s)'):
            full_single = full[:-3]
            abbrev_map[full_single] = accro
            abbrev_map[full_single + 's'] = accro
        else:
            abbrev_map[full] = accro
    ut.odict(abbrev_map)

PUBLICATIONS = []

CONFERENCES = [
    Pub('CVPR', 'Computer Vision and Pattern Recognition', [
        regex_word('CVPR'),
        '^Computer Vision and Pattern Recognition',
        r'Computer Vision, \d* IEEE \d*th International Conference on',
        'Computer Vision, 2003. Proceedings. Ninth IEEE International Conference on',
        'Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition',
        'Proceedings of the {IEEE} Conference on Computer Vision and Pattern Recognition',
        'IEEE Conference on Computer Vision and Pattern Recognition',
    ], places={
        2017: 'Honolulu, HI',
        2016: 'Las Vegas, NV',
        2015: 'Boston, MA',
        2014: 'Columbus, OH',
        2013: 'Portland, OR',
        2012: 'Providence, RI',
        2011: 'Colorado Springs, CO',
        2010: 'San Francisco, CA',
        2009: 'Miami, FL',
        2008: 'Anchorage, AL',
        2007: 'Minneapolis, MN',
        2006: 'New York City, NY',
        2005: 'San Diego, CA',
        2004: 'Washington, D.C.',
        2003: 'Madison, WI',
        2001: 'Kauai, HI',
        2000: 'Hilton Head, SC',
        1999: 'Fort Collins, CO',
        1998: 'Santa Barbara, CA',
        1997: 'San Juan, PR',
    },
    ),

    Pub('ICCV', 'International Conference on Computer Vision', [
        regex_word('ICCV'),
        'International Conference on Computer Vision$',
    ], places={
        2019: 'Seoul, Korea',
        2017: 'Venice, Italy',
        2015: 'Santiago, Chile',
        2013: 'Sydney, Australia',
        2011: 'Barcelona, Spain',
        2009: 'Kyoto, Japan',
        2007: 'Rio de Janeiro, Brazil',
        2005: 'Beijing, PRC',
        2003: 'Nice, France ',
        2001: 'Vancouver, British Columbia, Canada',
        1999: 'Corfu, Greece ',
        1998: 'Mumbai, India ',
        1995: 'Boston, Massachusetts, USA',
        1993: 'Berlin, Germany',
        1990: 'Osaka, Japan',
        1988: 'Tampa, Florida, USA',
        1987: 'London, Great Britain',
    }),

    Pub('ECCV', 'European Conference on Computer Vision', [
        regex_word('ECCV'),
        'Computer VisionECCV',
        'European Conference on Computer Vision',
    ], type='conference', places={
        2018: 'Munich, Germany',
        2016: 'Amsterdam, The Netherlands',
        2014: 'Zürich, Switzerland',
        2012: 'Florence, Italy',
        2010: 'Crete, Greece',
        2008: 'Marseille, France',
        2006: 'Graz, Austria',
        2004: 'Prague, Czech Republic',
        2002: 'Copenhagen, Denmark',
        2000: 'Dublin, Ireland',
        1998: 'Freiburg, Germany',
        1996: 'Cambridge, UK',
        1994: 'Stockholm, Sweden',
        1992: 'Santa Margherita Ligure, Italy',
        1990: 'Antibes, France',
    },),

    Pub('NIPS', 'Advances in Neural Information Processing Systems', [
        regex_word('NIPS'),
        'Advances in Neural Information Processing Systems',
    ], type='conference', places={
        1999: 'Denver, Colorado, United States',
        2000: 'Denver, Colorado, United States',
        2001: 'Vancouver, British Columbia, Canada',
        2009: 'Vancouver, British Columbia, Canada',
        2010: 'Vancouver, British Columbia, Canada',
        2011: 'Granada, Spain, EU',
        2012: 'South Lake Tahoe, Nevada, United States',
        2013: 'South Lake Tahoe, Nevada, United States',
        2014: 'Montréal, Quebec, Canada',
        2015: 'Montréal, Quebec, Canada',
    }),

    Pub('ICML', 'International Conference on Machine Learning', [
        regex_word('ICML'),
        '{International} {Conference} on {Machine} {Learning}',
    ], places={
        2014: 'Beijing, China',
        2013: 'Atlanta, United States',
        2012: 'Edinburgh, Great Britain',
        2011: 'Bellevue, United States',
        2010: 'Haifa, Israel',
    }),

    Pub('BMVC', 'British Machine Vision Conference', [
        regex_word('BMVC'),
        regex_word('BMVA'),
        'British Machine Vision Association',
        'BMVC92',
    ], type='conference', places={
        2012: 'Guildford, UK',
        2008: 'Leeds, UK',
        1992: 'Leeds, UK',
        1990: 'Oxford, UK',
    }),

    Pub('AVC', 'Alvey Vision Conference', [
        'Alvey vision conference',
    ], type='conference', places={
        1989: 'Reading, UK',
        1988: 'Manchester, UK',
        1987: 'Cambridge, UK',
    }),

    Pub('SoCG', 'Symposium on Computational Geometry', ['Twentieth Annual Symposium on Computational Geometry'], type='conference', places={
        2004: 'New York, NY, USA'
    }),

    Pub('ICMR', 'ACM International Conference on Multimedia Retrieval', [
        'International conference on multimedia retrieval',
    ], type='conference', places={
        2013: 'Dallas, TX, USA',
    }),

    Pub('ICONIP', 'International Conference on Neural Information Processing', [
        regex_word('ICONIP'),
        'International Conference on Neural Information Processing',
    ], places={
        2013: 'Daegu, Korea'
    }),

    Pub('ACMMM', 'ACM International Conference on Multimedia', [
        'ACM International Conference on Multimedia$',
    ], places={
        2013: 'Barcelona, Catalunya, Spain',
    }),

    Pub('IJCPR', 'International Joint Conference on Pattern Recognition', [
        'International Joint Conference on Pattern Recognition',
    ], places={
        1978: 'Kyoto, Japan'
    }),

    Pub('WACVW', 'Winter Applications of Computer Vision Workshops', [
        regex_word('WACVW'),
        'Winter Applications of Computer Vision Workshops',
    ], type='conference', places={
        2013: 'Clearwater Beach, FL, USA',
        2016: 'Lake Placid, NY, USA',
    }),

    Pub('WACV', 'Winter Applications of Computer Vision', [
        regex_word('WACV'),
    ], type='conference', places={
        2013: 'Clearwater Beach, FL, USA',
        2016: 'Lake Placid, NY, USA',
    }),

    Pub('ICDAR', 'International Conference on Document Analysis and Recognition',
        places={
            2003: 'Edinburgh, Scotland',
        }),

    Pub('VISAPP', 'International Conference on Computer Vision Theory and Applications', [
        'International Conference on Computer Vision Theory and Applications',
    ], places={
        2009: 'Lisboa, Portugal',
    }),

    Pub('AIStats', 'International Conference on Artificial Intelligence and Statistics',
        places={
            2005: 'Bridgetown, Barbados',
        }),

    Pub('ICASSP', 'International Conference on Acoustics, Speech and Signal Processing',
        type='conference', publisher='IEEE',
        places={
            2013: 'Vancouver, BC, Canada',
        }),

    Pub('STOC', 'ACM symposium on Theory of computing', [
        'ACM symposium on Theory of computing',
    ], type='conference', publisher='ACM', places={
        2002: 'Montréal, Québec, Canada',
    }),

    Pub('ICIP', 'International Conference on Image Processing', [], type='conference'),

    Pub('ICPR', 'International Conference on Pattern Recognition', type='conference', places={
        2012: 'Tsukuba Science City, Japan',
    }),

    Pub('ICLR', 'International Conference on Learning Representations', type='conference',
        places={
            2015: 'San Diego, California, USA',
        }),

    Pub('BTAS', 'Biometrics: Theory, Applications and Systems', [
        r'Biometrics: Theory, Applications and Systems .*, 2013 IEEE Sixth International Conference on',
    ], publisher='IEEE', type='conference', places={
        2013: 'Washington DC, USA'
    }),

    Pub('GCPR', 'German Conference on Pattern Recognition', [regex_word('DGAM')], type='conference', places={
        2003: 'Magdeburg, Germany',
    }),

    Pub('IJCNN', 'International Joint Conference on Neural Networks',
        type='conference', places={
            1992: 'Beijing, China',
        }),

    Pub('ACCV', 'Asian Conference on Computer Vision', type='conference',
        places={
            2014: 'Singapore',
            2016: 'Taiwan',
        }),

    Pub('ICOMIV', 'ACM International Conference on Multimedia, Internet, and Video Technologies',),

    Pub('CIVR', 'International Conference on Image and Video Retrieval', places={
        2009: 'Santorini, Fira, Greece',
    }),
]
PUBLICATIONS += CONFERENCES


ONLINE_JOURNALS = [
    Pub('CoRR', 'Computing Research Repository', [], isonline=True),
    Pub('PLOS ONE', 'PLOS ONE', ['PLoS ONE'], type='journal', isonline=True),
]
PUBLICATIONS += ONLINE_JOURNALS


PUBLICATIONS += [
    Pub(None, 'Nature Methods', type='journal'),

    Pub('IJCV', 'International Journal of Computer Vision', [
        regex_word('IJCV'),
        'International Journal of Computer Vision',
    ]),

    Pub('JMLT', 'Journal of Machine Learning Technologies', []),

    Pub('TPAMI', 'IEEE Transactions on Pattern Analysis and Machine Intelligence', [
        regex_word('TPAMI'),
        'Transactions on Pattern Analysis and Machine Intelligence',
        'Pattern Analysis and Machine Intelligence, IEEE Transactions on',
    ], type='journal'),

    Pub('Science', 'Science', [], type='journal'),

    Pub('Nature', 'Nature', [], type='journal'),

    Pub('CVIU', 'Computer Vision and Image Understanding', [], type='journal'),

    Pub('TNN', 'IEEE Transactions on Neural Networks', [
        'Transactions on Neural Networks',
        '^Neural Networks$',
    ], type='journal', publisher='IEEE'),

    Pub('TIP', 'IEEE Transactions on Image Processing', [
        'Transactions on Image Processing',
    ], type='journal', publisher='IEEE'),

    Pub('IT', 'IEEE Transactions on Information Theory', [
        'Transactions on Information Theory',
    ], type='journal', publisher='IEEE'),

    Pub('AMIDA', None, []),

    Pub('AAAI', 'Association for the Advancement of Artificial Intelligence', []),

    Pub('JMLR', 'Journal of Machine Learning Research', [
        re.escape('J. Mach. Learn. Res.'),
        'The Journal of Machine Learning Research',
    ]),

    Pub('SP', 'IEEE Transactions on Signal Processing', [
        'Transactions on Signal Processing',
    ], type='journal', publisher='IEEE'),

    Pub('CSUR', 'ACM Computing Surveys', ['ACM Comput. Surv.', 'ACM Computing Surveys'], type='journal'),

    Pub(None, 'Pattern Recognition', [
        '^Pattern Recognition$',
    ], type='journal'),

    Pub(None, 'Pattern Recognition Letters', [
        '^Pattern Recognition Letters$',
    ], type='journal'),

    Pub('CiSE', 'Computing in Science Engineering', [
        'Computing in Science Engineering',
    ]),

    Pub(None, 'Journal of Cognitive Neuroscience', []),

    Pub(None, 'Image and Vision Computing', [
        '^Image and Vision Computing$',
    ], type='journal'),

    Pub('PAA', 'Pattern Analysis and Applications', ['Pattern Analysis and Applications'], type='journal', publisher='Springer'),

    Pub('Siggraph', None, [
        'ACM Siggraph Computer Graphics',
    ]),

    Pub(None, 'Oecologia', [], type='journal', publisher='Springer'),

    Pub(None, 'Machine Learning', [], type='journal'),

    Pub(None, 'Journal of Algorithms', []),

    Pub('TOMS', 'ACM Transactions on Mathematical Software', ['ACM Transactions on Mathematical Software'], type='journal'),

    Pub('TOG', 'ACM Transactions on Graphics', [r'\bACM TOG\b'], type='journal'),

    Pub('PCM', None, ['Multimedia Information Processing']),

    Pub('Comput. J.', 'The Computer Journal', []),

    Pub(None, 'Biometrics', [], type='journal', publisher='Wiley'),

    Pub(None, 'Python in Science', ['Python in Science']),

    Pub(None, 'INRIA Research Report', [r'Rapport de recherche RR-[0-9]*, INRIA'], type='report'),

    Pub('Proc. IEEE', 'Proceedings of the IEEE', [], type='journal'),

    Pub(None, 'Foundations and Trends in Computer Graphics and Vision',
        ['Foundations and Trends. in Computer Graphics and Vision'],
        type='journal', publisher='World Scientific Publishing Co'),

    Pub('CVGIP', 'Graphical Models and Image Processing', ['Computer Vision, Graphics, and Image Processing'], type='journal'),

    Pub(None, 'Foundations and Trends in Machine Learning', [u'Foundations and Trends® in Machine Learning']),

    Pub(None, 'Wiley StatsRef: Statistics Reference Online', []),

    Pub(None, 'Communications ACM', ['Commun\. ACM'], type='journal'),

    Pub('JACM', 'Journal of the ACM', []),


    Pub(None, 'Biometrika', [], type='journal', publisher='Oxford University Press'),
    Pub(None, 'Algorithmica', [], type='journal', publisher='Springer'),

    Pub(None, 'Bird Study', [], type='journal'),

    Pub(None, 'SIAM Journal on Computing', []),
    Pub(None, 'Wildlife Monographs', [], type='journal'),
    Pub('JIEE', 'Journal of the Institution of Electrical Engineers', ['Journal of the Institution of Electrical Engineers']),

    Pub('ICDT', 'Database Theory', ['Database Theory — ICDT’99']),

    Pub('EMMCVPR', 'Energy Minimization Methods in Computer Vision and Pattern Recognition', [
        regex_word('EMMCVPR'),
        'Energy Minimization Methods in Computer Vision and Pattern Recognition'
    ]),

    Pub(None, 'Program MARK - A Gentle Introduction', type='incollection', isonline=True),

    Pub(None, 'Advances in the Study of Behavior', [], type='incollection'),

    Pub(None, 'Behavioral Ecology and Conservation Policy', [], type='incollection'),
]

PUBLICATIONS += [
    Pub(None, 'Kenya Wildlife Service'),
    Pub(None, 'Department of Computer Science, Rensselaer Polytechnic Institute'),
    Pub(None, 'Department of Electrical Engineering and Computer Science, University of Liège'),
    Pub(None, 'University of Massachusetts'),
    Pub(None, 'INRIA'),
    Pub(None, 'Department of Computer Science, University of Illinois at Chicago'),
    Pub(None, 'Dalle Molle Institute for Artificial Intelligence'),


]


def _test():
    """
    from fixtex.constants_tex_fixes import *
    """
    from fixtex.ieee_trans_journal_names import full_to_short
    for pub in PUBLICATIONS:
        if not pub.full().istitle():
            print(pub.full())

        print(pub.abbrev())
        full = pub.full()
        if full in full_to_short:
            short = full_to_short[full]
            assert pub.accro() == short
            print('pub.full = {!r}'.format(pub.full))
