from transformers import pipeline
import torch

# Set device: use GPU if available, else CPU
device = 0 if torch.cuda.is_available() else -1

# Load zero-shot classification pipeline with facebook/bart-large-mnli
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device)

# Define candidate labels for categorization
LABELS = ["audio equipment", "headphones", "mechanical keyboards", "key switches", "audio quality"]

def analyze_text(text):
    """
    Analyze text using zero-shot classification.
    Returns a dictionary with relevance, chosen category, and confidence.
    """
    result = classifier(text, LABELS, multi_label=True)
    top_label = result["labels"][0]
    confidence = result["scores"][0] * 100  # percentage

    return {
        "relevant": confidence > 60,  # adjust threshold as needed
        "text": text,
        "category": top_label,
        "confidence": confidence
    }