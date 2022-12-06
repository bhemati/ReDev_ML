import nltk, re
from word2number import w2n
import pandas as pd
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
class ExtractExpJ:
    
    information=[]
    inputString = ''
    tokens = []
    lines = []
    sentences = []
    max_weightage = 45
    min_variance = 5
    
    def get_features(self, dic): 
        #TODO: Download below package only once
        #nltk.download('punkt')
        #nltk.download('averaged_perceptron_tagger')
        #nltk.download('maxent_ne_chunker')
        #nltk.download('words')
        text = json.dumps(dic)
        self.preprocess_data(text)
        self.tokenize(text)
        
        return self.get_exp(dic)
            
    def preprocess_data(self, document):
        
        try:
            # Try to get rid of special characters
            try:
                document = document.decode('ascii', 'ignore')
            except:
                #Pass as document not encoded
                pass
            # Newlines are one element of structure in the data
            # Helps limit the context and breaks up the data as is intended in resumes - i.e., into points
            lines = [el.strip() for el in re.split("\r|\n",document) if len(el) > 0]  # Splitting on the basis of newlines 
            lines = [nltk.word_tokenize(el) for el in lines]    # Tokenize the individual lines
            lines = [nltk.pos_tag(el) for el in lines]  # Tag them
            # Below approach is slightly different because it splits sentences not just on the basis of newlines, but also full stops 
            # - (barring abbreviations etc.)
            # But it fails miserably at predicting names, so currently using it only for tokenization of the whole document
            sentences = nltk.sent_tokenize(document)    # Split/Tokenize into sentences (List of strings)
            sentences = [nltk.word_tokenize(sent) for sent in sentences]    # Split/Tokenize sentences into words (List of lists of strings)
            tokens = sentences
            sentences = [nltk.pos_tag(sent) for sent in sentences]    # Tag the tokens - list of lists of tuples - each tuple is (<word>, <tag>)
            # Next 4 lines convert tokens from a list of list of strings to a list of strings; basically stitches them together
            dummy = []
            for el in tokens:
                dummy += el
            tokens = dummy
            # tokens - words extracted from the doc, lines - split only based on newlines (may have more than one sentence)
            # sentences - split on the basis of rules of grammar
            return tokens, lines, sentences
        except Exception as e:
            print(e)
    
    def tokenize(self, inputString):
        try:
            self.tokens, self.lines, self.sentences = self.preprocess_data(inputString)
            return self.tokens, self.lines, self.sentences
        except Exception as e:
            print(e)
    
    def get_exp(self, input):
        experience = 0.0
        experience_df=pd.DataFrame(columns=( 'Years', 'Months', 'Location'))
        pos = 0
        for exp in input['user']['experiences']:
            if exp['endAt'] == None:
                enddate = datetime.now()
            else:
                enddate = datetime.strptime(exp['endAt'],"%Y-%m-%d")
            startdate = datetime.strptime(exp['startAt'],"%Y-%m-%d")
            years = relativedelta(enddate,startdate).years
            # expType=2
            pos = pos + 1
            experience_df.loc[experience_df.shape[0]] = [ years, 0, pos]
                           
            if not experience_df.empty:
                #experience_df = experience_df.sort_values(['Type', 'Years','Location'], ascending=[True, False, True])
                experience_df = experience_df.sort_values([ 'Years'], ascending=[False])
                experience = float(experience_df['Years'].sum())
                
            else:
                experience = 0.0
                        
        # except Exception as e:
        #     print (e)
            
        return experience

    def get_exp_weightage(self,jd_exp,resume_exp):
        
        score = 0
        resume_exp = int(round(resume_exp))
        #print(resume_exp)
        if jd_exp.find("-") == -1:
            jd_exp = "0-"+jd_exp[:]
            
        min_jd_exp =  int(jd_exp[0])
        max_jd_exp = int(jd_exp[2])
        
        if resume_exp == 0:
            score = 0
            
        elif resume_exp > min_jd_exp:
            if resume_exp > max_jd_exp:
                score = self.max_weightage - (self.min_variance*(resume_exp-max_jd_exp))
            else:
                score = self.max_weightage
                
        else:
            score = self.max_weightage - (self.min_variance*(min_jd_exp-resume_exp))
        
        if score < 0:
            score = 0
        return score 