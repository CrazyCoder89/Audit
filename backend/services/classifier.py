# Auto-classifies documents into Financial/Legal/Compliance/HR
# Simple but effective — no ML library needed for now
import re

# Keywords that indicate each category
CATEGORY_KEYWORDS = {
    "financial": [
        "invoice", "budget", "revenue", "expense", "financial", 
        "profit", "loss", "balance", "tax", "audit", "payment",
        "transaction", "ledger", "payroll", "receipt"
    ],
    "legal": [
        "contract", "agreement", "legal", "terms", "policy",
        "clause", "litigation", "jurisdiction", "liability",
        "indemnity", "warranty", "nda", "confidential"
    ],
    "compliance": [
        "compliance", "regulation", "regulatory", "gdpr", "iso",
        "standard", "requirement", "framework", "control",
        "assessment", "risk", "sox", "hipaa", "policy"
    ],
    "hr": [
        "employee", "hiring", "onboarding", "performance", "hr",
        "human resources", "salary", "benefits", "leave",
        "attendance", "appraisal", "recruitment", "termination"
    ]
}

def classify_document(filename: str, text_content: str = "") -> str:
    # Combine filename and content for classification
    combined_text = (filename + " " + text_content).lower()
    combined_text = re.sub(r'[^a-z0-9\s]', ' ', combined_text)

    # Count keyword matches for each category
    scores = {category: 0 for category in CATEGORY_KEYWORDS}
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined_text:
                scores[category] += 1

    # Return the category with the highest score
    best_category = max(scores, key=scores.get)

    # Only classify if at least one keyword matched
    if scores[best_category] == 0:
        return "unknown"

    return best_category

