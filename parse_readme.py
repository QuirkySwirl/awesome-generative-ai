import re
import json
import traceback

def parse_readme(readme_content):
    # Use splitlines() which handles different newline characters gracefully
    lines = readme_content.splitlines()
    data = []
    current_section = None
    current_subsection = None

    # Regex to find markdown links: [* Optional text [Link Text](URL)?: Description]
    # Handles optional leading text like [🔥], optional colon after URL.
    # Improved regex to better handle variations and avoid capturing unintended parts.
    link_regex = re.compile(r"^\s*\*\s*(?:\[.*?\]\s*)?\[(.+?)\]\((.+?)\)\s*:?\s*(.*)")

    for line in lines:
        line = line.strip()

        # Skip empty lines or lines that are just separators like '---'
        if not line or line.startswith('---'):
            continue

        # Section header (##)
        if line.startswith('## ') and not line.startswith('###'): # Ensure it's not H3
            title = line[3:].strip()
            # Skip specific headers if needed (like "Contribute", "License")
            if title in ["Repository Introduction", "Contribute", "License", "Stargazers over time"]:
                 current_section = None # Stop processing until a valid section starts
                 continue
            current_section = {"title": title, "subsections": [], "links": []}
            data.append(current_section)
            current_subsection = None # Reset subsection
            # print(f"Section: {current_section['title']}")
            continue

        # Subsection header (###)
        elif line.startswith('### '):
            if current_section: # Ensure we are within a valid section
                title = line[4:].strip()
                current_subsection = {"title": title, "links": []}
                current_section["subsections"].append(current_subsection)
                # print(f"  Subsection: {current_subsection['title']}")
            # If not inside a section, ignore the subsection header
            else:
                current_subsection = None
            continue

        # Link item (*) - Must be within a section or subsection
        elif line.startswith('* ') and (current_section or current_subsection):
            match = link_regex.match(line)
            if match:
                link_text, url, description = match.groups()
                link_item = {
                    "text": link_text.strip(),
                    "url": url.strip(),
                    "description": description.strip()
                }
                # Prioritize adding to subsection if it exists
                if current_subsection:
                    current_subsection["links"].append(link_item)
                    # print(f"    Link (sub): {link_item['text']}")
                elif current_section: # Otherwise add to section if it exists
                    current_section["links"].append(link_item)
                    # print(f"    Link (sec): {link_item['text']}")
            # else:
            #     # Optionally log lines that look like list items but don't match the regex
            #     print(f"    Non-matching list item?: {line}")
            continue

        # Ignore other lines (descriptions, images, etc.)

    # --- Post-processing ---

    # Remove subsections that ended up empty
    for section in data:
        if 'subsections' in section:
            section['subsections'] = [sub for sub in section['subsections'] if sub.get('links')]
            if not section['subsections']: # Remove empty list key
                del section['subsections'] 

    # Remove sections that ended up empty (no links AND no non-empty subsections)
    data = [
        section for section in data
        if section.get('links') or section.get('subsections')
    ]

    return data

# --- Script Execution ---
if __name__ == "__main__":
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            # Read the raw content
            content = f.read()

        # Parse the raw content
        parsed_data = parse_readme(content)

        # Write the structured data to a JSON file
        output_filename = "readme_data.json"
        with open(output_filename, "w", encoding="utf-8") as outfile:
            # Use ensure_ascii=False to handle potential non-ASCII characters correctly
            json.dump(parsed_data, outfile, indent=2, ensure_ascii=False)

        print(f"Successfully parsed README.md and created {output_filename}")
        print(f"Found {len(parsed_data)} main sections.")

    except FileNotFoundError:
        print("Error: README.md not found.")
    except Exception as e:
        print(f"An error occurred during parsing or writing: {e}")
        traceback.print_exc()
