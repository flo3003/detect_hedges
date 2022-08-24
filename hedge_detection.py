# This is an implementation of the lexicon- and rule-based algorithm that detects hedges from these papers:
# 
#     https://aclanthology.org/2020.lrec-1.380.pdf
#     
#     https://aclanthology.org/W18-1301.pdf



import stanza
from os.path import expanduser
from utils import txt2list, jaccard_similarity

def isTrueHedgeTerm(t, doc_dicts, ids):
    # rule-based algorithm
    
    true_hedge = False
    hedge_terms = ["feel", "suggest", "believe", "consider", "doubt", "guess", "hope"]
    
    for id in ids:
        if t == 'think':
            if id+1 < len(doc_dicts):
                if not (doc_dicts[id+1]['xpos'] =='IN'):
                    true_hedge = True
        if t == 'rather':
            if id+1 < len(doc_dicts):
                if not (doc_dicts[id+1]['text'] =='than'):
                    true_hedge = True
                    
        if doc_dicts[id]['xpos'] == 'VBP':
            is_verb = True
        else:
            is_verb = False
        if doc_dicts[id]['deprel'] == 'root':
            is_root = True
        else:
            is_root = False
            

        dependencies = {}
        for word in doc_dicts:
            if t == 'tend':
                if (word['deprel'] == 'xcomp') & (doc_dicts[word['head']-1]['text'] == doc_dicts[id]['text']):
                    true_hedge = True
                    
            if t == 'appear':
                if ((word['deprel'] == 'xcomp') | (word['deprel'] == 'ccomp')) & (doc_dicts[word['head']-1]['text'] == doc_dicts[id]['text']):
                    true_hedge = True
            if t in hedge_terms:
                if (is_root & is_verb & (word['deprel'] == 'nsubj')  & (doc_dicts[word['head']-1]['text'] == doc_dicts[id]['text'])):
                    true_hedge = True
            if t == 'assume':
                if (word['deprel'] == 'ccomp') & (doc_dicts[word['head']-1]['text'] == doc_dicts[id]['text']):
                        true_hedge = True                    

            parent = str(doc_dicts[word['head']-1]['text'] if word['head'] > 0 else 'ROOT')
            try:
                dependencies[parent].setdefault(word['deprel'],[]).append(word['text']) 

            except KeyError:
                dependencies[parent] = {}
                dependencies[parent][word['deprel']] = [word['text']]

        if t == 'suppose':
            true_hedge = True
            try:
                if 'xcomp' in dependencies[doc_dicts[id]['text']].keys():
                    xcomps = dependencies[doc_dicts[id]['text']]['xcomp']
                    for xcomp in xcomps:
                        try:
                            true_hedge = (not 'to' in dependencies[xcomp]['mark'])
                        except:
                            true_hedge = True   

            except:
                if doc_dicts[id]['deprel'] == 'advmod':
                    true_hedge = False 

        if t == 'likely':
            true_hedge = True
            if (doc_dicts[id]['deprel'] == 'amod') & (doc_dicts[doc_dicts[id]['head']-1]['xpos'] == 'NN'):
                true_hedge = False

        if t == 'should':
            true_hedge = True
            try:
                root = dependencies['ROOT']['root'][0]                
                if t in dependencies[root]['aux']:
                    flatten_values = [element for sublist in dependencies[root].values() for element in sublist]
                    true_hedge = not 'have' in flatten_values
            except:
                true_hedge = True 
                
        if t == 'about':
            true_hedge = True
            if doc_dicts[id]['xpos'] == 'IN':
                true_hedge = False
                
        if t == 'sure':
            try:
                flatten_values = [element for sublist in dependencies[doc_dicts[id]['text']].values() for element in sublist]
                true_hedge = ("not" in flatten_values) | ("n't" in flatten_values)
            except:
                true_hedge = False
                
        if t == 'completely':
            try:
                if doc_dicts[id]['head'] > 0:
                    
                    head_t = doc_dicts[doc_dicts[id]['head']-1]['text']
                flatten_values = [element for sublist in dependencies[head_t].values() for element in sublist]
                true_hedge = ("not" in flatten_values) | ("n't" in flatten_values)
            except:
                true_hedge = False
        
    if true_hedge:
        return True
    else:
        return False
    
