import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone


def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime(year, month, day, hour, minute, 0).astimezone().isoformat()
    return dt


def main():
    data = scrap_data()
    formated_data = format_data_api(data)
    return formated_data


def scrap_data():
    schedule = []
    data_website = "http://planzajec.uek.krakow.pl/index.php?typ=G&id=171131&okres=2"
    request = requests.get(data_website)
    soup = BeautifulSoup(request.content, "html.parser")

    table = soup.find("table")
    rows = table.find_all("tr")
    del rows[0]

    for row in rows:
        cells = row.find_all("td")

        if cells[2].get_text() == "Język obcy 2.3 - grupa przedmiotów":
            day = cells[1].get_text().split()[0]
            if day == "Pn":
                teacher = "Dorota Galata-Młyniec"
                subject = "Język angielski"
            elif day == "Pt":
                teacher = "Stanisław Górecki"
                subject = "Język niemiecki"
            else:
                continue
        else:
            teacher = cells[4].get_text().rstrip()
            subject = cells[2].get_text()

        try:
            link = cells[5].find("a").get("href")
        except:
            link = cells[5].get_text()

        day_data = {
            "term": cells[0].get_text(),
            "hour": cells[1].get_text(),
            "subject": subject,
            "type": cells[3].get_text(),
            "teacher": teacher,
            "room": link,
        }

        schedule.append(day_data)

    return schedule


def format_data_api(data_list):
    formated_data = []

    for el in data_list:
        description = f"Typ: {el['type']} / Nauczyciel: {el['teacher']}"
        date = el["term"].split("-")
        time = el["hour"].split()
        start_time = time[1].split(":")
        end_time = time[3].split(":")

        start_date = convert_to_RFC_datetime(
            int(date[0]),
            int(date[1]),
            int(date[2]),
            int(start_time[0]),
            int(start_time[1]),
        )

        end_date = convert_to_RFC_datetime(
            int(date[0]),
            int(date[1]),
            int(date[2]),
            int(end_time[0]),
            int(end_time[1]),
        )

        formated_el = {
            "summary": el["subject"],
            "startDate": f"{start_date}",
            "endDate": f"{end_date}",
            "description": description,
            "link": el["room"],
        }

        formated_data.append(formated_el)

    return formated_data

