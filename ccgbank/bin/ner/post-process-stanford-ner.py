"""
Take Stanford 'inlineXML' output from stdin, pipe processed version thereof to stdout.

E.g.,

$ echo "This is a <ORGANIZATION>US Dept of Defense</ORGANIZATION> example ." | python post-process-stanford-ner.py
This is a US_Dept_of_Defense_ORGANIZATION example .

Type:

$ python post-process-stanford-ner.py -h

for help on the command-line options.
"""

import codecs
import math
import optparse
import os
import sys

from ner_word import NERWord

SPARKY_IRRELEVANT_NE_LABELS = {"MONEY"}


def fuseNERWords(list_of_ner_words, labels_to_ignore):
    # If the NER category isn't one we care about, don't fuse the words and the category
    if list_of_ner_words[0].getLabel() in labels_to_ignore:
        return " ".join([nerWrd.getWord() for nerWrd in list_of_ner_words])
    # Otherwise, fuse them together with underscores
    else:
        return "_".join([nerWrd.getWord() for nerWrd in list_of_ner_words] + [list_of_ner_words[0].getLabel()])


optparser = optparse.OptionParser()
optparser.add_option("--known_verbs", type="string",
                     help="file containing known verbs (for split-at-verb-boundary heuristic) [defaults to an empty list of known verbs]",
                     default=None)

(ops, args) = optparser.parse_args()

known_verbs = set([v.strip() for v in open(ops.known_verbs, "rb").readlines()]) if not ops.known_verbs is None else set()
puncts = set([',', "'", '"', ".", "?", "!"])
heuristic_splitters = (known_verbs | puncts)

for l in sys.stdin:
    l = l.strip()
    if l == "":
        continue
    ner_parts = l.split()
    ner_parts = NERWord.parseLineOfWords(ner_parts)

    i = 0

    current_NE = None
    current_group = None

    res = []
    while i < len(ner_parts):
        prt = ner_parts[i]
        (wd,ne) = (prt.getWord(), prt.getLabel())

        if not ne is None:
            # we have a NE label. is it a continuation of what came before (if anything)?
            if ne == current_NE:
                current_group.append(prt)
            else: 
                if current_NE is None:
                    current_NE = ne
                    current_group = [prt]
                else:
                    res.append(fuseNERWords(current_group, SPARKY_IRRELEVANT_NE_LABELS))
                    current_NE = ne
                    current_group = [prt]
        else:
            if not current_NE is None:
                res.append(fuseNERWords(current_group, SPARKY_IRRELEVANT_NE_LABELS))
                current_NE = None
                current_group = None
            res.append(wd)
        
        i += 1
    
    if not current_NE is None:
        res.append(fuseNERWords(current_group, SPARKY_IRRELEVANT_NE_LABELS))

    print " ".join(res)

