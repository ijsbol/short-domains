from collections import defaultdict
from datetime import datetime, timezone
import json
import glob
import pathlib
from typing import TypedDict


class RawStats(TypedDict):
    tlds_tracked: set[str]
    domains_tracked: int
    available_domains_2l: int
    registration_rate_2l: list[float]


class StatsFormatted(TypedDict):
    tlds_tracked: int
    domains_tracked: int
    available_domains_2l: int
    registration_rate_2l: str
    data_formatted: str


def format_data_to_md(domain_data: dict[str, bool | int | None], tld: str, length: int) -> str:
    updated_at = datetime.fromtimestamp(
        timestamp=int(domain_data['___last_updated___'] or 0),
        tz=timezone.utc,
    )
    updated_at_str = updated_at.strftime("%m/%d/%Y, %H:%M:%S")

    del domain_data["___last_updated___"]
    registered_count = sum([1 for _, v in domain_data.items() if v == True])
    unregistered_count = sum([1 for _, v in domain_data.items() if v == False])
    failed_lookup_count = sum([1 for _, v in domain_data.items() if v == None])
    successful_lookup_count = registered_count + unregistered_count
    total_count = registered_count + unregistered_count + failed_lookup_count
    success_rate = round((successful_lookup_count / total_count) * 100, 2)
    registration_rate = round((registered_count / successful_lookup_count) * 100, 2)
    success_rate = int(100) if success_rate > 99.999 else success_rate
    registration_rate = int(100) if registration_rate > 99.999 else registration_rate

    unregistered_domains = [domain for domain, registered in domain_data.items() if not registered]

    output = f"# Available {length} character long domains for `.{tld}`"
    output += f"\n\n## Data last updated: {updated_at_str}"
    output += f"\n\n|Stat|Amount|"
    output += f"\n|--|--|"
    output += f"\n|Registered domains|{registered_count}|"
    output += f"\n|Unregistered domains|{unregistered_count}|"
    output += f"\n|Registration rate|{registration_rate}%|"
    output += f"\n|Failed lookups|{failed_lookup_count}|"
    output += f"\n|Successful lookups|{successful_lookup_count}|"
    output += f"\n|Lookup success rate|{success_rate}%|"
    output += f"\n\n"

    starts_with_sections: dict[str, list[str]] = defaultdict(lambda: [])
    for domain in unregistered_domains:
        starts_with_char = domain[0]
        starts_with_sections[starts_with_char].append(domain)

    for starts_with_section, domains in starts_with_sections.items():
        output += f"\n<details>\n<summary>{len(domains)} unregistered domains starting with <bold><code>{starts_with_section}</code></bold></summary>\n"
        output += f"\n{'\n'.join([f'- `{domain}.dev`' for domain in domains])}"
        output += "\n</details>"
    return output


def main() -> None:
    json_data_files = glob.glob("_data/json/*.json")
    raw_stats: RawStats = {
        "tlds_tracked": set(),
        "domains_tracked": 0,
        "available_domains_2l": 0,
        "registration_rate_2l": [],
    }
    data_formatted = ""

    for raw_file_path in json_data_files:
        file_path = pathlib.Path(raw_file_path)
        with open(file_path, "r") as fr:
            domain_json_data = json.load(fr)

        raw_file_name = file_path.name.strip(".json")
        tld = raw_file_name.split("-")[0]
        length = int(raw_file_name.split("-")[1])

        raw_stats["tlds_tracked"].add(tld)

        formatted_text = format_data_to_md(
            domain_data=domain_json_data,
            tld=tld,
            length=length,
        )

        registered_count = sum([1 for _, v in domain_json_data.items() if v == True])
        unregistered_count = sum([1 for _, v in domain_json_data.items() if v == False])
        successful_lookup_count = registered_count + unregistered_count
        registration_rate = round((registered_count / successful_lookup_count) * 100, 2)

        data_formatted += (
            f"\n#### [{unregistered_count} available <bold>{length} character long <code>.{tld}</code> domains</bold>]"
            + f"(https://github.com/Isabe1le/domain-registration-tracking/blob/main/out/{tld}-{length}-long-domains.md)"
            + f"\n"
        )

        raw_stats["domains_tracked"] += successful_lookup_count
        if length == 2:
            raw_stats["available_domains_2l"] += successful_lookup_count
            raw_stats["registration_rate_2l"].append(registration_rate)

        with open(f"out/{tld}-{length}-long-domains.md", "w+") as fw:
            fw.write(formatted_text)

    registration_rate_2l = sum(raw_stats["registration_rate_2l"]) / len(raw_stats["registration_rate_2l"])
    registration_rate_2l = int(100) if registration_rate_2l > 99.999 else registration_rate
    registration_rate_2l = f"{registration_rate_2l}%"
    stats_formatted: StatsFormatted = {
        "available_domains_2l": raw_stats["available_domains_2l"],
        "domains_tracked": raw_stats["domains_tracked"],
        "tlds_tracked": len(raw_stats["tlds_tracked"]),
        "registration_rate_2l": registration_rate_2l,
        "data_formatted": data_formatted,
    }

    with open(f"README.md", "w") as readme_f:
        with open(f"_data/README.md.template", "r") as template_f:
            template = template_f.read()
        print(template)
        readme_f.write(template % stats_formatted)


if __name__ == "__main__":
    main()
