import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Replace with your Slack bot token and channel ID
SLACK_BOT_TOKEN = "xoxb-2474535627892-8491755964343-OMmMQSFNQNyJPRGrbHCiGJwB"
SLACK_CHANNEL_ID = "C08EYLN1E6Q"

client = WebClient(token=SLACK_BOT_TOKEN)

# Dictionary to track pending responses:
# Key: Slack thread timestamp (or message id used in your integration)
# Value: tuple(message_id, source, response_text)
pending_responses = {}

def check_slack_approvals():
    """
    Fetch recent messages from Slack and check if any contain approval.
    """
    try:
        response = client.conversations_history(channel=SLACK_CHANNEL_ID, limit=10)
        for message in response["messages"]:
            text = message.get("text", "").strip().lower()
            thread_ts = message.get("thread_ts", None)  # Assuming approval is given in a thread reply
            if text in ["yes", "y"] and thread_ts in pending_responses:
                message_id, source, response_text = pending_responses.pop(thread_ts)
                if source == "discord":
                    approve_discord_reply(message_id, response_text)
                elif source == "reddit":
                    approve_reddit_reply(message_id, response_text)
    except SlackApiError as e:
        print(f"Slack API Error: {e.response['error']}")

def approve_discord_reply(message_id, response_text):
    """
    Approve and post the response to Discord.
    (Fill in with your Discord posting logic.)
    """
    print(f"Approved response for Discord message {message_id}: {response_text}")
    # TODO: Integrate Discord API to send the response

def approve_reddit_reply(message_id, response_text):
    """
    Approve and post the response to Reddit.
    (Fill in with your Reddit posting logic.)
    """
    print(f"Approved response for Reddit post {message_id}: {response_text}")
    # TODO: Integrate Reddit API to reply to the post

if __name__ == "__main__":
    # Continuously check for approvals every 10 seconds.
    while True:
        check_slack_approvals()
        time.sleep(10)
