import pandas as pd
import wikipedia

# Set Wikipedia language to German
wikipedia.set_lang("de")

# Read the CSV file
plant_data = pd.read_csv("Input.csv")

# Function to retrieve Wikipedia URL and summary
def fetch_wikipedia_info(latin_name, common_name):
    try:
        page = wikipedia.page(latin_name)
        summary = wikipedia.summary(latin_name, sentences=2)
        return page.url, summary
    except (wikipedia.DisambiguationError, wikipedia.PageError):
        try:
            # Fallback: Use common (German) name
            page = wikipedia.page(common_name)
            summary = wikipedia.summary(common_name, sentences=2)
            return page.url, summary
        except (wikipedia.DisambiguationError, wikipedia.PageError):
            return "Not found", ""
        except Exception as e:
            return f"Error: {str(e)}", ""
    except Exception as e:
        return f"Error: {str(e)}", ""

# Retrieve Wikipedia data for each plant
wikipedia_urls = []
wikipedia_summaries = []

for _, row in plant_data.iterrows():
    url, summary = fetch_wikipedia_info(row["Lateinischer Name"], row["Deutscher Name"])
    wikipedia_urls.append(url)
    wikipedia_summaries.append(summary)

# Add new columns with Wikipedia information
plant_data["Wikipedia URL"] = wikipedia_urls
plant_data["Wikipedia Summary"] = wikipedia_summaries

# Save updated data to new CSV
plant_data.to_csv("Output.csv", index=False)

print("Done! File saved as 'Outputo.csv'")
