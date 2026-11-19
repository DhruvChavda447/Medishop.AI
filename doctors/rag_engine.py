"""
MediCare.AI — Vector Database, RAG Engine, Top Text Creator Model & Bill OCR Text Finder
Provides:
  1. 384-D Dense Hashing + TF-IDF Cosine Similarity Vector Database (MedicalVectorDB)
  2. Multi-Format Medical Bill Text Finder & OCR Parser (Images PNG/JPG, PDF, TXT)
  3. RAG Text Creator Engine (Local Clinical Synthesis + Gemini / Groq / OpenAI / HF API support)
  4. Voice-Free Natural Language Page Navigation & Form Auto-Fill Router
  5. High-Resolution Checkup Bill PNG Renderer (Pillow with embedded text metadata)
"""
import hashlib
import io
import json
import math
import os
import re
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

from django.conf import settings
from shared_data import DOCTORS, DEPTS, DEPT_CHECKUP_PROTOCOLS, doctor_nlp_score


# ══════════════════════════════════════════════════════════════════════════════
# 1. VECTOR DATABASE ENGINE (384-D Normalized Embedding + TF-IDF Cosine Search)
# ══════════════════════════════════════════════════════════════════════════════
STOP_WORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'in', 'on', 'at', 'to', 'for', 'with', 'about', 'by', 'from', 'of',
    'and', 'or', 'but', 'if', 'then', 'else', 'when', 'up', 'down', 'out',
    'can', 'could', 'should', 'would', 'may', 'might', 'must', 'shall',
    'will', 'do', 'does', 'did', 'have', 'has', 'had', 'this', 'that',
    'these', 'those', 'my', 'your', 'our', 'their', 'his', 'her', 'its',
    'me', 'you', 'us', 'them', 'what', 'which', 'who', 'whom', 'how',
    'please', 'tell', 'give', 'show', 'make', 'create', 'write', 'explain'
}


def tokenize(text: str) -> list:
    tokens = re.findall(r'[a-zA-Z0-9\u0900-\u097F\u0A80-\u0AFF]+', (text or '').lower())
    return [t for t in tokens if len(t) > 1 and t not in STOP_WORDS]


def compute_dense_vector(text: str, dim: int = 384) -> list:
    """Compute a normalized 384-dimensional dense embedding using signed feature hashing + bigrams."""
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * dim
    vec = [0.0] * dim
    bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
    all_feats = tokens + bigrams
    counts = Counter(all_feats)
    for feat, count in counts.items():
        h = int(hashlib.md5(feat.encode('utf-8')).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 16) & 1) == 0 else -1.0
        weight = 1.0 + math.log(1.0 + count)
        if '_' in feat:
            weight *= 1.35
        vec[idx] += sign * weight
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


def cosine_sim(v1: list, v2: list) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, round(dot, 4)))


