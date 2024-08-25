import os
import re
import pprint
import ipinfo
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

PATH_TO_LOG = "ssl_access_log-20240811"
# Resources that you believe normally are not accessible by crawlers and bots.
REQUEST_STRING = "/assets/meshes/weapons/smg/smg.babylon"
# Log entries that will be considered
START_DATE = datetime.strptime("2024-08-05", "%Y-%m-%d")
END_DATE = datetime.strptime("2024-12-31", "%Y-%m-%d")
# Your external IP geolocation API details. You can easily integrate any. Really. Here is for ipinfo.
IP_INFO_ACCESS_TOKEN = "<Your_access_token-here>"
IP_HANDLER = ipinfo.getHandler(IP_INFO_ACCESS_TOKEN)

# Saves to the directory where the script is.
SAVE_TO_DISK=True
# Show report in CMD or Terminal
PRINT_ON_SCREEN=True

def isWithinDateRange(logEntry):
    pattern = r'\[(.*?)\]'
    dateString = re.findall(pattern, logEntry)[0].split(":")[0]
    dateFormat = '%d/%b/%Y'
    logDate = datetime.strptime(dateString, dateFormat)

    return START_DATE <= logDate <= END_DATE

# Loads all the log in the RAM before processing, not memory efficient, but fast.
def readDistinctIps():
    with open(PATH_TO_LOG, "r") as file:
        lines = file.readlines()
    file.close()

    filteredIps = [l.split(" ")[0] for l in lines if REQUEST_STRING in l and isWithinDateRange(l)]
    distinctIps = list(set(filteredIps))
    print(f"{len(distinctIps)} distinct IPs found.")
    return distinctIps

def getIpGeo(ip):
    return IP_HANDLER.getDetails(ip)

def generateReport():
    distinctIps = readDistinctIps()
    myDetails = {}
    areas = {}
    # Geolocation API calls are made in parallel. By default, the number of threads is equal to the amount of CPU cores.
    with ThreadPoolExecutor(max_workers=None) as executor:
        myFutures = {executor.submit(getIpGeo, ip): ip for ip in distinctIps}
        for future in as_completed(myFutures):
            try:
                data = future.result()
                area = f"{data.country_name},{data.region},{data.city}"
                myDetails[data.ip] = area
                if area not in areas:
                    areas[area] = 1
                else:
                    areas[area] += 1
            except Exception as ex:
                print(f"{future} generated an exception: {ex}")
    return areas

def saveReport(report):
    lines = []
    for key, value in report.items():
        lines.append(f"{key}: {value}\n")

    lines.sort()
    output = "".join(lines)
    
    if (SAVE_TO_DISK):
        # The date on when the report was created.
        currentDate = datetime.now().strftime('%Y-%m-%d')
        folderPath = currentDate
        fileName = 'report.txt'

        os.makedirs(folderPath, exist_ok=True)
        filePath = os.path.join(folderPath, fileName)

        with open(filePath, "w", encoding="utf-8") as file:
            file.write(output)
        file.close()

    if (PRINT_ON_SCREEN):
        pprint.pprint(output)

def main():
    report = generateReport()
    saveReport(report)

if __name__ == '__main__':
    main()


