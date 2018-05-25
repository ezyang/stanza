import argparse
import re
import sys

parser = argparse.ArgumentParser()

parser.add_argument('plaintext_file', type=str, help="Plaintext file containing the raw input")
parser.add_argument('char_level_pred', type=str, help="Plaintext file containing character-level predictions")
parser.add_argument('-o', '--output', default=None, type=str, help="Output file name; output to the console if not specified (the default)")

args = parser.parse_args()

with open(args.plaintext_file, 'r') as f:
    text = ''.join(f.readlines()).rstrip()

with open(args.char_level_pred, 'r') as f:
    char_level_pred = ''.join(f.readlines())

#assert len(text) == len(char_level_pred), 'Text has {} characters but there are {} char-level labels!'.format(len(text), len(char_level_pred))

output = sys.stdout if args.output is None else smart_open(args.output, 'w')

chunks = []
preds = []
lastchunk = ''
lastpred = ''
for idx in range(len(text)):
    if re.match('^\w$', text[idx], flags=re.UNICODE):
        lastchunk += text[idx]
    else:
        if len(lastchunk) > 0 and not re.match('^\W+$', lastchunk, flags=re.UNICODE):
            chunks += [lastchunk]
            assert len(lastpred) > 0
            preds += [lastpred]
            lastchunk = ''
        if not re.match('^\s$', text[idx], flags=re.UNICODE):
            # punctuation
            chunks += [text[idx]]
            assert len(lastpred) > 0
            preds += [char_level_pred[idx]]
        else:
            # prepend leading white spaces to chunks so we can tell the difference between "2 , 2" and "2,2"
            lastchunk += text[idx]
    lastpred = char_level_pred[idx]

print(list(zip(chunks[:20], preds[:20])))