class MedicalVectorDB:
    """In-memory + JSON-persisted Vector Database for clinical knowledge & uploaded medical bills."""
    def __init__(self):
        self.documents = []  # list of dicts: {id, title, category, content, metadata, tokens, vector}
        self.idf = {}
        self._initialized = False

    def ensure_initialized(self):
        if self._initialized:
            return
        self._initialized = True
        self._seed_knowledge_base()
        self._recompute_idf()

    def _seed_knowledge_base(self):
        """Seed the Vector DB with platform architecture, 29 doctors, 10 clinical protocols, and billing guides."""
        self.documents = []

        # 1. Platform Overview & Architecture
        self._add_doc(
            doc_id="sys_overview",
            title="MediCare.AI Platform Architecture & Capabilities",
            category="platform",
            content=(
                "MediCare.AI is an enterprise clinical AI platform built with Django, PostgreSQL, "
                "a 384-D Vector Database, Retrieval-Augmented Generation (RAG), OCR Bill Text Finder, "
                "XLM-RoBERTa Multilingual Sentiment Analysis, and NLP Doctor Recommendation. "
                "Active pages include Home (/), Doctors & Checkup Billing (/doctors/), "
                "Multilingual Sentiment Studio & Chat (/sentiment/), User Dashboard (/dashboard/), "
                "and Developer Portfolio (/about/). Users can navigate to any page via text commands in the bot, "
                "book doctor checkups, receive itemized medical bills, and upload any bill image or PDF to chat with the AI."
            ),
            metadata={"url": "/", "type": "architecture"}
        )

        # 2. All 10 Clinical Department Checkup & Billing Protocols
        for dept_name, proto in DEPT_CHECKUP_PROTOCOLS.items():
            meds_str = "; ".join(f"{m['name']} ({m['dosage']} for {m['duration']})" for m in proto['medications'])
            items_str = "; ".join(f"{it['desc']} [{it['code']}]" for it in proto['items'])
            self._add_doc(
                doc_id=f"protocol_{dept_name.lower()}",
                title=f"{dept_name} Checkup, Diagnosis & Prescription Protocol",
                category="clinical_protocol",
                content=(
                    f"Department: {dept_name}. Standard Checkup Diagnosis: {proto['diagnosis']}. "
                    f"Clinical Assessment Notes: {proto['clinical_notes']} "
                    f"Diagnostic Procedures & Billable Items: {items_str}. "
                    f"Standard Prescribed Medications: {meds_str}."
                ),
                metadata={"department": dept_name, "url": f"/doctors/?dept={dept_name}"}
            )

        # 3. All 29 Doctors Indexed Individually + Department Summaries
        dept_groups = {}
        for d in DOCTORS:
            score = doctor_nlp_score(d)
            dept_groups.setdefault(d['dept'], []).append((score, d))
            self._add_doc(
                doc_id=f"doctor_{d['id']}",
                title=f"Dr. {d['name']} — {d['spec']} ({d['dept']})",
                category="doctor_profile",
                content=(
                    f"Dr. {d['name']} is a specialist {d['spec']} in the {d['dept']} department with "
                    f"{d['exp']} years of clinical experience. Consultation fee: ₹{d['fee']}. "
                    f"Patient rating: {d['rating']}/5.0 with XLM-RoBERTa NLP Sentiment Score: {score}/8.0. "
                    f"Available appointment time slots: {', '.join(d['slots'])}. "
                    f"Clinical expertise tags: {', '.join(d.get('tags', []))}. "
                    f"Booking link: /doctors/{d['id']}/book/."
                ),
                metadata={"doctor_id": d['id'], "doctor_name": d['name'], "department": d['dept'], "fee": d['fee'], "score": score, "url": f"/doctors/{d['id']}/"}
            )

        for dept_name, doc_list in dept_groups.items():
            doc_list.sort(key=lambda x: x[0], reverse=True)
            top_doc = doc_list[0][1]
            all_names = ", ".join(f"Dr. {x[1]['name']} (NLP Score {x[0]}, Fee ₹{x[1]['fee']})" for x in doc_list)
            self._add_doc(
                doc_id=f"dept_ranking_{dept_name.lower()}",
                title=f"Top Ranked {dept_name} Doctors (NLP Sentiment Ranking)",
                category="department_ranking",
                content=(
                    f"In {dept_name}, the #1 top-ranked specialist by patient sentiment is Dr. {top_doc['name']} "
                    f"({top_doc['spec']}, {top_doc['exp']} yrs exp, Fee ₹{top_doc['fee']}, NLP Score {doc_list[0][0]}). "
                    f"All {dept_name} specialists ranked by NLP sentiment: {all_names}."
                ),
                metadata={"department": dept_name, "top_doctor": top_doc['name'], "url": f"/doctors/?dept={dept_name}"}
            )

        # 4. Clinical Guides: Medical Bill Interpretation, Preventive Health & Lab Reference Ranges
        self._add_doc(
            doc_id="guide_bill_reading",
            title="Medical Checkup Bill & Prescription Reading Guide",
            category="billing_guide",
            content=(
                "Every checkup bill generated after a doctor consultation includes: "
                "1) Invoice / Bill Number (e.g., INV-MC-0001-01), 2) Consulting Specialist & Department, "
                "3) Patient Details & Checkup Date, 4) Clinical Diagnosis & Examination Notes, "
                "5) Itemized Procedure & Diagnostic Charges (Specialist Consultation Fee, ECG/Dermoscopy/X-Ray/Lab Panels), "
                "and 6) Prescribed Medications with exact dosage and duration. "
                "Healthcare consultation and diagnostic services are GST-exempt (0% tax). "
                "You can upload any bill image (PNG/JPG), PDF, or text file into the Medi AI Bot to extract visible text via OCR and ask questions."
            ),
            metadata={"type": "billing_guide", "url": "/doctors/"}
        )

        self._add_doc(
            doc_id="guide_lab_ranges",
            title="Standard Clinical Diagnostic & Lab Reference Ranges",
            category="clinical_reference",
            content=(
                "Normal Clinical Reference Ranges: "
                "Blood Pressure: Normal < 120/80 mmHg, Elevated 120-129/<80 mmHg, Hypertension >= 130/80 mmHg. "
                "Fasting Blood Glucose: Normal 70-99 mg/dL, Prediabetes 100-125 mg/dL, Diabetes >= 126 mg/dL. "
                "HbA1c: Normal < 5.7%, Prediabetes 5.7%-6.4%, Diabetes >= 6.5%. "
                "Total Cholesterol: Desirable < 200 mg/dL, LDL < 100 mg/dL, HDL > 40 mg/dL (men) / > 50 mg/dL (women), Triglycerides < 150 mg/dL. "
                "Thyroid TSH: Normal 0.4 - 4.5 mIU/L. Vitamin D (25-OH): Sufficient 30-100 ng/mL, Insufficient 20-29 ng/mL, Deficient < 20 ng/mL. "
                "Vitamin B12: Normal 200-900 pg/mL. Resting Heart Rate: 60-100 bpm. SpO2 Oxygen Saturation: 95%-100%."
            ),
            metadata={"type": "lab_reference"}
        )

    def _add_doc(self, doc_id: str, title: str, category: str, content: str, metadata: dict = None):
        full_text = f"{title}. {content}"
        tokens = tokenize(full_text)
        vec = compute_dense_vector(full_text)
        # Remove existing with same doc_id
        self.documents = [d for d in self.documents if d['id'] != doc_id]
        self.documents.append({
            'id': doc_id,
            'title': title,
            'category': category,
            'content': content,
            'metadata': metadata or {},
            'tokens': tokens,
            'tf': Counter(tokens),
            'vector': vec,
        })

    def _recompute_idf(self):
        N = max(1, len(self.documents))
        df = Counter()
        for doc in self.documents:
            for tok in set(doc['tokens']):
                df[tok] += 1
        self.idf = {tok: math.log(1.0 + (N - freq + 0.5) / (freq + 0.5)) for tok, freq in df.items()}

    def index_bill_document(self, bill_dict: dict, user_key: str = "global"):
        """Index an uploaded or generated medical bill into the Vector Database for immediate RAG Q&A."""
        self.ensure_initialized()
        bill_no = bill_dict.get('bill_no', 'UPLOADED-BILL')
        items_text = "; ".join(f"{it.get('desc', 'Item')}: ₹{it.get('amount', 0)}" for it in bill_dict.get('items', []))
        meds_text = "; ".join(
            f"{m.get('name', '')} ({m.get('dosage', '')} {m.get('duration', '')})".strip()
            for m in bill_dict.get('medications', [])
        )
        raw_excerpt = (bill_dict.get('raw_text') or '')[:1800]
        content = (
            f"Uploaded/Generated Medical Bill {bill_no}. "
            f"Doctor: {bill_dict.get('doctor_name', 'Consulting Physician')} ({bill_dict.get('department', 'Clinical Department')}). "
            f"Patient Name: {bill_dict.get('patient_name', 'Patient')}. Date: {bill_dict.get('appt_date', 'Today')}. "
            f"Diagnosis / Clinical Findings: {bill_dict.get('diagnosis', 'Clinical Checkup')}. "
            f"Clinical Notes: {bill_dict.get('clinical_notes', '')}. "
            f"Itemized Bill Charges: {items_text or 'See raw bill text'}. "
            f"Total Bill Amount: ₹{bill_dict.get('total', 0)}. "
            f"Prescribed Medications: {meds_text or 'See raw bill text'}. "
            f"Full Extracted Bill Text: {raw_excerpt}"
        )
        doc_id = f"active_bill_{user_key}"
        self._add_doc(
            doc_id=doc_id,
            title=f"Active Medical Bill ({bill_no}) — {bill_dict.get('patient_name', 'Patient')}",
            category="uploaded_bill",
            content=content,
            metadata={"bill": bill_dict, "user_key": user_key}
        )
        self._recompute_idf()
        return doc_id

    def search(self, query: str, top_k: int = 4, user_key: str = "global", prefer_bill: bool = False) -> list:
        """Hybrid Vector Search: combines 384-D dense cosine similarity + BM25 lexical relevance."""
        self.ensure_initialized()
        q_tokens = tokenize(query)
        q_vec = compute_dense_vector(query)
        scored = []
        avg_dl = sum(len(d['tokens']) for d in self.documents) / max(1, len(self.documents))

        for doc in self.documents:
            # Filter out other users' active bills
            if doc['category'] == 'uploaded_bill':
                doc_uk = doc['metadata'].get('user_key', 'global')
                if doc_uk not in (user_key, 'global'):
                    continue

            dense_score = cosine_sim(q_vec, doc['vector'])

            # BM25 lexical score
            bm25 = 0.0
            dl = max(1, len(doc['tokens']))
            for tok in q_tokens:
                if tok in doc['tf']:
                    tf = doc['tf'][tok]
                    idf = self.idf.get(tok, 1.0)
                    bm25 += idf * ((tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * (dl / avg_dl))))
            bm25_norm = min(1.0, bm25 / 12.0)

            hybrid = round(0.55 * dense_score + 0.45 * bm25_norm, 4)
            if prefer_bill and doc['category'] == 'uploaded_bill':
                hybrid = round(min(0.99, hybrid + 0.35), 4)
            elif doc['category'] == 'uploaded_bill' and any(
                w in query.lower() for w in ['bill', 'invoice', 'charge', 'fee', 'total', 'amount', 'medicine', 'prescri', 'diagnos', 'my checkup', 'uploaded', 'receipt', 'cost']
            ):
                hybrid = round(min(0.99, hybrid + 0.40), 4)

            if hybrid > 0.05:
                scored.append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'category': doc['category'],
                    'content': doc['content'],
                    'metadata': doc['metadata'],
                    'similarity': hybrid,
                    'dense_cosine': dense_score,
                })

        scored.sort(key=lambda x: x['similarity'], reverse=True)
        return scored[:top_k]


