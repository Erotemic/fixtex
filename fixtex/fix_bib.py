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
import ubelt as ub
import six
import bibtexparser
from os.path import exists, relpath
from bibtexparser import bparser
from bibtexparser.bwriter import BibTexWriter
from fixtex import constants_tex_fixes


class BibMan(object):
    def __init__(bibman, fpath, doc='thesis'):
        bibman.fpath = fpath
        bibman.cleaned = None
        bibman.raw_entries = None
        bibman.raw_text = None
        bibman.doc = doc
        bibman.unregistered_pubs = []
        bibman._init()

    def sort_entries(bibman):

        def freq_group(items, groupids):
            groups = ut.group_items(items, groupids)
            hist = ut.map_vals(len, groups)
            for k in ut.argsort(hist):
                yield groups[k]

        high_level_alias = {
            'incollection': 'book',
            'conference': 'confjourn',
            'journal': 'confjourn',
            'online-journal': 'confjourn',
        }
        sorted_entries = []
        entries = list(bibman.cleaned.values())
        groups = [high_level_alias.get(entry['pub_type'], entry['pub_type'])
                  for entry in entries]
        entry_groups = freq_group(entries, groups)
        for group in entry_groups:
            subids = [entry['ENTRYTYPE'] for entry in group]
            for subgroup in freq_group(group, subids):
                subsubids = [entry['pub_full'] for entry in subgroup]
                # Group publications, and then sort conferences by max date
                pub_groups = []
                pub_maxdates = []
                for ssg in freq_group(subgroup, subsubids):
                    sssid = [(entry['date']) for entry in ssg]
                    ssg2 = ut.take(ssg, ut.argsort(sssid))
                    pub_groups.append(ssg2)
                    pub_maxdates.append(ssg2[-1]['date'])
                subgroup2 = ut.flatten(ut.sortedby2(pub_groups, pub_maxdates))
                sorted_entries.extend(subgroup2)
        new_entries = ut.odict([(e['ID'], e) for e in sorted_entries])
        [e['pub_type'] for e in sorted_entries]
        bibman.cleaned = new_entries

    def __getitem__(bibman, key):
        item = bibman.cleaned[key]
        return item

    def save(bibman):
        text2 = bibman.dumps()
        ut.writeto(bibman.fpath, text2)

    def dumps(bibman):
        db = bibtexparser.bparser.BibDatabase()
        db._entries_dict = bibman.cleaned
        db.entries = list(bibman.cleaned.values())
        writer = BibTexWriter()
        # writer.order_entries_by = ('type', 'author', 'year')
        writer.order_entries_by = None
        writer.contents = ['comments', 'entries']
        writer.indent = '    '
        new_text = bibtexparser.dumps(db, writer)
        return new_text

    def printdiff(bibman):
        text1 = bibman.raw_text
        text2 = bibman.dumps()

        def remove_lines(text, pats):
            text = '\n'.join([t for t in text.split('\n') if not any(p in t for p in pats)])
            return text

        # pats = ['CoRR', 'Computing Res.', 'pub_type', 'pub_abbrev',
        #         'pub_accro', 'pub_full']
        # pats = []
        # text1 = remove_lines(text1, pats)
        # text2 = remove_lines(text2, pats)
        print(ut.color_diff_text(ut.difftext(text1, text2,
                                             num_context_lines=10)))

    def _init(bibman):
        bibman._read_raw_entries()
        bibman._clean_entries()

    def _clean_entries(bibman):
        bibman.cleaned = {}
        for key, entry in bibman.raw_entries.items():
            cleaner = BibTexCleaner(key, entry, doc=bibman.doc)
            new_entry = cleaner.fix()
            pub = cleaner.publication()
            if not pub.registered:
                pub.entry = entry
                bibman.unregistered_pubs.append(pub)
            bibman.cleaned[key] = new_entry

    def _read_raw_entries(bibman):
        parser = bparser.BibTexParser()
        ut.delete_keys(parser.alt_dict, ['url', 'urls'])
        parser.ignore_nonstandard_types = False
        text = ut.read_from(bibman.fpath)

        # ensure good format
        flag = 0
        for x in re.finditer('^.*}\n[^}\n]', text, flags=re.MULTILINE):
            lineno = x.string[:x.start()].count('\n') + 1
            print('DID YOU FORGET A COMMA ON lineno = {!r}'.format(lineno))
            print(x.group())
            flag += 1
        assert not flag, 'fix formating'

        database = parser.parse(text)
        entries = database.entries
        raw_entries = database.get_entry_dict()
        raw_entries = ut.order_dict_by(raw_entries, [e['ID'] for e in entries])
        bibman.raw_text = text
        bibman.raw_entries = raw_entries

    def fix_conference_places(bibman):

        pubman = constants_tex_fixes.PubManager()

        needed = set()

        for entry in bibman.cleaned.values():
            if entry['pub_type'] == 'conference':
                accro, year = (entry['pub_accro'], entry['year'])
                pub = pubman.find(accro)
                if pub.places is None or int(year) not in pub.places:
                    needed.add((accro, year))
                else:
                    place = pub.places[int(year)]
                    print('place = {!r}'.format(place))
                    entry['address'] = place

        if needed:
            needed = list(needed)
            used_years = ut.group_items(needed, ut.take_column(needed, 0))
            for k, v in list(used_years.items()):
                used_years[k] = sorted(v)

            sortby = ut.map_vals(lambda vs: (len(vs), max(e[1] for e in vs)),
                                 used_years)
            used_years = ut.order_dict_by(used_years, ut.argsort(sortby))
            print('NEED CONFERENCE LOCATIONS')
            print(ut.repr4(used_years, nl=2))


