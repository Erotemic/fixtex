#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
References:

    pip install pygnotero
    pip install git+https://github.com/smathot/Gnotero.git

    pip install mozrepl
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import re
import utool as ut
import six
import bibtexparser
from bibtexparser import bparser
from bibtexparser.bwriter import BibTexWriter
from fixtex import constants_tex_fixes


class BibTexCleaner(object):
    def __init__(self, key, entry, full=False):
        self.key = key
        self.entry = entry
        self.USE_FULL = full
        if self.USE_FULL:
            self.FOR = 'thesis'
        else:
            self.FOR = 'conference'

    def clip_abstract(self):
        # Clip abstrat
        if 'abstract' in self.entry:
            parts = self.entry['abstract'].split(' ')[0:7]
            self.entry['abstract'] = ' '.join(parts)

    def fix_year(self):
        if 'year' not in self.entry:
            if 'date' in self.entry:
                if '-' in self.entry['date']:
                    dateparts = self.entry['date'].split('-')
                else:
                    dateparts = self.entry['date'].split('/')
                if len(dateparts) in {1, 2, 3} and len(dateparts[0]) == 4:
                    year = dateparts[0]
                else:
                    print('unknown year format')
                    import utool
                    utool.embed()
                self.entry['year'] = year

    def shorten_keys(self):
        # Remove Keys
        detail_level = {
            'thesis': 3,
            'journal': 2,
            'conference': 1,
        }
        level = detail_level[self.FOR]
        remove_keys = []
        if level <= 3:
            remove_keys += [
                'note',
                # 'series', 'publisher',
                'isbn', 'editor',
                'shorttitle', 'copyright', 'language',
                'rights', 'langid', 'keywords', 'shortjournal', 'issn', 'file',
            ]
        if level <= 2:
            remove_keys += ['number',  'pages', 'volume']

        self.entry = ut.delete_dict_keys(self.entry, remove_keys)

    def _pubkey(self):
        journal_keys = ['journal', 'journaltitle']
        conf_keys = ['booktitle', 'eventtitle']
        valid_keys = conf_keys + journal_keys

        # if 'journaltitle' in self.entry:
        #     return 'journaltitle'
        pubkeys = sorted(set(self.entry.keys()).intersection(valid_keys))
        if len(pubkeys) == 1:
            pubkey = pubkeys[0]
        else:
            if len(pubkeys) > 1:
                vals = ut.take(self.entry, pubkeys)
                flags = [v is not None for v in vals]
                if sum(flags) == 0:
                    print('pubkeys = %r' % (pubkeys,))
                    print(ut.repr4(self.entry))
                    raise AssertionError('missing pubkey')
                else:
                    pubkeys = ut.compress(pubkeys, flags)
                    vals = ut.compress(vals, flags)
                    # vals = ut.emap(self.transform_pubval, vals)
                    if sum(flags) == 1:
                        pubkey = pubkeys[0]
                    else:
                        if conf_keys[0] in pubkeys:
                            return conf_keys[0]
                        elif journal_keys[0] in pubkeys:
                            return journal_keys[0]
                        else:
                            print('pubkeys = %r' % (pubkeys,))
                            print('vals = %r' % (vals,))
                            print(ut.repr4(self.entry))
                            raise AssertionError('more than one pubkey=%r' % (pubkeys,))
            else:
                pubkey = None
        return pubkey

    def _pubval(self):
        """
        Finds conference or journal
        """
        pubkey = self._pubkey()
        if pubkey is None:
            pubval = None
        else:
            pubval = self.entry[pubkey]
            pubval = pubval.replace('{', '').replace('}', '')
        return pubval

    @property
    def pubval(self):
        return self.standard_pubval(full=False)

    def publication(self):
        old_pubval = self._pubval()
        if old_pubval is None:
            return None
        candidates = []
        # Check if the publication name matches any standard patterns
        if old_pubval.startswith('arXiv'):
            old_pubval = 'CoRR'
        for pub in constants_tex_fixes.PUBLICATIONS:
            if pub.matches(old_pubval):
                candidates.append(pub)
        if len(candidates) == 0:
            print('COULD NOT MATCH: %r' % old_pubval)
            return None
        elif len(candidates) == 1:
            return candidates[0]
        else:
            print('DOUBLE MATCH:')
            print(ut.repr4(self.entry))
            print('old_pubval = %r' % (old_pubval,))
            print('candidates = %r' % (candidates,))
            raise RuntimeError('double match')

    def transform_pubval(self, old_pubval, full=None):
        if full is None:
            full = self.USE_FULL
        pub = self.publication()
        if pub is not None:
            if full:
                new_confval = pub.full()
            else:
                new_confval = pub.abbrev()
        else:
            new_confval = self._pubval()
        return new_confval

        # candidates = []
        # old_pubval = old_pubval.replace('{', '').replace('}', '')
        # new_confval = old_pubval
        # # Check if the publication name matches any standard patterns
        # if old_pubval.startswith('arXiv'):
        #     old_pubval = 'CoRR'
        # for pub in constants_tex_fixes.PUBLICATIONS:
        #     if pub.matches(old_pubval):
        #         candidates.append(pub)
        # if len(candidates) == 0:
        #     print('COULD NOT MATCH: %r' % old_pubval)
        #     new_confval = None
        # elif len(candidates) == 1:
        #     if full:
        #         new_confval = candidates[0].full()
        #     else:
        #         new_confval = candidates[0].abbrev()
        # else:
        #     print('DOUBLE MATCH:')
        #     print(ut.repr4(self.entry))
        #     print('old_pubval = %r' % (old_pubval,))
        #     print('candidates = %r' % (candidates,))
        #     raise RuntimeError('double match')
        # return new_confval

    def standard_pubval(self, full=None):
        old_pubval = self._pubval()
        if old_pubval is None:
            return None
        new_confval = self.transform_pubval(old_pubval, full=full)
        return new_confval

    def fix_pubkey(self):
        pubkey = self._pubkey()
        if pubkey == 'journaltitle':
            # Fix pubkey for journals
            self.entry['journal'] = self.entry['journaltitle']
            del self.entry['journaltitle']
            pubkey = 'journal'

        if pubkey == 'eventtitle':
            # Fix pubkey for journals
            self.entry['booktitle'] = self.entry['eventtitle']
            del self.entry['eventtitle']
            pubkey = 'booktitle'

        if pubkey is not None:
            old_pubval = self._pubval()
            new_confval = self.standard_pubval()

            if new_confval is None:
                # Maybe the pattern is missing?
                return old_pubval
            else:
                # Overwrite the conference name
                self.entry[pubkey] = new_confval

    def fix_general(self):
        pub = self.publication()
        if pub is not None:
            if pub.type is None:
                print('TYPE NOT KNOWN FOR pub=%r' % pub)
            if pub.type == 'journal':
                if self.entry['ENTRYTYPE'] != 'article':
                    print('ENTRY IS A JOURNAL BUT NOT ARTICLE')
                    print(ut.repr4(self.entry))
            if pub.type == 'conference':
                # if self.entry['ENTRYTYPE'] == 'incollection':
                #     self.entry['ENTRYTYPE'] = 'conference'
                if self.entry['ENTRYTYPE'] == 'inproceedings':
                    self.entry['ENTRYTYPE'] = 'conference'

                if self.entry['ENTRYTYPE'] != 'conference':
                    print('ENTRY IS A CONFERENCE BUT NOT INPROCEEDINGS')
                    print(ut.repr4(self.entry))
                    # raise RuntimeError('bad conf')
            if pub.type == 'report':
                if self.entry['ENTRYTYPE'] != 'report':
                    print('ENTRY IS A REPORT BUT NOT REPORT')
                    print(ut.repr4(self.entry))
                    # raise RuntimeError('bad conf')
            if pub.type == 'book':
                if self.entry['ENTRYTYPE'] != 'book':
                    print('ENTRY IS A BOOK BUT NOT BOOK')
                    print(ut.repr4(self.entry))

            self.entry['pub_abbrev'] = pub.abbrev()
            self.entry['pub_full'] = pub.full()
            self.entry['pub_type'] = str(pub.type)
        else:
            if self.entry['ENTRYTYPE'] not in {'report', 'book', 'misc', 'online', 'thesis', 'phdthesis', 'mastersthesis'}:
                print('unknown entrytype')
                print(ut.repr4(self.entry))

        if self.entry['ENTRYTYPE'] == 'thesis':
            thesis_type = self.entry['type'].lower()
            thesis_type = thesis_type.replace('.', '').replace(' ', '')
            if thesis_type  == 'phdthesis':
                self.entry['ENTRYTYPE'] = 'phdthesis'
                self.entry.pop('type', None)
            if thesis_type == 'msthesis':
                self.entry['ENTRYTYPE'] = 'mastersthesis'
                self.entry.pop('type', None)
            self.entry['pub_type'] = 'thesis'

        if self.entry['ENTRYTYPE'] == 'online':
            # self.entry['ENTRYTYPE'] = 'misc'
            # self.entry['howpublished'] = '\\url{%s}' % self.entry['url']
            accessed = self.entry['urldate']
            self.entry['note'] = '[Accessed {}]'.format(accessed)
            self.entry['pub_type'] = 'online'
        else:
            self.entry.pop('url', None)

        if self.entry['ENTRYTYPE'] not in {'book', 'incollection'}:
            self.entry.pop('publisher', None)
            self.entry.pop('series', None)

    def fix_arxiv(self):
        if self.pubval == 'CoRR':
            import utool
            with utool.embed_on_exception_context:
                arxiv_id = None
                if 'doi' in self.entry and not arxiv_id:
                    arxiv_id = self.entry.get('doi').lstrip('arXiv:')
                if 'eprint' in self.entry and not arxiv_id:
                    arxiv_id = self.entry.get('eprint').lstrip('arXiv:')
                if not arxiv_id:
                    print(ut.repr4(self.entry))
                    raise RuntimeError('Unable to find archix id')

                self.entry['volume'] = 'abs/{}'.format(arxiv_id)

    def fix_authors(self):
        # Fix Authors
        if 'author' in self.entry:
            authors = six.text_type(self.entry['author'])
            for truename, alias_list in constants_tex_fixes.AUTHOR_NAME_MAPS.items():
                pattern = six.text_type(
                    ut.regex_or([ut.util_regex.whole_word(alias) for alias in alias_list]))
                authors = re.sub(pattern, six.text_type(truename), authors, flags=re.UNICODE)
            self.entry['author'] = authors

    def fix_paper_types(self):
        """
        Ensure journals and conferences have correct entrytypes.
        """
        # Record info about types of conferneces
        # true_confval = entry[pubkey].replace('{', '').replace('}', '')
        pubval = self.standard_pubval()
        type_key = 'ENTRYTYPE'

        # article = journal
        # inprocedings = converence paper

        # FIX ENTRIES THAT SHOULD BE CONFERENCES
        entry = self.entry
        if pubval in constants_tex_fixes.CONFERENCE_LIST:
            if entry[type_key] == 'inproceedings':
                pass
            elif entry[type_key] == 'article':
                entry['booktitle'] = entry['journal']
                del entry['journal']
            elif entry[type_key] == 'incollection':
                pass
            else:
                raise AssertionError('UNKNOWN TYPE: %r' % (entry[type_key],))
            if 'booktitle' not in entry:
                print('DOES NOT HAVE CORRECT CONFERENCE KEY')
                print(ut.dict_str(entry))
            assert 'journal' not in entry, 'should not have journal'
            entry[type_key] = 'inproceedings'

        # FIX ENTRIES THAT SHOULD BE JOURNALS
        if pubval in constants_tex_fixes.JOURNAL_LIST:
            if entry[type_key] == 'article':
                pass
            elif entry[type_key] == 'inproceedings':
                pass
                #print(ut.dict_str(entry))
            elif entry[type_key] == 'incollection':
                pass
            else:
                raise AssertionError('UNKNOWN TYPE: %r' % (entry['type'],))
            if 'journal' not in entry:
                print('DOES NOT HAVE CORRECT CONFERENCE KEY')
                print(ut.dict_str(entry))
            assert 'booktitle' not in entry, 'should not have booktitle'


