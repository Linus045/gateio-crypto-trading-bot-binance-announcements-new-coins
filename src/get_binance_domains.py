import re

# ATTENTION: import grequests before requests
import grequests
import requests


RETRIEVE_URLS_FROM_OFFICIAL_VERIFICATION_PAGE = False
MANUAL_DOMAINS_TO_CHECK = [
    "www.binance.com",
    "www.binance.us"
]


def get_binance_domains():
    if not RETRIEVE_URLS_FROM_OFFICIAL_VERIFICATION_PAGE:
        return MANUAL_DOMAINS_TO_CHECK

    response = (
        grequests.get("https://www.binance.com/en/official-verification")
        .send()
        .response
    )
    if response.status_code == 200:
        data = response.content.decode("utf-8")
        regex = r'"ACCELERATE_ENBLED_SITES":"([a-zA-Z.,]*)"'
        match = re.search(regex, data)
        if match:
            websites = match.group(1).split(",")
            websites.extend(MANUAL_DOMAINS_TO_CHECK)
            return websites
        else:
            print("No websites extracted from official verification page")
    else:
        print(
            f"Error retrieving domains from official verification page. Status code: {response.status_code}"
        )
    return MANUAL_DOMAINS_TO_CHECK


def is_binance_verified(domainOrOther):
    """
    Check if a domain is verified by Binance (synchronous)
    Input can also be a contact email address, telephone number, etc.
    See https://www.binance.com/en/official-verification for more info
    """
    verify_url = (
        "https://www.binance.com/bapi/composite/v1/public/official-channel/verify"
    )
    content_data = {
        "content": domainOrOther,
    }
    my_headers = {
        "Content-Type": "application/json",
        "Content-Length": f"{len(content_data)}",
    }

    # TODO: make this asynchronous (using grequests)
    response = requests.post(verify_url, json=content_data, headers=my_headers)
    if response and response.status_code == 200:
        # invalid response:
        # {"code":"000000","message":null,"messageDetail":null,
        #   "data":{
        #       "status":"OK","type":"GENERAL","code":"000000000","errorData":null,
        #       "data":[],
        #       "subData":null,"params":null},"success":true}

        # valid response:
        # {"code":"000000","message":null,"messageDetail":null,
        #   "data":{
        #       "status":"OK","type":"GENERAL","code":"000000000","errorData":null,
        #       "data":[{
        #               "id":100463,"type":100001,"typeCn":"域名","typeEn":"domain",
        #               "content":"www.binancezh.com","remark":"domain","createTime":1571716702000,"updateTime":1641541225000
        #        }],
        #       "subData":null,"params":null},"success":true}
        data = response.json()
        if "data" in data and "data" in data["data"]:
            return data["data"]["data"] != []
    return False


def measure_response_time(domains):
    def exception_handler(request, exception):
        # print("Request failed")
        pass

    measurements = []
    rs = (grequests.get(f"https://{website}") for website in domains)
    result = grequests.map(rs, exception_handler=exception_handler)
    for i, resp in enumerate(result):
        website = domains[i]
        if resp is not None:
            if resp.status_code == 200:
                measurements.append(
                    {
                        "website": website,
                        "status_code": resp.status_code,
                        "repsone_time": resp.elapsed.total_seconds(),
                        "binance_verified": is_binance_verified(website),
                    }
                )
            else:
                print(f"\t[-] {website} errors. Error: {resp.status_code}")
        else:
            print(f"\t[-] {website} is down.")
            pass
    measurements.sort(key=lambda x: x["repsone_time"])
    return measurements


def main():
    websites = get_binance_domains()
    print(f"{len(websites)} websites found")

    measurements = measure_response_time(websites)
    print("Verified domains by Binance:")
    for measurement in measurements:
        if measurement["binance_verified"]:
            print(f"{measurement['website']} - {measurement['repsone_time'] * 1000}")

    print("\nUnverified domains by Binance:")
    for measurement in measurements:
        if not measurement["binance_verified"]:
            print(f"{measurement['website']}")


if __name__ == "__main__":
    main()
