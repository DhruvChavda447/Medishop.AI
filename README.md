# MediCare.AI — RAG, 384-D Vector DB, Bill OCR & Multilingual Sentiment Platform

A clinical AI web platform built with **Django 4.2, PostgreSQL, a 384-D Hybrid Vector Database, Retrieval-Augmented Generation (RAG), Multi-Format Medical Bill OCR Text Finder, and XLM-RoBERTa Multilingual Sentiment & Aspect Analysis**.

## Core Modules

1. **RAG + 384-D Vector Database + Top Text Creator Bot (`doctors/rag_engine.py`)**:
   - Hybrid 384-dimensional dense feature-hashing + BM25 cosine similarity vector search.
   - Generates structured clinical reports, diet & recovery plans, and doctor follow-up emails.
   - Supports optional live LLM API keys (`GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`) plus a zero-dependency built-in Clinical RAG Text Synthesis engine.
   - **Voice-Free Command Page Navigation**: Navigate to any page via text commands (`"open doctors"`, `"go to sentiment"`, `"open dashboard"`, `"open about"`, `"go home"`).
2. **NLP Doctor Ranking & Post-Checkup Medical Bill Generator (`/doctors/`)**:
   - Ranks 29 specialists across 10 departments by XLM-RoBERTa patient review sentiment score.
   - Automatically generates an itemized **Doctor Checkup Bill & Clinical Prescription** after booking a checkup, downloadable as a high-resolution **PNG Image Bill** or **TXT Bill**.
3. **Medical Bill OCR Text Finder & Interactive Bill Chat (`/api/rag/upload-bill/`)**:
   - Upload any checkup bill or hospital invoice with visible text (`.png`, `.jpg`, `.pdf`, `.txt`) into the Medi AI Bot.
   - Extracts visible text via client-side WebAssembly OCR (`Tesseract.js`) + server-side `PyPDF` / `Pillow` metadata + `pytesseract`, indexes the bill in the Vector DB, and answers questions about charges, totals, diagnoses, and prescribed medicines.
4. **Multilingual Sentiment & 5-Aspect Chat Studio (`/sentiment/`)**:
   - Negation-aware sentiment classification across English, Gujarati (`ગુજરાતી`), Hindi (`हिन्दी`), French, Spanish, German, and Arabic.
   - Evaluates 5 healthcare aspects, polarity (`-1.0` to `+1.0`), emotion triggers, native-language empathetic responses, and includes an **Interactive Sentiment Chat Studio**.
5. **Montserrat Responsive UI**:
   - Styled globally with Google Font **Montserrat** and **JetBrains Mono**, responsive across desktop, tablet, and mobile viewports.
