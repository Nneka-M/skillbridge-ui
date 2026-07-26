---
title: SkillBridge Resume Analyzer
emoji: 🎯
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.42.0
app_file: app.py
pinned: false
---

# SkillBridge — AI Resume Analyzer

Upload your CV and get an employability score backed by real market data from 500+ job postings.

## What it does
- Extracts your skills from your CV (PDF or DOCX)
- Compares them against real job market requirements for your target role
- Identifies skill gaps with XAI explanations and market frequency data
- Gives you a weighted employability score

## Tech Stack
- **AI**: Google Gemini (extraction + XAI reasoning)
- **Vector DB**: Qdrant (role skill profiles from real job data)
- **Market Data**: JSearch API (500+ real job postings across 5 role buckets)
- **CV Parsing**: pdfplumber
- **Backend**: FastAPI
- **Frontend**: Gradio
