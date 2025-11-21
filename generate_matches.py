import csv
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from itertools import permutations
from functools import cmp_to_key

# Configuration - Update these values with your Google Sheets details
SPREADSHEET_ID = '12oyK0TvokO4i2c2nIBA0OqRQa-tWqCw5i7gadXXZhWE'  # Or use spreadsheet name
WORKSHEET_NAME = 'Ratings'  # Name of the worksheet/tab
CREDENTIALS_FILE = 'credentials.json'  # Path to your service account credentials file

# Set up Google Sheets API credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open the spreadsheet and worksheet
spreadsheet = client.open_by_key(SPREADSHEET_ID)  # Or use client.open(SPREADSHEET_NAME) if using name
worksheet = spreadsheet.worksheet(WORKSHEET_NAME)


# Get all records from the worksheet, specifying expected headers to avoid duplicate issues
expected_headers = ['Roles', 'TOP', 'JGL', 'MID', 'ADC', 'SUP']
records = worksheet.get_all_records(expected_headers=expected_headers, head=3)


players = ['Peiyan', 'Edward', 'John', 'Daniel', 'Mirl', 'Avery', 'Jackie', 'Roy', 'Tobi', 'Rooney']
player_index = [-1 for _ in range(len(players))]
player_dict = []

for i, lines in enumerate(records):
    top = float(lines['TOP']) if (lines['TOP'] != '-' and lines['TOP'] != '') else -1
    jgl = float(lines['JGL']) if (lines['JGL'] != '-' and lines['JGL'] != '') else -1
    mid = float(lines['MID']) if (lines['MID'] != '-' and lines['MID'] != '') else -1
    adc = float(lines['ADC']) if (lines['ADC'] != '-' and lines['ADC'] != '') else -1
    sup = float(lines['SUP']) if (lines['SUP'] != '-' and lines['SUP'] != '') else -1
    player_obj = [
        top,
        jgl,
        mid,
        adc,
        sup,
        lines['Roles']
    ]
    player_dict.append(player_obj)
    if lines['Roles'] in players:
        player_index[players.index(lines['Roles'])] = i

if -1 in player_index:
    print("Some players are missing in the spreadsheet.")
    exit(1)

maximum_team_delta = 1
maximum_lane_delta = 1
maximum_lane_delta_total = 2
results_list = []

counter = 0
all_permutations = permutations(player_index)
for permutation in all_permutations:
    if len(permutation) != 10:
        print(permutation)
    team1 = permutation[:5]
    team2 = permutation[5:]

    team1_score = [0, 0, 0, 0, 0]
    team2_score = [0, 0, 0, 0, 0]

    skip = False
    for i in range(5):
        team1_score[i] = player_dict[team1[i]][i]
        team2_score[i] = player_dict[team2[i]][i]
        if team1_score[i] == -1 or team2_score[i] == -1:
            skip = True
            break
    if skip:
        continue

    team1_total = sum(team1_score)
    team2_total = sum(team2_score)
    team_delta = abs(team1_total - team2_total)

    lane_deltas = [abs(team1_score[i] - team2_score[i]) for i in range(5)]
    lane_delta_total = sum(lane_deltas)

    if (team_delta <= maximum_team_delta and
        all(delta <= maximum_lane_delta for delta in lane_deltas) and
        lane_delta_total <= maximum_lane_delta_total):
        result = {
            'team1': team1,
            'team2': team2,
            'team1_score': team1_score,
            'team2_score': team2_score,
            'team1_total': team1_total,
            'team2_total': team2_total,
            'team_delta': team_delta,
            'lane_deltas': lane_deltas,
            'lane_delta_total': lane_delta_total
        }

        results_list.append(result)

    counter += 1
    if counter % 300000 == 0:
        print(f"Processed {counter} permutations...")

bad_synergy = [("Tobi", "Noelle")]
def has_bad_synergy(team_indices):
    team_names = [player_dict[idx][5] for idx in team_indices]
    for player1, player2 in bad_synergy:
        if player1 in team_names and player2 in team_names:
            return True
    return False

unique_results = []
seen_combinations = set()
for result in results_list:
    if has_bad_synergy(result['team1']) or has_bad_synergy(result['team2']):
        continue

    team1_tuple = tuple(result['team1'])
    team2_tuple = tuple(result['team2'])
    combination = (team1_tuple, team2_tuple)
    combination_2 = (team2_tuple, team1_tuple)
    if combination_2 not in seen_combinations:
        seen_combinations.add(combination)
        unique_results.append(result)
results_list = unique_results

# Sort results by team delta and then by lane delta total
def compare_results(a, b):
    if a['team_delta'] != b['team_delta']:
        return a['team_delta'] - b['team_delta']
    return a['lane_delta_total'] - b['lane_delta_total']
results_list.sort(key=cmp_to_key(compare_results))

print(f"Total valid matchups found: {len(results_list)}")
output_file_name = f"matches_{time.time()}.csv"
with open(output_file_name, mode='w', newline='') as file:
    writer = csv.writer(file)
    header = [
        'Team 1 TOP', 'Team 1 JGL', 'Team 1 MID', 'Team 1 ADC', 'Team 1 SUP',
        'Team 2 TOP', 'Team 2 JGL', 'Team 2 MID', 'Team 2 ADC', 'Team 2 SUP',
        'Team 1 Total', 'Team 2 Total',
        'Lane Deltas'
    ]
    writer.writerow(header)
    for result in results_list:
        row = []
        for player_index in result['team1']:
            row.append(player_dict[player_index][5])  # Append player name
        for player_index in result['team2']:
            row.append(player_dict[player_index][5])
        row.append(result['team1_total'])
        row.append(result['team2_total'])
        row.append(result['lane_deltas'])
        writer.writerow(row)
print("Saved results to", output_file_name)

random_result = random.choice(results_list) if results_list else None
if random_result:
    print("\nRandomly selected matchup:")
    print("Team 1:")
    for i, player_index in enumerate(random_result['team1']):
        print(f"  {['TOP', 'JGL', 'MID', 'ADC', 'SUP'][i]}: {player_dict[player_index][5]} (Score: {random_result['team1_score'][i]})")
    print("Team 2:")
    for i, player_index in enumerate(random_result['team2']):
        print(f"  {['TOP', 'JGL', 'MID', 'ADC', 'SUP'][i]}: {player_dict[player_index][5]} (Score: {random_result['team2_score'][i]})")
    print(f"Team 1 Total Score: {random_result['team1_total']}")
    print(f"Team 2 Total Score: {random_result['team2_total']}")
    print(f"Team Delta: {random_result['team_delta']}")
    print(f"Lane Deltas: {random_result['lane_deltas']}")
    print(f"Lane Delta Total: {random_result['lane_delta_total']}")
else:
    print("No valid matchups found.")