def isHedgedSentence(sentence):
    doc = nlp_s(sentence)
    doc_dicts = doc.sentences[0].to_dict()
    try:
        P = [doc_dict['lemma'] for doc_dict in doc_dicts]
    except KeyError:
        P = []
        for doc_dict in doc_dicts:
            try:
                P.append(doc_dict['lemma'])
            except KeyError:
                P.append(doc_dict['text'])
    
    status = False
    
    threshold = 0.8

    for A in DM:
        for B in P:
            if 1 - jaccard_similarity(A, B) >= threshold:
                status = True

    for booster in B:
        indices = [i for i, s in enumerate(sentence) if booster in s]
        if len(indices)>0:
            for idx in indices[1:]:
                if (sentence[idx-1] == 'not') or (sentence[idx-1] == 'without'):
                    status = True

    
    for hedge in HG:
        indices = [i for i, s in enumerate(P) if hedge in s]
        
        if (hedge in sentence) and isTrueHedgeTerm(hedge, doc_dicts, indices):

            status = True
            break
        else:
            status = False
            
            
    return status

def hedge_percentage(text, is_sentence = False):
    doc = nlp_p(text)
    list_hedges = []
    if is_sentence:
        return float(self.isHedgedSentence(text))
    for i, sentence in enumerate(doc.sentences):
        list_hedges.append(isHedgedSentence(sentence.text))
    
    return sum(list_hedges)/len(list_hedges)


home = expanduser("~")
directory = home+'/Documents/detect_hedges/'
DM = txt2list(directory+"resources/discourse_markers.txt") # List of discourse markers
HG1 = txt2list(directory+"resources/hedge_words.txt") # List of hedge words
HG2 = txt2list(directory+"resources/propositional_hedges.txt")
HG3 = txt2list(directory+"resources/relational_hedges.txt")
HG = list(set(HG1+HG2+HG3))
B = txt2list(directory+"resources/booster_words.txt") # List of booster words
nlp_s = stanza.Pipeline(lang='en')
nlp_p = stanza.Pipeline(lang='en', processors='tokenize')


# Ambiguous examples: 
# All answers must be s1: True, s2: False

# s1 = "We tend to never forget."
# s2 = "All political institutions tended toward despotism."
# t = 'tend'

# s1 = "I hope that I'm on the right track."
# s2 = "I'm still living with it, but without hope that I would find anyone."
# t = 'hope'

# s1 = "I think it's difficult to make generalizations about this kind of relationships."
# s2 = "Even if it's difficult, I always say, think about your children."
# t = 'think'

# s1 = "I assume they were responsible for this."
# s2 = "They have assumed the role of parents and are doing their best to fulfill it."
# t = "assume"

# s1 = "I suppose he was present during the discussion."
# s2 = "I could see that they were skewing the real truth, the one they are supposed to tell me."
# t = "suppose"

# s1 = "They will likely visit us in the future."
# s2 = "He is a fine, likely man."
# t = "likely"

# s1 = "That's precisely the message that should be sent to people who label others, isn't it?"
# s2 = "They should have been more careful."
# t = "should"

# s1 = "I never had the opportunity to go, but i know people who have gone and who came back rather depressed."
# s2 = "He would have protected his flock rather than shoot at them."
# t = "rather"

# s1 = "There are about 10 million packages in transit right now." 
# s2 = "We need to talk about Mark."
# t = "about"

# s1 = "I am not sure."
# s2 = "He is sure she will turn up tomorrow."
# t = "sure"

# s1 = "That isn't completely true." 
# s2 = "I am completely sure you will win"
# t = "completely"

# print dependencies
# for word in doc_dicts:
#   print ("{:<15} | {:<10} | {:<15} "
#          .format(str(word['text']),str(word['deprel']), str(doc_dicts[word['head']-1]['text'] if word['head'] > 0 else 'ROOT')))

# print(isHedgedSentence(s1))
# print(isHedgedSentence(s2))

