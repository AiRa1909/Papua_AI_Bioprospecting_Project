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
* Verified single-prompt handshake with gpt as Claude was not able to be reached through Github Models.
* Built extractor.py to handle batch JSON extraction.
* Added JSON-to-Pandas processing.
* Processed first 100 target bacterial species and generated Excel spreadsheet output.