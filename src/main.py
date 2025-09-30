# main.py
"""Module defines the main entry point for the Apify Actor."""
from __future__ import annotations
import os
import json
import subprocess
from apify import Actor
import time
from datetime import datetime, timezone


async def main() -> None:
    """
    Main entry point for the RPScrape Actor.
    Runs rpscrape racecards/racedays script and stores JSON output.
    """
    async with Actor:
        Actor.log.info('Starting RPScrape Actor...')

        # Get input configuration
        actor_input = await Actor.get_input() or {}
        command = actor_input.get('command', 'racecards')  # 'racecards' or 'racedays'
        date_arg = actor_input.get('date', 'today')  # 'today' or specific date

        Actor.log.info(f'Running {command}.py with date: {date_arg}')

        # Path to rpscrape scripts folder
        rpscrape_base = os.path.join(os.getcwd(), 'rpscrape')

        # Clone rpscrape if not present (for local development)
        if not os.path.exists(rpscrape_base):
            Actor.log.info('rpscrape not found, cloning from GitHub...')

            try:
                subprocess.run(
                    ['git', 'clone', 'https://github.com/joenano/rpscrape.git'],
                    cwd=os.getcwd(),
                    check=True
                )
                Actor.log.info('rpscrape cloned successfully')
            except subprocess.CalledProcessError as e:
                error_msg = f'Failed to clone rpscrape: {e}'
                Actor.log.error(error_msg)
                await Actor.fail(status_message=error_msg)
                return

        scripts_path = os.path.join(rpscrape_base, 'scripts')
        script_file = f'{command}.py'
        script_full_path = os.path.join(scripts_path, script_file)

        # Check if script exists
        if not os.path.exists(script_full_path):
            error_msg = f'Script not found: {script_full_path}'
            Actor.log.error(error_msg)
            await Actor.fail(status_message=error_msg)
            return

        try:
            # Run the rpscrape command
            Actor.log.info(f'Executing: python {script_file} {date_arg}')

            start = time.perf_counter()

            result = subprocess.run(
                ['python', script_file, date_arg],
                cwd=scripts_path,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout
            )

            duration = time.perf_counter() - start
            Actor.log.info(f"⏱ rpscrape script finished in {duration:.2f} seconds")

            if result.returncode != 0:
                error_msg = f'Script failed with code {result.returncode}: {result.stderr}'
                Actor.log.error(error_msg)
                Actor.log.error(f'stdout: {result.stdout}')
                await Actor.fail(status_message=error_msg)
                return

            Actor.log.info('Script executed successfully')

            # Look for output files in rpscrape data directory
            rpscrape_data_path = os.path.join(rpscrape_base, 'racecards')
            output_file = None

            if os.path.exists(rpscrape_data_path):
                json_files = [f for f in os.listdir(rpscrape_data_path) if f.endswith('.json')]
                Actor.log.info(f'Found JSON files in data directory: {json_files}')

                if json_files:
                    # Get most recent file
                    json_files.sort(key=lambda x: os.path.getmtime(os.path.join(rpscrape_data_path, x)), reverse=True)
                    output_file = os.path.join(rpscrape_data_path, json_files[0])
                    Actor.log.info(f'Using output file: {output_file}')

            if not output_file or not os.path.exists(output_file):
                error_msg = 'No JSON output file found from rpscrape'
                Actor.log.error(error_msg)
                await Actor.fail(status_message=error_msg)
                return

            # Load and process the JSON data
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                Actor.log.info(f'Loaded data from {output_file}')
                Actor.log.info(f'Data type: {type(data)}')
                Actor.log.info(f'Data length: {len(data) if hasattr(data, "__len__") else "N/A"}')

                # Show first few items to understand structure
                if isinstance(data, list) and len(data) > 0:
                    Actor.log.info(f'First item type: {type(data[0])}')
                    Actor.log.info(f'First item preview: {str(data[0])[:200]}')
                    if len(data) > 1:
                        Actor.log.info(f'Second item type: {type(data[1])}')
                elif isinstance(data, dict):
                    Actor.log.info(f'Data is a dict with keys: {list(data.keys())[:10]}')

                # If data is not a list, wrap it in a list
                if not isinstance(data, list):
                    data = [data]
                    Actor.log.info('Wrapped single item in list')

                Actor.log.info(f'Processing {len(data)} records from {output_file}')


                # Push each race record individually to dataset
                timestamp = datetime.now(timezone.utc).isoformat()

                for item in data:
                    # Add timestamp to each record
                    item["timestamp"] = timestamp

                    # Push to Apify dataset
                    await Actor.push_data(item)
                    Actor.log.debug(f"Pushed race record: {item.get('race_id', 'unknown')}")

                    # Save individual JSON file in KV store with meaningful filename
                    race_id = item.get('race_id', 'unknown')
                    course_name = item.get('racecourse_name', 'unknown')
                    race_time = item.get('race_time', 'unknown').replace(':', '')

                    filename = f"{date_arg}_{course_name}_{race_time}_{race_id}.json"
                    await Actor.set_value(filename, item)
                    Actor.log.debug(f"Saved to KV store: {filename}")

                Actor.log.info(f'✅ Successfully pushed {len(data)} race records to dataset')
                Actor.log.info(f'✅ Saved {len(data)} individual files to KV store')

                # Also save the complete dataset as one file for reference
                await Actor.set_value(f'complete_{command}_{date_arg}.json', data)
                Actor.log.info(f'✅ Saved complete dataset to KV store as complete_{command}_{date_arg}.json')

            except json.JSONDecodeError as e:
                error_msg = f'Failed to parse JSON from {output_file}: {e}'
                Actor.log.error(error_msg)
                await Actor.fail(status_message=error_msg)
                return

            except Exception as e:
                error_msg = f'Error processing JSON data: {e}'
                Actor.log.error(error_msg)
                await Actor.fail(status_message=error_msg)
                return

            Actor.log.info('✓ RPScrape Actor completed successfully!')
            Actor.log.info(f'✓ Original rpscrape file: {output_file}')
            Actor.log.info(f'✓ Data pushed to: Apify dataset + individual KV store files')

        except subprocess.TimeoutExpired:
            error_msg = 'Script execution timed out after 15 minutes'
            Actor.log.error(error_msg)
            await Actor.fail(status_message=error_msg)

        except Exception as e:
            error_msg = f'Unexpected error: {repr(e)}'
            Actor.log.error(error_msg)
            await Actor.fail(status_message=error_msg)