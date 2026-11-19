"""
MediCare.AI — Shared data: doctors, clinical departments & checkup billing protocols
XLM-RoBERTa transformer for sentiment scoring (free, multilingual, best for reviews)
"""
from functools import lru_cache

# ── XLM-RoBERTa sentiment pipeline (lazy loaded) ──────────────────
_pipe = None
def get_pipe():
    global _pipe
    if _pipe is None:
        try:
            from transformers import pipeline
            _pipe = pipeline("sentiment-analysis",
                             model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
                             max_length=512, truncation=True)
        except Exception:
            _pipe = None
    return _pipe

def xlm_score(texts: list) -> int:
    """
    Returns COUNT of positive reviews (integer 0 to len(texts), max 10).

    Logic:
      - If XLM-RoBERTa model is available: count reviews labelled 'positive'
      - Fallback: EVERY review is assumed positive by default.
        Only subtract if the review contains a clear negative word
        (English, Hindi Unicode, or Gujarati Unicode).
        This fixes the problem where neutral English reviews
        like "Trusted brand Cipla top quality" were not being counted
        because they had no keyword match.
    """
    pipe = get_pipe()
    if pipe and texts:
        try:
            results = pipe(texts[:10])
            pos = sum(1 for r in results if r['label'] == 'positive')
            return pos
        except Exception:
            pass

    # ── Keyword fallback ──────────────────────────────────────────
    # English negatives
    NEG_EN = [
        'bad','poor','worst','terrible','horrible','useless','waste','fake',
        'awful','disappointing','broken','pathetic','ineffective','wrong',
        'side effect','no improvement','did not work','not work','no result',
        'no effect','no benefit','no difference','money wasted','waste of money',
    ]
    # Hindi negatives (Unicode — actual Devanagari script)
    NEG_HI = [
        'बेकार','खराब','बुरा','बर्बाद','फायदा नहीं','कोई फायदा नहीं',
        'बहुत बुरा','कोई असर नहीं','पैसे बर्बाद','कोई फर्क नहीं',
        'साइड इफेक्ट','नहीं हुआ','बहुत खराब',
    ]
    # Gujarati negatives (Unicode — actual Gujarati script)
    NEG_GU = [
        'ખૂબ ખરાબ','બેકાર','ખૂબ નિરાશ','ફાયદો ઓછો','ફાયદો ન થયો',
        'પૈસા બગડ્યા','ફર્ક નથી','ફર્ક ન પડ્યો','ખૂબ ખરાબ',
        'કોઈ ફરક નથી','કોઈ ફાયદો ન','ખૂબ ખરાબ ક્વોલિટી',
    ]
    NEG_ALL = NEG_EN + NEG_HI + NEG_GU

    pos = 0
    for t in texts:
        tl = t.lower()
        # default: count as positive
        # only skip if review contains a negative signal
        is_negative = any(w in tl for w in NEG_ALL)
        if not is_negative:
            pos += 1
    return pos

@lru_cache(maxsize=256)
def cached_xlm(reviews_tuple: tuple) -> int:
    return xlm_score(list(reviews_tuple))

def product_nlp_score(p: dict) -> float:
    """
    Score = positive_count * 0.6 + rating * 0.4
    positive_count : 0-10  (positive reviews detected by NLP)
    rating         : 0-5   (star rating)
    Max possible   : 10*0.6 + 5*0.4 = 8.0
    """
    reviews = p.get('reviews', [])
    pos = cached_xlm(tuple(reviews)) if reviews else 7
    return round(pos * 0.6 + p['rating'] * 0.4, 1)

def doctor_nlp_score(d: dict) -> float:
    """
    Score = positive_count * 0.6 + rating * 0.4
    Same formula as product_nlp_score.
    """
    reviews = d.get('reviews', [])
    pos = cached_xlm(tuple(reviews)) if reviews else 7
    return round(pos * 0.6 + d['rating'] * 0.4, 1)

def discounted(p: dict) -> float:
    return round(p['price'] * (1 - p['disc'] / 100), 0)

# ── DEPARTMENTS ────────────────────────────────────────────────────
DEPTS = [
    {'name':'Cardiology',      'icon':'❤️', 'color':'#dc2626'},
    {'name':'Dermatology',     'icon':'✨', 'color':'#db2777'},
    {'name':'Pediatrics',      'icon':'👶', 'color':'#2563eb'},
    {'name':'Orthopedics',     'icon':'🦴', 'color':'#d97706'},
    {'name':'Neurology',       'icon':'🧠', 'color':'#7c3aed'},
    {'name':'Endocrinology',   'icon':'⚗️', 'color':'#059669'},
    {'name':'Gastroenterology','icon':'🫁', 'color':'#0891b2'},
    {'name':'Psychiatry',      'icon':'🧘', 'color':'#0369a1'},
    {'name':'Ophthalmology',   'icon':'👁️', 'color':'#065f46'},
    {'name':'ENT',             'icon':'👂', 'color':'#92400e'},
]

