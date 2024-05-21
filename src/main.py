import datetime
import json
import socket
import string
import itertools
import threading
import time

from constants import LAST_UPDATED_KEY, DomainStatus


def generate_strings_to_check(size: int) -> list[str]:
    """Generate all possible x-length domain combinations."""
    letters = string.ascii_lowercase + string.digits
    return [''.join(s) for s in itertools.product(letters, repeat=size)]


def check_domain_registration(domain: str, tld: str, whois: str, *, depth: int = 1) -> DomainStatus:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect_ex((whois, 43))

    try:
        s.send(bytes(domain, "utf-8") + b"\r\n")
    except TimeoutError:
        print(f"> [{tld}] [ !!! ] Timed out, trying again.")
        return check_domain_registration(domain, tld, whois)

    response = s.recv(1024)
    response_string = response.decode("utf-8")
    s.close()
    if "domain not found." in response_string.lower():
        return DomainStatus.UNREGISTERED
    elif f"domain name: {domain}" in response_string.lower():
        return DomainStatus.REGISTERED
    elif "application" in response_string.lower():
        return DomainStatus.AVAILABLE_FOR_APPLICATION
    elif "premium" in response_string.lower():
        return DomainStatus.PREMIUM
    elif len(response_string) > 10 or depth > 10:
        return DomainStatus.FAILED
    else:
        print(response_string)
        print(f"> [{tld}] [ ! ] Ratelimited, waiting a few seconds.")
        time.sleep(3)
        return check_domain_registration(domain, tld, whois, depth=depth + 1)


def load_tld_registration_information(tld: str, size: int, whois: str) -> None:
    time_start = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
    domains_to_check: list[str] = generate_strings_to_check(size)
    number_of_domains_to_check: int = len(domains_to_check)
    checked_domains: dict[str, DomainStatus | int] = {}

    for index, host_name in enumerate(domains_to_check):
        domain = f"{host_name}.{tld}"
        registered = check_domain_registration(domain, tld, whois)
        print(f"> [{tld}] [{index + 1}/{number_of_domains_to_check}] \t{domain} is {registered.name}")

        checked_domains[host_name] = registered.value

        if index % 10 == 0:
            print(f"> [{tld}] Saving progress...")
            checked_domains[LAST_UPDATED_KEY] = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
            with open(f"_data/json/{tld}-{size}.json", "w+") as f:
                json.dump(
                    obj=checked_domains,
                    fp=f,
                    indent=2,
                    ensure_ascii=True,
                    sort_keys=True,
                )

    time_end = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

    checked_domains[LAST_UPDATED_KEY] = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
    with open(f"_data/json/{tld}-{size}.json", "w+") as f:
        json.dump(
            obj=checked_domains,
            fp=f,
            indent=2,
            ensure_ascii=True,
            sort_keys=True,
        )

    registered_count = sum([1 for _, v in checked_domains.items() if v == True])
    unregistered_count = sum([1 for _, v in checked_domains.items() if v == False])
    failed_lookup_count = sum([1 for _, v in checked_domains.items() if v == None])
    successful_lookup_count = registered_count + unregistered_count
    total_count = registered_count + unregistered_count + failed_lookup_count
    success_rate = round((successful_lookup_count / total_count) * 100, 2)
    if success_rate > 99.999:
        success_rate = int(100)

    print(
        f"Fetched registration information for {total_count} domains."
        + f"\n  - Attempted: {number_of_domains_to_check}"
        + f"\n  - Failed: {failed_lookup_count}"
        + f"\n  - Lookup success rate: {success_rate}%"
        + f"\n  - {registered_count} registered"
        + f"\n  - {unregistered_count} unregistered"
        + f"\nTime taken: {round(time_end-time_start)} seconds."
    )


def main() -> None:
    with open("_data/config/tracked_tlds.json", "r") as f:
        config = json.load(f)
    for domain, data in config.items():
        lengths = data["lengths"]
        whois = data["whois"]
        for length in lengths:
            thread = threading.Thread(target=load_tld_registration_information, args=(domain, length, whois))
            thread.start()


if __name__ == "__main__":
    main()
