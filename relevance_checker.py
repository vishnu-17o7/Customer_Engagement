from transformers import pipeline
import torch

# Set device: use GPU if available, else CPU
device = 0 if torch.cuda.is_available() else -1

# Load zero-shot classification pipeline with facebook/bart-large-mnli
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device)

# Define candidate labels for categorization - focused on headphoneGeek's audio equipment specialties
LABELS = [
    "headphoneGeek",
    "audio equipment", 
    "headphones", 
    "in-ear monitors", 
    "IEMs",
    "earbuds",
    "wireless audio", 
    "noise cancellation", 
    "audiophile equipment",
    "sound quality", 
    "audio drivers",
    "planar magnetic", 
    "balanced armature",
    "true wireless",
    "gaming audio",
    "studio monitoring",
    "DACs",
    "amplifiers",
    "sound signature",
    "audio brands",
    "audio accessories",
    "audio quality",
    "listening experience",
    "sound systems"
]

def analyze_text(text):
    """
    Analyze text using zero-shot classification to determine if it's relevant 
    to headphoneGeek's audio equipment specialty.
    Returns a dictionary with relevance, chosen category, and confidence.
    """
    result = classifier(text, LABELS, multi_label=True)
    top_label = result["labels"][0]
    confidence = result["scores"][0] * 100  # percentage

    return {
        "relevant": confidence > 70, # lowered threshold to catch more audio-related queries
        "text": text,
        "category": top_label,
        "confidence": confidence
    }