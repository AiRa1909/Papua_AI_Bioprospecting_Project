import os
import re
import argparse
import pandas as pd
from openai import OpenAI
import time
import json
from logger_setup import log_info, log_error


def load_config():
    """Loads external configurations from config.json."""
    with open("config.json", "r") as f:
        return json.load(f)


def get_ai_client():
    """Initializes client pointing to Groq's API."""
    token = os.environ.get("GROQ_API_KEY")
    if not token:
        raise ValueError("Error: GROQ_API_KEY environment variable is missing in Run Configurations")

    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=token,
    )


def clean_species_name(line):
    """Removes leading index numbers in species' names"""
    line = re.sub(r'\[source.*?\]', '', line)
    line = re.sub(r'^\d+\s*', '', line.strip())
    return line


def extract_species_data_with_retry(client, species_name, config):
    """Prompts the LLM to extract structured trait data with retry logic."""
    max_retries = config.get("max_retries", 3)
    retry_delay = config.get("retry_delay", 2.0)
    model_name = config.get("model_name", "llama-3.3-70b-versatile")
    temperature = config.get("temperature", 0.1)

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
                model=model_name,
                messages=[
                    {"role": "system",
                     "content": "You are a scientific data extraction engine. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )

            raw_output = response.choices[0].message.content.strip()

            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()

            return json.loads(raw_output)

        except Exception as e:
            log_error(f"[Attempt {attempt}/{max_retries}] Failed for '{species_name}': {e}")
            time.sleep(retry_delay)

    return {
        "species_name": species_name,
        "primary_function": "Error / Extraction Failed",
        "sustainability_application": "N/A",
        "biosafety_level": "Unknown"
    }


def generate_summary_report(df, output_dir):
    """Generates a text summary of the bioprospecting matrix results."""
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
    bsl1_samples = df[df['biosafety_level'] == 'BSL-1'].head(5)
    for idx, row in bsl1_samples.iterrows():
        report_content += f" • {row['species_name']}: {row['sustainability_application']}\n"

    with open(summary_path, "w") as f:
        f.write(report_content)

    log_info(f"Generated text summary report at: {summary_path}")


def run_pipeline():
    parser = argparse.ArgumentParser(description="Papua Microbial Bioprospecting Pipeline")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of species to process for testing")
    args = parser.parse_args()

    config = load_config()
    client = get_ai_client()

    input_file = config.get("input_path", "Data/target-species.txt")
    if not os.path.exists(input_file):
        possible_paths = ["target-species.txt", "target_species.txt", "data/target-species.txt",
                          "data/target_species.txt"]
        input_file = None
        for path in possible_paths:
            if os.path.exists(path):
                input_file = path
                break

    if not input_file:
        log_error("Could not find target species text file! Please check the file location.")
        return

    log_info(f"Found species list at: '{input_file}'")

    with open(input_file, "r") as f:
        species_list = [clean_species_name(line) for line in f if line.strip() and not line.startswith("[source")]

    if args.limit:
        species_list = species_list[:args.limit]
        log_info(f"Test mode active: Limiting execution to first {args.limit} species.")

    log_info(f"Starting extraction pipeline for {len(species_list)} species...")

    os.makedirs("output", exist_ok=True)
    excel_path = "output/papua_microbial_sustainability_matrix.xlsx"
    csv_path = "output/papua_microbial_sustainability_matrix.csv"

    results = []
    for index, name in enumerate(species_list, 1):
        if not name:
            continue
        log_info(f"[{index}/{len(species_list)}] Extracting data for: {name}...")
        data = extract_species_data_with_retry(client, name, config)
        results.append(data)

        temp_df = pd.DataFrame(results)
        temp_df.to_csv(csv_path, index=False)
        time.sleep(config.get("retry_delay", 2.0))

    df = pd.DataFrame(results)
    df.to_excel(excel_path, index=False)
    generate_summary_report(df, "output")

    log_info("Pipeline execution complete successfully!")


if __name__ == "__main__":
    run_pipeline()