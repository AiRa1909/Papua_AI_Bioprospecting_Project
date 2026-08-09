# Internship Logbook 

## Project Overview
This project uses Anthropic's Claude 3.5 Sonnet (via the GitHub Models API) to automate literature extraction for microbial species in Papua, Indonesia for the purpose of bioprospecting. 

## Objectives
1. Parse through bacterial species lists provided by Econexus AI.
2. Extract metabolic functions, sustainability applications, and biosafety levels using Claude.
3. Export structured data to Sheets/Excel (`.xlsx`) and CSV (`.csv`) formats.
4. Benchmark AI extraction accuracy against NCBI and PubMed databases later on in report.

## June 17
* Sent the official project proposal email to Ibu Sharlini and Kak Yazid.
* Received their preferred contact channels.

## June 20 - 28
* Created the local PyCharm workspace and initiated the project directory.
* Created the report document and began writing sections 1.1-1.2

## June 28- July 19
* Set up PyCharm virtual environment and directory structure.
* Connected to GitHub Models API gateway using `GITHUB_TOKEN`.
* Verified single-              prompt handshake with gpt as Claude was not able to be reached through Github Models.
* Built extractor.py to handle batch JSON extraction.
* Added JSON-to-Pandas processing.
* Processed first 100 target bacterial species and generated Excel spreadsheet output.

## July 20--25
* Did research on how to reach Claude again through github models, but failed 
* Instead created free API Key on Anthropic developer account and did research on how to change code to accomodate Claude
* Applied changes but then reverted as it turns out Claude requires credits payment to be used

## July 25-27
* Realized I did not make commits for the Claude incident, so I changed code back to Claude-suitable, committed on 27th, and reverted and recommitted to show that exploration was made
* Upgraded `main.py` with automatic retry logic (`extract_species_data_with_retry`) to handle API timeouts smoothly.
* Added regex string cleaning (`clean_species_name`) to strip leading index numbers and source tags from species names.
* Added real-time incremental saving to `output/papua_microbial_sustainability_matrix.csv` so progress is never lost if a network error occurs.
* Added an automated summary report generator (`generate_summary_report`) to tally BSL-1 and BSL-2 distributions.

## August 2 
* Github API Models was shut down, so a switch was made to Groq's free OpenAI Models 
* Generated a Groq API Key and adjusted the code

## August 2 - 9
* Decoupled hardcoded parameters (model names, retry limits, delays, file paths etc.) into an external configuration file.  
* Replaced standard print statements with Python's native logging module to track pipeline execution milestones and error traces inside output/app.log