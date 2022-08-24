
import stanza
from os.path import expanduser
from utils import txt2list, jaccard_similarity
class Load_Lexicons:

    home = expanduser("~")
    def __init__(self, directory = home+'/Documents/detect_hedges/resources/'): 
        self.directory = directory
        self.DM_dir = self.directory+"discourse_markers.txt"
        self.HG1_dir = self.directory+"hedge_words.txt"
        self.HG2_dir = self.directory+"propositional_hedges.txt"
        self.HG3_dir = self.directory+"relational_hedges.txt"
        self.B_dir = self.directory+"booster_words.txt"


    def load(self) -> list:
        DM = txt2list(self.DM_dir) # List of discourse markers
        HG1 = txt2list(self.HG1_dir) # List of hedge words
        HG2 = txt2list(self.HG2_dir)
        HG3 = txt2list(self.HG3_dir)
        HG = list(set(HG1+HG2+HG3))
        B = txt2list(self.B_dir) # List of booster words
        lexicons = [DM, HG, B]

        return lexicons

class Hedge_Detector:
    '''
    class variables: shared variables shared among the class
    instance variables: 
    directory, lexicons, stanza pipeline
    '''
    # class attributes
    def __init__(self, lexicons: list): 

        self.DM = lexicons[0]
        self.HG = lexicons[1]
        self.B = lexicons[2]
        self.nlp_s = stanza.Pipeline(lang='en')
        self.nlp_p = stanza.Pipeline(lang='en', processors='tokenize')


    def isTrueHedgeTerm(self, t: str, doc_dicts: dict, ids: list) -> bool:
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


    def isHedgedSentence(self, sentence: str) -> bool:
        doc = self.nlp_s(sentence)
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

        for word1 in self.DM:
            for word2 in P:
                if 1 - jaccard_similarity(word1, word2) >= threshold:
                    status = True

        for booster in self.B:
            indices = [i for i, s in enumerate(sentence) if booster in s]
            if len(indices)>0:
                for idx in indices[1:]:
                    if (sentence[idx-1] == 'not') or (sentence[idx-1] == 'without'):
                        status = True

        
        for hedge in self.HG:
            indices = [i for i, s in enumerate(P) if hedge in s]
            
            if (hedge in sentence) and self.isTrueHedgeTerm(hedge, doc_dicts, indices):

                status = True
                break
            else:
                status = False
                
        return status


    def hedge_percentage(self, text: str, is_sentence = False) -> float:
        doc = self.nlp_p(text)
        list_hedges = []
        if is_sentence:
            return float(self.isHedgedSentence(text))
        for i, sentence in enumerate(doc.sentences):
            list_hedges.append(self.isHedgedSentence(sentence.text))
        
        return sum(list_hedges)/len(list_hedges)