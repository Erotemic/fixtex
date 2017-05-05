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
    def __init__(self, key, entry):
        self.key = key
        self.entry = entry

    def clip_abstract(self):
        # Clip abstrat
        if 'abstract' in self.entry:
            parts = self.entry['abstract'].split(' ')[0:7]
            self.entry['abstract'] = ' '.join(parts)

    def shorten_keys(self):
        # Remove Keys
        detail_level = {
            'thesis': 3,
            'journal': 2,
            'conference': 1,
        }
        # FOR = 'thesis'
        FOR = 'conference'
        level = detail_level[FOR]
        remove_keys = []
        if level <= 3:
            remove_keys += [
                'note', 'urldate', 'series', 'publisher', 'isbn', 'editor',
                'shorttitle', 'copyright', 'language', 'month',
            ]
        if level <= 2:
            remove_keys += ['number',  'pages', 'volume']

        self.entry = ut.delete_dict_keys(self.entry, remove_keys)

    def _confkey(self):
        valid_keys = {'journal', 'booktitle'}
        confkeys = sorted(set(self.entry.keys()).intersection(valid_keys))
        if len(confkeys) == 1:
            confkey = confkeys[0]
        else:
            if len(confkeys) > 1:
                raise AssertionError('more than one confkey=%r' % (confkeys,))
            confkey = None
        return confkey

    def _confval(self):
        """
        Finds conference or journal
        """
        confkey = self._confkey()
        if confkey is None:
            confval = None
        else:
            confval = self.entry[confkey]
            confval = confval.replace('{', '').replace('}', '')
        return confval

    def fix_paper_types(self):
        """
        Ensure journals and conferences have correct entrytypes.
        """
        # Record info about types of conferneces
        # true_confval = entry[confkey].replace('{', '').replace('}', '')
        confval = self.standard_confval()
        type_key = 'ENTRYTYPE'

        # article = journal
        # inprocedings = converence paper

        # FIX ENTRIES THAT SHOULD BE CONFERENCES
        entry = self.entry
        if confval in constants_tex_fixes.CONFERENCE_LIST:
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
        if confval in constants_tex_fixes.JOURNAL_LIST:
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

    def standard_confval(self):
        old_confval = self._confval()
        if old_confval is None:
            return None
        new_confval = None
        candidates = []
        # Check if the conference/journal name matches any standard patterns
        CONFERENCE_TITLE_MAPS = constants_tex_fixes.CONFERENCE_TITLE_MAPS
        for conf_title, patterns in CONFERENCE_TITLE_MAPS.items():
            match_exact = conf_title == old_confval
            match_regex = any(
                re.search(pattern, old_confval, flags=re.IGNORECASE)
                for pattern in patterns
            )
            if (match_exact or match_regex):
                new_confval = conf_title
                candidates.append(new_confval)

        if len(candidates) == 0:
            new_confval = None
        elif len(candidates) == 1:
            new_confval = candidates[0]
        else:
            raise RuntimeError('double match')

        if old_confval.startswith('arXiv'):
            new_confval = 'arXiv'

        return new_confval

    def fix_confkey(self):
        confkey = self._confkey()
        if confkey is not None:
            old_confval = self._confval()
            new_confval = self.standard_confval()

            if new_confval is None:
                # Maybe the pattern is missing?
                # unknown_confkeys.append(old_confval)
                return old_confval
            else:
                # Overwrite the conference name
                self.entry[confkey] = new_confval

    def fix_authors(self):
        # Fix Authors
        if 'author' in self.entry:
            authors = six.text_type(self.entry['author'])
            for truename, alias_list in constants_tex_fixes.AUTHOR_NAME_MAPS.items():
                pattern = six.text_type(
                    ut.regex_or([ut.util_regex.whole_word(alias) for alias in alias_list]))
                authors = re.sub(pattern, six.text_type(truename), authors, flags=re.UNICODE)
            self.entry['author'] = authors


def find_item_types(clean_text):
    item_type_pat = ut.named_field('gtem_type', '\w+')
    pattern = '@' + item_type_pat + '{'
    #header_list = [match.string[match.start():match.end()] for match in re.finditer(item_type_pat, clean_text)]
    header_list = [match.groupdict()['item_type'] for match in re.finditer(pattern, clean_text)]
    header_list = ut.unique_keep_order2(header_list)
    header_reprs = '\n'.join(['    \'' + x + '\', ' for x in header_list])
    print(header_reprs)