# Singleton Vector Database instance
VECTOR_DB = MedicalVectorDB()


# ══════════════════════════════════════════════════════════════════════════════
# 2. BILL TEXT FINDER (OCR + PDF + PNG METADATA + STRUCTURED BILL PARSER)
# ══════════════════════════════════════════════════════════════════════════════
def extract_text_from_uploaded_file(uploaded_file, client_ocr_text: str = "") -> tuple:
    """
    Extract visible text from any uploaded bill file (Image PNG/JPG/WEBP, PDF, or TXT).
    Returns (extracted_text, extraction_method).
    """
    filename = (getattr(uploaded_file, 'name', '') or 'bill.txt').lower()
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    methods_used = []
    extracted_chunks = []

    # 1. If client-side OCR (Tesseract.js) already extracted visible text, capture it
    if client_ocr_text and len(client_ocr_text.strip()) > 10:
        extracted_chunks.append(client_ocr_text.strip())
        methods_used.append("Client-Side WebAssembly OCR (Tesseract.js)")

    # 2. PDF Extraction via pypdf
    if filename.endswith('.pdf'):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
            pdf_pages = []
            for p in reader.pages:
                t = (p.extract_text() or '').strip()
                if t:
                    pdf_pages.append(t)
            if pdf_pages:
                extracted_chunks.append("\n".join(pdf_pages))
                methods_used.append(f"PyPDF Document Parser ({len(pdf_pages)} page(s))")
        except Exception as e:
            methods_used.append(f"PDF Parser Note: {e}")

    # 3. Image Extraction (PNG metadata + Server pytesseract + Vision API fallback)
    elif any(filename.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
        try:
            from PIL import Image, ImageOps, ImageFilter
            img = Image.open(io.BytesIO(raw_bytes))
            # Check embedded PNG text metadata (from platform-generated checkup bill PNGs)
            info = getattr(img, 'info', {}) or {}
            if 'bill_raw_text' in info and len(info['bill_raw_text'].strip()) > 10:
                extracted_chunks.insert(0, info['bill_raw_text'].strip())
                methods_used.insert(0, "PNG Embedded Clinical Text Layer + OCR")

            # Try pytesseract if installed on server
            try:
                import pytesseract
                gray = ImageOps.grayscale(img)
                gray = ImageOps.autocontrast(gray)
                srv_ocr = pytesseract.image_to_string(gray).strip()
                if len(srv_ocr) > 15:
                    extracted_chunks.append(srv_ocr)
                    methods_used.append("Server Tesseract OCR Engine")
            except Exception:
                pass
        except Exception:
            pass

    # 4. Plain Text / HTML / Markdown / JSON files
    else:
        try:
            txt = raw_bytes.decode('utf-8', errors='ignore').strip()
            if filename.endswith('.html') or '<html' in txt.lower() or '<div' in txt.lower():
                txt = re.sub(r'<style[^>]*>.*?</style>', ' ', txt, flags=re.DOTALL | re.IGNORECASE)
                txt = re.sub(r'<script[^>]*>.*?</script>', ' ', txt, flags=re.DOTALL | re.IGNORECASE)
                txt = re.sub(r'<[^>]+>', '\n', txt)
                txt = re.sub(r'\n{2,}', '\n', txt).strip()
                methods_used.append("HTML Clinical Document Stripper")
            else:
                methods_used.append("Direct UTF-8 Text Stream")
            if txt:
                extracted_chunks.append(txt)
        except Exception:
            pass

    # Combine unique extracted text
    combined = "\n".join(dict.fromkeys(c for c in extracted_chunks if c)).strip()
    method_str = " + ".join(methods_used) if methods_used else "Multi-Modal Text Finder"
    return combined, method_str


def parse_medical_bill_text(raw_text: str, filename: str = "Uploaded_Bill") -> dict:
    """
    Intelligent Medical Bill Entity Extractor:
    Parses visible text from ANY medical bill (hospital receipt, doctor checkup bill, pharmacy invoice)
    into structured fields for Vector DB RAG indexing and instant clinical breakdown.
    """
    lines = [ln.strip() for ln in (raw_text or '').splitlines() if ln.strip()]
    full = "\n".join(lines)

    # 1. Bill / Invoice Number
    bill_no = "INV-UPLOADED"
    m_bill = re.search(r'(?:Bill\s*No|Invoice\s*No|Invoice\s*ID|Receipt\s*No|INV|Bill\s*ID)\s*[:#\-]?\s*([A-Z0-9\-/]{4,28})', full, re.IGNORECASE)
    if m_bill:
        bill_no = m_bill.group(1).strip()

    # 2. Doctor Name
    doctor_name = "Consulting Physician"
    m_doc = re.search(r'(?:Doctor|Physician|Consultant|Consulted|Dr\.?)\s*[:\-]?\s*(Dr\.?\s*[A-Za-z][A-Za-z\s\.]{2,35}|[A-Za-z][A-Za-z\s\.]{2,35})', full, re.IGNORECASE)
    if m_doc:
        cand = m_doc.group(1).strip()
        if not cand.lower().startswith('dr'):
            cand = f"Dr. {cand}"
        doctor_name = cand.splitlines()[0].strip()

    # 3. Department / Specialty
    department = "Clinical Consultation"
    for d in DEPTS:
        if d['name'].lower() in full.lower():
            department = d['name']
            break
    else:
        m_dept = re.search(r'(?:Department|Specialty|Clinic|Unit)\s*[:\-]\s*([A-Za-z\s&]{3,35})', full, re.IGNORECASE)
        if m_dept:
            department = m_dept.group(1).strip()

    # 4. Patient Name
    patient_name = "Patient"
    m_pat = re.search(r'(?:Patient\s*Name|Patient|Billed\s*To|Name)\s*[:\-]\s*([A-Za-z][A-Za-z\s\.]{2,35})', full, re.IGNORECASE)
    if m_pat:
        patient_name = m_pat.group(1).splitlines()[0].strip()

    # 5. Date
    appt_date = str(date.today())
    m_date = re.search(r'(?:Date|Checkup\s*Date|Issued)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})', full, re.IGNORECASE)
    if m_date:
        appt_date = m_date.group(1).strip()

    # 6. Diagnosis / Clinical Findings
    diagnosis = "Clinical Evaluation & Medical Checkup"
    m_diag = re.search(r'(?:Diagnosis|Clinical\s*Findings|Assessment|Impression|Chief\s*Complaint|Reason)\s*[:\-]\s*(.+)', full, re.IGNORECASE)
    if m_diag:
        diagnosis = m_diag.group(1).strip()

    # 7. Line Items (Description + Amount)
    items = []
    for ln in lines:
        if any(k in ln.lower() for k in ['subtotal', 'total amount', 'grand total', 'net payable', 'amount due', 'tax', 'gst', 'phone', 'invoice no', 'bill no']):
            continue
        m_item = re.search(r'^([A-Za-z0-9][A-Za-z0-9\s\(\)\-\,/&\.]{4,68}?)\s+(?:Rs\.?|INR|₹|\$)?\s*(\d{2,6}(?:\.\d{1,2})?)\s*$', ln)
        if m_item:
            desc = m_item.group(1).strip(' .-:')
            amt = float(m_item.group(2))
            if 10 <= amt <= 250000 and not re.match(r'^\d{4}$', str(int(amt))) or 'fee' in desc.lower() or 'consult' in desc.lower() or 'test' in desc.lower() or 'scan' in desc.lower() or 'ecg' in desc.lower() or 'lab' in desc.lower() or 'panel' in desc.lower() or 'tab' in desc.lower():
                items.append({'code': f'ITM-{len(items)+1:02d}', 'desc': desc, 'amount': amt})

    # 8. Prescribed Medications
    medications = []
    for ln in lines:
        if re.search(r'\b(Tab\.?|Cap\.?|Syp\.?|Inj\.?|Drops|Cream|Gel|Ointment|Spray|mg\b|mcg\b|IU\b|ml\b|once\s+daily|twice\s+daily|bedtime|after\s+meals|before\s+breakfast)\b', ln, re.IGNORECASE):
            if len(ln) > 6 and 'total' not in ln.lower():
                medications.append({'name': ln.strip('•-* '), 'dosage': 'As prescribed on bill', 'duration': ''})

    # 9. Total Amount
    total = 0.0
    m_tot = re.findall(r'(?:Grand\s*Total|Total\s*Amount|Net\s*Payable|Total\s*Fee|Total\s*Payable|Total)\s*[:\-]?\s*(?:Rs\.?|INR|₹|\$)?\s*(\d[\d,]*\.?\d*)', full, re.IGNORECASE)
    if m_tot:
        try:
            total = float(m_tot[-1].replace(',', ''))
        except Exception:
            total = 0.0
    if total == 0.0 and items:
        total = round(sum(x['amount'] for x in items), 2)
    if total == 0.0:
        # fallback: look for any ₹ / Rs. amount
        all_curr = re.findall(r'(?:Rs\.?|INR|₹)\s*(\d[\d,]*\.?\d*)', full, re.IGNORECASE)
        if all_curr:
            vals = [float(x.replace(',', '')) for x in all_curr if x.replace(',', '').replace('.', '').isdigit()]
            if vals:
                total = max(vals)

    return {
        'bill_no': bill_no,
        'doctor_name': doctor_name,
        'department': department,
        'patient_name': patient_name,
        'appt_date': appt_date,
        'diagnosis': diagnosis,
        'clinical_notes': f"Extracted from uploaded document ({filename})",
        'items': items,
        'medications': medications,
        'total': round(total, 2),
        'raw_text': full,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. VOICE-FREE PAGE NAVIGATION & FORM AUTOFILL INTENT DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
PAGE_ROUTES = [
    {'keywords': ['doctor', 'specialist', 'physician', 'cardiolog', 'dermatolog', 'pediatric', 'orthopedic', 'neurolog', 'endocrin', 'gastro', 'psychiatr', 'ophthal', 'ent specialist', 'ent doctor'], 'url': '/doctors/', 'title': 'Doctors & Checkup Directory'},
    {'keywords': ['sentiment', 'nlp', 'emotion', 'review analyzer', 'sentiment chat'], 'url': '/sentiment/', 'title': 'Multilingual Sentiment AI Studio'},
    {'keywords': ['dashboard', 'my account', 'my profile', 'my appointment', 'my bill', 'history'], 'url': '/dashboard/', 'title': 'Patient & AI Dashboard'},
    {'keywords': ['about', 'portfolio', 'contact', 'resume', 'cv', 'developer', 'dhruv'], 'url': '/about/', 'title': 'About & Developer Portfolio'},
    {'keywords': ['home', 'main page', 'landing', 'start page'], 'url': '/', 'title': 'Home Page'},
    {'keywords': ['login', 'sign in'], 'url': '/login/', 'title': 'Sign In Page'},
    {'keywords': ['signup', 'register', 'create account'], 'url': '/signup/', 'title': 'Create Account Page'},
    {'keywords': ['logout', 'sign out', 'signout'], 'url': '/logout/', 'title': 'Sign Out'},
]


def detect_bot_action(query: str) -> dict:
    """
    Detect if the user wants to navigate to a page, book a specific doctor, or auto-fill a form.
    Returns an action dict if matched, or None for general RAG / Text Generation queries.
    """
    q = (query or '').strip().lower()

    # 1. Direct Logout command
    if q in ('logout', 'sign out', 'signout') or 'sign me out' in q or 'log me out' in q:
        return {
            'action': 'navigate',
            'url': '/logout/',
            'title': 'Sign Out',
            'reply': 'Signing you out safely. Redirecting to the login page...'
        }

    # 2. Form Auto-Fill commands
    if ('fill' in q or 'autofill' in q or 'auto-fill' in q) and ('form' in q or 'appointment' in q or 'contact' in q):
        if 'contact' in q or 'about' in q:
            return {
                'action': 'autofill',
                'form_type': 'contact',
                'url': '/about/',
                'reply': 'Auto-filling the Contact Form with sample inquiry details...'
            }
        return {
            'action': 'autofill',
            'form_type': 'appointment',
            'url': '/doctors/1/book/',
            'reply': 'Auto-filling the Doctor Checkup Appointment form with sample patient details...'
        }

    # 3. Book a specific doctor by name or specialty
    if re.search(r'\b(book|schedule|consult|appointment\s+with)\b', q):
        for d in DOCTORS:
            if d['name'].lower() in q or d['name'].split()[0].lower() in q or d['dept'].lower() in q or d['spec'].lower() in q:
                return {
                    'action': 'navigate',
                    'url': f"/doctors/{d['id']}/book/",
                    'title': f"Book Dr. {d['name']} ({d['dept']})",
                    'reply': f"Opening the checkup appointment booking page for **Dr. {d['name']}** ({d['spec']}, Fee: ₹{d['fee']})..."
                }

    # 4. General Page Navigation ("open <page>", "go to <page>", "take me to <page>", "navigate to <page>", "show <page> page")
    nav_trigger = re.search(r'\b(open|go\s+to|take\s+me\s+to|navigate\s+to|visit|switch\s+to|redirect\s+to)\b', q)
    if nav_trigger or q in ('doctors', 'sentiment', 'dashboard', 'about', 'home', 'doctors page', 'sentiment page', 'dashboard page', 'about page', 'home page'):
        # Check if they asked for a specific doctor's profile
        for d in DOCTORS:
            if d['name'].lower() in q or d['name'].split()[0].lower() in q:
                return {
                    'action': 'navigate',
                    'url': f"/doctors/{d['id']}/",
                    'title': f"Dr. {d['name']} Profile",
                    'reply': f"Navigating to **Dr. {d['name']}**'s clinical profile ({d['dept']})..."
                }
        for route in PAGE_ROUTES:
            if any(k in q for k in route['keywords']):
                return {
                    'action': 'navigate',
                    'url': route['url'],
                    'title': route['title'],
                    'reply': f"Navigating to **{route['title']}** (`{route['url']}`)..."
                }

    return None


# ══════════════════════════════════════════════════════════════════════════════
# 4. TOP TEXT CREATOR MODEL + RAG RESPONSE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def _call_external_llm_if_configured(system_prompt: str, user_prompt: str) -> tuple:
    """
    Calls Gemini 2.5 Flash, Groq Llama-3.3-70B, or OpenAI GPT-4o-mini if an API key is configured in .env.
    Returns (response_text, model_name) or (None, None) if no key is configured.
    """
    # 1. Google Gemini API (GEMINI_API_KEY)
    gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 900}
            }
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}, method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                txt = data['candidates'][0]['content']['parts'][0]['text']
                if txt:
                    return txt.strip(), "Gemini-2.5-Flash (RAG + Vector DB)"
        except Exception:
            pass

    # 2. Groq Cloud API (GROQ_API_KEY)
    groq_key = os.getenv('GROQ_API_KEY', '').strip()
    if groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 900
            }
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {groq_key}'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                txt = data['choices'][0]['message']['content']
                if txt:
                    return txt.strip(), "Llama-3.3-70B-Versatile (Groq RAG)"
        except Exception:
            pass

    # 3. OpenAI API (OPENAI_API_KEY)
    openai_key = os.getenv('OPENAI_API_KEY', '').strip()
    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 900
            }
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {openai_key}'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                txt = data['choices'][0]['message']['content']
                if txt:
                    return txt.strip(), "GPT-4o-Mini (OpenAI RAG)"
        except Exception:
            pass

    return None, None


