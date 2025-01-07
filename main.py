import cloudscraper

url = "https://www.sofascore.com/api/v1/sport/basketball/scheduled-events/2025-01-01"

scraper = cloudscraper.create_scraper()
response = scraper.get(url)
if response.status_code == 200:
    data = response.json().get("events", [])
    print(len(data))
    # the data
    for event in data:
        print(event.get("homeTeam").get("name"), event.get("awayTeam").get("name"))
else:
    print(f"Failed to retrieve data: {response.status_code}")