"""
Parses the xml conversion of orchid

https://github.com/korakot/thainlp/blob/master/xmlchid.xml
"""

import os
import random
import sys
import xml.etree.ElementTree as ET

# line "122819" has some error in the tokenization of the musical notation
# line "209380" is also messed up
# line "227768"

skipped_lines = {
    "122819",
    "209380",
    "227769",
    "245992",
    "347163",
    "409708",
    "431227",
}

escape_sequences = {
    '<left_parenthesis>': '(',
    '<right_parenthesis>': ')',
    '<circumflex_accent>': '^',
    '<full_stop>': '.',
    '<minus>': '-',
    '<asterisk>': '*',
    '<quotation>': '"',
    '<slash>': '/',
    '<colon>': ':',
    '<equal>': '=',
    '<comma>': ',',
    '<semi_colon>': ';',
    '<less_than>': '<',
    '<greater_than>': '>',
    '<ampersand>': '&',
    '<left_curly_bracket>': '{',
    '<right_curly_bracket>': '}',
    '<apostrophe>': "'",
    '<plus>': '+',
    '<number>': '#',
    '<dollar>': '$',
    '<at_mark>': '@',
    '<question_mark>': '?',
    '<exclamation>': '!',
    'app<LI>ances': 'appliances',
    'intel<LI>gence': 'intelligence',
    "<slash>'": "/'",
    '<100>': '100',
}

allowed_sequences = {
    '<a>',
    '<b>',
    '<c>',
    '<e>',
    '<f>',
    '<LI>',
    '<---vp',
    '<---',
    '<----',
}

def read_data(input_filename):
    tree = ET.parse(input_filename)

    # we will put each paragraph in a separate block in the output file
    # we won't pay any attention to the document boundaries unless we
    # later find out it was necessary
    # a paragraph will be a list of sentences
    # a sentence is a list of words, where each word is a string
    paragraphs = []

    root = tree.getroot()
    for document in root:
        # these should all be documents
        if document.tag != 'document':
            raise ValueError("Unexpected orchid xml layout: {}".format(document.tag))
        for paragraph in document:
            if paragraph.tag != 'paragraph':
                raise ValueError("Unexpected orchid xml layout: {} under {}".format(paragraph.tag, document.tag))
            sentences = []
            for sentence in paragraph:
                if sentence.tag != 'sentence':
                    raise ValueError("Unexpected orchid xml layout: {} under {}".format(sentence.tag, document.tag))
                if sentence.attrib['line_num'] in skipped_lines:
                    continue
                words = []
                for word_idx, word in enumerate(sentence):
                    if word.tag != 'word':
                        raise ValueError("Unexpected orchid xml layout: {} under {}".format(word.tag, sentence.tag))
                    word = word.attrib['surface']
                    word = escape_sequences.get(word, word)
                    if word == '<space>':
                        if word_idx == 0:
                            raise ValueError("Space character was the first token in a sentence: {}".format(sentence.attrib['line_num']))
                        else:
                            words[-1] = (words[-1][0], True)
                            continue
                    if len(word) > 1 and word[0] == '<' and word not in allowed_sequences:
                        raise ValueError("Unknown escape sequence {}".format(word))
                    words.append((word, False))
                if len(words) == 0:
                    continue
                sentences.append(words)
            paragraphs.append(sentences)

    print("Number of paragraphs: {}".format(len(paragraphs)))
    return paragraphs


def write_section(output_dir, section, paragraphs):
    # TODO: no MWT in this dataset?
    with open(os.path.join(output_dir, 'th_orchid-ud-%s-mwt.json' % section), 'w') as fout:
        fout.write("[]\n")

    text_out = open(os.path.join(output_dir, 'th_orchid.%s.txt' % section), 'w')
    label_out = open(os.path.join(output_dir, 'th_orchid-ud-%s.toklabels' % section), 'w')
    for paragraph in paragraphs:
        for sentence_idx, sentence in enumerate(paragraph):
            for word_idx, word in enumerate(sentence):
                # TODO: split with newlines to make it more readable?
                text_out.write(word[0])
                for i in range(len(word[0]) - 1):
                    label_out.write("0")
                if word_idx == len(sentence) - 1:
                    label_out.write("2")
                else:
                    label_out.write("1")
                if word[1] and sentence_idx != len(paragraph) - 1:
                    text_out.write(' ')
                    label_out.write('0')

        text_out.write("\n\n")
        label_out.write("\n\n")

    text_out.close()
    label_out.close()

    with open(os.path.join(output_dir, 'th_orchid.%s.gold.conllu' % section), 'w') as fout:
        for paragraph in paragraphs:
            for sentence in paragraph:
                for word_idx, word in enumerate(sentence):
                    # SpaceAfter is left blank if there is space after the word
                    space = '_' if word[1] else 'SpaceAfter=No'
                    # Note the faked dependency structure: the conll reading code
                    # needs it even if it isn't being used in any way
                    fake_dep = 'root' if word_idx == 0 else 'dep'
                    fout.write('{}\t{}\t_\t_\t_\t_\t{}\t{}\t{}:{}\t{}\n'.format(word_idx+1, word[0], word_idx, fake_dep, word_idx, fake_dep, space))
                fout.write('\n')

def main():
    input_filename = sys.argv[1]
    output_dir = sys.argv[2]
    paragraphs = read_data(input_filename)
    random.seed(1000)
    random.shuffle(paragraphs)
    num_train = int(len(paragraphs) * 0.8)
    num_dev = int(len(paragraphs) * 0.1)
    write_section(output_dir, 'train', paragraphs[:num_train])
    write_section(output_dir, 'dev', paragraphs[num_train:num_train+num_dev])
    write_section(output_dir, 'test', paragraphs[num_train+num_dev:])


if __name__ == '__main__':
    main()
