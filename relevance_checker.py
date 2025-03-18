from transformers import pipeline
import torch
from sklearn.metrics import accuracy_score, classification_report

# Check if GPU is available
device = 0 if torch.cuda.is_available() else -1
print(f"Device set to use {'cuda:0' if device == 0 else 'CPU'}")

# Use a better classification model
classifier = pipeline("zero-shot-classification", model="cross-encoder/nli-distilroberta-base", device=device)

# Simplified labels for better performance
LABELS = [
    "headphones", "IEMs", "wireless", "noise cancellation",
    "gaming", "DACs", "amplifiers", "studio"
]

def analyze_text(text):
    """
    Analyze text using zero-shot classification.
    Returns a dictionary with relevance, chosen category, and confidence.
    """
    result = classifier(text, LABELS, multi_label=False)
    top_label = result["labels"][0]
    confidence = result["scores"][0] * 100

    return {
        "relevant": confidence > 50,  # Lowered threshold
        "text": text,
        "category": top_label,
        "confidence": confidence
    }

# Example test dataset (Replace this with real test data)
test_data = [
    ("This amplifier has great bass response.", "amplifiers"),
    ("The new planar magnetic headphones sound amazing!", "headphones"),
    ("Wireless earbuds with noise cancellation are getting better.", "wireless"),
    ("IEMs provide great isolation for musicians.", "IEMs"),
    ("Studio monitoring headphones have flat sound signatures.", "studio"),
    ("DACs improve sound quality by processing audio signals.", "DACs"),
    ("Gaming headsets need surround sound for immersion.", "gaming"),
    ("Bluetooth headphones are great for travel.", "wireless"),
    ("Amplifiers power high-impedance headphones efficiently.", "amplifiers"),
    ("Noise cancellation helps in loud environments.", "noise cancellation"),
]

# Evaluate performance
y_true = []
y_pred = []

for text, true_label in test_data:
    result = analyze_text(text)
    y_true.append(true_label)
    y_pred.append(result["category"])

    # Debugging output to analyze predictions
    print(f"Text: {text}")
    print(f"Predicted: {result['category']} (Confidence: {result['confidence']:.2f}%)")
    print(f"Actual: {true_label}\n{'-'*40}")

# Calculate accuracy
accuracy = accuracy_score(y_true, y_pred)
print(f"\nAccuracy: {accuracy:.2f}\n")

# Print classification report
print("Classification Report:")
print(classification_report(y_true, y_pred))