def find_item_types(clean_text):
    item_type_pat = ut.named_field('gtem_type', '\w+')
    pattern = '@' + item_type_pat + '{'
    #header_list = [match.string[match.start():match.end()] for match in re.finditer(item_type_pat, clean_text)]
    header_list = [match.groupdict()['item_type'] for match in re.finditer(pattern, clean_text)]
    header_list = ut.unique_keep_order2(header_list)
    header_reprs = '\n'.join(['    \'' + x + '\', ' for x in header_list])
    print(header_reprs)


def main(bib_fpath=None):
    r"""
    intro point to fixbib script

    CommmandLine:
        fixbib
        python -m fixtex bib
        python -m fixtex bib --dryrun
        python -m fixtex bib --dryrun --debug
    """

    if bib_fpath is None:
        bib_fpath = 'My Library.bib'

    # DEBUG = ut.get_argflag('--debug')
    # Read in text and ensure ascii format
    dirty_text = ut.read_from(bib_fpath)

    from os.path import exists, relpath
    from fixtex.fix_tex import find_used_citations, testdata_fpaths

    if exists('custom_extra.bib'):
        extra_parser = bparser.BibTexParser(ignore_nonstandard_types=False)
        print('Parsing extra bibtex file')
        extra_text = ut.read_from('custom_extra.bib')
        extra_database = extra_parser.parse(extra_text, partial=False)
        print('Finished parsing extra')
        extra_dict = extra_database.get_entry_dict()
    else:
        extra_dict = None

    #udata = dirty_text.decode("utf-8")
    #dirty_text = udata.encode("ascii", "ignore")
    #dirty_text = udata

    # parser = bparser.BibTexParser()
    # bib_database = parser.parse(dirty_text)
    # d = bib_database.get_entry_dict()

    print('BIBTEXPARSER LOAD')
    parser = bparser.BibTexParser(ignore_nonstandard_types=False)
    print('Parsing bibtex file')
    bib_database = parser.parse(dirty_text, partial=False)
    print('Finished parsing')

    bibtex_dict = bib_database.get_entry_dict()
    old_keys = list(bibtex_dict.keys())
    new_keys = []
    import re
    for key in ut.ProgIter(old_keys, 'fixing keys'):
        new_key = key
        new_key = new_key.replace(':', '')
        new_key = new_key.replace('-', '_')
        new_key = re.sub('__*', '_', new_key)
        new_keys.append(new_key)
    import ubelt as ub

    # assert len(ut.find_duplicate_items(new_keys)) == 0, 'new keys created conflict'
    assert len(ub.find_duplicates(new_keys)) == 0, 'new keys created conflict'

    for key, new_key in zip(old_keys, new_keys):
        if key != new_key:
            entry = bibtex_dict[key]
            entry['ID'] = new_key
            bibtex_dict[new_key] = entry
            del bibtex_dict[key]

    # The bibtext is now clean. Print it to stdout
    #print(clean_text)
    verbose = None
    if verbose is None:
        verbose = 1

    # Find citations from the tex documents
    key_list = None
    if key_list is None:
        import ubelt as ub
        cacher = ub.Cacher('texcite1', enabled=0)
        data = cacher.tryload()
        if data is None:
            fpaths = testdata_fpaths()
            key_list, inverse = find_used_citations(fpaths, return_inverse=True)
            # ignore = ['JP', '?', 'hendrick']
            # for item in ignore:
            #     try:
            #         key_list.remove(item)
            #     except ValueError:
            #         pass
            if verbose:
                print('Found %d citations used in the document' % (len(key_list),))
            data = key_list, inverse
            cacher.save(data)
        key_list, inverse = data

    # else:
    #     key_list = None

    unknown_pubkeys = []
    debug_author = ut.get_argval('--debug-author', type_=str, default=None)
    # ./fix_bib.py --debug_author=Kappes

    if verbose:
        print('Fixing %d/%d bibtex entries' % (len(key_list), len(bibtex_dict)))

    # debug = True
    debug = False
    if debug_author is not None:
        debug = False

    known_keys = list(bibtex_dict.keys())
    missing_keys = set(key_list) - set(known_keys)
    if extra_dict is not None:
        missing_keys.difference_update(set(extra_dict.keys()))

    if missing_keys:
        print('The library is missing keys found in tex files %s' % (
            ut.repr4(missing_keys),))

    # Search for possible typos:
    candidate_typos = {}
    sedlines = []
    for key in missing_keys:
        candidates = ut.closet_words(key, known_keys, num=3, subset=True)
        if len(candidates) > 1:
            top = candidates[0]
            if ut.edit_distance(key, top) == 1:
                # "sed -i -e 's/{}/{}/g' *.tex".format(key, top)
                import os
                replpaths = ' '.join([relpath(p, os.getcwd()) for p in inverse[key]])
                sedlines.append("sed -i -e 's/{}/{}/g' {}".format(key, top, replpaths))
        candidate_typos[key] = candidates
        print('Cannot find key = %r' % (key,))
        print('Did you mean? %r' % (candidates,))

    print('Quick fixes')
    print('\n'.join(sedlines))

    # group by file
    just = max([0] + ut.lmap(len, missing_keys))
    missing_fpaths = [inverse[key] for key in missing_keys]
    for fpath in sorted(set(ut.flatten(missing_fpaths))):
        # ut.fix_embed_globals()
        subkeys = [k for k in missing_keys if fpath in inverse[k]]
        print('')
        ut.cprint('--- Missing Keys ---', 'blue')
        ut.cprint('fpath = %r' % (fpath,), 'blue')
        ut.cprint('{} | {}'.format('Missing'.ljust(just), 'Did you mean?'), 'blue')
        for key in subkeys:
            print('{} | {}'.format(
                ut.highlight_text(key.ljust(just), 'red'),
                ' '.join(candidate_typos[key]))
            )

    # for key in list(bibtex_dict.keys()):

    if extra_dict is not None:
        # Extra database takes precidence over regular
        key_list = list(ut.unique(key_list + list(extra_dict.keys())))
        for k, v in extra_dict.items():
            bibtex_dict[k] = v

    full = ut.get_argflag('--full')

    for key in key_list:
        try:
            entry = bibtex_dict[key]
        except KeyError:
            continue
        self = BibTexCleaner(key, entry, full=full)

        if debug_author is not None:
            debug = debug_author in entry.get('author', '')

        if debug:
            ut.cprint(' --- ENTRY ---', 'yellow')
            print(ut.repr3(entry))

        self.clip_abstract()
        self.shorten_keys()
        self.fix_authors()
        self.fix_year()
        old_pubval = self.fix_pubkey()
        if old_pubval:
            unknown_pubkeys.append(old_pubval)
        self.fix_arxiv()
        self.fix_general()
        # self.fix_paper_types()

        if debug:
            print(ut.repr3(self.entry))
            ut.cprint(' --- END ENTRY ---', 'yellow')
        bibtex_dict[key] = self.entry

    unwanted_keys = set(bibtex_dict.keys()) - set(key_list)
    if verbose:
        print('Removing unwanted %d entries' % (len(unwanted_keys)))
    ut.delete_dict_keys(bibtex_dict, unwanted_keys)

    if 0:
        d1 = bibtex_dict.copy()
        full = True
        for key, entry in d1.items():
            self = BibTexCleaner(key, entry, full=full)
            pub = self.publication()
            if pub is None:
                print(self.entry['ENTRYTYPE'])

            old = self.fix_pubkey()
            x1 = self._pubval()
            x2 = self.standard_pubval(full=full)
            # if x2 is not None and len(x2) > 5:
            #     print(ut.repr4(self.entry))

            if x1 != x2:
                print('x2 = %r' % (x2,))
                print('x1 = %r' % (x1,))
                print(ut.repr4(self.entry))

            # if 'CVPR' in self.entry.get('booktitle', ''):
            #     if 'CVPR' != self.entry.get('booktitle', ''):
            #         break
            if old:
                print('old = %r' % (old,))
            d1[key] = self.entry

    if full:
        d1 = bibtex_dict.copy()

        import numpy as np
        import pandas as pd
        df = pd.DataFrame.from_dict(d1, orient='index')

        paged_items = df[~pd.isnull(df['pub_abbrev'])]
        has_pages = ~pd.isnull(paged_items['pages'])
        print('have pages {} / {}'.format(has_pages.sum(), len(has_pages)))
        print(ut.repr4(paged_items[~has_pages]['title'].values.tolist()))

        entrytypes = dict(list(df.groupby('pub_type')))
        if False:
            # entrytypes['misc']
            g = entrytypes['online']
            g = g[g.columns[~np.all(pd.isnull(g), axis=0)]]

            entrytypes['book']
            entrytypes['thesis']
            g = entrytypes['article']
            g = entrytypes['incollection']
            g = entrytypes['conference']

        def lookup_pub(e):
            if e == 'article':
                return 'journal', 'journal'
            elif e == 'incollection':
                return 'booksection', 'booktitle'
            elif e == 'conference':
                return 'conference', 'booktitle'
            return None, None

        for e, g in entrytypes.items():
            print('e = %r' % (e,))
            g = g[g.columns[~np.all(pd.isnull(g), axis=0)]]
            if 'pub_full' in g.columns:
                place_title = g['pub_full'].tolist()
                print(ut.repr4(ut.dict_hist(place_title)))
            else:
                print('Unknown publications')

        if 'report' in entrytypes:
            g = entrytypes['report']
            missing = g[pd.isnull(g['title'])]
            if len(missing):
                print('Missing Title')
                print(ut.repr4(missing[['title', 'author']].values.tolist()))

        if 'journal' in entrytypes:
            g = entrytypes['journal']
            g = g[g.columns[~np.all(pd.isnull(g), axis=0)]]

            missing = g[pd.isnull(g['journal'])]
            if len(missing):
                print('Missing Journal')
                print(ut.repr4(missing[['title', 'author']].values.tolist()))

        if 'conference' in entrytypes:
            g = entrytypes['conference']
            g = g[g.columns[~np.all(pd.isnull(g), axis=0)]]

            missing = g[pd.isnull(g['booktitle'])]
            if len(missing):
                print('Missing Booktitle')
                print(ut.repr4(missing[['title', 'author']].values.tolist()))

        if 'incollection' in entrytypes:
            g = entrytypes['incollection']
            g = g[g.columns[~np.all(pd.isnull(g), axis=0)]]

            missing = g[pd.isnull(g['booktitle'])]
            if len(missing):
                print('Missing Booktitle')
                print(ut.repr4(missing[['title', 'author']].values.tolist()))

        if 'thesis' in entrytypes:
            g = entrytypes['thesis']
            g = g[g.columns[~np.all(pd.isnull(g), axis=0)]]
            missing = g[pd.isnull(g['institution'])]
            if len(missing):
                print('Missing Institution')
                print(ut.repr4(missing[['title', 'author']].values.tolist()))

        # import utool
        # utool.embed()

    # Overwrite BibDatabase structure
    bib_database._entries_dict = bibtex_dict
    bib_database.entries = list(bibtex_dict.values())

    #conftitle_to_types_set_hist = {key: set(val) for key, val in conftitle_to_types_hist.items()}
    #print(ut.dict_str(conftitle_to_types_set_hist))

    print('Unknown conference keys:')
    print(ut.list_str(sorted(unknown_pubkeys)))
    print('len(unknown_pubkeys) = %r' % (len(unknown_pubkeys),))

    writer = BibTexWriter()
    writer.contents = ['comments', 'entries']
    writer.indent = '  '
    writer.order_entries_by = ('type', 'author', 'year')

    new_bibtex_str = bibtexparser.dumps(bib_database, writer)

    # Need to check
    #jegou_aggregating_2012

    # Fix the Journal Abreviations
    # References:
    # https://www.ieee.org/documents/trans_journal_names.pdf

    # Write out clean bibfile in ascii format
    clean_bib_fpath = ut.augpath(bib_fpath.replace(' ', '_'), '_clean')

    if not ut.get_argflag('--dryrun'):
        ut.write_to(clean_bib_fpath, new_bibtex_str)


if __name__ == '__main__':
    #bib_fpath = 'nsf-mri-2014'
    bib_fpath = 'My Library.bib'
    main(bib_fpath)