# ── DOCTORS — 5 per department ─────────────────────────────────────
# Some doctors have mixed Hindi/Gujarati/English reviews with negatives
# so NLP can actually differentiate and rank meaningfully within each dept.
DOCTORS = [
    # CARDIOLOGY
    {'id':1,'name':'Priya Sharma','dept':'Cardiology','spec':'Interventional Cardiologist','exp':14,'rating':4.9,'fee':800,'emoji':'👩‍⚕️','slots':['9:00 AM','10:00 AM','11:00 AM','2:00 PM','3:00 PM','4:00 PM'],'tags':['heart','cardiac','bp','chest'],'reviews':['Best cardiologist in the city very thorough examination','Excellent doctor diagnosed my blockage immediately','Very professional and caring explains everything clearly','My father recovered well under her care highly recommend','Quick diagnosis and right medication no side effects','Stent procedure was very smooth and painless','Regular follow-ups are very detailed and reassuring','Treated my mother for 2 years outstanding results','Very calm and composed even in emergency','Explained everything before procedure very well']},
    {'id':2,'name':'Vikram Nair','dept':'Cardiology','spec':'Cardiac Electrophysiologist','exp':11,'rating':4.7,'fee':900,'emoji':'👨‍⚕️','slots':['8:00 AM','9:00 AM','10:00 AM','2:00 PM','3:00 PM'],'tags':['arrhythmia','pacemaker','heart rhythm'],'reviews':['Fixed my arrhythmia problem perfectly thank you doctor','Very knowledgeable about heart rhythm disorders','Pacemaker procedure went very smoothly under his care','Explained the procedure in very simple language','Good follow-up care after the surgery helped recovery','Ablation was a success no more palpitations','Very patient with all my questions before procedure','ECG interpretation skills are excellent','Changed my medication and symptoms improved greatly','Saved me from unnecessary surgery with correct diagnosis']},
    # Mixed reviews — Hindi/Gujarati negatives, will rank lower in Cardiology
    {'id':3,'name':'Ananya Krishnan','dept':'Cardiology','spec':'Preventive Cardiologist','exp':9,'rating':4.6,'fee':700,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','12:00 PM','3:00 PM','4:00 PM'],'tags':['cholesterol','prevention','lifestyle'],'reviews':['Great advice on diet and lifestyle changes that worked','Very helpful in preventing my heart disease development','બહુ ખરાબ અનુભવ થયો ડૉક્ટર ધ્યાન નથી આપતા','પૈસા બગડ્યા કોઈ ફાયદો ન થયો ખૂબ નિરાશ','Prevented me from needing medication with lifestyle changes','Young doctor but very knowledgeable about prevention','बहुत लंबा इंतजार करना पड़ा और फिर भी कोई हल नहीं बुरा','Very scientific approach to cardiac prevention','पैसे बर्बाद हुए कोई फायदा नहीं हुआ बहुत खराब','Best preventive cardiology consultation I have had']},
    {'id':4,'name':'Suresh Menon','dept':'Cardiology','spec':'Echocardiography Specialist','exp':16,'rating':4.8,'fee':750,'emoji':'👨‍⚕️','slots':['9:00 AM','11:00 AM','2:00 PM','4:00 PM'],'tags':['echo','valve','heart scan'],'reviews':['Best echocardiography specialist I have visited hands down','Accurate diagnosis of my valve problem first time','Very experienced has seen thousands of cases clearly','Reports explained clearly with visual aids shown','Reasonable fees for the outstanding quality of service','Found my mitral valve problem that others missed','Very thorough echo examination takes time to explain','Stress echo was conducted very professionally','Detailed wall motion analysis was very helpful','Would recommend to anyone needing cardiac imaging']},
    {'id':5,'name':'Deepa Iyer','dept':'Cardiology','spec':'Heart Failure Specialist','exp':12,'rating':4.7,'fee':850,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','3:00 PM','4:00 PM','5:00 PM'],'tags':['heart failure','pump','ejection fraction'],'reviews':['Managed my heart failure wonderfully quality of life improved','Quality of life improved significantly after her treatment plan','Very compassionate doctor with great clinical knowledge','Regular monitoring and timely intervention saved my life','Excellent coordination with other specialists when needed','Fluid management protocol she designed is excellent','Device therapy recommendation was absolutely correct','BNP levels came down dramatically with her care','Very clear explanation of heart failure self management','Best heart failure doctor in the region without doubt']},
    # DERMATOLOGY
    {'id':6,'name':'Arjun Mehta','dept':'Dermatology','spec':'Cosmetic & Clinical Dermatologist','exp':10,'rating':4.8,'fee':600,'emoji':'👨‍⚕️','slots':['10:00 AM','11:00 AM','12:00 PM','3:00 PM','4:00 PM'],'tags':['skin','acne','hair','rash'],'reviews':['Acne cleared completely in 3 months amazing results','Best dermatologist for skin problems highly recommend','Hair fall stopped completely after his treatment protocol','Very modern approach with latest treatments and technology','Great results for my hyperpigmentation dark spots gone','Chemical peel results were outstanding very professional','Prescribed isotretinoin carefully with proper monitoring','Post acne scarring treatment gave excellent improvement','Very hygenic clinic and professional staff','Would not go anywhere else for my skin concerns']},
    {'id':7,'name':'Kavitha Rao','dept':'Dermatology','spec':'Trichologist & Hair Specialist','exp':8,'rating':4.7,'fee':550,'emoji':'👩‍⚕️','slots':['9:00 AM','10:00 AM','11:00 AM','2:00 PM','3:00 PM'],'tags':['hair loss','alopecia','scalp'],'reviews':['My hair regrowth has been absolutely amazing','Best trichologist with very scientific approach to hair','PRP treatment done here gave excellent visible results','Detailed scalp analysis before starting any treatment','Very honest about what treatments will actually work','Diagnosed my DUPA early and started right treatment','Hair transplant referral was excellent and timely','Nutritional deficiency causing hair loss found quickly','Minoxidil protocol and monitoring has been perfect','Very empathetic about hair loss being distressing issue']},
    # Mixed — some negative reviews, will rank lower in Dermatology
    {'id':8,'name':'Rahul Bhat','dept':'Dermatology','spec':'Psoriasis & Eczema Specialist','exp':13,'rating':4.6,'fee':650,'emoji':'👨‍⚕️','slots':['8:00 AM','9:00 AM','10:00 AM','2:00 PM','4:00 PM'],'tags':['psoriasis','eczema','atopic'],'reviews':['Psoriasis under control for first time in years great','સારવાર પછી કોઈ ફરક નથી પડ્યો ખૂબ નિરાશ થઈ','Very up-to-date with the latest treatment guidelines','No major side effects with the treatment plan given','दवाई से कोई फायदा नहीं हुआ पैसे बर्बाद बेकार डॉक्टर','UVB phototherapy protocol designed was very effective','Taught me excellent trigger avoidance strategies','ઘણા મોંઘા ચાર્જ છે ફાયદો ઓછો ખૂબ ખરાબ','Regular monitoring makes me feel very safe on biologics','Best psoriasis doctor I have seen in 10 years of suffering']},
    {'id':9,'name':'Sneha Pillai','dept':'Dermatology','spec':'Aesthetic & Laser Dermatologist','exp':7,'rating':4.9,'fee':800,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','2:00 PM','3:00 PM','4:00 PM'],'tags':['laser','botox','anti-aging'],'reviews':['Laser treatment results are truly outstanding incredible','Best aesthetic dermatologist in this entire area without doubt','Very natural looking filler results no frozen face at all','Skin is absolutely glowing after chemical peel session','Very hygienic clinic with absolutely latest equipment','CO2 laser for acne scars gave amazing improvement','Thread lift results were very natural and long lasting','Botox dosing was perfect no frozen look at all','Always does what is actually needed no overselling','Best investment I made in my skin career']},
    {'id':10,'name':'Mohan Das','dept':'Dermatology','spec':'Pediatric Dermatologist','exp':11,'rating':4.7,'fee':500,'emoji':'👨‍⚕️','slots':['9:00 AM','10:00 AM','11:00 AM','3:00 PM','4:00 PM'],'tags':['child skin','baby rash','pediatric'],'reviews':['Very gentle with my baby daughter made her feel safe','Child friendly approach with no fear or crying at all','Diagnosed my son condition correctly in very first visit','Mother friendly explanations very patient with our questions','Great at managing childhood eczema with gentle approach','Baby atopic dermatitis now well controlled with his regimen','Very good at reassuring anxious parents like me','Molluscum treatment was quick and relatively painless','Excellent at differentiating viral from bacterial skin infections','Would not take my children to any other skin doctor']},
    # NEUROLOGY
    {'id':11,'name':'Kavita Reddy','dept':'Neurology','spec':'Stroke & Epilepsy Specialist','exp':12,'rating':4.8,'fee':1000,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','2:00 PM','3:00 PM','4:00 PM'],'tags':['brain','migraine','seizure','stroke'],'reviews':['Migraine completely controlled with her comprehensive protocol','Best neurologist very thorough investigation of all symptoms','Epilepsy seizures reduced by 90 percent significant improvement','Very systematic approach to diagnosis using all evidence','Explains complex MRI reports in very simple terms','Started me on right AED that has no side effects','EEG interpretation and explanation was excellent','Stroke prevention advice has been outstanding and practical','Very quick to respond to medication changes needed','Changed my life with correct epilepsy diagnosis finally']},
    {'id':12,'name':'Anand Gupta','dept':'Neurology','spec':'Movement Disorder Specialist','exp':15,'rating':4.7,'fee':1100,'emoji':'👨‍⚕️','slots':['9:00 AM','10:00 AM','2:00 PM','3:00 PM'],'tags':['parkinson','tremor','movement'],'reviews':['Parkinson management dramatically improved my quality of life','Very experienced with deep brain stimulation procedures','Movement tremors reduced significantly after his treatment plan','Very compassionate with elderly patients and their families','Latest treatment protocols are always used in his practice','DBS programming was excellent tremors completely controlled','Levodopa optimization was done very carefully and effectively','Very good at explaining Parkinson progression to family','Always available for urgent calls regarding medication issues','Best Parkinson specialist in the region by far']},
    {'id':13,'name':'Preethi Nair','dept':'Neurology','spec':'Headache & Migraine Specialist','exp':8,'rating':4.9,'fee':900,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','12:00 PM','3:00 PM','4:00 PM'],'tags':['headache','migraine','cluster'],'reviews':['Chronic headache cured after 10 long years of suffering','Best migraine specialist I have ever seen in my life','Botox for chronic migraine worked absolutely brilliantly','Preventive treatment protocol completely changed my entire life','Very scientific systematic approach to headache management','Diagnosed my NDPH when others called it stress headache','Nerve block procedure for cluster headache was very effective','Keeping a headache diary as she advised was very helpful','Topamax dosing was done very gradually no side effects','From 20 headache days to 2 per month remarkable result']},
    # Mixed — negative reviews, ranks lower in Neurology
    {'id':14,'name':'Rajesh Kumar','dept':'Neurology','spec':'Spine & Nerve Specialist','exp':13,'rating':4.6,'fee':950,'emoji':'👨‍⚕️','slots':['8:00 AM','9:00 AM','10:00 AM','2:00 PM','3:00 PM'],'tags':['spine','disc','nerve','sciatica'],'reviews':['Sciatica pain completely gone after nerve block procedure','Avoided major surgery with his conservative management approach','ઘૂંટણ અને કમરનો દુખાવો ઓછો નથી થયો ખૂબ ખરાબ','EMG and NCS results explained very clearly and understandably','बहुत महंगी फीस है और कोई खास फर्क नहीं पड़ा बुरा','L4-L5 disc issue managed without surgery brilliant','दवाई से साइड इफेक्ट हुआ डॉक्टर ने ध्यान नहीं दिया बुरा','Very good at determining which cases actually need surgery','Physiotherapy referral combined with medication worked perfectly','MRI findings explained in language I could actually understand']},
    {'id':15,'name':'Meena Sharma','dept':'Neurology','spec':'Dementia & Memory Specialist','exp':10,'rating':4.7,'fee':850,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','2:00 PM','3:00 PM','5:00 PM'],'tags':['dementia','alzheimer','memory'],'reviews':['Mother dementia is now well managed under her care','Very empathetic approach to a very difficult condition','Family counseling sessions were absolutely invaluable help','Latest cognitive assessment tools give clear picture','Great support system provided for caregivers like me','Diagnosed early MCI which allowed us to plan well','Caregiver burnout addressed very sensitively and practically','Cognitive rehabilitation program has helped mother stay engaged','Very clear guidance on legal and financial planning needed','Best doctor we have found for this terrible condition']},
    # OPHTHALMOLOGY
    {'id':16,'name':'Deepa Gupta','dept':'Ophthalmology','spec':'Retina & Cataract Surgeon','exp':14,'rating':4.8,'fee':700,'emoji':'👩‍⚕️','slots':['9:00 AM','10:00 AM','11:00 AM','2:00 PM','3:00 PM'],'tags':['eye','vision','cataract','retina'],'reviews':['Cataract surgery done with absolutely zero complications excellent','Vision restored to perfect 6/6 after her brilliant surgery','Retinal detachment treated very successfully full vision saved','Very advanced modern equipment in her excellent clinic','LASIK results here are outstanding 5 years still perfect','Vitrectomy procedure was very smooth quick recovery','AMD treatment with injections is expertly managed here','Post cataract care instructions were very clear and detailed','Always explains procedure risks and benefits very clearly','Best eye surgeon I know incredible surgical skill']},
    {'id':17,'name':'Rajiv Sinha','dept':'Ophthalmology','spec':'Glaucoma Specialist','exp':11,'rating':4.7,'fee':650,'emoji':'👨‍⚕️','slots':['9:00 AM','10:00 AM','2:00 PM','3:00 PM','4:00 PM'],'tags':['glaucoma','eye pressure','optic nerve'],'reviews':['Glaucoma detected very early and now perfectly well managed','Eye pressure completely controlled with minimal number of drops','Very thorough visual field testing and interpretation skills','Explained glaucoma progression risks very clearly to me','Regular careful monitoring has absolutely preserved my vision','SLT laser procedure was very effective and pain free','Very good at explaining iridotomy procedure beforehand','Trabeculectomy surgery was excellently performed with great result','Optic nerve analysis is extremely thorough every visit','Best glaucoma doctor and prevented me from going blind']},
    {'id':18,'name':'Sunita Khanna','dept':'Ophthalmology','spec':'Cornea & External Eye','exp':9,'rating':4.6,'fee':600,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','12:00 PM','3:00 PM','4:00 PM'],'tags':['cornea','dry eye','contact lens'],'reviews':['Keratoconus treated perfectly with cross-linking procedure here','Dry eye syndrome finally well managed with her guidance','Contact lens fitting advice was the best I have received','Very gentle examination technique makes it comfortable always','Corneal graft coordinated absolutely seamlessly excellent team work','Best corneal topography analysis and explanation I received','Corneal ulcer treated very aggressively and effectively','Eye drop compliance schedule she designed is very practical','Scleral lens fitting was perfect for my dry eye','Best cornea specialist in the city without any doubt']},
    {'id':19,'name':'Karthik Iyer','dept':'Ophthalmology','spec':'Pediatric Ophthalmologist','exp':8,'rating':4.8,'fee':550,'emoji':'👨‍⚕️','slots':['9:00 AM','10:00 AM','11:00 AM','3:00 PM','4:00 PM'],'tags':['child eye','squint','amblyopia'],'reviews':['Squint surgery on my daughter gave perfect aligned result','Lazy eye amblyopia treatment was very very successful','Very child-friendly playful approach children like him a lot','Vision therapy program for my son is very well designed','Spectacle prescription was very accurate for child first visit','Strabismus diagnosed correctly when local doctor missed it','Patching therapy compliance improved with his encouragement','Very good at explaining to parents what is happening','My child does not cry at all in his clinic','Surgery outcome for squint was absolutely beautiful result']},
    {'id':20,'name':'Madhuri Bose','dept':'Ophthalmology','spec':'Neuro-Ophthalmologist','exp':13,'rating':4.7,'fee':800,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','2:00 PM','3:00 PM'],'tags':['optic nerve','visual field','double vision'],'reviews':['Rare optic neuritis was diagnosed correctly here thankfully','Visual field loss has stabilized completely with her treatment','Complex double vision case was solved with correct prism','Excellent coordination with neurology team for my case','Very thorough investigation always done before starting treatment','Idiopathic intracranial hypertension managed perfectly here','Lumbar puncture was done very smoothly and professionally','Explained papilloedema significance very clearly to me','Thyroid eye disease treatment was very comprehensive good','Best specialist at the intersection of eye and brain']},
    # PSYCHIATRY
    {'id':21,'name':'Suresh Nair','dept':'Psychiatry','spec':'Anxiety & Depression Specialist','exp':9,'rating':4.7,'fee':600,'emoji':'👨‍⚕️','slots':['9:00 AM','10:00 AM','11:00 AM','4:00 PM','5:00 PM'],'tags':['anxiety','depression','stress','OCD'],'reviews':['Depression finally under complete control after his therapy','Very non-judgmental and deeply compassionate approach always','CBT sessions have completely changed my negative thinking patterns','Absolutely no stigma or judgment in this clinic at all','Medication adjustments were done very carefully and thoughtfully','Recovered from severe depression in just 3 months amazing','OCD treatment with ERP therapy was excellently conducted','Very good at explaining the science behind mental illness','SSRI dosing was gradual and side effects were minimal','Changed my entire perspective on mental health treatment']},
    {'id':22,'name':'Nisha Patel','dept':'Psychiatry','spec':'Child & Adolescent Psychiatrist','exp':8,'rating':4.8,'fee':700,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','2:00 PM','3:00 PM','4:00 PM'],'tags':['ADHD','autism','child mental health'],'reviews':['Son ADHD is now managed absolutely beautifully excellent','Autism spectrum assessment was extremely thorough and detailed','Very patient with difficult child behaviors during sessions','Family therapy sessions have been incredibly helpful for us','School performance has improved so dramatically since starting','ADHD medication dosing was done very carefully step by step','Behavioral intervention plan she designed works very well','Social skills group she recommended was very beneficial','Very good at helping parents understand child needs','Best child psychiatrist for developmental conditions in city']},
    # Mixed — negative reviews in Hindi/Gujarati, ranks lower
    {'id':23,'name':'Deepak Mishra','dept':'Psychiatry','spec':'Addiction Specialist','exp':12,'rating':4.6,'fee':650,'emoji':'👨‍⚕️','slots':['9:00 AM','10:00 AM','2:00 PM','3:00 PM'],'tags':['addiction','alcohol','de-addiction'],'reviews':['Brother has recovered from alcohol addiction here truly amazing','Very structured comprehensive de-addiction program they follow','ડૉ. સાથે વાત કરવી ખૂબ અઘરી હતી ઓછો સમય આપ્યો ખૂબ ખરાબ','Relapse prevention strategies he taught are very effective','इलाज से कोई फायदा नहीं हुआ पैसे बर्बाद बेकार डॉक्टर','Family therapy component of his program was invaluable','Motivational interviewing approach made brother want to change','बहुत बुरा अनुभव डॉक्टर ने ध्यान नहीं दिया और पैसे लिए','12 step program integration with medical treatment works','Two years sober now thanks to this excellent doctor']},
    {'id':24,'name':'Priya Menon','dept':'Psychiatry','spec':'Sleep Disorder Specialist','exp':7,'rating':4.7,'fee':550,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','3:00 PM','4:00 PM','5:00 PM'],'tags':['sleep','insomnia','sleep apnea'],'reviews':['Insomnia was completely cured without any heavy medication','Sleep hygiene advice she gave was absolutely excellent practical','CBT for insomnia was incredibly effective no sleeping pills','Sleep study was conducted very professionally good report','10 years of terrible sleep problems solved in only 2 months','CPAP titration for sleep apnea was excellently managed','Diagnosed my restless legs syndrome correctly when others missed','Sleep diary analysis was very detailed and informative','Light therapy timing advice dramatically improved my sleep','Best sleep doctor completely changed my quality of life']},
    {'id':25,'name':'Amit Sharma','dept':'Psychiatry','spec':'Trauma & PTSD Specialist','exp':10,'rating':4.8,'fee':700,'emoji':'👨‍⚕️','slots':['10:00 AM','11:00 AM','2:00 PM','3:00 PM'],'tags':['trauma','PTSD','grief'],'reviews':['PTSD from terrible accident finally treated very effectively','EMDR therapy worked absolute wonders for my trauma','Very safe completely confidential and non-judgmental environment','Trauma processing sessions were deeply healing thank you doctor','Referred me to support groups which have helped greatly','Prolonged exposure therapy was well paced and effective','Complex PTSD from childhood correctly diagnosed and treated','Somatic therapy component was very innovative and helpful','Flashbacks and nightmares reduced by 90 percent remarkable','Best trauma specialist helped me reclaim my entire life']},
    # ENT
    # Mixed — negative reviews, ranks lower in ENT
    {'id':26,'name':'Rajan Pillai','dept':'ENT','spec':'Head & Neck Surgeon','exp':11,'rating':4.6,'fee':550,'emoji':'👨‍⚕️','slots':['8:00 AM','9:00 AM','10:00 AM','3:00 PM','4:00 PM'],'tags':['ear','nose','throat','sinus'],'reviews':['Sinus surgery done very professionally excellent result','Hearing aid fitting advice was absolutely excellent helpful','ઓપરેશન પછી ઘણી તકલીફ થઈ ડૉ. ઉપલબ્ધ ન હતા ખૂબ ખરાબ','Very experienced surgeon with consistently good patient outcomes','Post operative care instructions were very clear and detailed','सर्जरी के बाद बहुत दर्द था और डॉक्टर मिले नहीं बुरा','Voice change after thyroid surgery was avoided skillfully','ફોલો-અપ માટે ઘણો સમય વેઈટ કરવો પડ્યો ખૂબ ખરાબ સેવા','Parotid surgery was done with excellent facial nerve preservation','Best ENT surgeon in the region very highly skilled']},
    {'id':27,'name':'Shilpa Verma','dept':'ENT','spec':'Cochlear Implant Specialist','exp':9,'rating':4.8,'fee':800,'emoji':'👩‍⚕️','slots':['10:00 AM','11:00 AM','2:00 PM','3:00 PM'],'tags':['cochlear','deaf','hearing loss'],'reviews':['Cochlear implant has completely changed my daughters entire life','Hearing was mapped absolutely perfectly under her expert guidance','Very patient in teaching hearing rehabilitation exercises to family','Excellent post-implant therapy coordination with rehab team','Best decision we ever made was to come here for CI','Programming sessions for cochlear implant have been excellent','Audiological assessment before implant was very comprehensive','Helped family understand realistic expectations from CI very well','Follow-up care after surgery has been outstanding consistent','Two years post implant daughter now speaks clearly excellent']},
    {'id':28,'name':'Arvind Shah','dept':'ENT','spec':'Voice & Throat Specialist','exp':10,'rating':4.7,'fee':600,'emoji':'👨‍⚕️','slots':['9:00 AM','10:00 AM','11:00 AM','3:00 PM','4:00 PM'],'tags':['voice','larynx','swallowing','singer'],'reviews':['Voice disorder was treated completely without any surgery','Professional singer nodule was managed very conservatively well','Stroboscopy voice analysis was extremely detailed and helpful','Thyroid surgery done here with perfect voice preservation','Speech therapy referral after laryngeal surgery was very helpful','Dysphagia evaluation and treatment was very comprehensive good','Laryngeal cancer screening was very thorough and reassuring','Professional singers receive very specialized care here excellent','Voice rest and steam therapy advice was very practical','Microlaryngoscopy procedure was done with excellent surgical skill']},
    {'id':29,'name':'Pooja Jain','dept':'ENT','spec':'Rhinologist & Allergy','exp':8,'rating':4.7,'fee':500,'emoji':'👩‍⚕️','slots':['9:00 AM','10:00 AM','12:00 PM','3:00 PM','4:00 PM'],'tags':['allergy','rhinitis','sinusitis','polyp'],'reviews':['Chronic sinusitis was finally completely and properly cured','Nasal polyp surgery was very successfully done excellent','Allergy skin testing was done very comprehensively thorough','Immunotherapy she prescribed is working very well so far','Breathing has improved so dramatically after treatment amazing','Septoplasty for deviated septum was excellently performed','Nasal endoscopy was done very skillfully minimal discomfort','Smell loss after COVID treated successfully here great','Allergic rhinitis now controlled without daily antihistamines','Best nose and allergy specialist I have consulted']},
]


# ── CLINICAL CHECKUP & BILLING PROTOCOLS BY DEPARTMENT ─────────────
DEPT_CHECKUP_PROTOCOLS = {
    'Cardiology': {
        'diagnosis': 'Comprehensive Cardiovascular & Hemodynamic Checkup (ECG & Blood Pressure Evaluation)',
        'clinical_notes': 'Heart sounds S1/S2 normal. Sinus rhythm confirmed on 12-lead ECG. Blood pressure and lipid profile reviewed; advised low-sodium heart-healthy diet and regular aerobic exercise.',
        'items': [
            {'desc': 'Specialist Cardiology Consultation & Clinical Examination', 'code': 'CRD-101', 'amount': 0},  # filled from doctor fee
            {'desc': '12-Lead Digital Electrocardiogram (ECG) & Rhythm Strip', 'code': 'CRD-204', 'amount': 450},
            {'desc': 'Cardiac Biomarker & Lipid Panel Screening', 'code': 'LAB-310', 'amount': 650},
        ],
        'medications': [
            {'name': 'Tab. Atorvastatin 10mg', 'dosage': '1 tablet once daily at bedtime', 'duration': '30 Days'},
            {'name': 'Tab. Telmisartan 40mg', 'dosage': '1 tablet every morning after breakfast', 'duration': '30 Days'},
            {'name': 'Cap. Omega-3 Marine Lipid 1000mg', 'dosage': '1 capsule daily with lunch', 'duration': '30 Days'},
        ]
    },
    'Dermatology': {
        'diagnosis': 'Clinical Dermatological Assessment & Epidermal Barrier Evaluation',
        'clinical_notes': 'Dermoscopy examination performed. Mild epidermal inflammation and barrier sensitivity noted. Prescribed targeted topical therapy and broad-spectrum UV protection.',
        'items': [
            {'desc': 'Specialist Dermatology Consultation & Dermoscopy', 'code': 'DRM-101', 'amount': 0},
            {'desc': 'Digital Dermoscopic Skin & Follicle Mapping', 'code': 'DRM-210', 'amount': 350},
            {'desc': 'Allergy & Sensitivity Patch Screening', 'code': 'LAB-118', 'amount': 400},
        ],
        'medications': [
            {'name': 'Ceramide & Hyaluronic Barrier Repair Cream', 'dosage': 'Apply twice daily on clean skin', 'duration': '21 Days'},
            {'name': 'Tab. Levocetirizine 5mg', 'dosage': '1 tablet at night if itching occurs', 'duration': '10 Days'},
            {'name': 'SPF 50+ PA++++ Broad-Spectrum Medical Sunscreen Gel', 'dosage': 'Apply every morning 20 mins before sun exposure', 'duration': '30 Days'},
        ]
    },
    'Pediatrics': {
        'diagnosis': 'Pediatric Growth, Immunization & General Wellness Checkup',
        'clinical_notes': 'Height, weight, and head circumference within healthy WHO percentile curves. Chest auscultation clear. Nutritional micronutrient supplementation advised.',
        'items': [
            {'desc': 'Specialist Pediatric Consultation & Growth Assessment', 'code': 'PED-101', 'amount': 0},
            {'desc': 'Pediatric Complete Blood Count (CBC) & Iron Profile', 'code': 'LAB-205', 'amount': 400},
            {'desc': 'Developmental Milestone & Nutritional Charting', 'code': 'PED-115', 'amount': 250},
        ],
        'medications': [
            {'name': 'Syp. Pediatric Multivitamin & Zinc Drops', 'dosage': '5 ml once daily after meals', 'duration': '30 Days'},
            {'name': 'Cholecalciferol (Vitamin D3) 400 IU Oral Drops', 'dosage': '1 ml daily in the morning', 'duration': '30 Days'},
            {'name': 'Syp. Paracetamol Pediatric 125mg/5ml', 'dosage': '5 ml SOS only if fever > 100°F', 'duration': '5 Days'},
        ]
    },
    'Orthopedics': {
        'diagnosis': 'Musculoskeletal, Joint Mobility & Bone Density Evaluation',
        'clinical_notes': 'Range of motion evaluated across primary weight-bearing joints. Mild myofascial stiffness and Vitamin D insufficiency noted. Advised posture ergonomics and guided physiotherapy.',
        'items': [
            {'desc': 'Specialist Orthopedic Consultation & Mobility Assessment', 'code': 'ORT-101', 'amount': 0},
            {'desc': 'Digital Radiography (X-Ray) & Joint Alignment Scan', 'code': 'RAD-302', 'amount': 550},
            {'desc': 'Serum Calcium, Phosphorus & Vitamin D3 Panel', 'code': 'LAB-412', 'amount': 600},
        ],
        'medications': [
            {'name': 'Tab. Calcium Carbonate 500mg + Vitamin D3', 'dosage': '1 tablet daily after lunch', 'duration': '30 Days'},
            {'name': 'Cap. Cholecalciferol 60,000 IU', 'dosage': '1 capsule once weekly with milk', 'duration': '8 Weeks'},
            {'name': 'Diclofenac Diethylamine Topical Pain Relief Gel', 'dosage': 'Apply gently to affected joint twice daily', 'duration': '14 Days'},
        ]
    },
    'Neurology': {
        'diagnosis': 'Comprehensive Neurological & Cranial Nerve Evaluation',
        'clinical_notes': 'Cranial nerves II-XII intact. Deep tendon reflexes symmetric and normoactive. Evaluated for tension/migraine headache triggers; sleep hygiene and hydration recommended.',
        'items': [
            {'desc': 'Specialist Neurology Consultation & Reflex Exam', 'code': 'NEU-101', 'amount': 0},
            {'desc': 'Neuro-Conduction & Autonomic Reflex Screening', 'code': 'NEU-220', 'amount': 700},
            {'desc': 'Serum Vitamin B12, Folate & Homocysteine Assay', 'code': 'LAB-509', 'amount': 550},
        ],
        'medications': [
            {'name': 'Tab. Methylcobalamin (Vitamin B12) 1500mcg', 'dosage': '1 tablet daily after breakfast', 'duration': '30 Days'},
            {'name': 'Tab. Magnesium Glycinate 400mg', 'dosage': '1 tablet at bedtime for neural relaxation', 'duration': '30 Days'},
            {'name': 'Tab. Naproxen 250mg + Domperidone 10mg', 'dosage': '1 tablet SOS at onset of acute migraine', 'duration': '10 Days'},
        ]
    },
    'Endocrinology': {
        'diagnosis': 'Metabolic, Glycemic & Thyroid Endocrine Profile Checkup',
        'clinical_notes': 'Evaluated fasting glycemic control and thyroid hormone balance. Advised low-glycemic index meals, 35 minutes of daily brisk walking, and quarterly HbA1c tracking.',
        'items': [
            {'desc': 'Specialist Endocrinology & Metabolic Consultation', 'code': 'END-101', 'amount': 0},
            {'desc': 'HbA1c (Glycated Hemoglobin) & Fasting Glucose Assay', 'code': 'LAB-601', 'amount': 480},
            {'desc': 'Complete Thyroid Panel (TSH, Free T3, Free T4)', 'code': 'LAB-615', 'amount': 520},
        ],
        'medications': [
            {'name': 'Tab. Metformin Hydrochloride SR 500mg', 'dosage': '1 tablet twice daily with meals', 'duration': '30 Days'},
            {'name': 'Cap. Alpha Lipoic Acid & Chromium Picolinate', 'dosage': '1 capsule daily after breakfast', 'duration': '30 Days'},
            {'name': 'Tab. Thyroxine Sodium 25mcg (if TSH elevated)', 'dosage': '1 tablet empty stomach 30 mins before breakfast', 'duration': '30 Days'},
        ]
    },
    'Gastroenterology': {
        'diagnosis': 'Gastrointestinal Motility, Acid-Peptic & Hepatic Wellness Checkup',
        'clinical_notes': 'Abdomen soft, non-tender, normal bowel sounds. Mild gastroesophageal reflux and dyspepsia symptoms evaluated. Advised avoiding late-night meals and spicy triggers.',
        'items': [
            {'desc': 'Specialist Gastroenterology Consultation', 'code': 'GAS-101', 'amount': 0},
            {'desc': 'Hepatic Function Panel (LFT) & Amylase Screening', 'code': 'LAB-704', 'amount': 550},
            {'desc': 'H. Pylori Antigen & Gut Microbiome Assessment', 'code': 'LAB-718', 'amount': 450},
        ],
        'medications': [
            {'name': 'Cap. Pantoprazole 40mg + Domperidone 30mg SR', 'dosage': '1 capsule daily 30 minutes before breakfast', 'duration': '14 Days'},
            {'name': 'Cap. Multi-Strain Probiotic (Saccharomyces & Lactobacillus)', 'dosage': '1 capsule twice daily after meals', 'duration': '15 Days'},
            {'name': 'Syp. Magaldrate & Simethicone Antacid Gel', 'dosage': '10 ml after meals if acidity occurs', 'duration': '10 Days'},
        ]
    },
    'Psychiatry': {
        'diagnosis': 'Behavioral Health, Stress Resilience & Sleep Architecture Consultation',
        'clinical_notes': 'Conducted structured cognitive and stress inventory assessment. Discussed mindfulness-based stress reduction (MBSR), circadian sleep hygiene, and cognitive behavioral strategies.',
        'items': [
            {'desc': 'Specialist Psychiatry & Behavioral Wellness Consultation', 'code': 'PSY-101', 'amount': 0},
            {'desc': 'Psychometric Stress, Anxiety & Sleep Quality Assessment', 'code': 'PSY-205', 'amount': 400},
            {'desc': 'Serum Cortisol & Vitamin D Neuro-Wellness Check', 'code': 'LAB-812', 'amount': 500},
        ],
        'medications': [
            {'name': 'Tab. Melatonin 3mg + L-Theanine 100mg', 'dosage': '1 tablet 30 minutes before bedtime', 'duration': '21 Days'},
            {'name': 'Tab. Magnesium + Vitamin B6 Neuro-Calm Complex', 'dosage': '1 tablet daily after dinner', 'duration': '30 Days'},
            {'name': 'Guided CBT & Box-Breathing Protocol (4-4-4-4)', 'dosage': '10 minutes morning and evening', 'duration': 'Daily'},
        ]
    },
    'Ophthalmology': {
        'diagnosis': 'Comprehensive Ophthalmic Refraction, Intraocular Pressure & Retinal Checkup',
        'clinical_notes': 'Slit-lamp biomicroscopy and non-contact tonometry normal (IOP 14 mmHg OU). Mild digital eye strain and tear-film instability noted; advised 20-20-20 screen rule.',
        'items': [
            {'desc': 'Specialist Ophthalmology & Slit-Lamp Consultation', 'code': 'OPH-101', 'amount': 0},
            {'desc': 'Computerized Autorefraction & Tonometry (IOP) Scan', 'code': 'OPH-212', 'amount': 350},
            {'desc': 'Digital Fundus Photography & Tear Film Breakup Test', 'code': 'OPH-308', 'amount': 450},
        ],
        'medications': [
            {'name': 'Carboxymethylcellulose 0.5% Lubricating Eye Drops (Preservative-Free)', 'dosage': '1 drop in both eyes 3 to 4 times daily', 'duration': '30 Days'},
            {'name': 'Cap. Lutein 10mg + Zeaxanthin 2mg Macular Care', 'dosage': '1 capsule daily with breakfast', 'duration': '30 Days'},
            {'name': '20-20-20 Digital Screen Rest Protocol', 'dosage': 'Look 20 ft away for 20 sec every 20 mins', 'duration': 'Daily'},
        ]
    },
    'ENT': {
        'diagnosis': 'Otolaryngology (Ear, Nose, Throat), Sinus & Audiometric Checkup',
        'clinical_notes': 'Video otoscopy shows intact tympanic membranes bilaterally. Mild allergic rhinitis and nasal turbinate congestion observed; steam inhalation and nasal hygiene recommended.',
        'items': [
            {'desc': 'Specialist ENT Consultation & Video Otoscopy', 'code': 'ENT-101', 'amount': 0},
            {'desc': 'Diagnostic Nasal Endoscopy & Sinus Patency Check', 'code': 'ENT-209', 'amount': 400},
            {'desc': 'Pure-Tone Audiometry & Tympanometry Screening', 'code': 'ENT-315', 'amount': 350},
        ],
        'medications': [
            {'name': 'Fluticasone Furoate 27.5mcg Aqueous Nasal Spray', 'dosage': '1 spray in each nostril once daily in morning', 'duration': '21 Days'},
            {'name': 'Tab. Fexofenadine 120mg (Non-Drowsy Antihistamine)', 'dosage': '1 tablet once daily in the evening', 'duration': '10 Days'},
            {'name': 'Isotonic Sterile Saline Nasal Wash', 'dosage': '2 sprays in each nostril twice daily', 'duration': '30 Days'},
        ]
    },
}

def get_doctor(did):
    return next((d for d in DOCTORS if d['id'] == did), None)

def build_checkup_bill_payload(doctor: dict, appointment) -> dict:
    """Build structured checkup bill data for an appointment."""
    dept = doctor.get('dept', 'Cardiology')
    proto = DEPT_CHECKUP_PROTOCOLS.get(dept, DEPT_CHECKUP_PROTOCOLS['Cardiology'])
    fee = float(doctor.get('fee', 700))
    items = []
    subtotal = 0.0
    for idx, it in enumerate(proto['items']):
        amt = fee if idx == 0 else float(it['amount'])
        subtotal += amt
        items.append({
            'code': it['code'],
            'desc': it['desc'],
            'amount': round(amt, 2),
        })
    tax = 0.0  # Healthcare consultation & diagnostics exempt from GST
    total = round(subtotal + tax, 2)
    bill_no = f"INV-MC-{appointment.id:04d}-{doctor['id']:02d}"
    return {
        'bill_no': bill_no,
        'appointment_id': appointment.id,
        'doctor_id': doctor['id'],
        'doctor_name': f"Dr. {doctor['name']}",
        'doctor_spec': doctor.get('spec', dept),
        'department': dept,
        'patient_name': appointment.patient_name,
        'patient_phone': appointment.patient_phone or 'Not Provided',
        'appt_date': str(appointment.appt_date),
        'time_slot': appointment.time_slot,
        'reason': appointment.reason or 'Routine Specialist Checkup & Clinical Evaluation',
        'diagnosis': proto['diagnosis'],
        'clinical_notes': proto['clinical_notes'],
        'items': items,
        'medications': proto['medications'],
        'subtotal': round(subtotal, 2),
        'tax': tax,
        'total': total,
        'bot_notice': (
            "You can upload this checkup bill (or any medical bill with visible text) "
            "into the Medi AI Bot using the Upload Bill button to extract the text and "
            "talk directly with the AI about your charges, diagnosis, and prescribed medicines."
        ),
    }
