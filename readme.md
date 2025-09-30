# RPScrape Apify Actor

Scrapes UK and Irish horse racing data using [rpscrape](https://github.com/joenano/rpscrape) and stores the results in Apify datasets.

## Features

- 🏇 Scrapes racecards and raceday data from Racing Post
- 📊 Outputs structured JSON data
- 💾 Triple storage: Apify dataset + key-value store + rpscrape file
- 🔄 Auto-clones rpscrape on first run (local development)
- ⚙️ Configurable date and script selection

## Usage

### Input Configuration

The actor accepts the following input parameters:

```json
{
  "command": "racecards",
  "date": "today"
}
```

**Parameters:**

| Field | Type | Description | Default | Required |
|-------|------|-------------|---------|----------|
| `command` | string | Script to run: `racecards` or `racedays` | `racecards` | Yes |
| `date` | string | Date to scrape (e.g., `today`, `2025-09-30`) | `today` | No |

### Output

The actor stores data in three locations:

1. **Apify Dataset** - Full racing data in JSON format, queryable via Apify API
2. **Key-Value Store** - Stored under key `OUTPUT` for easy access
3. **rpscrape File** - Native file output in `rpscrape/data/` folder

**Example Output Structure:**
```json
[
  {
    "racecourse_name": "Cheltenham",
    "race_time": "14:30",
    "race_name": "Champion Hurdle",
    "field_size": 12,
    "is_maiden": "false",
    "is_handicap": "false"
  }
]
```

## Local Development

### Prerequisites

- Python 3.11+
- Git
- Apify CLI: `npm install -g apify-cli`

### Setup

1. Clone this repository:
```bash
git clone <your-repo-url>
cd rpscrape-raceday-actor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run locally:
```bash
apify run
```

The actor will automatically clone rpscrape on first run if not present.

### Manual rpscrape Installation (Optional)

If you prefer to install rpscrape manually:

```bash
git clone https://github.com/joenano/rpscrape.git
cd rpscrape
pip install -r requirements.txt
cd ..
```

## Deployment

### Deploy to Apify Platform

1. Login to Apify CLI:
```bash
apify login
```

2. Push to Apify:
```bash
apify push
```

### Docker Build

The actor uses the official Apify Python image and automatically installs rpscrape during build:

```dockerfile
FROM apify/actor-python:3.11
# Clones rpscrape and installs dependencies
```

## Project Structure

```
rpscrape-raceday-actor/
├── .actor/
│   ├── actor.json           # Actor configuration
│   └── input_schema.json    # Input parameter schema
├── src/
│   ├── __main__.py          # Entry point
│   └── main.py              # Main actor logic
├── Dockerfile               # Docker configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Error Handling

The actor includes comprehensive error handling for:

- Missing rpscrape installation (auto-clones)
- Script execution failures
- JSON parsing errors
- Timeout after 5 minutes
- Invalid input parameters

All errors are logged to Apify console with detailed messages.

## Examples

### Scrape Today's Racecards

```json
{
  "command": "racecards",
  "date": "today"
}
```

### Scrape Specific Date

```json
{
  "command": "racecards",
  "date": "2025-09-30"
}
```

### Get Race Days

```json
{
  "command": "racedays",
  "date": "today"
}
```

## Accessing Results

### Via Apify API

```bash
# Get dataset items
curl "https://api.apify.com/v2/datasets/[DATASET_ID]/items"

# Get from key-value store
curl "https://api.apify.com/v2/key-value-stores/[STORE_ID]/records/OUTPUT"
```

### Via Apify Console

1. Go to your actor run page
2. Click on "Dataset" or "Key-value store" tabs
3. View or download the data

## Troubleshooting

**Issue: Script not found**
- Solution: Ensure rpscrape is cloned. Run `git clone https://github.com/joenano/rpscrape.git` in the actor directory.

**Issue: No JSON output**
- Solution: Check that rpscrape is writing to `rpscrape/data/` folder. The actor will automatically find the most recent JSON file.

**Issue: Timeout errors**
- Solution: Large date ranges may take longer. Consider splitting into multiple runs or increase timeout in `main.py`.

## Credits

- Built on [rpscrape](https://github.com/joenano/rpscrape) by joenano
- Uses [Apify SDK for Python](https://docs.apify.com/sdk/python/)

## License

This actor is provided as-is. Please respect Racing Post's terms of service when scraping data.

## Support

For issues specific to:
- **This actor**: Open an issue in this repository
- **rpscrape functionality**: See [rpscrape repo](https://github.com/joenano/rpscrape)
- **Apify platform**: Visit [Apify documentation](https://docs.apify.com)