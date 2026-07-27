import os
import re
import pandas as pd
from openai import OpenAI
import time
import json

def get_ai_client():
    """Initializes client pointing to GitHub Models API."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("Error: GITHUB_TOKEN environment variable is missing in Run Configurations")

    return OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )

def clean_species_name(line):
    """Removes leading index numbers in species' names"""
    line = re.sub(r'\[source.*?\]', '', line)
    line = re.sub(r'^\d+\s*', '', line.strip())
    return line

def extract_species_data_with_retry(client, species_name, max_retries=3):
    """Prompting the LLM to extract structured trait data for a single species."""
    """Retries up to 3 times if the API call or JSON parsing fails."""
    prompt = f"""
    Analyze the bacterial species "{species_name}" for sustainable bioprospecting.
    Return ONLY a raw JSON object (no markdown formatting, no extra text) with these exact keys:
    {{
        "species_name": "{species_name}",
        "primary_function": "Summary of biological role",
        "sustainability_application": "How it can be used for eco-friendly tech or agriculture",
        "biosafety_level": "BSL-1, BSL-2, or Unknown"
    }}
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
            # GitHub Models hosted model identifier:
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a scientific data extraction engine. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
            # Using GPT because Anthropic requires payment
            temperature=0.1
            )

            raw_output = response.choices[0].message.content.strip()

            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()

            data = json.loads(raw_output)
            return data

        except Exception as e:
            print(f" [Attempt {attempt}/{max_retries}] Failed for '{species_name}': {e}")
            time.sleep(2)
    return {
            "species_name": species_name,
            "primary_function": "Error / Extraction Failed",
            "sustainability_application": "N/A",
            "biosafety_level": "Unknown"
            }


def generate_summary_report(df, output_dir):
    """Generating a text summary of the bioprospecting matrix results."""
    summary_path = os.path.join(output_dir, "summary_report.txt")

    total = len(df)
    bsl1 = len(df[df['biosafety_level'] == 'BSL-1'])
    bsl2 = len(df[df['biosafety_level'] == 'BSL-2'])
    unknown = total - (bsl1 + bsl2)

    report_content = f"""==========================================
PAPUA MICROBIAL BIOPROSPECTING SUMMARY
==========================================
Total Species Processed: {total}

Biosafety Breakdown:
 - BSL-1 (Safe for general research): {bsl1}
 - BSL-2 (Moderate biosafety risk): {bsl2}
 - Unknown / Unclassified: {unknown}

Top Recommended BSL-1 Candidates:
"""
    # Sample up to 5 BSL-1 species for a quick review
    bsl1_samples = df[df['biosafety_level'] == 'BSL-1'].head(5)
    for idx, row in bsl1_samples.iterrows():
        report_content += f" • {row['species_name']}: {row['sustainability_application']}\n"

    with open(summary_path, "w") as f:
        f.write(report_content)

    print(f"Generated text summary report at: {summary_path}")

def run_pipeline():
    client = get_ai_client()

    # Check possible file paths for target species list
    possible_paths = [
        "target-species.txt",
        "target_species.txt",
        "data/target-species.txt",
        "data/target_species.txt"
    ]

    input_file = None
    for path in possible_paths:
        if os.path.exists(path):
            input_file = path
            break

    if not input_file:
        print("Error: Could not find target species text file! Please check the file location.")
        return

    print(f"Found species list at: '{input_file}'")

    with open(input_file, "r") as f:
        species_list = [clean_species_name(line) for line in f if line.strip() and not line.startswith("[source")]

    print(f"Starting extraction pipeline for {len(species_list)} species...\n")

    os.makedirs("output", exist_ok=True)
    excel_path = "output/papua_microbial_sustainability_matrix.xlsx"
    csv_path = "output/papua_microbial_sustainability_matrix.csv"

    results = []
    for index, name in enumerate(species_list, 1):
        if not name:
            continue
        print(f"[{index}/{len(species_list)}] Extracting data for: {name}...")
        data = extract_species_data_with_retry(client, name)
        results.append(data)
        temp_df = pd.DataFrame(results)
        temp_df.to_csv(csv_path, index=False)
        # pause to respect API rate limits
        time.sleep(2.0)

    # Convert results array to dataframe and export files yay!
    df = pd.DataFrame(results)
    df.to_excel(excel_path, index=False)
    generate_summary_report(df, "output")

    print("\n==========================================")
    print("SUCCESS: Pipeline execution complete!")
    print(f"Saved generated results to:\n - {excel_path}\n - {csv_path}")
    print("==========================================")

if __name__ == "__main__":
    run_pipeline()