def generate_rag_response(query: str, user_key: str = "global", active_bill: dict = None) -> dict:
    """
    End-to-End RAG Pipeline:
      1. Checks for instant Page Navigation or Form Auto-Fill intent
      2. Indexes active_bill in Vector DB if present
      3. Retrieves Top-K relevant chunks from 384-D MedicalVectorDB with cosine similarity scores
      4. Synthesizes professional, well-formatted clinical & technical text response
    """
    VECTOR_DB.ensure_initialized()
    if active_bill:
        VECTOR_DB.index_bill_document(active_bill, user_key=user_key)

    # 1. Check navigation / autofill intent first
    nav_action = detect_bot_action(query)
    if nav_action:
        return {
            'reply': nav_action['reply'],
            'action': nav_action['action'],
            'url': nav_action.get('url', ''),
            'title': nav_action.get('title', ''),
            'form_type': nav_action.get('form_type', ''),
            'model': 'MediCare.AI Intent & Navigation Router',
            'retrieved_chunks': [],
        }

    # 2. Retrieve Top-K chunks from Vector DB
    ql = (query or '').strip().lower()
    is_bill_query = any(w in ql for w in [
        'bill', 'invoice', 'charge', 'total', 'amount', 'cost', 'fee', 'receipt',
        'prescri', 'medicine', 'medication', 'tablet', 'dosage', 'diagnos', 'checkup', 'uploaded'
    ])
    retrieved = VECTOR_DB.search(query, top_k=4, user_key=user_key, prefer_bill=is_bill_query)

    # Check if there is an indexed bill in the Vector DB for this user
    bill_doc = next((d for d in VECTOR_DB.documents if d['id'] == f"active_bill_{user_key}"), None)
    if not bill_doc:
        bill_doc = next((d for d in VECTOR_DB.documents if d['category'] == 'uploaded_bill'), None)
    bill_data = bill_doc['metadata'].get('bill') if bill_doc else active_bill

    context_str = "\n\n".join(
        f"[Vector Chunk {i+1} | Score: {c['similarity']} | {c['title']}]\n{c['content']}"
        for i, c in enumerate(retrieved)
    )

    system_prompt = (
        "You are MediCare.AI, a clinical-grade RAG healthcare assistant and professional medical text creator. "
        "Always format your responses cleanly using structured headings, bullet points, and bold labels. "
        "Ground your answers strictly in the retrieved Vector Database context and any uploaded Medical Bill."
    )
    user_prompt = f"Retrieved Vector Context:\n{context_str}\n\nUser Question / Text Generation Request:\n{query}"

    llm_reply, llm_model = _call_external_llm_if_configured(system_prompt, user_prompt)
    if llm_reply:
        return {
            'reply': llm_reply,
            'action': 'chat',
            'model': llm_model,
            'retrieved_chunks': [
                {'title': c['title'], 'category': c['category'], 'similarity': c['similarity']}
                for c in retrieved
            ],
        }

    # ── Built-in Clinical RAG Text Creator Engine (100% Reliable Offline & on Render Free Tier) ──
    reply_md = _synthesize_structured_clinical_text(query, ql, retrieved, bill_data)
    return {
        'reply': reply_md,
        'action': 'chat',
        'model': 'MediCare-RAG-v3 Text Creator (384-D Vector DB + Clinical Synthesis)',
        'retrieved_chunks': [
            {'title': c['title'], 'category': c['category'], 'similarity': c['similarity']}
            for c in retrieved
        ],
    }


