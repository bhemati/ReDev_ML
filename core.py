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
import PyPDF2
import getCategoryJ as skills
from extract_expJ import ExtractExpJ
from striprtf.striprtf import rtf_to_text
from pathlib import Path
import pandas as pd
import json

warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')




class ResultElement:
    def __init__(self, jd,applicantId, filename,skillRank, name, phoneNo, email, nonTechSkills,exp,finalRank):
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
    
def res(jobfile,skillset,jd_exp):
    Resume_Vector = []
    Resume_skill_vector = []
    Resume_email_vector = []
    Resume_phoneNo_vector = []
    Resume_name_vector = []
    Resume_nonTechSkills_vector = []
    Resume_exp_vector = []
    Ordered_list_Resume = []
    LIST_OF_FILES = []
    LIST_OF_FILES_PDF = []
    LIST_OF_FILES_DOC = []
    LIST_OF_FILES_DOCX = []
    LIST_OF_FILES_JSON = []
    Resumes = []
    Jresumes = []
    Temp_pdf = []
    os.chdir("..")
    print(os.getcwd())
    os.chdir('Upload-Resume')
    jd_weightage = 15
    not_found = 'Not Found'
    extract_expJ = ExtractExpJ()
    
    
    for file in glob.glob('**/*.pdf', recursive=True):
        LIST_OF_FILES_PDF.append(file)
    for file in glob.glob('**/*.doc', recursive=True):
        LIST_OF_FILES_DOC.append(file)
    for file in glob.glob('**/*.docx', recursive=True):
        LIST_OF_FILES_DOCX.append(file)
    for file in glob.glob('**/*.rtf', recursive=True):
        LIST_OF_FILES_DOCX.append(file)
    for file in glob.glob('**/*.txt', recursive=True):
        LIST_OF_FILES_DOCX.append(file)  
    for file in glob.glob('**/*.json', recursive=True):
        LIST_OF_FILES_JSON.append(file)     

    LIST_OF_FILES = LIST_OF_FILES_DOC + LIST_OF_FILES_DOCX + LIST_OF_FILES_PDF + LIST_OF_FILES_JSON
    # LIST_OF_FILES.remove("antiword.exe")
    print("This is LIST OF FILES")
    print(LIST_OF_FILES)

    
    print("####### PARSING ########")
    # pythoncom.CoInitialize()
    
    for count,i in enumerate(LIST_OF_FILES):
       
        Temp = i.rsplit('.', 1)
        if Temp[1] == "pdf" or Temp[1] == "Pdf" or Temp[1] == "PDF":
            try:
                print(count," This is PDF" , i)
                with open(i,'rb') as pdf_file:
                    
                    read_pdf = PyPDF2.PdfFileReader(pdf_file)
                    # page = read_pdf.getPage(0)
                    # page_content = page.extractText()
                    # Resumes.append(Temp_pdf)

                    number_of_pages = read_pdf.getNumPages()
                    for page_number in range(number_of_pages): 

                        page = read_pdf.getPage(page_number)
                        page_content = page.extractText()
                        page_content = page_content.replace('\n', ' ')
                        # page_content.replace("\r", "")
                        Temp_pdf = str(Temp_pdf) + str(page_content)
                        # Temp_pdf.append(page_content)
                        # print(Temp_pdf)
                    Resumes.extend([Temp_pdf])
                    Temp_pdf = ''
                    Ordered_list_Resume.append(i)
                    # f = open(str(i)+str("+") , 'w')
                    # f.write(page_content)
                    # f.close()
            except Exception as e: 
                print(e)
                print(traceback.format_exc())
        elif Temp[1] == "doc" or Temp[1] == "Doc" or Temp[1] == "DOC":
            print(count," This is DOC" , i)
                
            parse_docfile(i)
         
        elif Temp[1] == "rtf" or Temp[1] == "Rtf" or Temp[1] == "RTF":
            print(count," This is Rtf" , i)
                
            try:
                
                rtf_path = Path(i)
                with rtf_path.open() as source:
                    docText = rtf_to_text(source.read())
                    
                c = [docText]
                Resumes.extend(c)
                Ordered_list_Resume.append(i)
            except Exception as e: print(e)
                
        elif Temp[1] == "docx" or Temp[1] == "Docx" or Temp[1] == "DOCX":
            print(count," This is DOCX" , i)
            try:
                a = textract.process(i)
                a = a.replace(b'\n',  b' ')
                a = a.replace(b'\r',  b' ')
                b = str(a)
                c = [b]
                Resumes.extend(c)
                Ordered_list_Resume.append(i)
            except Exception as e: print(e)
            
        elif Temp[1] == "txt" or Temp[1] == "Txt" or Temp[1] == "TXT":
            print(count," This is txt" , i)
            try:
                f = open(file,'r')
                lines = f.readlines()
                a =  "\n".join(lines)
                c = [str(a)]
                Resumes.extend(c)
                Ordered_list_Resume.append(i)
                f.close()
            except Exception as e: print(e) 

        elif Temp[1] == "json" :
            print(count," This is json" , i)
            try:
                with open(i) as json_data:
                    data = json.load(json_data)
                # df = pd.json_normalize(data)
                idx = 0
                for applicant in data:
                    Jresumes.append(applicant)
                    Ordered_list_Resume.append(applicant['user']['id'])
                print(Jresumes[0])
            except Exception as e: print(e)     
                    
                
        elif Temp[1] == "ex" or Temp[1] == "Exe" or Temp[1] == "EXE":
            print("This is EXE" , i)
            pass

    print("Done Parsing.")
    print("Please wait we are preparing ranking.")

    Job_Desc = 0
    
    try:
        tttt = str(jobfile)
        tttt = summarize(tttt, word_count=100)
        text = [tttt]
    except:
        text = 'None'

    
    vectorizer = TfidfVectorizer(stop_words='english')
    # print(text)
    vectorizer.fit(text)
    vector = vectorizer.transform(text)

    Job_Desc = vector.toarray()
    # print("\n\n")
    # print("This is job desc : " , Job_Desc)
    tempList = Ordered_list_Resume 
    os.chdir('../')
    flask_return = []
    
    for index,i in enumerate(Jresumes):

        # text = i
        # temptext = str(text)
        # tttt = str(text)
       
        
        try:
            # tttt = summarize(tttt, word_count=100) 
            # text = [tttt]
            # vector = vectorizer.transform(text)
            id = i['user']['id']
            exp_text = json.dumps(i['user']['experiences'])
            text = [exp_text]
            vector = vectorizer.transform(text)
            Resume_Vector.append(vector)
            user_skills = ", ".join([x['title'] for x in i['user']['skills']])
            skill_text = user_skills + exp_text
            Resume_skill_vector.append(skills.programmingScore(skill_text,jobfile+skillset))
            # exp_text = i.Work.to_string()
            experience = extract_expJ.get_features(i)
            first_name = i['user']['firstName']
            last_name = i['user']['lastName']
            applicant_name = first_name + ' ' + last_name
            Resume_name_vector.append(applicant_name)
            # temp_phone = entity.extract_phone_numbers(temptext)
            temp_phone = i["phoneNumber"]
            if(len(temp_phone) == 0):
                Resume_phoneNo_vector.append(not_found)
            else:
                 Resume_phoneNo_vector.append(temp_phone)
            # temp_email = entity.extract_email_addresses(temptext)
            temp_email = i["email"]
            if(len(temp_email) == 0):
                Resume_email_vector.append(not_found)
            else:
                 Resume_email_vector.append(temp_email)
                
           
            Resume_exp_vector.append(extract_expJ.get_exp_weightage(jd_exp,experience))
            Resume_nonTechSkills_vector.append(skills.NonTechnicalSkillScore(exp_text,jobfile+skillset))
            print("index:", index)
            print("Rank prepared for ",Ordered_list_Resume.__getitem__(index))
        except Exception:
            print(traceback.format_exc())
            tempList.__delitem__(index)
            
   
    # for index,i in enumerate(Resumes):

    #     text = i
    #     temptext = str(text)
    #     tttt = str(text)
       
        
    #     try:
    #         tttt = summarize(tttt, word_count=100) 
    #         text = [tttt]
    #         vector = vectorizer.transform(text)
    #         Resume_Vector.append(vector.toarray())
    #         Resume_skill_vector.append(skills.programmingScore(temptext,jobfile+skillset))
    #         experience = extract_exp.get_features(temptext)
    #         Resume_name_vector.append(experience)
    #         temp_phone = entity.extract_phone_numbers(temptext)
    #         if(len(temp_phone) == 0):
    #             Resume_phoneNo_vector.append(not_found)
    #         else:
    #              Resume_phoneNo_vector.append(temp_phone)
    #         temp_email = entity.extract_email_addresses(temptext)
    #         if(len(temp_email) == 0):
    #             Resume_email_vector.append(not_found)
    #         else:
    #              Resume_email_vector.append(temp_email)
                
           
    #         Resume_exp_vector.append(extract_exp.get_exp_weightage(jd_exp,experience))
    #         Resume_nonTechSkills_vector.append(skills.NonTechnicalSkillScore(temptext,jobfile+skillset))
    #         print("Rank prepared for ",Ordered_list_Resume.__getitem__(index))
    #     except Exception:
    #         print(traceback.format_exc())
    #         tempList.__delitem__(index)
            
   
    for index,i in enumerate(Resume_Vector):

        samples = i
        similarity = cosine_similarity(samples,Job_Desc)[0][0]
        """Ordered_list_Resume_Score.extend(similarity)"""
        #print(Resume_skill_vector)
        #print(Resume_nonTechSkills_vector)
        #print(Resume_exp_vector)
        final_rating = round(similarity*jd_weightage,2)+Resume_skill_vector.__getitem__(index)+Resume_nonTechSkills_vector.__getitem__(index)+Resume_exp_vector.__getitem__(index)
        res = ResultElement(round(similarity*jd_weightage,2), tempList.__getitem__(index),tempList.__getitem__(index),round(Resume_skill_vector.__getitem__(index),2),
                           Resume_name_vector.__getitem__(index),Resume_phoneNo_vector.__getitem__(index),Resume_email_vector.__getitem__(index),
                           Resume_nonTechSkills_vector.__getitem__(index),Resume_exp_vector.__getitem__(index),round(final_rating,2))
        flask_return.append(res)
    flask_return.sort(key=lambda x: x.finalRank, reverse=True)
    return flask_return
 