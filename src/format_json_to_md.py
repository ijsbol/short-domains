from collections import defaultdict
from datetime import datetime, timezone
import json
import glob
import pathlib


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
    for raw_file_path in json_data_files:
        file_path = pathlib.Path(raw_file_path)
        with open(file_path, "r") as fr:
            domain_json_data = json.load(fr)

        raw_file_name = file_path.name.strip(".json")
        tld = raw_file_name.split("-")[0]
        length = int(raw_file_name.split("-")[1])

        formatted_text = format_data_to_md(
            domain_data=domain_json_data,
            tld=tld,
            length=length,
        )

        with open(f"out/{tld}-{length}-long-domains.md", "w+") as fw:
            fw.write(formatted_text)


if __name__ == "__main__":
    main()
