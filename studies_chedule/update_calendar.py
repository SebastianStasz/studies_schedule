from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import os
import json
import time
import scrap_data
from datetime import datetime, timedelta

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
service = None


def check():
    global service
    calendar_settings = "calendar_info.json"

    if not os.path.isfile(f"./{calendar_settings}"):
        print(f'ERROR 404. File "{calendar_settings}" does not exist.')
        return False

    with open("calendar_info.json", "r+") as calendar_info_file:
        calendar_info = json.load(calendar_info_file)
        calendar_id = calendar_info["calendar_id"]

        try:
            calendar = service.calendarList().get(calendarId=calendar_id).execute()

            # Update calendar_info file
            calendar_info["summary"] = calendar["summary"]
            calendar_info["colorId"] = calendar["colorId"]
            calendar_info["updated"] = str(datetime.now())
            calendar_info_file.seek(0)
            calendar_info_file.truncate()
            json.dump(calendar_info, calendar_info_file)

            return calendar_id
        except:
            print(f"ERROR 404. Calendar with ID: {calendar_id} does not exist.")

    return False


def get_events_list(calendar_id):
    global service
    events_list = []

    page_token = None
    while True:
        events = (
            service.events()
            .list(calendarId=calendar_id, pageToken=page_token)
            .execute()
        )
        page_token = events.get("nextPageToken")
        events_list += events["items"]
        if not page_token:
            break
    return events_list


def delete_events(calendar_id, events_list):
    global service

    for event in events_list:
        service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()


def create_events(calendar_id, events_list):
    global service

    for element in events_list:
        event = {
            "summary": element["summary"],
            "location": element["link"],
            "description": element["description"],
            "start": {"dateTime": element["startDate"], "timeZone": "Europe/Warsaw",},
            "end": {"dateTime": element["endDate"], "timeZone": "Europe/Warsaw"},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 5},
                    {"method": "popup", "minutes": 60},
                ],
            },
        }

        events = service.events().insert(calendarId=calendar_id, body=event).execute()


def update_events(calendar_id):
    global service
    events_to_update = []
    schedule_data_list = scrap_data.main()
    today = datetime.now()
    inSevenDays = (today + timedelta(days=7)).isoformat()[:10]
    today_str = today.isoformat()[:10]

    new_data = list(
        filter(
            lambda x: (inSevenDays >= x["startDate"][:10] >= today_str),
            schedule_data_list,
        )
    )

    events = get_events_list(calendar_id)
    for event in events:
        if inSevenDays >= event["start"]["dateTime"][:10] >= today_str:
            events_to_update.append(event)

    delete_events(calendar_id, events_to_update)
    create_events(calendar_id, new_data)


def main():
    global service
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)
    calendar_id = check()

    if calendar_id:
        print("Calendar is updating now.")

        start_time = time.time()
        update_events(calendar_id)

        print(f"- update_events: {round(time.time() - start_time, 2)} seconds.")
        print("Updated Study Schedule.")


def show_calendars():
    global service
    calendar_list = service.calendarList().list().execute()

    print("Your calendars:")
    for calendar in calendar_list["items"]:
        print(f'- {calendar["summary"]:30} ID: {calendar["id"]}')


if __name__ == "__main__":
    main()
