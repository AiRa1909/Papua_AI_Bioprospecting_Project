import os
import json
import pandas as pd
import anthropic

def get_claude_client():
    """Initializes client pointing to GitHub Models API."""
    token = os.environ.get("ANTHROPIC_API_KEY")
    if not token:
        raise ValueError("Error: ANTHROPIC_API_KEY environment variable is missing.")

    return anthropic.Anthropic(api_key=token)

def extract_species_data(client, species_name):
    """Prompting the LLM to extract structured trait data for a single species."""
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

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Using the Official Claude model now
            max_tokens=1024,
            temperature=0.1,
            system="You are a scientific data extraction engine. Output valid JSON only.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        raw_output = response.content[0].text.strip() #new Anthropic response syntax

        # Cleaning markdown code blocks if returned!
        if raw_output.startswith("```json"):
            raw_output = raw_output.replace("```json", "").replace("```", "").strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output.replace("```", "").strip()

        return json.loads(raw_output)

    except Exception as error:
        print(f"Error processing '{species_name}': {error}")
        return {
            "species_name": species_name,
            "primary_function": "Error / Extraction Failed",
            "sustainability_application": "N/A",
            "biosafety_level": "Unknown"
        }


def run_pipeline():
    client = get_claude_client()

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
        species_list = [line.strip() for line in f if line.strip()]

    print(f"Starting extraction pipeline for {len(species_list)} species...\n")

    results = []
    for index, name in enumerate(species_list, 1):
        print(f"[{index}/{len(species_list)}] Extracting data for: {name}...")
        data = extract_species_data(client, name)
        results.append(data)

    # Convert results array to dataframe and export files yay!
    df = pd.DataFrame(results)

    os.makedirs("output", exist_ok=True)

    excel_path = "output/papua_microbial_sustainability_matrix.xlsx"
    csv_path = "output/papua_microbial_sustainability_matrix.csv"

    df.to_excel(excel_path, index=False)
    df.to_csv(csv_path, index=False)

    print("\n==========================================")
    print("SUCCESS: Pipeline execution complete!")
    print(f"Saved generated results to:\n - {excel_path}\n - {csv_path}")
    print("==========================================")


if __name__ == "__main__":
    run_pipeline()