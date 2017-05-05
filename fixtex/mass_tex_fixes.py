#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
References:
    http://www.cogsci.nl/blog/tutorials/97-writing-a-command-line-zotero-client-in-9-lines-of-code

    pip install pygnotero
    pip install git+https://github.com/smathot/Gnotero.git

CommandLine:

    ./mass_tex_fixes.py --findcite

    ./mass_tex_fixes.py --fixcap --dryrun

"""
from __future__ import absolute_import, division, print_function, unicode_literals
import re
import utool as ut
import six
import bibtexparser
import logging
import logging.config
from fixtex import constants_tex_fixes
from fixtex.latex_parser import LatexDocPart
print, rrr, profile = ut.inject2(__name__, '[masstexfix]')


#def fix_acronmy_capitlaization():
#    ACRONYMN_LIST
#    text = ut.read_from(tex_fpath)
#    text

logger = logging.getLogger(__name__)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s:%(lineno)d: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'WARNING',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'WARNING',
            'formatter': 'standard',
            'propagate': True
        }
    }
})


def check_for_informal_words():
    """
    these are words I will really tend to use a whole lot when I probably
    should never use these words in a formal document
    """

    informal_word_list = [
        'much',
        'very',
        'really',
        'will',
    ]

    for word in informal_word_list:
        pass


def conjugate_stuff():
    """
    References:
        http://stackoverflow.com/questions/18942096/how-to-conjugate-a-verb-in-nltk-given-pos-tag
        pattern.en.conjugate(
            verb,
            tense="past",           # INFINITIVE, PRESENT, PAST, FUTURE
            person=3,               # 1, 2, 3 or None
            number="singular",      # SG, PL
            mood="indicative",      # INDICATIVE, IMPERATIVE, CONDITIONAL, SUBJUNCTIVE
            aspect="imperfective",  # IMPERFECTIVE, PERFECTIVE, PROGRESSIVE
            negated=False)          # True or False
    """
    import pattern.en
    verb = 'score'
    multi_dict = dict(
        mood=['indicative', 'imperative', 'conditional', 'subjunctive'],
        person=[1, 2, 3],  # , None],
        #number=['sg', 'pl'],
        aspect=['imperfective', 'perfective', 'progressive'],
        #negated=[False, True],
    )

    text = 'name score'
    for conjkw in ut.all_dict_combinations(multi_dict):
        words = text.split(' ')
        verb = words[-1]
        conj_verb = pattern.en.conjugate(verb, **conjkw)
        if conj_verb is not None:
            newtext = ' '.join(words[1:-1] + [conj_verb] if len(words) > 1 else [conj_verb])
            print(newtext)
            print(conjkw)
            print(conj_verb)


def find_citations(text):
    """
    tex_fpath = 'chapter1-intro.tex'
    """

    # remove comments
    text = re.sub('%.*', '', text)

    pattern = 'cite{' + ut.named_field('contents', '[^}]*') + '}'
    citekey_list = []
    for match in re.finditer(pattern, text, re.MULTILINE | re.DOTALL):
        contents = match.groupdict()['contents']
        #match.string[match.start():match.end()]
        citekey_list.extend(contents.replace(' ', '').replace('\n', '').split(','))
    return citekey_list


def fix_section_title_capitalization(tex_fpath, dryrun=True):
    # Read in text and ensure ascii format
    text = ut.read_from(tex_fpath)

    section_type_list = [
        'chapter',
        'section',
        'subsection',
        'subsubsection',
        'paragraph',
    ]
    re_section_type = ut.named_field('section_type', ut.regex_or(section_type_list))
    re_section_title = ut.named_field('section_title', '[^}]*')

    re_spaces = ut.named_field('spaces', '^ *')

    pattern = re_spaces + re.escape('\\') + re_section_type + '{' + re_section_title + '}'

    def fix_capitalization(match):
        dict_ = match.groupdict()
        section_title = dict_['section_title']
        #if section_title == 'The Great Zebra Count':
        #    return match.string[slice(*match.span())]
        #    #return 'The Great Zebra Count'
        # general logic
        #words = section_title.split(' ')
        tokens = re.split(ut.regex_or([' ', '/']), section_title)
        #if 'Coverage' in section_title:
        #    ut.embed()
        #    pass
        #words = [word if count == 0 else word.lower() for count, word in enumerate(words)]
        #new_section_title = ' '.join(words)
        tokens = [t if count == 0 else t.lower() for count, t in enumerate(tokens)]
        new_section_title = ''.join(tokens)

        # hacks for caps of expanded titles
        search_repl_list = constants_tex_fixes.CAPITAL_TITLE_LIST
        for repl in search_repl_list:
            new_section_title = re.sub(re.escape(repl), repl,
                                       new_section_title, flags=re.IGNORECASE)
        # hacks fo acronyms
        for full, acro in constants_tex_fixes.ACRONYMN_LIST:
            new_section_title = re.sub(r'\b' + re.escape(acro) + r'\b', acro,
                                       new_section_title, flags=re.IGNORECASE)

        #'the great zebra and giraffe count'

        #new_section_title = section_title.lower()
        new_text = dict_['spaces'] + '\\' + dict_['section_type'] + '{' + new_section_title + '}'
        VERBOSE = True
        if VERBOSE:
            old_text = match.string[slice(*match.span())]
            if new_text != old_text:
                print(ut.dict_str(dict_))
                print('--- REPL ---')
                print(old_text)
                print(new_text)
        return new_text

    #for match in re.finditer(pattern, text, flags=re.MULTILINE):
    #    fix_capitalization(match)

    new_text = re.sub(pattern, fix_capitalization, text, flags=re.MULTILINE)

    if not dryrun:
        ut.write_to(tex_fpath, new_text)
    else:
        ut.print_difftext(ut.get_textdiff(text, new_text, 0))
    #print(new_text[0:100])


def fix_section_common_errors(tex_fpath, dryrun=True):
    # Read in text and ensure ascii format
    text = ut.read_from(tex_fpath)

    new_text = text
    # Fix all capitals
    search_repl_list = constants_tex_fixes.CAPITAL_LIST
    for repl in search_repl_list:
        pattern = ut.regex_word(re.escape(repl))
        new_text = re.sub(pattern, repl, new_text, flags=re.IGNORECASE)
    #new_text = re.sub(pattern, fix_capitalization, text, flags=re.MULTILINE)

    if not dryrun:
        ut.write_to(tex_fpath, new_text)
    else:
        ut.print_difftext(ut.get_textdiff(text, new_text, 0))


def find_used_citations(tex_fpath_list, return_inverse=False):
    citekey_list = []
    inverse = ut.ddict(list)
    for tex_fpath in tex_fpath_list:
        text = ut.read_from(tex_fpath)
        #print('\n\n+-----')
        local_cites = find_citations(text)
        citekey_list.extend(local_cites)
        for key in local_cites:
            inverse[key].append(tex_fpath)

    citekey_list = sorted(set(citekey_list))
    if return_inverse:
        return citekey_list, inverse
    else:
        return citekey_list


def get_thesis_tex_fpaths():
    """
    Grabs tex files that are relevant to the document.
    (Ideally, but this is super hacked for me right now)
    """
    dpath = '.'
    #tex_fpath_list = ut.ls(dpath, 'chapter*.tex') + ut.ls(dpath, 'appendix.tex')
    patterns = [
        'chapter*.tex',
        'sec-*.tex',
        'figdef*.tex',
        'def.tex',
        'main.tex',
        'graph_id.tex',
    ]
    exclude_dirs = ['guts']
    tex_fpath_list = sorted(
        ut.glob(dpath, patterns, recursive=True, exclude_dirs=exclude_dirs)
    )
    tex_fpath_list = ut.get_argval('--fpaths', type_=list, default=tex_fpath_list)
    return tex_fpath_list


def findcite():
    """
    prints info about used and unused citations
    """
    tex_fpath_list = get_thesis_tex_fpaths()
    citekey_list = find_used_citations(tex_fpath_list)

    # Find uncited entries
    #bibtexparser = ut.tryimport('bibtexparser')
    bib_fpath = 'My_Library_clean.bib'
    bibtex_str = ut.read_from(bib_fpath)
    bib_database = bibtexparser.loads(bibtex_str)
    bibtex_dict = bib_database.get_entry_dict()

    for key in bibtex_dict.keys():
        entry = bibtex_dict[key]
        entry = ut.map_dict_keys(six.text_type, entry)
        entry = ut.map_dict_keys(six.text_type.lower, entry)
        bibtex_dict[key] = entry

    print('ALL')
    ignore = ['JP', '?']
    citekey_list = ut.setdiff_ordered(sorted(ut.unique_keep_order2(citekey_list)), ignore)
    #print(ut.indentjoin(citekey_list))
    print('len(citekey_list) = %r' % (len(citekey_list),))

    unknown_keys = list(set(citekey_list) - set(bibtex_dict.keys()))
    unused_keys = list(set(bibtex_dict.keys()) - set(citekey_list))

    try:
        if len(unknown_keys) != 0:
            print('\nUNKNOWN KEYS:')
            print(ut.list_str(unknown_keys))
            raise AssertionError('unknown keys')
    except AssertionError as ex:
        ut.printex(ex, iswarning=True, keys=['unknown_keys'])

    @ut.argv_flag_dec(indent='    ')
    def close_keys():
        if len(unknown_keys) > 0:
            bibtex_dict.keys()
            print('\nDid you mean:')
            for key in unknown_keys:
                print('---')
                print(key)
                print(ut.closet_words(key, bibtex_dict.keys(), 3))
            print('L___')
        else:
            print('no unkown keys')
    close_keys()

    @ut.argv_flag_dec(indent='    ')
    def print_unused():
        print(ut.indentjoin(ut.sortedby(unused_keys, map(len, unused_keys))))

        print('len(unused_keys) = %r' % (len(unused_keys),))
    print_unused()

    all_authors = []
    for key in bibtex_dict.keys():
        entry = bibtex_dict[key]
        toremove = ['author', '{', '}', r'\\textbackslash']
        author = ut.multi_replace(entry.get('author', ''), toremove, '')
        authors = author.split(' and ')
        all_authors.extend(authors)

    @ut.argv_flag_dec(indent='    ')
    def author_hist():
        #print(all_authors)
        hist_ = ut.dict_hist(all_authors, ordered=True)
        hist_[''] = None
        del hist_['']
        print('Author histogram')
        print(ut.dict_str(hist_)[-1000:])
    author_hist()

    @ut.argv_flag_dec(indent='    ')
    def unused_important():
        important_authors = [
            'hinton',
            'chum',
            'Jegou',
            'zisserman',
            'schmid',
            'sivic',
            'matas',
            'lowe',
            'perronnin',
            'douze',
        ]

        for key in unused_keys:
            entry = bibtex_dict[key]
            author = entry.get('author', '')
            #authors = author.split(' and ')
            hasimportant = any(auth in author.lower() for auth in important_authors)
            if hasimportant or 'smk' in str(entry).lower():
                toremove = ['note', 'month', 'type', 'pages', 'urldate',
                            'language', 'volume', 'number', 'publisher']
                entry = ut.delete_dict_keys(entry, toremove)
                print(ut.dict_str(entry, strvals=True,
                                  key_order=['title', 'author', 'id']))
    unused_important()
    #print('\n\nEND FIND CITE')


if __name__ == '__main__':
    #dryrun = ut.get_argflag('--dryrun')
    dryrun = not ut.get_argflag('-w')
    if dryrun:
        print('dryrun=True, specify --w to save any changes')
    find_text = ut.get_argval('--grep')
    if find_text is not None:
        tup = ut.grep(find_text,
                      fpath_list=get_thesis_tex_fpaths(),
                      verbose=True)
        found_fpath_list, found_lines_list, found_lxs_list = tup
    else:
        print('~~~ --grep [text] ~~~')

    findrepl = ut.get_argval('--sed', type_=list, default=None)
    if findrepl is not None:
        assert len(findrepl) == 2, 'must specify a search and replace'
        search, repl = findrepl
        tup = ut.sed(search, repl, fpath_list=get_thesis_tex_fpaths(),
                     verbose=True, force=not dryrun)

    @ut.argv_flag_dec(indent='    ')
    def fix_common_errors():
        for tex_fpath in get_thesis_tex_fpaths():
            fix_section_common_errors(tex_fpath, dryrun)

    @ut.argv_flag_dec(indent='    ')
    def fixcap():
        for tex_fpath in get_thesis_tex_fpaths():
            fix_section_title_capitalization(tex_fpath, dryrun)

    @ut.argv_flag_dec(indent='    ')
    def glossterms():
        re_glossterm = ut.named_field('glossterm', '.' + ut.REGEX_NONGREEDY)
        pat = r'\\glossterm{' + re_glossterm + '}'
        tup = ut.grep(pat, fpath_list=get_thesis_tex_fpaths(), verbose=True)
        found_fpath_list, found_lines_list, found_lxs_list = tup
        glossterm_list = []
        for line in ut.flatten(found_lines_list):
            match = re.search(pat, line)
            glossterm = match.groupdict()['glossterm']
            glossterm_list.append(glossterm)
        print('Glossary Terms: ')
        print(ut.repr2(ut.dict_hist(glossterm_list), nl=True, strvals=True))

    @ut.argv_flag_dec(indent='    ')
    def fix_chktex():
        import parse
        fpaths = ut.get_argval('--fpaths', type_=list, default=get_thesis_tex_fpaths())
        output_list = [ut.cmd('chktex', fpath, verbose=False)[0] for fpath in fpaths]

        for fpath, output in zip(fpaths, output_list):
            text = ut.readfrom(fpath)
            buffer = text.split('\n')
            pat = '\n' + ut.positive_lookahead('Warning')
            warn_list = list(filter(lambda x: x.startswith('Warning'), re.split(pat, output)))
            delete_linenos = []

            fixcite = ut.get_argflag('--fixcite')
            fixlbl = ut.get_argflag('--fixlbl')
            fixcmdterm = ut.get_argflag('--fixcmdterm')
            if not (fixcmdterm or fixlbl or fixcite):
                print(' CHOOSE A FIX ')

            modified_lines = []

            for warn in warn_list:
                warnlines = warn.split('\n')
                pres = parse.parse('Warning {num} in {fpath} line {lineno}: {warnmsg}', warnlines[0])
                if pres is not None:
                    fpath_ = pres['fpath']
                    lineno = int(pres['lineno']) - 1
                    warnmsg = pres['warnmsg']
                    try:
                        assert fpath == fpath_, ('%r != %r' % (fpath, fpath_))
                    except AssertionError:
                        continue
                    if 'No errors printed' in warn:
                        #print('Cannot fix')
                        continue
                    if lineno in modified_lines:
                        print('Skipping modified line')
                        continue
                    if fixcmdterm and warnmsg == 'Command terminated with space.':
                        print('Fix command termination')
                        errorline = warnlines[1]  # NOQA
                        carrotline = warnlines[2]
                        pos = carrotline.find('^')
                        if 0:
                            print('pos = %r' % (pos,))
                            print('lineno = %r' % (lineno,))
                            print('errorline = %r' % (errorline,))
                        modified_lines.append(lineno)
                        line = buffer[lineno]
                        pre_, post_ = line[:pos], line[pos + 1:]
                        newline = (pre_ + '{} ' + post_).rstrip(' ')
                        #print('newline   = %r' % (newline,))
                        buffer[lineno] = newline
                    elif fixlbl and warnmsg == 'Delete this space to maintain correct pagereferences.':
                        print('Fix label newline')
                        fpath_ = pres['fpath']
                        errorline = warnlines[1]  # NOQA
                        new_prevline = buffer[lineno - 1].rstrip() + errorline.lstrip(' ')
                        buffer[lineno - 1] = new_prevline
                        modified_lines.append(lineno)
                        delete_linenos.append(lineno)
                    elif fixcite and re.match('Non-breaking space \\(.~.\\) should have been used', warnmsg):
                        #print(warnmsg)
                        #print('\n'.join(warnlines))
                        print('Fix citation space')
                        carrotline = warnlines[2]
                        pos = carrotline.find('^')
                        modified_lines.append(lineno)
                        line = buffer[lineno]
                        if line[pos] == ' ':
                            pre_, post_ = line[:pos], line[pos + 1:]
                            newline = (pre_ + '~' + post_).rstrip(' ')
                        else:
                            pre_, post_ = line[:pos + 1], line[pos + 1:]
                            newline = (pre_ + '~' + post_).rstrip(' ')
                            print(warn)
                            print(line[pos])
                            assert False
                            #assert line[pos] == ' ', '%r' % line[pos]
                            break
                        if len(pre_.strip()) == 0:
                            new_prevline = buffer[lineno - 1].rstrip() + newline.lstrip(' ')
                            buffer[lineno - 1] = new_prevline
                            delete_linenos.append(lineno)
                        else:
                            #print('newline   = %r' % (newline,))
                            buffer[lineno] = newline
                    #print(warn)

            if len(delete_linenos) > 0:
                mask = ut.index_to_boolmask(delete_linenos, len(buffer))
                buffer = ut.compress(buffer, ut.not_list(mask))
            newtext = '\n'.join(buffer)

            #ut.dump_autogen_code(fpath, newtext, 'tex', fullprint=False)
            ut.print_difftext(ut.get_textdiff(text, newtext, num_context_lines=4))
            if ut.get_argflag('-w'):
                ut.writeto(fpath, newtext)
            else:
                print('Specify -w to finialize change')

    @ut.argv_flag_dec(indent='    ')
    def reformat():
        """
        ./mass_tex_fixes.py --reformat --fpaths NewParts.tex
        >>> from mass_tex_fixes import *  # NOQA
        """
        #import parse
        default = get_thesis_tex_fpaths()
        #default = ['NewParts.tex']
        fpaths = ut.get_argval('--fpaths', type_=list, default=default)
        #import numpy as np

        for fpath in fpaths:
            text = ut.readfrom(fpath)
            root = LatexDocPart.parse_latex(text, debug=0)

            #print(root.children)
            #root.children = root.children[0:5]
            #print('Parsed Str Full')
            #ut.colorprint(root.tostr(True), 'red')
            #print('Parsed Str Short')
            new_text = '\n'.join(root.reformat_blocks(debug=0))
            # remove trailing spaces
            new_text = re.sub(' *$', '', new_text, flags=re.MULTILINE)
            # remove double newlines
            new_text = re.sub('(\n *)+\n+', '\n\n', new_text, flags=re.MULTILINE)

            if ut.get_argflag('--outline'):
                #ut.colorprint(root.summary_str(outline=True), 'yellow')
                print('---outline---')
                summary = ut.highlight_text(root.summary_str(outline=True), 'latex')
                summary = ut.highlight_regex(summary, r'^[a-z.]+ *\(...\)', reflags=re.MULTILINE, color='darkyellow')
                print(summary)
                print('---/outline---')
            else:
                print('---summary---')
                print(ut.highlight_text(root.summary_str(outline=False), 'latex'))
                print('---/summary---')
                # ut.colorprint(root.summary_str(), 'blue')

            numchars1 = len(text.replace(' ', '').replace('\n', ''))
            numchars2 = len(new_text.replace(' ', '').replace('\n', ''))

            print('numchars1 = %r' % (numchars1,))
            print('numchars2 = %r' % (numchars2,))
            #assert numchars1 == numchars2, '%r == %r' % (numchars1, numchars2)

            print('old newlines = %r' % (text.count('\n'),))
            print('new newlines = %r' % (new_text.count('\n'),))
            # len(text)
            # len(new_text)

            #ut.print_code(new_text, 'latex')
            #import utool
            #import unicodedata
            #new_text = unicodedata.normalize('NFKD', new_text).encode('ascii','ignore')
            #print('new_text = %r' % (new_text,))


            ut.dump_autogen_code(fpath, new_text, codetype='latex', fullprint=False)
            #indents = np.array([ut.get_indentation(line) for line in buffer])
            #bad_lines = (indents % 2) != 0

            #print('\n'.join(ut.compress(buffer, bad_lines)))

    @ut.argv_flag_dec(indent='    ')
    def outline():
        #import parse
        default = get_thesis_tex_fpaths()
        #default = ['NewParts.tex']
        fpaths = ut.get_argval('--fpaths', type_=list, default=default)
        #import numpy as np

        for fpath in fpaths:
            text = ut.readfrom(fpath)
            root = LatexDocPart.parse_latex(text, debug=0)

            new_text = '\n'.join(root.reformat_blocks(debug=0))
            # remove trailing spaces
            new_text = re.sub(' *$', '', new_text, flags=re.MULTILINE)
            # remove double newlines
            new_text = re.sub('(\n *)+\n+', '\n\n', new_text, flags=re.MULTILINE)

            #ut.colorprint(root.summary_str(outline=True), 'yellow')
            print('---outline---')
            outline_text = root.summary_str(outline=True)
            summary = ut.highlight_text(outline_text, 'latex')
            summary = ut.highlight_regex(summary, r'^[a-z.]+ *\(...\)', reflags=re.MULTILINE, color='darkyellow')
            if not ut.get_argflag('-w'):
                print(summary)
            print('---/outline---')

            ut.dump_autogen_code(ut.augpath(fpath, augpref='outline_'), outline_text, codetype='latex', fullprint=False)

    @ut.argv_flag_dec(indent='    ')
    def tozip():
        re_fpath = ut.named_field('fpath', 'figure.*?[jp][pn]g') + '}'
        patterns = ['chapter4-application.tex', 'figdef4*', 'main.tex', 'def.tex', 'Crall*', 'thesis.cls', 'header*', 'colordef.tex', '*.bib']
        exclude_dirs = ['guts']
        fpaths = sorted(
            ut.glob('.', patterns, recursive=True, exclude_dirs=exclude_dirs)
        )

        tup = ut.grep(re_fpath, fpath_list=fpaths, verbose=True)
        found_fpath_list, found_lines_list, found_lxs_list = tup
        fig_fpath_list = []
        for line in ut.flatten(found_lines_list):
            if not line.startswith('%'):
                for match in re.finditer(re_fpath, line):
                    fig_fpath = match.groupdict()['fpath']
                    if 'junc' not in fig_fpath and 'markov' not in fig_fpath and 'bayes' not in fig_fpath:
                        fig_fpath_list += [fig_fpath]

        fpath_list = fig_fpath_list + fpaths
        ut.archive_files('chap4.zip', fpath_list)

    fix_common_errors()
    fixcap()
    glossterms()
    fix_chktex()
    reformat()
    outline()
    tozip()

    ut.argv_flag_dec(findcite, indent='    ')()

    print('Use --fpaths to specify specific files')

    """
    ./mass_tex_fixes.py --reformat --fpaths chapter4-application.tex
    ./mass_tex_fixes.py --fix-chktex --fixcmdterm
    ./mass_tex_fixes.py --fix-chktex --fixcite --fpaths old-chapter4-application.tex
    ./mass_tex_fixes.py --fix-chktex --fixlbl --fpaths old-chapter4-application.tex
    ./mass_tex_fixes.py --reformat --fpaths old-chapter4-application.tex
    ./mass_tex_fixes.py --outline --fpaths old-chapter4-application.tex
    ./mass_tex_fixes.py --grep " encounter "

    ./mass_tex_fixes.py --dryrun --fixcap
    ./mass_tex_fixes.py

    ./mass_tex_fixes.py --findcite


    ./mass_tex_fixes.py --fixcap

    ./mass_tex_fixes.py --fix-common-errors --dryrun

    from mass_tex_fixes import *

    pip install bibtexparser


    # TODO: Rectify number styles
    # http://tex.stackexchange.com/questions/38820/numbers-outside-math-environment

    ./mass_tex_fixes.py --grep " \\d+,?\\d* "

    ./mass_tex_fixes.py --grep "\\$\\d+,?\\d*\\$"
    ./mass_tex_fixes.py --grep "\<three\>"
    ./mass_tex_fixes.py --grep "\<two\>"
    ./mass_tex_fixes.py --grep "\<one\>"

    ./mass_tex_fixes.py --grep "\c\<we\>"
    ./mass_tex_fixes.py --grep "\c\<us\>"

    ./mass_tex_fixes.py --grep "encounter"
    ./mass_tex_fixes.py --grep "figure.*[jp][pn]g"

    ./mass_tex_fixes.py --sed "\<encounter\>" "occurrence" -w
    ./mass_tex_fixes.py --sed "\<encountername\>" "occurrencename"
    ./mass_tex_fixes.py --sed "Encounter" "Occurrence"
    ./mass_tex_fixes.py --sed "occurence" "occurrence"
    ./mass_tex_fixes.py --sed "intraencounter" "intraoccurrence"
    ./mass_tex_fixes.py --sed "Intraencounter" "Intraoccurrence" -w

    >>> from mass_tex_fixes import *  # NOQA
    """
