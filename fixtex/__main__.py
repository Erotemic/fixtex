#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from fixtex import fix_bib
from fixtex import fix_tex


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'bib':
        fix_bib.main()
    else:
        fix_tex.main()

if __name__ == '__main__':
    main()
