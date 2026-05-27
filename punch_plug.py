from nltk.corpus import wordnet as wn
print([s.name() for s in wn.synsets("punch", pos=wn.VERB)])
print([s.name() for s in wn.synsets("plug", pos=wn.VERB)])
for s1 in wn.synsets("punch", pos=wn.VERB):
    for s2 in wn.synsets("plug", pos=wn.VERB):
        print(s1.name(), s2.name(), s1.wup_similarity(s2))