class BibTexCleaner(object):
    def __init__(cleaner, key, entry, doc=None, full=False):
        cleaner.key = key
        cleaner.entry = entry
        cleaner._pub = None
        if doc is not None:
            cleaner.FOR = doc
        else:
            if full:
                cleaner.FOR = 'thesis'
            else:
                cleaner.FOR = 'conference'

    def clip_abstract(cleaner):
        # Clip abstrat
        if 'abstract' in cleaner.entry:
            parts = cleaner.entry['abstract'].split(' ')[0:7]
            cleaner.entry['abstract'] = ' '.join(parts)

    def fix(cleaner):
        cleaner.clip_abstract()
        cleaner.shorten_keys()
        cleaner.fix_authors()
        cleaner.fix_pubkey()
        cleaner.fix_arxiv()
        cleaner.fix_general()

        cleaner.fix_year()

        return cleaner.entry

    def fix_year(cleaner):
        import calendar
        month_lookup = {v: k for k, v in
                        enumerate(calendar.month_abbr)}
        if cleaner.FOR == 'thesis':
            pub = cleaner.publication()
            needs_month = pub.type == 'journal'
        else:
            needs_month = False
        if 'month' in cleaner.entry:
            needs_month = False
        needs_year = 'year' not in cleaner.entry

        if needs_year or needs_month:
            if 'date' in cleaner.entry:
                if '-' in cleaner.entry['date']:
                    dateparts = cleaner.entry['date'].split('-')
                else:
                    dateparts = cleaner.entry['date'].split('/')
                if needs_year:
                    if len(dateparts) in {1, 2, 3} and len(dateparts[0]) == 4:
                        year = dateparts[0]
                    else:
                        print(ut.repr4(cleaner.entry))
                        print('unknown year format')
                        import utool
                        utool.embed()
                    cleaner.entry['year'] = year
                if needs_month:
                    month = None
                    if len(dateparts) in {2, 3} and len(dateparts[0]) == 4:
                        month = dateparts[1]
                    else:
                        if 'issue' in cleaner.entry:
                            issue = cleaner.entry['issue']
                            month = month_lookup[issue]

                    if month is None:
                        if pub.accro() == 'CoRR':
                            print('PARSING NEW MONTH FOR')
                            print(ut.repr4(cleaner.entry))
                            url = cleaner.entry['url']
                            import bs4
                            import requests
                            import parse
                            r = requests.get(url)
                            data = r.text
                            soup = bs4.BeautifulSoup(data, 'html.parser')
                            elems = soup.find_all(text=re.compile(
                                '\\(this version.*', flags=re.IGNORECASE))
                            if elems:
                                assert len(elems) == 1
                                elem = elems[0]
                                result = parse.parse(
                                    '{}revised {day:d} {mo} {year:d} (this{}', elem)
                            else:
                                elems = soup.find_all(text=re.compile(
                                    '.Submitted on.*', flags=re.IGNORECASE))
                                assert len(elems) == 1
                                elem = elems[0]
                                result = parse.parse(
                                    '{}Submitted on {day:d} {mo} {year:d}{}', elem)

                            year = result['year']
                            month = month_lookup[result['mo']]
                            day = result['day']
                            print('{}-{}-{}'.format(year, month, day))

                    if month is None:
                        print('UNKNOWN MONTH FORMAT')
                        print(ut.repr4(cleaner.entry))
                    else:
                        cleaner.entry['month'] = str(month)
        try:
            if 'date' not in cleaner.entry:
                if 'year' in cleaner.entry:
                    if 'month' in cleaner.entry:
                        cleaner.entry['date'] = (
                            cleaner.entry['year'] + '-' + cleaner.entry['month'])
                    else:
                        cleaner.entry['date'] = cleaner.entry['year']
            if 'month' in cleaner.entry:
                try:
                    # print('month_str = {!r}'.format(month_str))
                    # print('month_no = {!r}'.format(month_no))
                    month_str = cleaner.entry['month']
                    month_no = int(month_str)
                    cleaner.entry['month'] = calendar.month_abbr[month_no]
                except Exception:
                    pass
        except Exception:
            print('ISSUE WITH DATE PARSE')
            print(ut.repr4(cleaner.entry))
            raise
            pass

    def shorten_keys(cleaner):
        # Remove Keys
        detail_level = {
            'thesis': 3,
            'journal': 2,
            'conference': 1,
        }
        level = detail_level[cleaner.FOR]
        remove_keys = []
        if level <= 3:
            remove_keys += [
                'note',
                # 'series', 'publisher',
                'isbn',
                # 'editor',
                'shorttitle', 'copyright', 'language',
                'rights', 'langid',
                'keywords', 'shortjournal',
                'issn', 'file',
            ]
        if level <= 2:
            remove_keys += ['number',  'pages', 'volume']

        cleaner.entry = ut.delete_dict_keys(cleaner.entry, remove_keys)

    def _pubkey(cleaner):
        journal_keys = ['journal', 'journaltitle']
        conf_keys = ['booktitle', 'eventtitle']
        report_keys = ['institution']
        valid_keys = conf_keys + journal_keys + report_keys

        # if 'journaltitle' in cleaner.entry:
        #     return 'journaltitle'
        pubkeys = sorted(set(cleaner.entry.keys()).intersection(valid_keys))
        if len(pubkeys) == 1:
            pubkey = pubkeys[0]
        else:
            if len(pubkeys) > 1:
                vals = ut.take(cleaner.entry, pubkeys)
                flags = [v is not None for v in vals]
                if sum(flags) == 0:
                    print('pubkeys = %r' % (pubkeys,))
                    print(ut.repr4(cleaner.entry))
                    raise AssertionError('missing pubkey')
                else:
                    pubkeys = ut.compress(pubkeys, flags)
                    vals = ut.compress(vals, flags)
                    # vals = ut.emap(cleaner.transform_pubval, vals)
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
                            print(ut.repr4(cleaner.entry))
                            raise AssertionError('more than one pubkey=%r' % (pubkeys,))
            else:
                pubkey = None
        return pubkey

    def _pubval(cleaner):
        """
        Finds conference or journal
        """
        pubkey = cleaner._pubkey()
        if pubkey is None:
            pubval = None
        else:
            pubval = cleaner.entry[pubkey]
            pubval = pubval.replace('{', '').replace('}', '')
        return pubval

    @property
    def pubval(cleaner):
        return cleaner.standard_pubval(full=False)

    def publication(cleaner):
        if cleaner._pub is None:
            old_pubval = cleaner._pubval()
            if old_pubval is None:
                # Non-standard publications (that shouldn't be registerd)
                type = cleaner.entry['ENTRYTYPE']
                if type == 'book':
                    old_pubval = cleaner.entry['title']
                cleaner._pub = constants_tex_fixes.Pub(
                    type=type, full=old_pubval, registered=False,
                    publisher=cleaner.entry.get('publisher', None)
                )
            else:
                pubman = constants_tex_fixes.PubManager()
                candidates = pubman.findall(old_pubval)

                if len(candidates) == 0:
                    print('UNREGISTERED PUBLICATION: %r' % old_pubval)
                    type = cleaner.entry['ENTRYTYPE']
                    # Try to make a pub as best as we can
                    cleaner._pub = constants_tex_fixes.Pub(
                        None, full=old_pubval, type=type, registered=False)
                elif len(candidates) == 1:
                    cleaner._pub = candidates[0]
                else:
                    print('NON-UNIQUE PUBLICATION (DOUBLE MATCH):')
                    print(ut.repr4(cleaner.entry))
                    print('old_pubval = %r' % (old_pubval,))
                    print('candidates = %r' % (candidates,))
                    raise RuntimeError('double match')
        return cleaner._pub

    def transform_pubval(cleaner, old_pubval, full=None):
        if full is None:
            full = cleaner.FOR == 'thesis'
        pub = cleaner.publication()
        if pub:
            if full:
                if pub.type in {'conference', 'journal'}:
                    new_confval = pub.abbrev()
                else:
                    new_confval = pub.full()
            else:
                new_confval = pub.accro()
        else:
            new_confval = cleaner._pubval()
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
        #         new_confval = candidates[0].accro()
        # else:
        #     print('DOUBLE MATCH:')
        #     print(ut.repr4(cleaner.entry))
        #     print('old_pubval = %r' % (old_pubval,))
        #     print('candidates = %r' % (candidates,))
        #     raise RuntimeError('double match')
        # return new_confval

    def standard_pubval(cleaner, full=None):
        old_pubval = cleaner._pubval()
        if old_pubval is None:
            return None
        new_confval = cleaner.transform_pubval(old_pubval, full=full)
        return new_confval

    def fix_pubkey(cleaner):
        pubkey = cleaner._pubkey()
        if pubkey == 'journaltitle':
            # Fix pubkey for journals
            cleaner.entry['journal'] = cleaner.entry['journaltitle']
            del cleaner.entry['journaltitle']
            pubkey = 'journal'

        if pubkey == 'eventtitle':
            # Fix pubkey for journals
            cleaner.entry['booktitle'] = cleaner.entry['eventtitle']
            del cleaner.entry['eventtitle']
            pubkey = 'booktitle'

        if pubkey is not None:
            old_pubval = cleaner._pubval()
            new_confval = cleaner.standard_pubval()

            if new_confval is None:
                # Maybe the pattern is missing?
                return old_pubval
            else:
                # Overwrite the conference name
                cleaner.entry[pubkey] = new_confval

    def fix_general(cleaner):
        pub = cleaner.publication()
        if pub.type is not None:
            # if pub.type is None:
            #     print('TYPE NOT KNOWN FOR pub=%r' % pub)
            if pub.type == 'journal':
                if cleaner.entry['ENTRYTYPE'] != 'article':
                    print('ENTRY IS A JOURNAL BUT NOT ARTICLE')
                    print(ut.repr4(cleaner.entry))
            if pub.type == 'conference':
                # if cleaner.entry['ENTRYTYPE'] == 'incollection':
                #     cleaner.entry['ENTRYTYPE'] = 'conference'
                if cleaner.entry['ENTRYTYPE'] == 'inproceedings':
                    cleaner.entry['ENTRYTYPE'] = 'conference'

                if cleaner.entry['ENTRYTYPE'] != 'conference':
                    print('ENTRY IS A CONFERENCE BUT NOT INPROCEEDINGS')
                    print(ut.repr4(cleaner.entry))
                    # raise RuntimeError('bad conf')
            if pub.type == 'report':
                if cleaner.entry['ENTRYTYPE'] != 'report':
                    print('ENTRY IS A REPORT BUT NOT REPORT')
                    print(ut.repr4(cleaner.entry))
                    # raise RuntimeError('bad conf')
            if pub.type == 'book':
                if cleaner.entry['ENTRYTYPE'] != 'book':
                    print('ENTRY IS A BOOK BUT NOT BOOK')
                    print(ut.repr4(cleaner.entry))
            if pub.type == 'incollection':
                if cleaner.entry['ENTRYTYPE'] != 'incollection':
                    print('ENTRY IS IN BOOK WITH AUTHORS FOR EACH CHAPTER '
                          'BUT NOT INCOLLECTION')
                    print(ut.repr4(cleaner.entry))
            cleaner.entry['pub_type'] = str(pub.type)
        else:
            if cleaner.entry['ENTRYTYPE'] not in {'incollection', 'report',
                                                  'book', 'misc', 'online',
                                                  'thesis', 'phdthesis',
                                                  'mastersthesis'}:
                print('unknown entrytype')
                print(ut.repr4(cleaner.entry))

        if cleaner.entry['ENTRYTYPE'] == 'phdthesis':
            cleaner.entry['pub_type'] = 'thesis'
        if cleaner.entry['ENTRYTYPE'] == 'mastersthesis':
            cleaner.entry['pub_type'] = 'thesis'

        if cleaner.entry['ENTRYTYPE'] == 'thesis':
            thesis_type = cleaner.entry['type'].lower()
            thesis_type = thesis_type.replace('.', '').replace(' ', '')
            if thesis_type  == 'phdthesis':
                cleaner.entry['ENTRYTYPE'] = 'phdthesis'
                cleaner.entry.pop('type', None)
            if thesis_type == 'msthesis':
                cleaner.entry['ENTRYTYPE'] = 'mastersthesis'
                cleaner.entry.pop('type', None)
            cleaner.entry['pub_type'] = 'thesis'

        if cleaner.entry['ENTRYTYPE'] == 'report':
            cleaner.entry['pub_type'] = 'report'

        if pub.published_online():
            # cleaner.entry['ENTRYTYPE'] = 'misc'
            # cleaner.entry['howpublished'] = '\\url{%s}' % cleaner.entry['url']
            if 'urldate' in cleaner.entry:
                accessed = cleaner.entry['urldate']
                cleaner.entry['note'] = '[Accessed {}]'.format(accessed)
                if pub.type == 'journal':
                    cleaner.entry['pub_type'] = 'online-journal'
                else:
                    cleaner.entry['pub_type'] = 'online'
            else:
                print('PUBLISHED ONLINE BUT NO URLDATE')
                print(ut.repr4(cleaner.entry))
        else:
            cleaner.entry.pop('url', None)

        if cleaner.entry['ENTRYTYPE'] not in {'book', 'incollection'}:
            pass
            # cleaner.entry.pop('publisher', None)
            # cleaner.entry.pop('series', None)

        cleaner.entry['pub_accro'] = str(pub.accro())
        cleaner.entry['pub_abbrev'] = str(pub.abbrev())
        cleaner.entry['pub_full'] = str(pub.full())

    def fix_arxiv(cleaner):
        if cleaner.publication().accro() != 'CoRR':
            return
        arxiv_id = None
        if 'doi' in cleaner.entry and not arxiv_id:
            arxiv_id = cleaner.entry.get('doi').lstrip('arXiv:')
        if 'eprint' in cleaner.entry and not arxiv_id:
            arxiv_id = cleaner.entry.get('eprint').lstrip('arXiv:')
        if 'url' in cleaner.entry and not arxiv_id:
            try:
                import parse
                url = cleaner.entry['url']
                result = parse.parse('http://arxiv.org/abs/{doi}', url)
                arxiv_id = result['doi']
            except Exception:
                pass
        if not arxiv_id:
            print('CANNOT FIND ARCHIX ID')
            print(ut.repr4(cleaner.entry))
            # raise RuntimeError('Unable to find archix id')
        else:
            cleaner.entry['volume'] = 'abs/{}'.format(arxiv_id)

        if 'url' not in cleaner.entry:
            cleaner.entry['url'] = 'https://arxiv.org/abs/{}'.format(arxiv_id)
            # print('NEEDS ARXIV URL')
            # print(ut.repr4(cleaner.entry))

    def fix_authors(cleaner):
        # Fix Authors
        if 'author' in cleaner.entry:
            authors = six.text_type(cleaner.entry['author'])
            for truename, alias_list in constants_tex_fixes.AUTHOR_NAME_MAPS.items():
                pattern = six.text_type(
                    ut.regex_or([ut.util_regex.whole_word(alias) for alias in alias_list]))
                authors = re.sub(pattern, six.text_type(truename), authors, flags=re.UNICODE)
            cleaner.entry['author'] = authors

    def fix_paper_types(cleaner):
        """
        Ensure journals and conferences have correct entrytypes.
        """
        # Record info about types of conferneces
        # true_confval = entry[pubkey].replace('{', '').replace('}', '')
        pubval = cleaner.standard_pubval()
        type_key = 'ENTRYTYPE'

        # article = journal
        # inprocedings = converence paper

        # FIX ENTRIES THAT SHOULD BE CONFERENCES
        entry = cleaner.entry
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

    from fixtex.fix_tex import find_used_citations, testdata_fpaths

    if exists('custom_extra.bib'):
        extra_parser = bparser.BibTexParser(ignore_nonstandard_types=False)
        parser = bparser.BibTexParser()
        ut.delete_keys(parser.alt_dict, ['url', 'urls'])
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
    parser = bparser.BibTexParser(ignore_nonstandard_types=False,
                                  common_strings=True)
    ut.delete_keys(parser.alt_dict, ['url', 'urls'])
    print('Parsing bibtex file')
    bib_database = parser.parse(dirty_text, partial=False)
    print('Finished parsing')

    bibtex_dict = bib_database.get_entry_dict()
    old_keys = list(bibtex_dict.keys())
    new_keys = []
    for key in ut.ProgIter(old_keys, 'fixing keys'):
        new_key = key
        new_key = new_key.replace(':', '')
        new_key = new_key.replace('-', '_')
        new_key = re.sub('__*', '_', new_key)
        new_keys.append(new_key)

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

        entry = self.fix()
        # self.clip_abstract()
        # self.shorten_keys()
        # self.fix_authors()
        # self.fix_year()
        # old_pubval = self.fix_pubkey()
        # if old_pubval:
        #     unknown_pubkeys.append(old_pubval)
        # self.fix_arxiv()
        # self.fix_general()
        # self.fix_paper_types()

        if debug:
            print(ut.repr3(entry))
            ut.cprint(' --- END ENTRY ---', 'yellow')
        bibtex_dict[key] = entry

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

        paged_items = df[~pd.isnull(df['pub_accro'])]
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
