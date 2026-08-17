from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.chatbot import FAQMatcher

bot = FAQMatcher(ROOT / "data" / "faqs.json")

questions = [
    "I forgot my password",
    "someone stole my debit card",
    "how much cash can I withdraw from an ATM",
    "how long does a bank transfer take",
    "what are your customer service hours",
    "who won the football match yesterday",
]

for question in questions:
    result = bot.match(question)
    print("\\nQUESTION:", question)
    print("MATCH:", result["matched_question"])
    print("CONFIDENCE:", result["confidence"])
    print("ANSWER:", result["answer"])
