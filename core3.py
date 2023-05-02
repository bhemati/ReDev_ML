# import pythoncom
import glob
import os
import warnings
import textract
# from win32com.client import Dispatch
import traceback
import extractEntities as entity
from gensim.summarization.summarizer import summarize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# import PyPDF2
import getCategoryJ as skills
from extract_expJ import ExtractExpJ
# from striprtf.striprtf import rtf_to_text
from pathlib import Path
import pandas as pd
import json
import urllib.request
import spacy
from spacy.pipeline import EntityRuler
from multiprocessing import Process, Manager

manager = Manager()
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')




class ResultElement:
    def __init__(self, jd,applicantId, filename,skillRank, name, phoneNo, email, nonTechSkills,exp,finalRank, education, location):
        self.jd = jd
        self.filename = filename
        self.skillRank = skillRank
        self.name = name
        self.applicantId = applicantId
        # self.jobId = jobId
        self.phoneNo = phoneNo
        self.email = email
        self.nonTechSkills = nonTechSkills
        self.exp = exp
        self.finalRank = finalRank
        self.education = education
        self.location = location


def getfilepath(loc):
    temp = str(loc)
    temp = temp.replace('\\', '/')
    return temp

def parse_docfile(file):
    # pythoncom.CoInitialize()
    # wordapp = Dispatch("Word.Application")
    # doc = wordapp.Documents.Open(os.getcwd()+"/"+file)
    # docText = doc.Content.Text
    # wordapp.Quit()
    docText = textract.process(os.getcwd()+"/"+file)
    return docText



def get_degree_res(edu_info):
    try:
        for edu in edu_info:
            list_edu = [edu['degree'] + ' ' + edu['field'] for edu in edu_info]
            deg_res = ", ".join(list_edu)
        return deg_res
    except Exception: 
        return None

