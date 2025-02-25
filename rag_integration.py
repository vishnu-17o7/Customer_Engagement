#### filepath: /c:/Users/vishn/Desktop/Programs/Customer_Engagement/rag_integration.py
import os
import json
import time
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv()

# Load Slack API credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Path for shared pending responses file
PENDING_RESPONSES_FILE = "pending_responses.json"

# Import for backward compatibility
from slack_approval import pending_responses

# Function to load pending responses from file
def load_pending_responses():
    """Load pending responses from JSON file"""
    try:
        if os.path.exists(PENDING_RESPONSES_FILE):
            with open(PENDING_RESPONSES_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"⚠️ Error loading pending responses: {e}")
        return {}

# Function to save pending responses to file
def save_pending_responses(responses):
    """Save pending responses to JSON file"""
    try:
        # Convert tuple values to lists for JSON serialization
        serializable_responses = {}
        for key, value in responses.items():
            serializable_responses[key] = list(value)
            
        with open(PENDING_RESPONSES_FILE, 'w') as f:
            json.dump(serializable_responses, f)
    except Exception as e:
        print(f"⚠️ Error saving pending responses: {e}")

def generate_rag_response(context, user_input):
    """
    Call your RAG model to generate a response.
    (This example returns a dummy response.)
    """
    # TODO: Integrate your RAG model here.
    return f"AI-generated response based on: {user_input}"

def send_to_slack(context, generated_response, source, message_id, channel_id):
    """
    Send the generated response and context to Slack for manual approval.
    """
    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text="🔍 *New AI Response Pending Approval* 🔍",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"📌 *Source:* {source}\n"
                            f"📜 *Context:* {context}\n"
                            f"💡 *Generated Response:* {generated_response}\n\n"
                            f"Reply with `yes` or `y` in this thread to approve."
                        ),
                    },
                }
            ],
        )

        if response["ok"]:
            thread_ts = response["ts"]
            print(f"✅ Sent approval request to Slack for {source} - {message_id}")
            
            # Load existing pending responses
            file_pending_responses = load_pending_responses()
            
            # Store the pending response for Slack approval (both in memory and file)
            pending_responses[thread_ts] = (message_id, channel_id, source, generated_response)
            file_pending_responses[thread_ts] = [message_id, channel_id, source, generated_response]
            
            # Save updated pending responses to file
            save_pending_responses(file_pending_responses)
            
            print(f"💾 Saved pending response to file for thread {thread_ts}")
        else:
            print(f"⚠️ Failed to send to Slack: {response['error']}")

    except SlackApiError as e:
        print(f"⚠️ Slack API Error: {e.response['error']}")

if __name__ == "__main__":
    # Example usage
    test_context = "Example context"
    test_message_id = 12345
    test_channel_id = 67890
    rag_response = generate_rag_response(test_context, "Sample query?")
    send_to_slack(test_context, rag_response, "testing", test_message_id, test_channel_id)