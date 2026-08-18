# SecureBank FAQ Chatbot

A complete student FAQ chatbot project built with:

- **Frontend:** HTML + CSS + JavaScript
- **Backend:** Python
- **NLP:** NLTK
- **Matching:** TF-IDF + Cosine Similarity
- **FAQ storage:** JSON
- **Deployment:** GitHub + Vercel

The project uses a **fictional bank called SecureBank**. It is intended for coursework and demonstration purposes only.

## What the chatbot does

1. Accepts a customer question from the chat interface.
2. Preprocesses the text using NLTK:
   - tokenization
   - lowercase normalization
   - stopword removal
   - Porter stemming
3. Converts the stored FAQ questions and the user query into TF-IDF vectors.
4. Measures cosine similarity.
5. Selects the FAQ with the highest similarity score.
6. Returns the stored answer if the score passes the confidence threshold.
7. Returns a safe fallback response if no FAQ is similar enough.

The matching engine uses both word TF-IDF and a small character TF-IDF component to make short questions and minor spelling differences more reliable.

## Optional grounded AI answers (Gemini)

For more natural answers to paraphrased questions, the chatbot can use the Gemini API with `gemini-3.5-flash-lite`. It first retrieves the closest FAQ records. SecureBank questions are answered from that context; general questions are answered by the model without unrelated FAQ context.

1. Create a Gemini API key at https://aistudio.google.com/app/apikey.
2. In Vercel, open **Project Settings → Environment Variables**.
3. Add `GEMINI_API_KEY` with your key for Production, Preview, and Development.
4. Redeploy the project.

Never put a real key in source code or commit it to GitHub. If `GEMINI_API_KEY` is not configured or the service is unavailable, the chatbot automatically uses TF-IDF matching only.

## Knowledge base

The repository contains:

- `data/knowledge_base.txt` — the complete human-readable SecureBank knowledge base.
- `data/faqs.json` — structured FAQ data used by the Python matcher.

**Total structured FAQ entries: 240**

The knowledge base covers:

- Checking accounts
- Savings accounts
- Debit cards
- Credit cards
- Online and mobile banking
- Password/login problems
- Transfers and wires
- ATMs
- Direct deposit
- Checks
- Bill Pay
- Overdrafts and fees
- Fraud/security
- Personal loans
- Account alerts
- Branch services
- Pending transactions
- Refunds and disputes
- Account restrictions
- Customer support information
- Account ownership, beneficiaries, deceased-account support, and accessibility
- Mobile deposits, digital wallets, automatic payments, and tax documents
- Expanded fraud, dispute, credit-card, loan, ATM, branch, and transfer support

## Project structure

```text
securebank-faq-chatbot/
├── api/
│   └── chat.py
├── data/
│   ├── faqs.json
│   └── knowledge_base.txt
├── lib/
│   ├── __init__.py
│   └── chatbot.py
├── scripts/
│   └── test_chatbot.py
├── index.html
├── styles.css
├── script.js
├── requirements.txt
├── vercel.json
├── .gitignore
└── README.md
```

## Run the matching engine locally

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it, then install dependencies:

```bash
pip install -r requirements.txt
```

Test the FAQ matcher:

```bash
python scripts/test_chatbot.py
```

This test does not require any external AI API or API key.

## Run the full app locally

The easiest way to test the complete Vercel project locally is with the Vercel CLI:

```bash
npm install -g vercel
vercel dev
```

Then open the local URL shown by Vercel.

## Deploy with GitHub + Vercel

1. Create a new GitHub repository.
2. Upload all files from this project to the repository root.
3. Push/commit the repository.
4. Sign in to Vercel.
5. Select **Add New → Project**.
6. Import the GitHub repository.
7. Leave the project settings at their defaults.
8. Deploy.

Vercel serves the HTML/CSS/JS frontend and runs `api/chat.py` as a Python serverless function.

## API request

The frontend sends:

```json
{
  "question": "I forgot my online banking password"
}
```

to:

```text
POST /api/chat
```

Example response:

```json
{
  "answer": "Select \"Forgot Password\" on the login page...",
  "matched": true,
  "confidence": 0.72,
  "matched_question": "I forgot my online banking password. What should I do?",
  "category": "Online Banking"
}
```

## Why no NLTK downloads are required

The project intentionally uses `RegexpTokenizer` and `PorterStemmer`, which do not require downloading the NLTK `punkt` or `stopwords` datasets. A small stopword list is included directly in the project.

This makes deployment on Vercel simpler and more reliable.

## Safety

This is a fictional educational bank. The chatbot:

- does not access real bank accounts;
- cannot move money or change account information;
- never needs passwords, PINs, full card numbers, or verification codes;
- returns answers only from the supplied FAQ knowledge base.

## Assignment requirement mapping

| Requirement | Implementation |
|---|---|
| Collect FAQs | `data/faqs.json` |
| Questions and answers | 240 structured FAQ entries |
| NLP preprocessing | NLTK tokenizer + Porter stemmer |
| Similarity matching | TF-IDF + cosine similarity |
| Best answer selection | Highest scoring FAQ above threshold |
| Chatbot response | Python `/api/chat` endpoint |
| Chat UI | HTML + CSS + JavaScript |
| Deployment | GitHub + Vercel |