def res(jobfile,skillset,jd_exp, user_ids):
    Resume_Vector = []
    Resume_skill_vector = []
    Resume_email_vector = []
    Resume_phoneNo_vector = []
    Resume_name_vector = []
    Resume_nonTechSkills_vector = []
    Resume_exp_vector = []
    Resume_edu_vector = []
    Ordered_list_Resume = []
    Resume_assessment_score = []
    Jresumes = []
    # os.chdir("..")
    # print(os.getcwd())
    # os.chdir('Upload-Resume')
    jd_weightage = 15
    not_found = 'Not Found'
    extract_expJ = ExtractExpJ()
    assessment_weightage = 15

    PROJECT_DIR = os.path.dirname(os.getcwd()) + '/'
    skill_pattern_path = "/home/behrad/ReDev_ML-main/skill_patterns.jsonl"
    absolutepath = os.path.dirname(__file__)
    skillset_path = absolutepath + "/skillset"

    nlp = spacy.load(skillset_path)
    resume_text = jobfile+skillset
    def add_newruler_to_pipeline(skill_pattern_path):
        '''Reads in all created patterns from a JSONL file and adds it to the pipeline after PARSER and before NER'''
        ruler = nlp.add_pipe("entity_ruler")
        ruler.from_disk(skill_pattern_path)
    def create_skill_set(doc):
        '''Create a set of the extracted skill entities of a doc'''
        
        return set([ent.label_.upper()[6:] for ent in doc.ents if 'skill' in ent.label_.lower()])

    
    # add_newruler_to_pipeline(skill_pattern_path)
    jd_skillsets = create_skill_set(nlp(resume_text))
    # print("skillsets:",jd_skillsets)
    jd_degree_required = skills.get_degree_jd(skillset)
    
    # print("####### PARSING ########")
    
    ####### TODO
    ## Get input the same way that its on postman, the links will come as 'job' and 'applicant'
    # print("Parsing the URL")
    for user in user_ids:
        user_url = "https://api.redev.jobs/ml/user/{}/".format(user)
        try:
            with urllib.request.urlopen(user_url) as url:
                applicant = json.load(url)
                data2 = {"user": ""}
                data2['user'] = applicant
                Jresumes.append(data2)
                Ordered_list_Resume.append(applicant['id'])
                    
        except Exception as e: print(e)
    
    # try:
    #     with open('resumes.json', 'r') as fin:
    #         data = json.load(fin)
    #         for applicant in data:
    #             data2 = {"user": ""}
    #             data2['user'] = applicant
    #             Jresumes.append(data2)
    #             Ordered_list_Resume.append(applicant['id'])
    # except Exception as e: print(e)
    # print("Done Parsing.")
    # print("Please wait we are preparing ranking.")

    Job_Desc = 0
    text = ["init text"]
    # print("jobfile: ", jobfile)
    # print("text: ", text)
    try:
        tttt = str(jobfile)
        # tttt = summarize(tttt, word_count=100) ## code breaking bug
        text = [tttt]
        # print("text in try: ", text)
    except:
        text = 'None'

    
    vectorizer = TfidfVectorizer(stop_words='english')
    # print("print text line 219 core: ",text)
    vectorizer.fit(text)
    vector = vectorizer.transform(text)

    Job_Desc = vector.toarray()
    # print("\n\n")
    # print("This is job desc : " , Job_Desc)
    tempList = Ordered_list_Resume 
    # os.chdir('../')
    flask_return = manager.list()
    # def rank(index, i):
    for index,i in enumerate(Jresumes):

        # text = i
        # temptext = str(text)
        # tttt = str(text)
       
        
        try:
            # tttt = summarize(tttt, word_count=100) 
            # text = [tttt]
            # vector = vectorizer.transform(text)
            ### Changed from user.id to id
            id = i['user'].get('id')
            exp_text = json.dumps(i['user'].get('experiences'))
            text_e = [exp_text]
            vector = vectorizer.transform(text_e)
            
            user_skills = ", ".join([x['title'] for x in i['user'].get('skills')])
            skill_text = user_skills + exp_text
            resume_skillset = create_skill_set(nlp(skill_text))
            # print("resume skill set:", resume_skillset)
            user_interest = ", ".join([x['title'] for x in i['user'].get('interests')])
            interest_skillset = create_skill_set(nlp(user_interest))
            # print("interest skillset:", interest_skillset)
            # exp_text = i.Work.to_string()
            experience = extract_expJ.get_features(i)
            edu_list = get_degree_res(i['user'].get('educations'))
            
                
            first_name = i['user'].get('firstName')
            last_name = i['user'].get('lastName')
            applicant_name = first_name + ' ' + last_name
            # temp_phone = entity.extract_phone_numbers(temptext)
            temp_phone = i.get("phoneNumber")
            if(i.get("assessmentScore") != None):
                try:
                    ass_score = float(i.get("assessmentScore"))
                except Exception as e:
                    print(e)
            else:
                ass_score = 0.0
            if(temp_phone is None or len(temp_phone) == 0 ):
                phone_no = not_found
                Resume_phoneNo_vector.append(phone_no)
            else:
                phone_no = temp_phone
                Resume_phoneNo_vector.append(phone_no)
            # temp_email = entity.extract_email_addresses(temptext)
            temp_email = i["user"].get("email")
            if(len(temp_email) == 0):
                user_email = not_found
                Resume_email_vector.append(not_found)
            else:
                user_email = temp_email
                Resume_email_vector.append(temp_email)
                
            if jd_degree_required and edu_list:
                edu_score = skills.eduScore(edu_list, jd_degree_required, skill_weightage=20)
                # Resume_edu_vector.append(edu_score)
            elif edu_list:
                edu_score = skills.eduScore(edu_list, skillset, skill_weightage=20)
                # Resume_edu_vector.append(edu_score)
            else:
                edu_score = 0
                # Resume_edu_vector.append(edu_score)
            applicant_location = ""
            edu_score = round(edu_score)
            skill_score = skills.programmingScore(resume_skillset,jd_skillsets)
            exp_score = extract_expJ.get_exp_weightage(jd_exp,experience)
            nontech_skill_score = skills.NonTechnicalSkillScore(interest_skillset,jd_skillsets)
            Resume_edu_vector.append(edu_score)
            Resume_skill_vector.append(skill_score)
            Resume_name_vector.append(applicant_name)
            Resume_exp_vector.append(exp_score)
            Resume_nonTechSkills_vector.append(nontech_skill_score)
            Resume_Vector.append(vector)
            Resume_assessment_score.append(ass_score)
            # print("Applicant Name:", applicant_name)
            # print("index:", index)
            samples = vector
            similarity = cosine_similarity(samples,Job_Desc)[0][0]
            """Ordered_list_Resume_Score.extend(similarity)"""
            #print(Resume_skill_vector)
            #print(Resume_nonTechSkills_vector)
            #print(Resume_exp_vector)
            # final_rating = round(similarity*jd_weightage,2)+Resume_skill_vector.__getitem__(index) \
            # +Resume_nonTechSkills_vector.__getitem__(index)+Resume_exp_vector.__getitem__(index) \
            # +round(Resume_assessment_score.__getitem__(index)*assessment_weightage,2) \
            # +Resume_edu_vector.__getitem__(index)
            # res = ResultElement(round(similarity*jd_weightage,2), tempList.__getitem__(index),tempList.__getitem__(index),round(Resume_skill_vector.__getitem__(index),2),
            #                 Resume_name_vector.__getitem__(index),Resume_phoneNo_vector.__getitem__(index),Resume_email_vector.__getitem__(index),
            #                 Resume_nonTechSkills_vector.__getitem__(index),Resume_exp_vector.__getitem__(index),round(final_rating,2),
            #                 Resume_edu_vector.__getitem__(index))
            final_rating = round(similarity*jd_weightage,2)+skill_score \
            +nontech_skill_score+exp_score \
            +round(ass_score*assessment_weightage,2) \
            +edu_score
            final_rating = final_rating / 120 * 100
            res = ResultElement(round(similarity*jd_weightage,2), i['user']['id'],id,round(skill_score,2),
                            applicant_name,phone_no,user_email,
                            nontech_skill_score,exp_score,round(final_rating,2),
                            edu_score, applicant_location)
            flask_return.append(res.__dict__)
            # print("edu score: ", edu_score)
            # print("Rank prepared for ",Ordered_list_Resume.__getitem__(index))
        except Exception:
            print(traceback.format_exc())
            tempList.__delitem__(index)
            # Resume_Vector.__delitem__(index)
            
    ## Multi processing logic
    # processes = [Process(target=rank, args=(ind, inst)) for ind,inst in enumerate(Jresumes)]
    # rank
# start all processes
#     for process in processes:
#         process.start()
# # wait for all processes to complete
#     for process in processes:
#         process.join()   

    ## End of Multiproccessing logic    
    # for index,i in enumerate(Resume_Vector):

        
    # flask_return.sort(key=lambda x: x.finalRank, reverse=True)
    # print(flask_return[0])
    # print(type(flask_return[0]))
    skills.deleteResults()
    return flask_return
 