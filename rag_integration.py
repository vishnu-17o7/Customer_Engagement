import requests
import json

# Replace with your actual Slack webhook URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def generate_rag_response(context, user_input):
    """
    Call your RAG model to generate a response.
    (This example returns a dummy response.)
    """
    # TODO: Integrate your RAG model here.
    return f"AI-generated response based on: {user_input}"

def send_to_slack(context, generated_response, source, message_id):
    """
    Send the generated response and context to Slack for manual approval.
    """
    payload = {
        "text": (
            f"🔍 *New AI Response Pending Approval* 🔍\n\n"
            f"📌 *Source:* {source}\n"
            f"📜 *Context:* {context}\n"
            f"💡 *Generated Response:* {generated_response}\n\n"
            f"Reply with `yes` or `y` in this thread to approve."
        )
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
    
    if response.status_code == 200:
        print(f"Sent approval request to Slack for {source} - {message_id}")
    else:
        print(f"Failed to send to Slack: {response.status_code}, {response.text}")