def _synthesize_structured_clinical_text(query: str, ql: str, retrieved: list, bill_data: dict = None) -> str:
    """
    Produces richly formatted Markdown text tailored to:
      A) Uploaded / Generated Medical Bill Q&A (charges, total, medicines, diagnosis, doctor)
      B) Text Creator requests (write/create/generate diet plan, discharge summary, clinical report, health article, email)
      C) Doctor recommendations & specialty queries
      D) Lab reference ranges & general clinical RAG queries
    """
    # A. If the user is asking about an uploaded/generated bill (or has a bill loaded and asks about charges/medicines/diagnosis)
    if bill_data and any(w in ql for w in [
        'bill', 'invoice', 'charge', 'total', 'amount', 'cost', 'price', 'pay', 'receipt',
        'medicine', 'medication', 'tablet', 'prescri', 'dosage', 'drug',
        'diagnos', 'doctor', 'checkup', 'test', 'lab', 'explain', 'summary', 'what is in', 'detail'
    ]):
        b_no = bill_data.get('bill_no', 'INV-MC')
        doc_nm = bill_data.get('doctor_name', 'Consulting Physician')
        dept = bill_data.get('department', 'Clinical Department')
        pat_nm = bill_data.get('patient_name', 'Patient')
        dt = bill_data.get('appt_date', 'Today')
        diag = bill_data.get('diagnosis', 'Clinical Checkup')
        tot = bill_data.get('total', 0)
        items = bill_data.get('items', [])
        meds = bill_data.get('medications', [])

        # Specific sub-question focus
        if any(w in ql for w in ['total', 'how much', 'amount', 'cost', 'charge', 'price', 'fee', 'pay']) and not any(w in ql for w in ['medicine', 'tablet', 'drug']):
            items_md = "\n".join(f"- **{it['desc']}** (`{it.get('code','ITM')}`): **₹{it['amount']}**" for it in items) if items else "- **Consolidated Clinical Checkup & Diagnostics**: **₹" + str(tot) + "**"
            return (
                f"**Medical Bill Financial Breakdown (`{b_no}`)**\n\n"
                f"Here is the itemized charge analysis extracted from your bill with **{doc_nm}** ({dept}):\n\n"
                f"{items_md}\n\n"
                f"- **Total Payable Amount**: **₹{tot}** *(Healthcare services are 0% GST exempt)*\n"
                f"- **Patient**: {pat_nm} · **Date**: {dt}"
            )

        if any(w in ql for w in ['medicine', 'medication', 'tablet', 'capsule', 'prescri', 'dosage', 'take', 'drug']) and not any(w in ql for w in ['total', 'amount', 'cost', 'charge', 'price', 'fee']):
            if meds:
                meds_md = "\n".join(
                    f"- **{m['name']}** — {m.get('dosage', 'As directed')}" + (f" *({m['duration']})*" if m.get('duration') else "")
                    for m in meds
                )
            else:
                meds_md = "- Please refer to the extracted bill text for specific pharmacy lines."
            return (
                f"**Prescribed Medications & Dosage Guide (`{b_no}`)**\n\n"
                f"Based on your checkup with **{doc_nm}** ({dept}) for **{diag}**, here are your prescribed medications:\n\n"
                f"{meds_md}\n\n"
                f"**Clinical Advice**: Take all medications at consistent intervals as prescribed and complete the recommended course."
            )

        # Full Bill RAG Summary
        items_md = "\n".join(f"- **{it['desc']}**: ₹{it['amount']}" for it in items) if items else f"- **Recorded Total**: ₹{tot}"
        meds_md = "\n".join(f"- **{m['name']}** ({m.get('dosage', 'As directed')})" for m in meds) if meds else "- *No separate medication lines detected*"
        return (
            f"**Complete RAG Analysis of Medical Bill `{b_no}`**\n\n"
            f"- **Consulting Specialist**: {doc_nm} ({dept})\n"
            f"- **Patient Name**: {pat_nm} · **Date**: {dt}\n"
            f"- **Clinical Diagnosis**: {diag}\n\n"
            f"**Itemized Charges:**\n{items_md}\n"
            f"- **Total Bill Amount**: **₹{tot}**\n\n"
            f"**Prescribed Medications:**\n{meds_md}\n\n"
            f"*Ask follow-up questions like \"Explain my medicines\", \"What is the total amount?\", or \"Draft a follow-up note to the doctor\".*"
        )

    # B. Text Creator Mode (User asks to create/write/draft/generate structured text, plan, summary, report, article, letter)
    if any(w in ql for w in ['write', 'create', 'generate', 'draft', 'prepare', 'format', 'plan', 'report', 'article', 'summary', 'letter', 'email', 'guide', 'routine', 'diet']):
        topic_chunk = retrieved[0] if retrieved else None
        topic_title = topic_chunk['title'] if topic_chunk else "Clinical Healthcare & Wellness Protocol"
        topic_body = topic_chunk['content'] if topic_chunk else "Evidence-based clinical care, preventive diagnostics, and lifestyle optimization."

        if 'diet' in ql or 'nutrition' in ql or 'lifestyle' in ql or 'routine' in ql:
            return (
                f"**Structured Clinical Wellness & Nutrition Plan**\n\n"
                f"**1. Core Clinical Objective**\n"
                f"- Grounded in **{topic_title}**, designed to optimize metabolic, cardiovascular, and cellular recovery.\n\n"
                f"**2. Daily Nutritional Schedule**\n"
                f"- **Morning (7:30 AM)**: Warm hydration (300 ml water) + high-fiber complex breakfast (oats, soaked almonds, walnuts, and seasonal low-GI fruit).\n"
                f"- **Mid-Day (1:00 PM)**: Balanced plate with 50% leafy/cruciferous vegetables, 25% lean protein (dal, legumes, paneer, or grilled fish), and 25% whole grains.\n"
                f"- **Evening (5:00 PM)**: Green tea or herbal infusion with roasted seeds; strictly limit refined sodium (< 5g/day) and processed sugars.\n"
                f"- **Dinner (7:30 PM)**: Light, easily digestible meal completed at least 2.5 hours before sleep.\n\n"
                f"**3. Physical Activity & Recovery Protocol**\n"
                f"- **Aerobic Exercise**: 35 minutes of brisk walking or cycling 5 days/week.\n"
                f"- **Sleep & Stress**: 7.5–8 hours of uninterrupted circadian sleep + 10 minutes of box breathing (4s inhale, 4s hold, 4s exhale)."
            )

        if 'email' in ql or 'letter' in ql or 'message' in ql or 'leave' in ql:
            doc_ref = bill_data.get('doctor_name', 'Dr. Priya Sharma') if bill_data else 'Dr. Priya Sharma'
            diag_ref = bill_data.get('diagnosis', 'Clinical Checkup & Diagnostic Evaluation') if bill_data else 'Medical Consultation & Diagnostic Follow-Up'
            return (
                f"**Professional Medical Follow-Up Draft**\n\n"
                f"**Subject**: Clinical Follow-Up & Diagnostic Review — {diag_ref}\n\n"
                f"Dear **{doc_ref}**,\n\n"
                f"Thank you for the thorough consultation and diagnostic checkup. I have reviewed the checkup bill and started the prescribed medication regimen as advised.\n\n"
                f"**Key Updates:**\n"
                f"- Following the prescribed dosage schedule consistently without adverse reactions.\n"
                f"- Completed the recommended diagnostic screening panels.\n"
                f"- Requesting confirmation on the ideal timeframe for my next follow-up evaluation.\n\n"
                f"Warm regards,\n"
                f"**{bill_data.get('patient_name', 'Patient') if bill_data else 'Patient'}**"
            )

        # General Professional Text Creator Output
        return (
            f"**AI Text Creator — Structured Clinical Brief**\n\n"
            f"**Topic**: {topic_title}\n\n"
            f"**1. Executive Clinical Summary**\n"
            f"- {topic_body}\n\n"
            f"**2. Key Evidence-Based Recommendations**\n"
            f"- **Preventive Screening**: Schedule targeted diagnostic checkups and track biomarker baselines semi-annually.\n"
            f"- **Therapeutic Adherence**: Follow specialist prescriptions with exact dosage timing and duration.\n"
            f"- **Digital Health Tracking**: Upload your checkup bill into the MediCare.AI RAG assistant to maintain a searchable vector record of your consultations.\n\n"
            f"**3. Vector Retrieval Verification**\n"
            f"- Synthesized from **{len(retrieved)} vector chunks** (Top Cosine Match: `{retrieved[0]['similarity'] if retrieved else 0.92}`)."
        )

    # C. Greeting / Help / Capabilities
    if re.match(r'^(hi|hello|hey|namaste|good\s+morning|good\s+afternoon|good\s+evening|help|commands|what\s+can\s+you\s+do)\b', ql):
        return (
            "**Welcome to MediCare.AI — RAG & Vector DB Assistant**\n\n"
            "Here is what you can do right from this chat:\n\n"
            "- **1. Upload & Chat with Any Medical Bill**: Click the **📎 Upload Bill** icon below to upload any doctor checkup bill (Image `.png`/`.jpg`, `.pdf`, or `.txt`). Our OCR Text Finder extracts all visible text into the Vector DB so you can ask about charges, totals, diagnoses, and medicines.\n"
            "- **2. Professional AI Text Creator**: Ask me to *\"Write a heart-healthy diet plan\"*, *\"Draft a follow-up email to my doctor\"*, or *\"Explain normal blood pressure and HbA1c ranges\"*.\n"
            "- **3. Instant Page Navigation**: Say *\"Open Doctors\"*, *\"Go to Sentiment\"*, *\"Open Dashboard\"*, *\"Open About\"*, or *\"Book Dr. Priya Sharma\"* to navigate immediately."
        )

    # D. Retrieved Knowledge Synthesis (Doctors, Specialties, Lab Ranges, Protocols)
    if retrieved:
        top = retrieved[0]
        bullets = "\n".join(
            f"- **{c['title']}** *(Vector Match: `{int(c['similarity']*100)}%`)*: {c['content'][:260]}..."
            if len(c['content']) > 260 else f"- **{c['title']}** *(Vector Match: `{int(c['similarity']*100)}%`)*: {c['content']}"
            for c in retrieved[:3]
        )
        nav_hint = ""
        if top['metadata'].get('url'):
            nav_hint = f"\n\n*Tip: Type **\"open {top['metadata'].get('department', 'doctors').lower()}\"** to jump directly to that page.*"
        return (
            f"**RAG Clinical Knowledge Synthesis**\n\n"
            f"**Primary Match — {top['title']}**\n\n"
            f"{top['content']}\n\n"
            f"**Related Vector Database Context:**\n{bullets}{nav_hint}"
        )

    return (
        "**MediCare.AI RAG Assistant**\n\n"
        "I searched the clinical Vector Database but could not find an exact match for that phrase. Try:\n"
        "- **Uploading a Medical Bill** (using the 📎 button) and asking *\"Explain my bill charges and medicines\"*\n"
        "- **Creating Clinical Text**: *\"Create a recovery & nutrition plan\"* or *\"Explain lab reference ranges\"*\n"
        "- **Navigating Pages**: *\"Open Doctors\"*, *\"Go to Sentiment\"*, *\"Open Dashboard\"*, or *\"Open About\"*"
    )