"""
    if False:
        # Remove each field in the list
        for field in fields_remove_list:
            # pattern1 removes field + curly-braces without any internal curly-braces
            #  up to a newline. The line may or may not have a comma at the end
            field_pattern1 = field + r' = {[^}]*},? *\n'
            # pattern2 removes field + curly-braces in a greedy fashion up to a newline.
            # The line MUST have a comma at the end. (or else we might get too greedy)
            field_pattern2 = field + r' = {.*}, *\n'
            #print(field_pattern1)
            #print(field_pattern2)
            clean_text = re.sub(field_pattern1, '', clean_text, flags=re.MULTILINE)
            clean_text = re.sub(field_pattern2, '', clean_text, flags=re.MULTILINE)

            # some fields are very pesky (like annot)
            # Careful. Any at symobls may screw things up in an annot field
            REMOVE_NONSAFE = True
            if REMOVE_NONSAFE:
                next_header_field = ut.named_field('nextheader', '@' + ut.regex_or(item_type_list))
                next_header_bref = ut.bref_field('nextheader')

                field_pattern3 = field + r' = {[^@]*}\s*\n\s*}\s*\n\n' + next_header_field
                clean_text = re.sub(field_pattern3, r'}\n\n' + next_header_bref, clean_text, flags=re.MULTILINE | re.DOTALL)

                field_pattern4 = field + r' = {[^@]*},\s*\n\s*}\s*\n\n' + next_header_field
                clean_text = re.sub(field_pattern4, r'}\n\n' + next_header_bref, clean_text, flags=re.MULTILINE | re.DOTALL)

            if DEBUG:
                print(field)
                if field == 'annote':
                    assert re.search(field_pattern1, clean_text, flags=re.MULTILINE) is None
                    assert re.search(field_pattern2, clean_text, flags=re.MULTILINE) is None
                    assert re.search(field_pattern3, clean_text, flags=re.MULTILINE) is None
                    assert re.search(field_pattern4, clean_text, flags=re.MULTILINE) is None

                    field_pattern_annot = 'annote = {'
                    match = re.search(field_pattern_annot, clean_text, flags=re.MULTILINE)
                    if match is not None:
                        print(match.string[match.start():match.end()])
                        print(match.string[match.start():match.start() + 1000])

                        #pattern = 'annote = {.*}'
                        #pattern = 'annote = {[^@]*} *'
                        #match = re.search(pattern, clean_text, flags=re.MULTILINE | re.DOTALL)
                        #print('----')
                        #print(match.string[match.start():match.end()])
                        #print('----')
                        #print(match.string[match.start():match.start() + 1000])
                        #print('----')

    # Clip abstract to only a few words
    clip_abstract = False
    # Done elsewhere now
    if clip_abstract:
        field = 'abstract'
        cmdpat_head = ut.named_field('cmdhead', field + r' = {')
        valpat1 = ut.named_field(field, '[^}]*')
        valpat2 = ut.named_field(field, '.*')
        cmdpat_tail1 = ut.named_field('cmdtail', '},? *\n')
        cmdpat_tail2 = ut.named_field('cmdtail', '}, *\n')

        field_pattern1 = cmdpat_head + valpat1 + cmdpat_tail1
        field_pattern1 = cmdpat_head + valpat2 + cmdpat_tail2

        def replace_func(match):
            groupdict_ = match.groupdict()
            oldval = groupdict_[field]
            newval = ' '.join(oldval.split(' ')[0:7])
            cmdhead = groupdict_['cmdhead']
            cmdtail = groupdict_['cmdtail']
            new_block = cmdhead + newval + cmdtail
            return new_block
        clean_text = re.sub(field_pattern1, replace_func, clean_text, flags=re.MULTILINE)
        clean_text = re.sub(field_pattern2, replace_func, clean_text, flags=re.MULTILINE)

    # Remove the {} around title words
    fix_titles = False
    if fix_titles:
        field = 'title'
        cmdpat_head = ut.named_field('cmdhead', field + r' = {')
        valpat1 = ut.named_field(field, '[^}]*')
        valpat2 = ut.named_field(field, '.*')
        cmdpat_tail1 = ut.named_field('cmdtail', '},? *\n')
        cmdpat_tail2 = ut.named_field('cmdtail', '}, *\n')

        field_pattern1 = cmdpat_head + valpat1 + cmdpat_tail1
        field_pattern1 = cmdpat_head + valpat2 + cmdpat_tail2

        def replace_func(match):
            groupdict_ = match.groupdict()
            oldval = groupdict_[field]
            newval = oldval.replace('}', '').replace('{', '')
            cmdhead = groupdict_['cmdhead']
            cmdtail = groupdict_['cmdtail']
            new_block = cmdhead + newval + cmdtail
            return new_block
        clean_text = re.sub(field_pattern1, replace_func, clean_text, flags=re.MULTILINE)
        clean_text = re.sub(field_pattern2, replace_func, clean_text, flags=re.MULTILINE)

    if False:
        # Remove invalid characters from the bibtex tags
        bad_tag_characters = [':', '-']
        # Find invalid patterns
        tag_repl_list = []
        for item_type in item_type_list:
            prefix = '@' + item_type + '{'   # }
            header_search = prefix + ut.named_field('bibtex_tag', '[^,]*')
            matchiter = re.finditer(header_search, clean_text)
            for match in matchiter:
                groupdict_ = match.groupdict()
                bibtex_tag = groupdict_['bibtex_tag']
                for char in bad_tag_characters:
                    if char in bibtex_tag:
                        # if char == ':':
                        #     print('FIX: bibtex_tag = %r' % (bibtex_tag,))
                        bibtex_tag_old = bibtex_tag
                        bibtex_tag_new = bibtex_tag.replace(char, '')
                        repltup = (bibtex_tag_old, bibtex_tag_new)
                        tag_repl_list.append(repltup)
                        bibtex_tag = bibtex_tag_new
        # Replace invalid patterns
        for bibtex_tag_old, bibtex_tag_new in tag_repl_list:
            clean_text = clean_text.replace(bibtex_tag_old, bibtex_tag_new)
"""


