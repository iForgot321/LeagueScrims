# League Scrims Match Generator

Generates balanced 5v5 scrim matchups from a roster of rated players. Player
ratings (per role) are pulled from a Google Sheet, or from a local
`sheet.csv` backup if no Google credentials are configured. The script tries
every possible way to split the selected players into two teams, keeps the
ones that are close in skill, and writes them to a CSV file.

## How it works

1. Loads player ratings (`TOP`, `JGL`, `MID`, `ADC`, `SUP`) for everyone in
   the roster.
2. Picks out the players listed in the `players` variable in
   `generate_matches.py`.
3. Tries every permutation of those players split into two 5-player teams
   (one player per role per team).
4. Keeps only matchups where:
   - the total team score difference is within `maximum_team_delta`
   - every individual lane matchup difference is within `maximum_lane_delta`
   - the summed lane differences are within `maximum_lane_delta_total`
5. Drops matchups containing pairs of players flagged as bad synergy
   (`bad_synergy` list) and removes duplicate team pairings.
6. Sorts the remaining matchups by closeness (team delta, then lane delta)
   and writes them all to a timestamped CSV file.
7. Prints one randomly chosen matchup from the results to the console.

## Requirements

- Python 3
- [`gspread`](https://pypi.org/project/gspread/) and
  `google-auth` — **only required if you're pulling ratings from Google
  Sheets**. Install with:

  ```bash
  pip install gspread google-auth
  ```

  If you're using the local `sheet.csv` fallback instead, no extra
  dependencies are needed beyond the Python standard library.

## Setting up your ratings source

The script picks its data source automatically:

- **Google Sheets** — used if `credentials.json` (a Google service account
  key) exists in the project root. Update `SPREADSHEET_ID` and
  `WORKSHEET_NAME` at the top of `generate_matches.py` to point at your
  sheet. The sheet is expected to have its header row on row 3
  (`Roles, TOP, JGL, MID, ADC, SUP`).
- **Local CSV** — used automatically if `credentials.json` is missing.
  Ratings are read from `sheet.csv` in the project root instead. This file
  should be a plain CSV with a header row:

  ```csv
  Roles,TOP,JGL,MID,ADC,SUP
  Avery,5,8,5,7,8
  Bono,7,5,5,7,6
  ```

In both sources, a `-` or blank cell means the player doesn't play that role
and will be excluded from matchups requiring it.

## Configuration

Edit these values directly in `generate_matches.py`:

| Variable | Description |
|---|---|
| `players` | Names of the players to include in this run's matchmaking (must match `Roles` values exactly). |
| `maximum_team_delta` | Max allowed difference between the two teams' total scores. |
| `maximum_lane_delta` | Max allowed rating difference for any single lane matchup. |
| `maximum_lane_delta_total` | Max allowed sum of all lane differences. |
| `bad_synergy` | List of `(player1, player2)` pairs that should never be placed on the same team. |

## Usage

```bash
python generate_matches.py
```

Output:
- A CSV file named `matches_<timestamp>.csv` containing every valid,
  deduplicated matchup, sorted from most to least balanced.
- A console printout of one randomly selected matchup with per-lane scores.

If any player in the `players` list is missing from the ratings source, the
script prints an error and exits without generating matches.
