# main.py
"""Module defines the main entry point for the Apify Actor."""
from __future__ import annotations
import os
import json
import subprocess
from apify import Actor


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

            result = subprocess.run(
                ['python', script_file, date_arg],
                cwd=scripts_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = f'Script failed with code {result.returncode}: {result.stderr}'
                Actor.log.error(error_msg)
                Actor.log.error(f'stdout: {result.stdout}')
                await Actor.fail(status_message=error_msg)
                return

            Actor.log.info('Script executed successfully')

            # rpscrape writes to file, not stdout - find the output file
            output_file = None
            rpscrape_data_path = os.path.join(rpscrape_base, 'data')

            # Look for JSON files in data folder
            if os.path.exists(rpscrape_data_path):
                json_files = [f for f in os.listdir(rpscrape_data_path) if f.endswith('.json')]
                if json_files:
                    # Get most recent file
                    json_files.sort(key=lambda x: os.path.getmtime(os.path.join(rpscrape_data_path, x)), reverse=True)
                    output_file = os.path.join(rpscrape_data_path, json_files[0])
                    Actor.log.info(f'Found output file: {output_file}')

            # Try to load from file first, fallback to stdout
            output_data = None
            if output_file and os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        output_data = json.load(f)
                    Actor.log.info(
                        f'Loaded JSON from file: {len(output_data) if isinstance(output_data, list) else "data"} records')
                except json.JSONDecodeError as e:
                    Actor.log.warning(f'Could not parse file as JSON: {e}')

            # Fallback to stdout if file parse failed
            if not output_data and result.stdout.strip():
                try:
                    output_data = json.loads(result.stdout)
                    Actor.log.info(f'Parsed JSON from stdout: {len(output_data)} records')
                except json.JSONDecodeError:
                    Actor.log.info('Treating stdout as raw text')
                    output_data = {'raw_output': result.stdout}

            # Final fallback
            if not output_data:
                output_data = {'message': 'No output generated', 'stdout': result.stdout}

            # Store results in Apify dataset
            await Actor.push_data(output_data)
            Actor.log.info(f'Data pushed to Apify dataset successfully')

            # Also store in key-value store for easy access
            await Actor.set_value('OUTPUT', output_data)
            Actor.log.info('Data stored in key-value store as OUTPUT')

            # Log where rpscrape saved the file
            if output_file:
                Actor.log.info(f'rpscrape file location: {output_file}')
            else:
                Actor.log.info('rpscrape may have saved file in data/ folder')

            Actor.log.info('✓ RPScrape Actor completed successfully!')
            Actor.log.info(f'✓ Data available in: Apify dataset + rpscrape file + key-value store')

        except subprocess.TimeoutExpired:
            error_msg = 'Script execution timed out after 5 minutes'
            Actor.log.error(error_msg)
            await Actor.fail(status_message=error_msg)

        except Exception as e:
            error_msg = f'Unexpected error: {repr(e)}'
            Actor.log.error(error_msg)
            await Actor.fail(status_message=error_msg)
