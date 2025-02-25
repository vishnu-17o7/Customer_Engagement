import os
import time
import threading
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

# Dictionary to store pending responses for approval tracking
pending_responses = {}

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
            thread_ts = response["ts"]  # Store thread timestamp for tracking approvals
            print(f"✅ Sent approval request to Slack for {source} - {message_id}")

            # Store the pending response for tracking in approval system
            pending_responses[thread_ts] = (message_id, channel_id, source, generated_response)

        else:
            print(f"⚠️ Failed to send to Slack: {response['error']}")

    except SlackApiError as e:
        print(f"⚠️ Slack API Error: {e.response['error']}")

def check_slack_approvals():
    """
    Fetch recent messages from Slack and check for approvals.
    """
    print(f"🔍 Running Slack approval check... (Pending: {len(pending_responses)})")

    if not pending_responses:
        return  # Skip checking if there are no pending approvals

    try:
        response = slack_client.conversations_history(channel=SLACK_CHANNEL_ID, limit=10)

        for message in response["messages"]:
            text = message.get("text", "").strip().lower()
            thread_ts = message.get("thread_ts") or message.get("ts")  # Use ts if no thread_ts
            print(message)
            if text in ["yes", "y"] and thread_ts in pending_responses:
                message_id, channel_id, source, response_text = pending_responses.pop(thread_ts)

                if source == "discord":
                    print(f"✅ Approved response for Discord (Channel: {channel_id}, Message: {message_id}): {response_text}")
                    # Call function to post to Discord (implement separately)

                elif source == "reddit":
                    print(f"✅ Approved response for Reddit (Post ID: {message_id}): {response_text}")
                    # Call function to post to Reddit (implement separately)

    except SlackApiError as e:
        print(f"⚠️ Slack API Error: {e.response['error']}")

def approval_loop():
    """ Continuously checks Slack approvals every 10 seconds. """
    while True:
        check_slack_approvals()
        time.sleep(10)

# Start Slack approval loop in a separate thread
threading.Thread(target=approval_loop, daemon=True).start()

# Example usage
if __name__ == "__main__":
    # Test sending a response to Slack for approval
    send_to_slack(
        context="Example context here...",
        generated_response="This is an AI-generated response.",
        source="discord",
        message_id="123456789",
        channel_id="987654321"
    )

    # Keep script running (needed if running outside a bot framework)
    while True:
        time.sleep(1)
