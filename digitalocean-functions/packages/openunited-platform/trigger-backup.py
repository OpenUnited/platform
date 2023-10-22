import os
import logging
import requests


logger = logging.getLogger("trigger-backup")


def main(event, context):
    url = os.environ["BACKUP_WEBHOOK_URL"]
    api_key = os.environ["BACKUP_WEBHOOK_KEY"]
    response = requests.post(url, headers={"X-API-KEY": api_key})
    logger.info("Response status: %s\nContent: %s\n", response.status_code, response.content)
    return {
        "body": {
            "status_code": response.status_code
        }
    }
