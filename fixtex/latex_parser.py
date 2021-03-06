"""
./texfix.py --reformat --outline  --fpaths chapter4-application.tex
./texfix.py --reformat --fpaths chapter4-application.tex --print
./texfix.py --reformat --outline  --fpaths testchap.tex

./texfix.py --fpaths chapter4-application.tex --reformat

./texfix.py --fpaths chapter4-application.tex --outline --showtype --numlines
./texfix.py --fpaths chapter4-application.tex --outline --showtype --numlines --singleline
./texfix.py --fpaths chapter4-application.tex --outline --showtype --numlines --singleline | less -R


./texfix.py --fpaths chapter4-application.tex --outline --noshowtype --numlines --singleline --noindent

./texfix.py --fpaths chapter4-application.tex --outline --showtype --numlines --singleline --noindent

./texfix.py --fpaths chapter4-application.tex --outline --numlines --singleline --keeplabel --fpaths figdef1.tex

# Write outline for entire thesis
./texfix.py --outline --keeplabel -w

./texfix.py --outline --keeplabel --fpaths chapter*.tex --numlines --singleline -w
./texfix.py --outline --keeplabel --fpaths chapter2-related-work.tex --numlines --singleline -w
./texfix.py --outline --keeplabel --fpaths chapter1-intro.tex  -w
./texfix.py --outline --keeplabel --fpaths figdef1.tex -w
./texfix.py --outline --keeplabel --fpaths figdef1.tex --showtype

./texfix.py --outline --keeplabel --fpaths sec-3-4-expt.tex --showtype --debug-latex


./texfix.py --outline --keeplabel --fpaths sec-2-1-featdetect.tex --print --showtype --debug-latex
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import re
import utool as ut
print, rrr, profile = ut.inject2(__name__)


RE_TEX_COMMENT = ut.negative_lookbehind(re.escape('\\')) + re.escape('%') + '.*$'
RE_VARNAME = ut.REGEX_VARNAME


def find_nth_pos(str_, list_, n):
    pos_list = [[m.start() for m in re.finditer(c, str_)] for c in list_]
    # print(repr(re.escape(c)))
    pos_list = sorted(ut.flatten(pos_list))
    # pos_list = [str_.find(c) for c in list_]
    # pos_list = [p for p in pos_list if p > -1]
    if len(pos_list) >= n:
        return pos_list[n - 1]
    else:
        return len(str_)


@ut.memoize
def hack_read_figdict():
    fig_defs = [
        LatexDocPart.parse_fpath('figdef1.tex'),
        LatexDocPart.parse_fpath('figdef2.tex'),
        LatexDocPart.parse_fpath('figdef3.tex'),
        LatexDocPart.parse_fpath('figdef4.tex'),
        LatexDocPart.parse_fpath('figdef5.tex'),
        # LatexDocPart.parse_fpath('figdefexpt.tex'),
        # LatexDocPart.parse_fpath('figdefindiv.tex'),
        # LatexDocPart.parse_fpath('figdefdbinfo.tex'),
    ]
    # figdict = figdef1.parse_figure_captions()
    figdict = ut.dict_union(*[f.parse_figure_captions()[0] for f in fig_defs])
    return figdict


class _Reformater(object):

    _config = ut.argparse_dict({
            #'skip_subtypes': ['comment', 'def'],
            'skip_subtypes': ['comment', 'devmark'],
            'skip_types': ['comment', 'keywords', 'outline', 'devnewpage',
                           'devcomment', 'renewcommand', 'newcommand', 'setcounter',
                           'bibliographystyle', 'bibliography'],
            'numlines': 0,
            'max_width': 120,
            'nolabel': True,
            'showtype': False,
            'asmarkdown': False,
            'includeon': True,
            'full': [],
            'remove_leading_space': True,
            #skip_subtypes = ['comment']
    })

    def _put_debug_type(self, block, outline=False):
        """
        Prefixes a summary block with parser debuging information
        """
        show_type = not outline or self._config['showtype']
        # show_type = True
        if show_type:
            type_just = 20
            type_str = self.type_
            if self.subtype is not None:
                type_str += '.' + self.subtype
            type_part = type_str.ljust(15) + ('(%3d)' % (len(self.lines)))
            block = ut.hz_str(type_part.ljust(type_just) + ' ', block)
        return block

    def in_full_outline_section(self, outline):
        if outline:
            fullformat_types = self._config['full']
        else:
            fullformat_types = []
        container_type = self.get_ancestor(TexNest.toc_heirarchy).type_
        return container_type in fullformat_types

    def _summary_headerblocks(self, outline=False, numlines=None):
        """
        Create a new formatted headerblock for the node summary string
        """

        if len(self.lines) == 0:
            return []
        elif self.type_ == 'lines':
            header_block = self.get_lines(outline, numlines=numlines)
        else:
            header_block = self.get_header(outline)
        header_block = self._put_debug_type(header_block, outline)
        header_blocks = [header_block]
        return header_blocks

    def is_header(self):
        return self.type_ in TexNest.toc_heirarchy

    def get_lines(self, outline=False, numlines=None, nolabel=None,
                  asmarkdown=None):
        if numlines is None:
            numlines = self._config['numlines']
        if nolabel is None:
            nolabel = self._config['nolabel']
        if asmarkdown is None:
            asmarkdown = self._config['asmarkdown']

        # Use ... to represent lines unless a full reformat is requested for outline
        if self.in_full_outline_section(outline):
            header_block = ut.unindent('\n'.join(self.reformat_blocks(stripcomments=False)))
        elif numlines == 0:
            if self.type_ == 'lines' and self.parent.type_ in TexNest.listables:
                header_block = ''
            else:
                if self.subtype == 'space':
                    header_block = ''
                else:
                    header_block = '...'
        else:
            #header_block = '\ldots'
            if self.subtype == 'space':
                header_block = ''
            else:
                if asmarkdown:
                    header_block = '\n'.join(self._local_sentences())
                else:
                    header_block = ut.unindent('\n'.join(self.reformat_blocks(stripcomments=False)))

            if numlines >= 1 and self.subtype == 'par':
                if self.parent_type() in TexNest.rawformat_types:
                    #if self.parent.type_ == 'pythoncode*':
                    # hack to not do next hack for pythoncode
                    header_block = '\n'.join(self.lines)
                else:
                    # hack to return the n sentences from every paragrpah
                    pos = find_nth_pos(header_block, ['\\.',  ':\r'], numlines)
                    header_block = header_block[:pos + 1]

        # only remove labels from ends of nonempty lines
        if nolabel:
            pref = ut.positive_lookbehind('[^ ]')
            header_block = re.sub(pref + '\\\\label{.*$', '', header_block, flags=re.MULTILINE)

        header_block = ut.unindent(header_block)
        if asmarkdown:
            pass
        else:
            header_block = ut.indent(header_block, ('    ' * self.level))
        # header_block = ut.indent(ut.unindent(header_block), ('    ' * self.level))
        return header_block

    def get_header(self, outline=False, nolabel=None, asmarkdown=None,
                   max_width=None):

        if max_width is None:
            max_width = self._config['max_width']
        if nolabel is None:
            max_width = self._config['nolabel']
        if asmarkdown is None:
            max_width = self._config['asmarkdown']

        if outline:
            # Print introduction
            # allow_multiline_headers = True
            allow_multiline_headers = False
        else:
            allow_multiline_headers = False

        if self.is_header():
            header_block = self.lines[0]
        else:
            if allow_multiline_headers and len(self.lines) > 1:
                # Header is multiline
                header_block = '\n'.join(self.lines)
                max_width = max_width
                header_block = ut.format_multi_paragraphs(header_block,
                                                          myprefix=True,
                                                          sentence_break=True,
                                                          max_width=max_width)
                # HACKS FOR PERSONAL STUFF
                if self.type_ == 'ImageCommand':
                    header_block = header_block.replace('ImageCommand', 'ImageCommandDraft')
                if self.type_ == 'MultiImageFigure':
                    header_block = header_block.replace('MultiImageFigure', 'MultiImageFigureDraft')
                if self.type_ == 'MultiImageFigureII':
                    header_block = header_block.replace('MultiImageFigureII', 'MultiImageFigureDraft')
            else:
                header_block = self.lines[0]

        if nolabel:
            # only remove labels from ends of nonempy lines
            pref = ut.positive_lookbehind('[^ ]')
            header_block = re.sub(pref + '\\\\label{.*$', '', header_block, flags=re.MULTILINE)
        header_block = ut.unindent(header_block)

        if asmarkdown:
            try:
                header_block = header_block.replace('\\%s{' % self.type_, '')

                if header_block.endswith('}'):
                    header_block = header_block[:-1]

                header_level = (TexNest.toc_heirarchy + ['paragraph']).index(self.type_) + 1

                if header_level == 1:
                    header_block =  header_block + '\n' + '=' * len(header_block)
                elif header_level == 2:
                    header_block =  header_block + '\n' + '-' * len(header_block)
                else:
                    header_block = ('#' * header_level) + ' ' + header_block
            except ValueError:
                if self.type_ in TexNest.listables:
                    header_block = ''
                elif self.type_ in ['item']:
                    header_block = header_block.replace('\\item', '*')
                elif self.type_ in ['equation']:
                    header_block = '\n$$'
                elif self.type_ in ['figure']:
                    header_block = '\n#### figure caption.'
                elif self.type_ in ['pythoncode*']:
                    header_block = '\n```python'
                else:
                    header_block = '\n'.join(self.lines)
                    # raise

        else:
            header_block = ut.indent(header_block, ('    ' * self.level))

        return header_block

    def _summary_footerblocks(self, outline=False):
        """
        Create a new formatted footerblock for the node summary string
        """
        if self._config['asmarkdown']:
            return []

        if len(self.footer) > 0:
            footer_block = '\n'.join([l.strip() for l in self.footer])
            footer_block = ut.indent(footer_block, '    ' * self.level)

            footer_block = self._put_debug_type(footer_block, outline)
            footer_blocks = [footer_block]
        else:
            footer_blocks = []
        return footer_blocks

    def _summary_childblocks(self, outline=False, depth=None, numlines=None):
        if depth is not None:
            depth = depth - 1
            if depth < 0:
                return []

        if outline:
            skip_types = self._config['skip_types']
            skip_subtypes =  self._config['skip_subtypes']
        else:
            skip_types = []
            skip_subtypes = []

        # Skip certain node types
        child_nodes = self.children
        def is_skiptype(node):
            return node.type_ not in skip_types

        skip_type_flags = [is_skiptype(x)  for x in child_nodes]
        child_nodes = ut.compress(child_nodes, skip_type_flags)

        skip_subtype_flags = [x.subtype not in skip_subtypes for x in child_nodes]
        child_nodes = ut.compress(child_nodes, skip_subtype_flags)

        if self._config['remove_leading_space']:
            if len(child_nodes) > 2:
                # remove first space in each section
                if child_nodes[0].subtype == 'space':
                    child_nodes = child_nodes[1:]

        # Correct way to remove double spaces
        flags = [(count == 0 or count == len(child_nodes) - 1) or not (x.subtype == 'space' and y.subtype == 'space')
                 for count, (x, y) in enumerate(ut.itertwo(child_nodes, wrap=True))]
        child_nodes = ut.compress(child_nodes, flags)

        child_blocks = ut.flatten([child.summary_str_blocks(outline=outline,
                                                            depth=depth,
                                                            numlines=numlines)
                                   for child in child_nodes])
        return child_blocks

    def summary_str_blocks(self, outline=False, depth=None, numlines=None):
        """
        Recursive function that builds summary strings
        """

        header_blocks = self._summary_headerblocks(outline=outline, numlines=numlines)
        footer_blocks = self._summary_footerblocks(outline=outline)

        # Make child strings
        if self.type_ == 'figure' and outline:
            child_blocks = [self.get_caption()]
        elif self.type_ == 'equation' and outline:
            if self._config['asmarkdown']:
                # http://jaxedit.com/mark/
                footer_blocks = ['$$\n']
            else:
                header_blocks[0] += r'\end{equation}'
                child_blocks = []
                footer_blocks = []
            pass
        if self.type_ == 'pythoncode*' and outline:
            if self._config['asmarkdown']:
                footer_blocks = ['```\n']
            else:
                header_blocks[0] += r'\end{pythoncode*}'
                child_blocks = []
                footer_blocks = []
        else:
            child_blocks = self._summary_childblocks(outline=outline,
                                                     numlines=numlines,
                                                     depth=depth)

        block_parts = []
        block_parts += header_blocks
        block_parts += child_blocks
        block_parts += footer_blocks
        return block_parts

    def get_caption(self):
        assert self.type_ in {'figure', 'table'}

        child_blocks = self._summary_childblocks(outline=True, numlines=float('inf'))

        # child_blocks = ['this is a figure']
        text = '\n'.join(child_blocks)
        # match = re.search('\\\\caption\[[^\]]*\]{.*}(\n|\s)*\\label', text, flags=re.DOTALL)
        ref = ut.named_field
        try:
            match = re.search('\\\\capt[ie][ox][nt]\[.*\]{' + ref('caption', '.*?') +
                              '}(\n|\s)*\\\\label', text, flags=re.DOTALL)
            figcap = (match.groupdict()['caption'])
        except Exception:
            print('failed to parse')
            print(text)
            return self._summary_childblocks()
            raise
        figcap = re.sub('\\\\caplbl{[^}]*}', '', figcap).strip()
        if match is None:
            if ut.VERBOSE:
                child_blocks = [
                    ('WARNING match = %r\n' % (match,))
                    ('NONE DEF\n')
                    (str(self))
                ]
        else:
            return figcap
            child_blocks = [figcap]

    def summary_str(self, outline=False, highlight=False, depth=None,
                    hack_figdef=True, numlines=None):
        block_parts = self.summary_str_blocks(outline, depth=depth,
                                              numlines=numlines)
        summary = '\n'.join(block_parts)

        if outline:
            # Hack to deal with figures
            if self._config['includeon'] and self._config['asmarkdown']:
                if hack_figdef:
                    figdict = hack_read_figdict()
                    for key, val in figdict.items():
                        figcomment = strip_latex_comments(val)
                        figcomment = re.sub(r'\\caplbl{' + ut.named_field('inside', '.*?') + '}', '', figcomment)
                        # figcomment = '*' + '\n'.join(ut.split_sentences2(figcomment)) + '*'
                        figcomment = '\n'.join(ut.split_sentences2(figcomment))
                        figstr = '![`%s`](%s.jpg)' % (key, key) + '\n' + figcomment
                        # figstr = '![%s](figures1/%s.jpg)' % (figcomment, key)
                        summary = summary.replace('\\' + key + '{}', figstr)
            if self._config['asmarkdown']:
                summary = re.sub(r'\\rpipe{}', r'=>', summary)
                summary = re.sub(r'\\rarrow{}', r'->', summary)
                summary = re.sub(r'\\rmultiarrow{}', r'\\*->', summary)

            # hack to replace straightup definitions
            # TODO: read from def.tex
            cmd_map, cmd_map1 = self.read_static_defs()
            defmap = self.parse_newcommands()
            cmd_map.update(defmap.get(0, {}))
            cmd_map1.update(defmap.get(1, {}))

            #cmd_map = {}
            for key, val in cmd_map.items():
                summary = summary.replace(key + '{}', val)
                summary = summary.replace(key + '}', val + '}')  # hack

        # HACK for \\an
        def argrepl(match):
            firstchar = match.groups()[0][0]
            if firstchar.lower() in ['a', 'e', 'i', 'o', 'u']:
                astr = 'an'
            else:
                astr = 'a'
            if ut.get_match_text(match)[1] == 'A':
                astr = ut.to_camel_case(astr)
            argcmd_val = '%s #1' % (astr,)
            return argcmd_val.replace('#1', match.groupdict()['arg1'])

        # hand aan Aan
        pat = '\\\\[Aa]an{' + ut.named_field('arg1', '[ A-Za-z0-9_]*?') + '}'
        summary = re.sub(pat, argrepl, summary)

        #cmd_map = {}
        if outline:
            # Try and hack replace commands with one arg
            for key, val in cmd_map1.items():
                val_ = val.replace('\\', r'\\').replace('#1', ut.bref_field('arg1'))
                pat = '\\' + key + '{' + ut.named_field('arg1', '[ A-Za-z0-9_]*?') + '}'
                # re.search(pat, summary)
                # summary_ = summary
                summary = re.sub(pat, val_, summary)
            #cmd_map = {}
            for key, val in cmd_map.items():
                summary = summary.replace(key + '{}', val)
                summary = summary.replace(key + '}', val + '}')  # hack
                # Be very careful when replacing versions without curlies
                esckey = re.escape(key)
                keypat = esckey + '\\b'
                summary = re.sub(keypat, re.escape(val), summary)

            # Try and hack replace commands with one arg
            for key, val in cmd_map1.items():
                val_ = val.replace('\\', r'\\').replace('#1', ut.bref_field('arg1'))
                pat = '\\' + key + '{' + ut.named_field('arg1', '[ =,A-Za-z0-9_]*?') + '}'
                # re.search(pat, summary)
                #summary_ = summary
                summary = re.sub(pat, val_, summary)
                # if 'pvar' in key:
                #     if summary_ == summary:
                #         raise Exception('agg')

        if self._config['asmarkdown']:
            summary = re.sub(r'\\ensuremath', r'', summary)
            summary = re.sub(r'\\_', r'_', summary)
            summary = re.sub(r'\\ldots{}', r'...', summary)
            summary = re.sub(r'\\eg{}', r'e.g.', summary)
            summary = re.sub(r'\\Eg{}', r'E.g.', summary)
            # summary = re.sub(r'\\wrt{}', r'w.r.t.', summary)
            summary = re.sub(r'\\wrt{}', r'with respect to', summary)
            summary = re.sub(r'\\etc{}', r'etc.', summary)
            summary = re.sub(r'\\ie{}', r'i.e.', summary)
            summary = re.sub(r'\\st{}', r'-st', summary)
            summary = re.sub(r'\\nd{}', r'-nd', summary)
            # summary = re.sub(r'\\glossterm{', r'\\textbf{', summary)
            summary = re.sub(r'glossterm', r'textbf', summary)
            summary = re.sub(r'\\OnTheOrderOf{' + ut.named_field('inside', '.*?') + '}', '~10^{' + ut.bref_field('inside') + '}', summary)

            ref = ut.named_field
            bref = ut.bref_field

            SHORT_REF = ut.get_argflag('--shortcite')

            if SHORT_REF:
                summary = re.sub(
                    r'~\\cite(\[.*?\])?{' + ref('inside', '.*?') + '}',
                    ' (cite)',
                    summary)
            else:
                summary = re.sub(
                    r'~\\cite(\[.*?\])?{' + ref('inside', '.*?') + '}',
                    ' ![cite](' + bref('inside') + ')',
                    summary)
            # summary = re.sub(
            #     r'~\\cite\[.*?\]{' + ref('inside', '.*?') + '}',
            #     ' ![cite][' + bref('inside') + ']',
            #     summary)
            # summary = re.sub(r'~\\cite{' + ut.named_field('inside', '.*?') + '}', '', summary)
            # summary = re.sub(r'~\\cite\[.*?\]{' + ut.named_field('inside', '.*?') + '}', '', summary)

            counter = ut.ddict(dict)

            def parse_cref(match):
                if match.re.pattern.startswith('~'):
                    pref = ' '
                else:
                    pref = ''
                inside = match.groupdict()['inside']
                parts = inside.split(',')
                type_ = parts[0][0:parts[0].find(':')]
                if SHORT_REF:
                    parts2 = []
                    for p in parts:
                        t = p[0:p.find(':')]
                        c = counter[t]
                        if p not in c:
                            # c[p] = str(len(c) + 1)
                            c[p] = str(len(c) + 1)
                        parts2.append(c[p])
                    parts = parts2

                # phrase = '[' + ut.conj_phrase(parts, 'and') + ']()'
                if SHORT_REF:
                    phrase = ut.conj_phrase(parts, 'and')
                else:
                    phrase = ut.conj_phrase(['[`' + p + '`]()' for p in parts], 'and')
                # phrase = '[' + ','.join(parts) + ']()'
                if type_ == 'fig':
                    return pref + 'Figure ' + phrase
                elif type_ == 'sec':
                    return pref + 'Section ' + phrase
                elif type_ == 'subsec':
                    return pref + 'Subsection ' + phrase
                elif type_ == 'chap':
                    return pref + 'Chapter ' + phrase
                elif type_ == 'eqn':
                    return pref + 'Equation ' + phrase
                elif type_ == 'tbl':
                    return pref + 'Table  ' + phrase
                elif type_ == 'app':
                    return pref + 'Appendix ' + phrase
                elif type_ == 'sub':
                    return pref + phrase
                elif type_ == '#':
                    return pref + phrase
                else:
                    raise Exception('Unknown reference type: ' + type_ +
                                    ' groupdict=' + str(match.groupdict()))
            summary = re.sub(r'~\\[Cc]ref{' + ref('inside', '.*?') + '}', parse_cref, summary)
            summary = re.sub(r'\\[Cc]ref{' + ref('inside', '.*?') + '}', parse_cref, summary)

            summary = re.sub(r'\\emph{' + ref('inside', '.*?') + '}', '*' + bref('inside') + '*', summary)
            summary = re.sub(r'\\textbf{' + ref('inside', '.*?') + '}', '**' + bref('inside') + '**', summary)
            summary = re.sub(r'\$\\tt{' + ref('inside', '[A-Z0-9a-z_]*?') + '}\$', '*' + bref('inside') + '*', summary)
            # summary = re.sub(r'{\\tt{' + ref('inside', '.*?') + '}}', '*' + bref('inside') + '*', summary)
            summary = re.sub(r'{\\tt{' + ref('inside', '.*?') + '}}', '`' + bref('inside') + '`', summary)
            summary = re.sub('\n\n(\n| )*', '\n\n', summary)
            summary = re.sub(ut.positive_lookbehind('\s') + ref('inside', '[a-zA-Z]+') + '{}', bref('inside'), summary)
            summary = re.sub( ut.negative_lookbehind('`') + '``' + ut.negative_lookahead('`'), '"', summary)
            summary = re.sub('\'\'', '"', summary)

        if highlight:
            if self._config['asmarkdown']:
                # pip install pygments-markdown-lexer
                summary = ut.highlight_text(summary, 'markdown')
            else:
                summary = ut.highlight_text(summary, 'latex')
            summary = ut.highlight_regex(summary, r'^[a-z.]+ *\(...\)',
                                         reflags=re.MULTILINE,
                                         color='darkyellow')
        return summary

    def parse_command_def(self):
        assert self.type_ in {'newcommand', 'renewcommand'}
        field = ut.named_field
        newcommand_pats = [
            '\\\\(re)?newcommand{' + field('key', '\\\\' + RE_VARNAME) + '}{' + field('val', '.*') + '}',
            '\\\\(re)?newcommand{' + field('key', '\\\\' + RE_VARNAME) + '}\[1\]{' + field('val', '.*') + '}',
        ]
        sline = '\n'.join(self.lines).strip()
        for nargs, pat in enumerate(newcommand_pats):
            match = re.match(pat, sline, flags=re.MULTILINE | re.DOTALL)
            if match is not None:
                key = match.groupdict()['key']
                val = match.groupdict()['val']
                val = val.replace('\\zspace', '')
                val = val.replace('\\xspace', '')
                yield key, val, nargs
                # defmap[nargs] = cmd_map = defmap.get(nargs, {})
                # cmd_map[key] = val

    def parse_includegraphics(self):
        assert self.type_ == 'figure'
        text = self.summary_str(outline=True, numlines=float('inf'))
        field = ut.named_field
        pat = 'includegraphics(\[' + field('options', '.*') + '\])?' + '{' + field('fpath', '.*?') + '}'
        for match in re.finditer(pat, text):
            yield match.groupdict()

    def parse_newcommands(self):
        # Hack to read all defined commands in this document
        def_list = list(self.find_descendant_types('newcommand'))
        redef_list = list(self.find_descendant_types('renewcommand'))
        def_list += redef_list
        defmap = ut.odict()
        # field = ut.named_field
        # newcommand_pats = [
        #     '\\\\(re)?newcommand{' + field('key', '\\\\' + RE_VARNAME) + '}{' + field('val', '.*') + '}',
        #     '\\\\(re)?newcommand{' + field('key', '\\\\' + RE_VARNAME) + '}\[1\]{' + field('val', '.*') + '}',
        # ]
        for defnode in def_list:
            for key, val, nargs in defnode.parse_command_def():
                if val is not None:
                    defmap[nargs] = cmd_map = defmap.get(nargs, {})
                    cmd_map[key] = val

            # sline = '\n'.join(defnode.lines).strip()
            # for nargs, pat in enumerate(newcommand_pats):
            #     match = re.match(pat, sline)
            #     if match is not None:
            #         key = match.groupdict()['key']
            #         val = match.groupdict()['val']
            #         val = val.replace('\\zspace', '')
            #         val = val.replace('\\xspace', '')
            #         defmap[nargs] = cmd_map = defmap.get(nargs, {})
            #         cmd_map[key] = val

        usage_pat = ut.regex_or(['\\\\' + RE_VARNAME + '{}', '\\\\' + RE_VARNAME])
        cmd_map0 = defmap.get(0, {})
        for key in cmd_map0.keys():
            val = cmd_map0[key]
            changed = None
            while changed or changed is None:
                changed = False
                for match in re.findall(usage_pat, val):
                    key2 = match.replace('{}', '')
                    if key2 in cmd_map0:
                        val = val.replace(match, cmd_map0[key2])
                        changed = True
                if changed:
                    cmd_map0[key] = val
        return defmap
        # print(ut.repr3(cmd_map))

    @staticmethod
    @ut.memoize
    def read_static_defs():
        """
        Reads global and static newcommand definitions in def and CrallDef
        """
        def_node = LatexDocPart.parse_fpath('def.tex', debug=False)
        defmap = def_node.parse_newcommands()
        cmd_map = defmap[0]
        cmd_map1 = defmap[1]

        if 0:
            cralldef = LatexDocPart.parse_fpath('CrallDef.tex')
            crall_defmap = cralldef.parse_newcommands()
            cmd_map.update(crall_defmap.get(0, {}))
            cmd_map1.update(crall_defmap.get(1, {}))

        extras = {
            '\\ie': 'i.e.',
            '\\wrt': 'w.r.t.',
            '\\FloatBarrier': '',
        }

        for k, v in extras.items():
            if k not in cmd_map:
                cmd_map[k] = v
        return cmd_map, cmd_map1

    def reformat_text(self):
        return '\n'.join(self.reformat_blocks())

    def reformat_blocks(self, debug=False, stripcomments=False):
        """
        # TODO: rectify this with summary string blocks
        """
        is_rawformat = self.parent_type() in TexNest.rawformat_types
        if debug:
            print('-----------------')
            print('Formating Part %s - %s' % (self.type_, self.subtype,))
            print('lines = ' + ut.repr3(self.lines))
            print('is_rawformat = %r' % (is_rawformat,))
            print('self.parent_type() = %r' % (self.parent_type(),))

        use_indent = True
        myprefix = True
        sentence_break = True

        # FORMAT HEADER
        if is_rawformat:
            raw = '\n'.join([line for line in self.lines])
            header_block = ut.unindent(raw)
        else:
            header_block = '\n'.join([line.strip() for line in self.lines])
            # header_block = '\n'.join([line for line in self.lines])

        if use_indent:
            header_block = ut.indent(header_block, '    ' * self.level)

        # is_rawformat = True
        if self.type_ == 'lines' and not is_rawformat and self.subtype != 'comment':
            max_width = self._config['max_width']
            header_block_ = ut.format_multi_paragraphs(
                header_block, myprefix=myprefix,
                max_width=max_width,
                sentence_break=sentence_break, debug=0)
            header_block = header_block_
        else:
            header_block = header_block
        header_blocks = [header_block]

        # Hack to remove spaces in equation
        if self.parent_type() == 'equation':
            if len(header_blocks) == 1 and header_blocks[0].strip() == '':
                header_blocks = []

        if self.type_ == 'root':
            header_blocks = []

        # FORMAT FOOTER
        if len(self.footer) > 0:
            footer_block = '\n'.join([line.strip() for line in self.footer])
            if use_indent:
                footer_block = ut.indent(footer_block, '    ' * self.level)
            footer_blocks = [footer_block]
        else:
            footer_blocks = []

        if debug:
            print('+ -- Formated Header ')
            print(header_blocks)
            print('L___')

        if debug:
            print('+ -- Formated Footer ')
            print(footer_blocks)
            print('L___')

        # FORMAT BODY

        body_blocks = ut.flatten([child.reformat_blocks(debug=debug)
                                  for child in self.children])

        blocks = (header_blocks + body_blocks + footer_blocks)

        if stripcomments:
            # pat = RE_TEX_COMMENT
            blocks = ut.lmap(strip_latex_comments, blocks)
            #pat = (ut.negative_lookbehind(re.escape('\\')) + re.escape('%')) + '.*'
            # blocks = [re.sub('\n *' + pat, '', block, flags=re.MULTILINE) for block in blocks]
            # blocks = [re.sub(pat, '', block, flags=re.MULTILINE) for block in blocks]

        return blocks


def strip_latex_comments(block):
    pat = RE_TEX_COMMENT
    #pat = (ut.negative_lookbehind(re.escape('\\')) + re.escape('%')) + '.*'
    block = re.sub('\n *' + pat, '', block, flags=re.MULTILINE)
    block = re.sub(pat, '', block, flags=re.MULTILINE)
    return block


class TexNest(object):
    """
    Defines the table of contents heirarchy.

    This should probably just turn into a grammar.
    """
    # table of contents heirarchy
    #toc_heirarchy = ['chapter', 'section', 'subsection', 'subsubsection']
    toc_heirarchy = ['document', 'chapter', 'section', 'subsection',
                     'subsubsection']
    # things that look like \<type_>
    headers = ['chapter', 'section', 'subsection', 'subsubsection',
               'paragraph', 'item']

    # things that look like \begin{<type_>}\end{type_>}
    sections = ['document', 'equation', 'table', 'comment', 'pythoncode*']

    # things that can have nested items
    listables = ['enumerate', 'itemize']
    # TODO: parse newlist commands
    # HACK CUSTOM newlist commands
    listables += ['enumin', 'enumln', 'itemln', 'itemin']

    containers = toc_heirarchy + ['paragraph', 'item', 'if', 'else'] + [
        'newcommand', 'table'
    ]

    # This defines what is allowed to be nested in what
    ancestor_lookup = {
        'document'      : ['root'],
        'chapter'       : ['root', 'document'],
        'section'       : ['chapter'],
        'subsection'    : ['section'],
        'subsubsection' : ['subsection'],
        'paragraph'     : toc_heirarchy + ['item'],
        'pythoncode*'   : toc_heirarchy,
        'equation'      : toc_heirarchy + ['paragraph', 'item'],
        'comment'       : toc_heirarchy + ['paragraph', 'item'],
        'table'         : ['renewcommand', 'newcommand'] + [toc_heirarchy],
        'figure'        : ['renewcommand', 'newcommand'] + [toc_heirarchy],
        # 'subfigure'     : ['figure'],
        # 'minted'        : ['figure'],
        'input'         : ['root', 'newcommand', 'table'],
        'tabular'       : ['table'],
        'if'            : ['if'] + toc_heirarchy + ['paragraph', 'item'],
        'fi'            : 'if',
        'else'          : 'if',
    }
    for listable in listables:
        ancestor_lookup[listable] = toc_heirarchy + ['item']
    ancestor_lookup['item'] = listables
    float_envs = ['table', 'figure']
    # , 'subfigure', 'minted']
    sections += listables
    sections += float_envs

    rawformat_types = ['equation', 'comment', 'pythoncode*']


def get_testtext():
    r"""
    Args:
        text (str):
            debug (None): (default = None)

    Returns:
        LatexDocPart: root

    CommandLine:
        python latex_parser.py --exec-get_testtext --debug-latex --max-width=70

    Example:
        >>> # DISABLE_DOCTEST
        >>> from latex_parser import *  # NOQA
        >>> cls = LatexDocPart
        >>> text = get_testtext()
        >>> debug = True
        >>> self = root = cls.parse_text(text, 'text', debug=debug)
        >>> ut.colorprint('-- DEBUG TREE---', 'yellow')
        >>> print(self.get_debug_tree_text())
        >>> ut.colorprint('--- PRINT RAW LINES ---', 'yellow')
        >>> print(root.tostr())
        >>> ut.colorprint('--- PRINT SUMMARY --', 'yellow')
        >>> root.print_summary()
        >>> ut.colorprint('-- REFORMAT BLOCKS ---', 'yellow')
        >>> output_text = self.reformat_text()
        >>> print(output_text)
    """
    text = ut.codeblock(
        r'''
        % tex comments
        \newif\ifchecka{}
        \chapter{my chapter}\label{chap:chap1}

            Chapter 1 sentence 1 is long long long long long long long long long too long.
            Chapter 1 sentence 2 is short.

            \section{section 1}\label{sec:sec1}
                \newifcond
                \ifcond
                   cond1
                \else
                    cond2
                \fi

                \subsection{subsection 1.1}
                    \devcomment{ one }
                    Subsection 1.1.1 sentence 1.
                    % subsection comment
                    Subsection 1.1.1 sentence 2.

                    \devcomment{ one
                        foobar
                    }

            \section{section2}\label{sec:sec2}

                Section 1.2 sentence 1.
                Section 1.2 sentence 2.

        \chapter{chapter 2}\label{sec:chap1}
            pass

        Onetwo

        ''')
    return text


class _Parser(object):
    @classmethod
    def parse_fpath(cls, fpath, **kwargs):
        text = ut.read_from(fpath)
        root = cls.parse_text(text, name=fpath, **kwargs)
        return root

    @classmethod
    def parse_text(cls, text, name=None, debug=None, ignoreinputstartswith=[]):
        r"""
        PARSE LATEX

        CommandLine:
            ./texfix.py --reformat --fpaths chapter4-application.tex
            ./texfix.py --reformat --fpaths figdefdbinfo.tex --debug-latex
            ./texfix.py --reformat --fpaths main.tex --debug-latex --includeon=False
        """

        if debug is None:
            debug = ut.get_argflag('--debug-latex')
        root = cls('root', subtype=name)
        node = root

        text = ut.ensure_unicode(text)

        buff = text.split('\n')

        ignoreinputstartswith = ut.get_argval('--ignoreinputstartswith', type_=list, default=ignoreinputstartswith)

        # if name is not None and name.startswith('figdef'):
        #     debug = False

        if debug:
            ut.colorprint(' --- PARSE LATEX --- ', 'yellow')
            ut.colorprint('name = %r' % (name,), 'yellow')
            action = ['MAKE root']
            actstr = ut.highlight_text((', '.join(action)).ljust(25), 'yellow')
            dbgjust = 35
            print(actstr )
            #print('root = %r' % (root.tostr(),))

        # We push unfinished nodes onto the stack, and can always modify
        # the head. When we are done, we pop the node from the stack.
        # TODO; parse with a stack instead
        # nest_stack = []
        buff_stack = list(reversed(list(enumerate(buff))))
        while buff_stack:
            count, line = buff_stack.pop()
            #print(repr(line))
            action = []
            RECORD_ACTION = action.append

            sline = line.strip()
            indent = ut.get_indentation(line)  # NOQA

            headers = cls.headers

            # try:
            #     parent_type = node.parent_type()
            # except Exception as ex:
            #     ut.printex(ex, keys=['count', 'line'])
            #     raise

            # Flag is set to true when line type is determined
            found = False

            # Check for standard chapter, section, subsection header definitions
            for key in headers:
                if sline.startswith('\\' + key):
                    # Mabye this is a naming issue.
                    anscestor = node.find_root(key)  # FIXME: should be ancestor?
                    RECORD_ACTION('HEADER(%s)' % key)
                    node = anscestor.append_part(key, line_num=count)
                    node.lines.append(line)
                    # nest_stack  # TODO multiline headers
                    found = True
                    break

            if not found:
                # Check for begin / end blocks like document, equation, and itemize.
                for key in TexNest.sections:
                    if sline.startswith('\\begin{' + key + '}'):
                        # Mabye this is a naming issue.
                        anscestor = node.find_root(key)  # FIXME: should be ancestor?
                        node = anscestor.append_part(key, line_num=count)
                        RECORD_ACTION('BEGIN_KEY(%s)' % key)
                        RECORD_ACTION('ANCESTOR(%s)' % (anscestor.type_str))
                        # RECORD_ACTION('node(%s)' % (node.type_str))
                        node.lines.append(line)

                        if key == 'comment':
                            if debug:
                                actstr = (', '.join(action))
                                dbgjust = max(dbgjust, len(actstr) + 1)
                                actstr2 = ut.highlight_text(actstr.ljust(dbgjust), 'yellow')
                                #print(repr(node.parent) + '--' + repr(node))
                                print(actstr2 + ' %3d ' % (count,) + repr(line))
                            # Hacked together subparser for comments only
                            while True:
                                action = []
                                RECORD_ACTION = action.append
                                count, line = buff_stack.pop()
                                sline = line.strip()
                                if sline.startswith('\\end{comment}'):
                                    anscestor = node.get_ancestor([key])
                                    RECORD_ACTION('END_KEY(%s)' % key)
                                    anscestor.footer.append(line)
                                    parent_node = anscestor.parent
                                    break
                                else:
                                    subtype = 'par'
                                    if node.type_ != 'lines':
                                        RECORD_ACTION('start_comment')
                                        node = node.append_part('lines', subtype=subtype, line_num=count)
                                    else:
                                        RECORD_ACTION('in_comment')
                                        node.lines.append(line)
                                if debug:
                                    actstr = (', '.join(action))
                                    dbgjust = max(dbgjust, len(actstr) + 1)
                                    actstr2 = ut.highlight_text(actstr.ljust(dbgjust), 'yellow')
                                    #print(repr(node.parent) + '--' + repr(node))
                                    print(actstr2 + ' %3d ' % (count,) + repr(line))
                            continue
                        else:
                            # nest_stack.append(node)
                            found = True
                            break

                    if sline.startswith('\\end{' + key + '}'):
                        # if in_comment and key != 'comment':
                        #     break
                        anscestor = node.get_ancestor([key])
                        RECORD_ACTION('END_KEY(%s)' % key)
                        anscestor.footer.append(line)
                        parent_node = anscestor.parent
                        #parent_node = anscestor
                        #RECORD_ACTION('ANCESTOR(%s)' % (anscestor.nice()))
                        #RECORD_ACTION('PARENT(%s)' % (parent_node.nice()))
                        try:
                            assert parent_node is not None, (
                                'unexpected end of environment ' + str(
                                    (repr(node), sline, count))
                            )
                        except AssertionError as ex:
                            error_lines = []
                            prerr = error_lines.append
                            prerr('')
                            prerr('-----')
                            prerr('Error')
                            prerr('-----')
                            prerr(str(ex))
                            prerr('Perhaps the TOC heirarchy does not cover this case?')
                            prerr('Does %r have defined anscestors?' % key)
                            prerr('Error')
                            prerr('node = %r' % (node,))
                            prerr('anscestor = %r' % (anscestor,))
                            prerr('parent_node = %r' % (parent_node,))
                            prerr('count = %r' % (count,))
                            prerr('sline = %r' % (sline,))
                            err_msg = '\n'.join(error_lines)
                            # print(err_msg)
                            # print('-- Outline -----')
                            # root.print_outline(hack_figdef=False)
                            print(err_msg)
                            raise AssertionError(err_msg)
                            raise
                        node = parent_node
                        found = True
                        break

                # Check if statement
                if 1:
                    if sline.startswith('\\if'):
                        # Mabye this is a naming issue.
                        key = 'if'
                        condition_var = sline[slice(3, sline.find('{') if '{' in sline else None)]
                        anscestor = node.find_root(key)  # FIXME: should be ancestor?
                        node = anscestor.append_part(key, subtype=condition_var, line_num=count)
                        RECORD_ACTION('BEGIN_IF(%s)' % condition_var)
                        #RECORD_ACTION('ANCESTOR(%s)' % (anscestor.nice()))
                        #RECORD_ACTION('node(%s)' % (node.nice()))
                        node.lines.append(line)
                        found = True

                    if sline.startswith('\\else'):
                        # Mabye this is a naming issue.
                        key = 'else'
                        anscestor = node.get_ancestor(['if'])
                        condition_var = anscestor.subtype
                        node = anscestor.append_part(key, subtype=condition_var, line_num=count)
                        RECORD_ACTION('ELSE(%s)' % condition_var)
                        node.lines.append(line)
                        found = True

                    if sline == '\\fi':
                        key = 'fi'
                        anscestor = node.get_ancestor(['if'])
                        condition_var = anscestor.subtype
                        RECORD_ACTION('ENDIF(%s)' % condition_var)
                        anscestor.footer.append(line)
                        #print('node = %r' % (node,))
                        #print('anscestor = %r' % (anscestor,))
                        #print('parent_node = %r' % (parent_node,))
                        parent_node = anscestor.parent
                        try:
                            assert parent_node is not None, 'parent of %r is None' % (node,)
                        except AssertionError:
                            print('anscestor = %r' % (anscestor,))
                            anscestor.print_debug_tree()
                            raise

                        node = parent_node
                        print('node = %r' % (node,))
                        found = True

            # HACK
            # Check for special hacked commands
            special_texcmds = ['keywords', 'relatedto', 'outline', 'input', 'include',
                               'ImageCommand', 'MultiImageCommandII',
                               'SingleImageCommand', 'newcommand',
                               'renewcommand', 'devcomment', 'setcounter',
                               'bibliographystyle', 'bibliography' ]
            if not found:
                texcmd_pat = ut.named_field('texcmd', RE_VARNAME)
                regex = r'\s*\\' + texcmd_pat + '{'
                match = re.match(regex, sline)
                if match:
                    texmcd = match.groupdict()['texcmd']
                    simpleregex = r'^\s*\\' + texcmd_pat + '{}$'
                    simplematch = re.match(simpleregex, sline)
                    # HACK FOR SPECIAL CASES COMMANDS
                    if texmcd in special_texcmds or simplematch:
                        curlycount = sline.count('{') - sline.count('}')
                        if node.type_ == 'lines':
                            #print('FIX THIS')
                            node = node.find_ancestor_container()  # hack, fix this
                            pass
                        if curlycount == 0:
                            # HACK
                            RECORD_ACTION('BEGIN_X{%s}' % texmcd)
                            # RECORD_ACTION('CURRENT NODE: %r' % (node,))
                            if texmcd in ['input', 'include'] and root._config['includeon']:
                                # Read and parse input
                                fname = line.replace('\\' + texmcd + '{', '').replace('}', '').strip()
                                fname = ut.ensure_ext(fname, '.tex')
                                flag = True
                                # HACK
                                if fname.startswith('figuresY'):
                                    flag = False
                                for tmp in ignoreinputstartswith:
                                    if fname.startswith(tmp):
                                        flag = False
                                if flag:
                                    try:
                                        input_node = LatexDocPart.parse_fpath(fname, debug=debug)
                                    except Exception as ex:
                                        print('FAILED PARSING %r' % (fname,))
                                        pass

                                    node = node.append_part(input_node, line_num=count)
                                else:
                                    node = node.append_part(texmcd, istexcmd=True, line_num=count)
                                    if True:
                                        node.lines.append('')
                                        RECORD_ACTION('IGNORE(%s)' % texmcd)
                                    else:
                                        pass
                            else:
                                node = node.append_part(texmcd, istexcmd=True, line_num=count)
                                node.lines.append(line)
                            node.curlycount = curlycount
                            found = True
                            if node.curlycount == 0:
                                RECORD_ACTION('END_X(%s)' % texmcd)
                                #RECORD_ACTION('PARENT(%s)' % (node.parent.nice()))
                                node = node.parent
                        else:
                            RECORD_ACTION('BEGIN_X(%s){' % texmcd)
                            #node = node.find_ancestor_container()  # hack, fix this
                            node = node.append_part(texmcd, istexcmd=True, line_num=count)
                            node.lines.append(line)
                            node.curlycount = curlycount
                            found = True

            # Everything else is interpreted as soem sort of lines object
            if not found:
                #ancestor_container = node.find_ancestor_container()
                #ancestor_container.children
                #print('ancestor_container = %r' % (ancestor_container,))
                #print('ancestor_container.children = %r' % (ancestor_container.children,))
                # Parse subtype of line
                subtype = None
                if len(sline) == 0:
                    subtype = 'space'
                elif sline.startswith('%'):
                    if re.match('% [ A-Z0-9]+$', sline):
                        subtype = 'devmark'
                    else:
                        subtype = 'comment'
                # elif any(sline.startswith(x) for x in ['\\newcommand',
                #                                        '\\renewcommand']):
                #     subtype = 'def'
                elif len(sline) > 0:
                    if node.parent_type() in ['equation']:
                        subtype = 'math'
                    else:
                        subtype = 'par'
                #hack_can_append_lines = True

                if node.type_ in special_texcmds:
                    curlycount = sline.count('{') - sline.count('}')
                    node.curlycount += curlycount
                    RECORD_ACTION('append special line')
                    #hack_can_append_lines = False
                    node.lines.append(line)
                    found = True
                    if node.curlycount == 0:
                        action.append('}END(%s)' % texmcd)
                        #RECORD_ACTION('PARENT\'(%s)' % (node.parent.nice()))
                        node = node.parent

                elif node.type_ != 'lines':
                    RECORD_ACTION('MAKE %s lines' % (subtype,))
                    node = node.append_part('lines', subtype=subtype, line_num=count)
                else:
                    if node.type_ == 'lines' and node.subtype != subtype:
                        RECORD_ACTION('MAKE %s sub-lines' % (subtype,))
                        node = node.parent.append_part('lines', subtype=subtype, line_num=count)
                        #RECORD_ACTION('PARENT\'(%s)' % (node.parent.nice()))
                if node.type_ == 'lines':
                    #if node.type_ not in special_texcmds:
                    #if hack_can_append_lines:
                    RECORD_ACTION('append lines')
                    node.lines.append(line)

            if debug:
                actstr = (', '.join(action))
                dbgjust = max(dbgjust, len(actstr) + 1)
                actstr2 = ut.highlight_text(actstr.ljust(dbgjust), 'yellow')
                #print(repr(node.parent) + '--' + repr(node))
                print(actstr2 + ' %3d ' % (count,) + repr(line))
        if debug:
            ut.colorprint(' --- END PARSE LATEX --- ', 'yellow')
            #utool.embed()
            #print(root.tostr(1))
            #print(ut.repr3(ut.lmap(repr, root.children)))
            #chap = root.children[-1]
            #print(ut.repr3(ut.lmap(repr, chap.children)))
        return root


class LatexDocPart(_Reformater, _Parser, TexNest, ut.NiceRepr):
    """
    Class that contains parse-tree-esque heierarchical blocks of latex and can
    reformat them.
    """

    def __init__(self, type_='root', parent=None, level=0, istexcmd=False, subtype=None, line_num=None):
        self.type_ = type_
        self.subtype = subtype
        self.level = level
        self.parent = parent
        # Parsed line num
        self.line_num = line_num
        self.lines = []
        self.footer = []
        self.children = []
        self.istexcmd = istexcmd  # Is this needed anymore?
        self.curlycount = 0

    def to_netx_graph(self):
        """
        >>> from texfix import *  # NOQA
        >>> self = root = testdata_main()
        >>> import plottool as pt
        >>> pt.qt4ensure()
        >>> graph = self.to_netx_graph()
        >>> print(len(graph.node))
        """
        import networkx as nx
        graph = nx.DiGraph()
        adjacency_list = self.adjacency_list()
        nodes = list(adjacency_list.keys())
        edges = [(u, v) for u, children in adjacency_list.items() for v in children]
        graph.add_nodes_from(nodes)
        graph.add_edges_from(edges)
        return graph

    def adjacency_list(self):
        node = self.nicerepr()
        adjacency_list = ut.odict([
            (node, [child.nicerepr() for child in self.children])
        ])
        for child in self.children:
            adjacency_list.update(child.adjacency_list())
        return adjacency_list

    def iter_nodes(self, invalid_types=[]):
        yield self
        for child in self.children:
            if child.type_ not in invalid_types:
                for node in child.iter_nodes(invalid_types=invalid_types):
                    yield node

    @property
    def type_str(self):
        type_str = self.type_
        if self.subtype is not None:
            type_str += '.' + self.subtype
        return type_str

    def __nice__(self):
        #return '(%s -- %d) L%s' % (type_str, len(self.lines), self.level)
        return '(%s -- %d -- %d)' % (self.type_str, len(self.lines),
                                     len(self.children))

    def nice(self):
        return self.__nice__()

    def nicerepr(self):
        return repr(self).replace(self.__class__.__name__, '')

    def __str__(self):
        return self.tostr()

    def tolist(self):
        list_ = [child if len(child.children) == 0 else child.tolist()
                 for child in self.children]
        return list_

    def flatten(self):
        """
        Flattens entire structure.
        """
        if len(self.children) == 0:
            yield self
        else:
            for part in self.lines:
                yield part
            for child in self.children:
                for part in child.flatten():
                    yield part
            for part in self.footer:
                yield part
            # return [self.lines[:]] + [child.tolist2() for child in
            #                           self.children] + [self.footer[:]]

    def tostr(self):
        lines = self.lines[:]
        lines += [child.tostr() for child in self.children]
        lines += self.footer
        return '\n'.join(lines)

    def print_outline(self, depth=None, hack_figdef=True):
        summary = self.summary_str(outline=True, highlight=True, depth=depth, hack_figdef=hack_figdef)
        print(summary)

    def print_summary(self, depth=None):
        summary = self.summary_str(outline=False, highlight=True, depth=depth)
        print(summary)

    def get_debug_tree_blocks(self, indent=''):
        treeblocks = [indent + self.nicerepr()]
        for child in self.children:
            child_treeblocks = child.get_debug_tree_blocks(indent=indent + '    ')
            treeblocks.extend(child_treeblocks)
        return treeblocks

    def get_debug_tree_text(self):
        treetext = '\n'.join(self.get_debug_tree_blocks())
        return treetext

    def print_debug_tree(self):
        print(self.get_debug_tree_text())

    def fpath_root(self):
        """ returns file path that this node was parsed in """
        return self.find_ancestor_type('root').subtype

    def parsed_location_span(self):
        """ returns file path that this node was parsed in """
        idx = self.parent.children.index(self)
        sibling = None if len(self.parent.children) == idx else self.parent.children[idx + 1]
        return self.fpath_root() + ' between lines %r and %r' % (self.line_num, sibling.line_num)
        #return self.find_ancestor_type('root').subtype

    def title(self):
        if len(self.lines) == 0:
            return None
        valid_headers = TexNest.headers[:]
        valid_headers.remove('item')
        # parse curlies
        if self.type_ in valid_headers:
            # recombine part only in section header.
            # these functions are very preliminary
            parsed_blocks = ut.parse_nestings(self.lines[0])
            title = ut.recombine_nestings(parsed_blocks[1][1][1:-1])
            return title
        return None

    def find_descendant_type(self, type_, pat=None):
        gen = self.find_descendant_types(type_, pat)
        import six
        try:
            return six.next(gen)
        except StopIteration:
            return None
        #for child in self.children:
        #    if child.type_ == type_:
        #        if pat is None:
        #            return child
        #        else:
        #            title = child.title()
        #            if pat == title:
        #                return child
        #    descendant = child.find_descendant_type(type_, pat=pat)
        #    if descendant is not None:
        #        return descendant
        #return None

    def find_descendant_types(self, type_, pat=None):
        for child in self.children:
            if child.type_ == type_:
                if pat is None:
                    yield child
                else:
                    title = child.title()
                    if pat == title:
                        yield child
            for descendant in child.find_descendant_types(type_, pat=pat):
                yield descendant

    def find_ancestor_type(self, type_):
        parent = self.parent
        if parent.type_ == type_:
            return parent
        else:
            anscestor = parent.find_ancestor_type(type_)
            if anscestor is not None:
                return anscestor
        return None

    def find(self, regexpr_list, findtype=('lines', 'par'), verbose=False):
        r"""
        Finds all nodes of a given type:

        list_ = ut.total_flatten(root.tolist2())
        list_ = root.find(' \\\\cref')
        self = list_[-1]
        """
        returnlist = []
        regexpr_list = ut.ensure_iterable(regexpr_list)
        if self.type_ in [findtype[0]] and (findtype[1] is None or self.subtype in [findtype[1]]):
            found_lines, found_lxs = ut.greplines(self._local_sentences(), regexpr_list)
            found_fpath_list = ['<string>']
            grepresult = [found_fpath_list, [found_lines], [found_lxs]]
            grepstr = ut.make_grep_resultstr(grepresult, regexpr_list, reflags=0, colored=True)
            if grepstr.strip():
                if verbose:
                    print(grepstr.strip('\n'))
                returnlist += [self]
        for child in self.children:
            returnlist += child.find(regexpr_list, findtype)
        return returnlist

    def parse_figure_captions(self):
        r"""
        Returns:
            dict: figdict

        CommandLine:
            python -m latex_parser parse_figure_captions --show

        Example:
            >>> # DISABLE_DOCTEST
            >>> from latex_parser import *  # NOQA
            >>> debug = False
            >>> text = ut.readfrom('figdefexpt.tex')
            >>> self = LatexDocPart.parse_text(text, debug)
            >>> fig_defs = [LatexDocPart.parse_fpath(fpath) for fpath in ut.glob('.', 'figdef*')]
            >>> fpathsdict = ut.dict_union(*[f.parse_figure_captions()[1]['fpaths'] for f in fig_defs])
            >>> defined_fpaths = ut.flatten(fpathsdict.values())
            >>> undefined_fpaths = [f for f in defined_fpaths if not exists(f)]
            >>> used_fpaths = sorted([f for f in defined_fpaths if exists(f)])
            >>> figsizes = [ut.util_cplat.get_file_nBytes(f) for f in used_fpaths]
            >>> sortx = ut.argsort(figsizes)
            >>> sort_sizes = ut.take(figsizes, sortx)
            >>> sort_paths = ut.take(used_fpaths, sortx)
            >>> offenders = [(ut.util_str.byte_str2(s), p) for s, p in zip(sort_sizes, sort_paths)]
            >>> print(ut.repr3(offenders, nl=1))

            # Quantize pngs to make them a bit smaller
            for p in ut.ProgIter(sort_paths):
                if p.endswith('.png'):
                    ut.cmd('pngquant --quality=65-80 -f --ext .png ' + p)

            unused_dpath = 'unused_figures'

            #for x in undefined_fpaths:
            #    y = unused_dpath + '/' + ut.tail(x, 1, False)
            #    if exists(y):
            #        print(x)
            #        print(y)
            #        ut.move(y, x)

            dpaths = ut.unique([dirname(p) for p in sort_paths])
            allfigs = sorted([ut.tail(z, 2, False) for z in ut.flatten([ut.ls(p) for p in dpaths])])
            unused_figs = ut.setdiff(allfigs, used_fpaths)
            ut.ensuredir(unused_dpath)
            [ut.ensuredir(unused_dpath + '/' + d) for d in dpaths]
            move_list = [(f, unused_dpath + '/' + ut.util_path.tail(f, 2, trailing=False)) for f in unused_figs]
            [ut.move(a, b) for a, b in move_list]
            pngquant --quality=65-80

        HACK
        list_ = ut.total_flatten(root.tolist2())
        list_ = root.find(' \\\\cref')
        self = list_[-1]
        self = root
        """
        # defs = self.find('.*', ('lines', 'def'))
        # Read definitions of figures to grab the captions
        def_list = self.find('.*', ('newcommand', None))
        ref = ut.partial(ut.named_field)

        figdict = {}
        figdict2 = ut.defaultdict(dict)

        imgpath_pattern = r'[/a-zA-Z_0-9\.]*?\.(png|jpg|jpeg)\b'

        for node in def_list:
            text = str(node)
            match = re.search('\\\\newcommand{\\\\' + ref('cmdname', '.*?') +
                              '}.*\\\\capt[ie][ox][nt]\[.*\]{' + ref('caption', '.*?') +
                              '}(\n|\s)*\\\\label', text, flags=re.DOTALL)
            if match is None:
                if ut.VERBOSE:
                    print('WARNING match = %r' % (match,))
                    print('NONE DEF')
                    print(str(node))
                continue
            figname = (match.groupdict()['cmdname'])
            figcap = (match.groupdict()['caption'])
            figdict[figname] = figcap
            figdict2['caption'][figname] = figcap
            fpaths = [ut.get_match_text(m) for m in re.finditer(imgpath_pattern, text)]
            figdict2['fpaths'][figname] = fpaths

        return figdict, figdict2

    def find_sentences(self):
        for lines in self.find_descendant_types('lines'):
            if lines.subtype == 'par':
                yield from lines._local_sentences()

    def _local_sentences(self):
        lines = [re.sub(RE_TEX_COMMENT + r'\s*$', '', l, flags=re.MULTILINE)
                 for l in self.lines]
        # lines = ut.lmap(strip_latex_comments, self.lines)
        sentences = ut.split_sentences2('\n'.join(lines))
        return sentences

    def parent_type(self):
        return None if self.parent is None else self.parent.type_

    def get_ancestor(self, target_types):
        if self.type_ in target_types or self.parent is None:
            return self
        elif self.type_ != target_types:
            return self.parent.get_ancestor(target_types)

    def find_root(self, type_):
        node = None
        ancestors = TexNest.ancestor_lookup[type_]
        node = self.get_ancestor(ancestors)
        return node

    def find_ancestor_container(self):
        node = self.get_ancestor(TexNest.containers)
        return node

    def append_part(self, type_='root', istexcmd=False, subtype=None, line_num=None):
        noincrease_types = ['root']
        #noincrease_types = ['root', 'item', 'paragraph', 'chapter']
        #noincrease_types = ['root', 'item']
        # noincrease_types = ['root', 'item', 'chapter']
        noincrease_types = ['root', 'document', 'chapter', 'paragraph']
        if self.type_ in noincrease_types or ut.get_argflag('--noindent'):
            level = self.level
        else:
            level = self.level + 1

        if isinstance(type_, LatexDocPart):
            # Node created externally
            new_node = type_
            new_node.parent = self
        else:
            new_node = LatexDocPart(type_=type_, parent=self, level=level,
                                    istexcmd=istexcmd, subtype=subtype,
                                    line_num=line_num)
        self.children.append(new_node)
        return new_node


if __name__ == '__main__':
    r"""
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/latex/crall-candidacy-2015
        python ~/latex/crall-candidacy-2015/latex_parser.py
        python ~/latex/crall-candidacy-2015/latex_parser.py --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
