
import os
from spacy.matcher import Matcher
import spacy
nlp = spacy.load("en_core_web_lg")

def get_degree_jd(edu_info):
    if edu_info == None:
        return None
    matcher = Matcher(nlp.vocab)
    patterns_bach = [
        [{"LOWER": "bachelor"}, {"IS_PUNCT": True}, {"LOWER": "s"}],
        [{"LOWER": "bachelors"}],
        [{"LOWER": "bachelor"}],
        [{"LOWER": "b"}, {"IS_PUNCT": True}, {"LOWER": "sc"}],
        [{"LOWER": "bs"}],
        [{"LOWER": "bsc"}]
        ]
    patterns_mast = [
        [{"LOWER": "master"}, {"IS_PUNCT": True}, {"LOWER": "s"}],
        [{"LOWER": "masters"}],
        [{"LOWER": "master"}],
        [{"LOWER": "m"}, {"IS_PUNCT": True}, {"LOWER": "sc"}, {"IS_PUNCT": True}],
        [{"LOWER": "ms"}],
        [{"LOWER": "msc"}]
        ]
    matcher.add("Bachelor", patterns_bach)
    matcher.add("Master", patterns_mast)
    doc = nlp(edu_info)
    matches = matcher(doc)
    sents = ""
    if matches != None:
        for match_id, start, end in matches:
            string_id = nlp.vocab.strings[match_id]  # Get string representation
            span = doc[start:end]  # The matched span
            sents += span.sent.text
            # print(match_id, string_id, start, end, span.text, sents)
        return sents
    return None

def eduScore(resume_edu, jd_edu, skill_weightage = 15):
    # resumeCorpus = [x.lower() for x in resumeCorpus if isinstance(x, str)]
    # jdSkillMatched = [x.lower() for x in jd if isinstance(x, str)]
    # list1 = jdSkillMatched
    # list2 = resumeCorpus
    # results = {}
    # for i in list1:
    #     results[i] = list2.count(i) 
    doc1 = nlp(resume_edu)
    doc2 = nlp(jd_edu)
    return ((doc1.similarity(doc2)) * skill_weightage)

def programmingScore(resume, jdss, progWords = None, skill_weightage = 40):
    # skill_weightage = 40
    skill_threshold = 5
    # fout = open("results.tex", "a")
 
   # My Code 
    """resumeCorpus = resume.split()
    resumeCorpus = [x.lower() for x in resumeCorpus if isinstance(x, str)]
    jdSkillMatched = [x.lower() for x in jdSkillMatched if isinstance(x, str)]
    list1 = jdSkillMatched
    list2 = resumeCorpus
    results = {}
    for i in list1:
        results[i] = list2.count(i) 
    """
    #print("Dictionary is ",results)
    
   #end of code
    
    jdSkillMatched = []
    if isinstance(resume, str):
        resume = [x.lower() for x in resume if isinstance(x, str)]
    if isinstance(jdss, str):
        jdss = [x.lower() for x in jdSkillMatched if isinstance(x, str)]
    jdSkillMatched = jdss.intersection(resume)
    jdSkillCount = len(jdSkillMatched)
    if( jdSkillCount > 0):
        individualSkillWeightage = skill_weightage/jdSkillCount
    # list1 = jdSkillMatched
    # list2 = resumeCorpus
    # results = {}
    # for i in list1:
    #     results[i] = list2.count(i)  
    # constantValue = (individualSkillWeightage/skill_threshold)
    # Updating Dictionary
    # results.update({n: constantValue * results[n] for n in results.keys()})
    #print("updated dict is ", results)
    # print("Required Skills: ", jdss)
    # print("Matched Skills: ", jdSkillMatched)
    pct_match = round(len(jdSkillMatched) / len(jdss) * 100, 0)
    # TotalScore = sum(results.values())

    #print("Score is ", TotalScore)

    # fout.close()

    #progScore = min(programmingTotal/10.0, 1) * 5.0


    return (pct_match*skill_weightage)/100

def NonTechnicalSkillScore(interests, jdss, progWords = None):
    skill_weightage = 0
    skill_threshold = 5


    jdSkillMatched = []
    jdSkillMatched = jdss.intersection(interests)
    jdSkillCount = len(jdSkillMatched)
    if( jdSkillCount > 0):
        individualSkillWeightage = skill_weightage/jdSkillCount
    
    # print("Required Skills: ", jdss)
    # print("Matched Interests: ", jdSkillMatched)
    pct_match = round(len(jdSkillMatched) / len(jdss) * 100, 0)
    # TotalScore = sum(results.values())

    #print("Score is ", TotalScore)

    # fout.close()

    #progScore = min(programmingTotal/10.0, 1) * 5.0


    return (pct_match*skill_weightage)/100
    # return TotalScore
def rankEducation(jd_edu, res_edu):
    pass
def deleteResults():
    try:
        if os.path.exists("results.tex"):
            os.remove("results.tex")
        else:
            print("The file does not exist")
    except Exception as e:
        print(e)