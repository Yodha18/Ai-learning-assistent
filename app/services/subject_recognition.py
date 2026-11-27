import re
from pathlib import Path
from typing import Optional


SUBJECT_TERMS = {
    "Machine Learning": (
        "machine learning", "supervised learning", "unsupervised learning",
        "neural network", "training data", "classification model", "regression model",
    ),
    "Computer Science": (
        "computer science", "data structure", "algorithm", "programming",
        "operating system", "database", "compiler", "software engineering",
    ),
    "Mathematics": (
        "mathematics", "calculus", "algebra", "trigonometry", "derivative",
        "integral", "matrix", "polynomial", "theorem",
    ),
    "Physics": (
        "physics", "newton", "force", "momentum", "kinematics", "electromagnetic",
        "quantum", "optics", "thermodynamics", "velocity",
    ),
    "Chemistry": (
        "chemistry", "chemical reaction", "periodic table", "molecule", "atom",
        "stoichiometry", "organic chemistry", "acid", "covalent bond",
    ),
    "Biology": (
        "biology", "cell", "genetics", "dna", "photosynthesis", "organism",
        "ecology", "anatomy", "evolution", "mitosis",
    ),
    "Economics": (
        "economics", "supply and demand", "inflation", "gross domestic product",
        "monetary policy", "fiscal policy", "market equilibrium", "opportunity cost",
    ),
    "Statistics": (
        "statistics", "standard deviation", "hypothesis test", "probability distribution",
        "regression analysis", "confidence interval", "sample mean", "variance",
    ),
    "History": (
        "history", "historical", "civilization", "revolution", "world war",
        "ancient", "empire", "treaty", "colonialism",
    ),
    "Geography": (
        "geography", "climate", "landform", "population density", "latitude",
        "longitude", "tectonic", "watershed", "urbanization",
    ),
    "English": (
        "english literature", "grammar", "literary analysis", "poetry", "prose",
        "metaphor", "shakespeare", "rhetoric", "composition",
    ),
    "Accounting": (
        "accounting", "balance sheet", "income statement", "debit", "credit",
        "ledger", "cash flow statement", "accounts payable", "accounts receivable",
    ),
}


def detect_subject(text: str, filename: Optional[str] = None) -> Optional[str]:
    """Infer a subject from distinctive document vocabulary, or return None if uncertain."""
    title = Path(filename or "").stem.lower().replace("_", " ").replace("-", " ")
    normalized_text = f"{title}\n{text}".lower()
    scores = {
        subject: sum(
            1 for term in terms
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized_text)
        )
        for subject, terms in SUBJECT_TERMS.items()
    }

    title_matches = [
        subject for subject in SUBJECT_TERMS
        if re.search(rf"(?<!\w){re.escape(subject.lower())}(?!\w)", title)
    ]
    if title_matches:
        return max(title_matches, key=lambda subject: scores[subject])

    best_subject = max(scores, key=scores.get)
    return best_subject if scores[best_subject] >= 2 else None