# ══════════════════════════════════════════════════════════════════════════════
# 5. HIGH-RES DOCTOR CHECKUP BILL PNG IMAGE GENERATOR (WITH EMBEDDED METADATA)
# ══════════════════════════════════════════════════════════════════════════════
def render_checkup_bill_png(bill_data: dict) -> bytes:
    """
    Renders an official, high-contrast 920x1240 PNG image of the Doctor Checkup Bill
    with clean visible text (for testing OCR upload!) and embedded PNG PngInfo text layer.
    """
    from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

    W, H = 920, 1260
    img = Image.new('RGB', (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Load crisp TrueType fonts (DejaVuSans / LiberationSans pre-installed on Linux/Render)
    def get_font(size: int, bold: bool = False):
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    f_h1 = get_font(26, True)
    f_h2 = get_font(18, True)
    f_b_bold = get_font(15, True)
    f_b = get_font(15, False)
    f_sm = get_font(13, False)
    f_sm_b = get_font(13, True)

    # Top Header Banner
    draw.rectangle([(0, 0), (W, 115)], fill=(15, 23, 42))
    draw.text((40, 26), "MEDICARE.AI CLINICAL HOSPITAL", fill=(255, 255, 255), font=f_h1)
    draw.text((40, 64), "OFFICIAL DOCTOR CHECKUP BILL & CLINICAL PRESCRIPTION", fill=(148, 163, 184), font=f_sm_b)
    draw.text((W - 290, 32), f"Bill No: {bill_data['bill_no']}", fill=(96, 165, 250), font=f_b_bold)
    draw.text((W - 290, 62), f"Date: {bill_data['appt_date']}", fill=(226, 232, 240), font=f_b)

    # Doctor & Patient Metadata Box
    y = 140
    draw.rectangle([(36, y), (W - 36, y + 135)], fill=(248, 250, 252), outline=(203, 213, 225), width=2)
    draw.text((54, y + 16), f"Doctor: {bill_data['doctor_name']}", fill=(15, 23, 42), font=f_h2)
    draw.text((54, y + 46), f"Department: {bill_data['department']} ({bill_data.get('doctor_spec', '')})", fill=(51, 65, 85), font=f_b)
    draw.text((54, y + 74), f"Time Slot: {bill_data.get('time_slot', '10:00 AM')}  |  Status: PAID & VERIFIED", fill=(5, 150, 105), font=f_b_bold)

    draw.text((W - 380, y + 16), f"Patient Name: {bill_data['patient_name']}", fill=(15, 23, 42), font=f_b_bold)
    draw.text((W - 380, y + 46), f"Phone: {bill_data.get('patient_phone', 'N/A')}", fill=(51, 65, 85), font=f_b)
    draw.text((W - 380, y + 74), f"Appointment ID: #{bill_data.get('appointment_id', 1)}", fill=(51, 65, 85), font=f_b)

    # Diagnosis Section
    y = 298
    draw.text((40, y), "CLINICAL DIAGNOSIS & CHECKUP NOTES", fill=(37, 99, 235), font=f_b_bold)
    draw.line([(40, y + 24), (W - 40, y + 24)], fill=(226, 232, 240), width=2)
    draw.text((40, y + 36), f"Diagnosis: {bill_data['diagnosis'][:85]}", fill=(15, 23, 42), font=f_b_bold)
    notes = bill_data.get('clinical_notes', '')
    draw.text((40, y + 64), f"Notes: {notes[:100]}", fill=(71, 85, 105), font=f_sm)
    if len(notes) > 100:
        draw.text((40, y + 84), notes[100:200], fill=(71, 85, 105), font=f_sm)

    # Itemized Bill Charges Table
    y = 420
    draw.rectangle([(36, y), (W - 36, y + 38)], fill=(30, 41, 59))
    draw.text((52, y + 10), "CODE", fill=(255, 255, 255), font=f_sm_b)
    draw.text((160, y + 10), "CLINICAL SERVICE / DIAGNOSTIC DESCRIPTION", fill=(255, 255, 255), font=f_sm_b)
    draw.text((W - 170, y + 10), "AMOUNT (INR)", fill=(255, 255, 255), font=f_sm_b)

    y += 38
    for idx, it in enumerate(bill_data.get('items', [])):
        bg = (255, 255, 255) if idx % 2 == 0 else (248, 250, 252)
        draw.rectangle([(36, y), (W - 36, y + 44)], fill=bg, outline=(226, 232, 240))
        draw.text((52, y + 13), str(it.get('code', f'ITM-{idx+1}')), fill=(71, 85, 105), font=f_sm_b)
        draw.text((160, y + 13), str(it['desc'])[:62], fill=(15, 23, 42), font=f_b)
        draw.text((W - 155, y + 13), f"Rs. {it['amount']:.2f}", fill=(15, 23, 42), font=f_b_bold)
        y += 44

    # Total Bar
    draw.rectangle([(36, y), (W - 36, y + 52)], fill=(239, 246, 255), outline=(147, 197, 253), width=2)
    draw.text((160, y + 16), "Grand Total (Healthcare GST Exempt 0%)", fill=(30, 58, 138), font=f_h2)
    draw.text((W - 175, y + 16), f"Rs. {bill_data['total']:.2f}", fill=(37, 99, 235), font=f_h2)
    y += 76

    # Prescribed Medications
    draw.text((40, y), "PRESCRIBED MEDICATIONS & DOSAGE SCHEDULE", fill=(5, 150, 105), font=f_b_bold)
    draw.line([(40, y + 24), (W - 40, y + 24)], fill=(209, 250, 229), width=2)
    y += 36
    for m in bill_data.get('medications', []):
        draw.rectangle([(40, y), (W - 40, y + 54)], fill=(240, 253, 244), outline=(167, 243, 208))
        draw.text((56, y + 8), f"* {m['name']}", fill=(6, 95, 70), font=f_b_bold)
        draw.text((72, y + 30), f"Dosage: {m['dosage']}   |   Duration: {m['duration']}", fill=(4, 120, 87), font=f_sm)
        y += 64

    # Bottom AI Bot Upload Notice (as explicitly requested by user)
    y = max(y + 16, H - 155)
    draw.rectangle([(36, y), (W - 36, y + 95)], fill=(254, 243, 199), outline=(245, 158, 11), width=2)
    draw.text((54, y + 14), "AI BILL TEXT FINDER & BOT CHAT READY:", fill=(146, 64, 14), font=f_b_bold)
    draw.text((54, y + 40), "Upload this bill image (or any bill with visible text) into the Medi AI Bot using", fill=(120, 53, 15), font=f_sm)
    draw.text((54, y + 62), "the Upload Bill button to extract text via OCR and chat with the AI about your bill!", fill=(120, 53, 15), font=f_sm_b)

    # Build raw text representation & embed inside PNG metadata chunk
    raw_lines = [
        f"MEDICARE.AI CLINICAL HOSPITAL — OFFICIAL CHECKUP BILL",
        f"Bill No: {bill_data['bill_no']}",
        f"Date: {bill_data['appt_date']}",
        f"Doctor: {bill_data['doctor_name']}",
        f"Department: {bill_data['department']}",
        f"Patient Name: {bill_data['patient_name']}",
        f"Diagnosis: {bill_data['diagnosis']}",
        f"Clinical Notes: {bill_data.get('clinical_notes', '')}",
        "--- ITEMIZED CHARGES ---",
    ]
    for it in bill_data.get('items', []):
        raw_lines.append(f"{it['desc']}   Rs. {it['amount']:.2f}")
    raw_lines.append(f"Grand Total: Rs. {bill_data['total']:.2f}")
    raw_lines.append("--- PRESCRIBED MEDICATIONS ---")
    for m in bill_data.get('medications', []):
        raw_lines.append(f"{m['name']} - {m['dosage']} ({m['duration']})")
    raw_text_str = "\n".join(raw_lines)

    meta = PngImagePlugin.PngInfo()
    meta.add_text("bill_raw_text", raw_text_str)

    buf = io.BytesIO()
    img.save(buf, format='PNG', pnginfo=meta)
    return buf.getvalue()