def main(bib_fpath=None):
    r"""
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

    if exists('custom_extra.bib'):
        dirty_text += '\n'
        dirty_text += ut.read_from('custom_extra.bib')

    #udata = dirty_text.decode("utf-8")
    #dirty_text = udata.encode("ascii", "ignore")
    #dirty_text = udata

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
    from fixtex.mass_tex_fixes import find_used_citations, get_thesis_tex_fpaths
    verbose = None
    if verbose is None:
        verbose = 1

    # Find citations from the tex documents
    key_list = None
    if key_list is None:
        fpaths = get_thesis_tex_fpaths()
        key_list, inverse = find_used_citations(fpaths, return_inverse=True)
        ignore = ['JP', '?', 'hendrick']
        for item in ignore:
            try:
                key_list.remove(item)
            except ValueError:
                pass
        if verbose:
            print('Found %d citations used in the document' % (len(key_list),))
    # else:
    #     key_list = None

    unknown_confkeys = []
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
        ut.fix_embed_globals()
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

    for key in key_list:
        try:
            entry = bibtex_dict[key]
        except KeyError:
            continue
        self = BibTexCleaner(key, entry)

        if debug_author is not None:
            debug = debug_author in entry.get('author', '')

        if debug:
            ut.cprint(' --- ENTRY ---', 'yellow')
            print(ut.repr3(entry))

        self.clip_abstract()
        self.shorten_keys()
        self.fix_authors()
        old_confval = self.fix_confkey()
        if old_confval:
            unknown_confkeys.append(old_confval)
        # self.fix_paper_types()

        if debug:
            print(ut.repr3(self.entry))
            ut.cprint(' --- END ENTRY ---', 'yellow')
        bibtex_dict[key] = self.entry

    unwanted_keys = set(bibtex_dict.keys()) - set(key_list)
    if verbose:
        print('Removing unwanted %d entries' % (len(unwanted_keys)))
    ut.delete_dict_keys(bibtex_dict, unwanted_keys)

    # Overwrite BibDatabase structure
    bib_database._entries_dict = bibtex_dict
    bib_database.entries = list(bibtex_dict.values())

    #conftitle_to_types_set_hist = {key: set(val) for key, val in conftitle_to_types_hist.items()}
    #print(ut.dict_str(conftitle_to_types_set_hist))

    print('Unknown conference keys:')
    print(ut.list_str(sorted(unknown_confkeys)))
    print('len(unknown_confkeys) = %r' % (len(unknown_confkeys),))

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
