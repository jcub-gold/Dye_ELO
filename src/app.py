from flask import Flask, request, jsonify
import trueskill as ts
import pickle
import os

RATING_SCALING_FACTOR = 40

app = Flask(__name__)
env = ts.TrueSkill()

# Load or initialize player ratings
if os.path.exists('ratings.pkl'):
    with open('ratings.pkl', 'rb') as f:
        player_ratings = pickle.load(f)
else:
    player_ratings = {}

# Create initial rating for a new player
def get_or_create_rating(player_id):
    if player_id not in player_ratings:
        player_ratings[player_id] = env.create_rating()
    return player_ratings[player_id]

# Endpoint to get player rating
@app.route('/rating/<player_id>', methods=['GET'])
def get_rating(player_id):
    if player_id not in player_ratings:
        return jsonify({'error': 'Player not found'}), 404
    rating = player_ratings[player_id]
    mu_int = int(rating.mu * RATING_SCALING_FACTOR)
    sigma_int = int(rating.sigma * RATING_SCALING_FACTOR)
    return jsonify({'player_id': player_id, 'mu': mu_int, 'sigma': sigma_int})

# Endpoint to update ratings after a match
@app.route('/match', methods=['POST'])
def update_ratings():
    data = request.json
    winning_team_ids = data['winning_team']
    losing_team_ids = data['losing_team']

    winning_team = [get_or_create_rating(pid) for pid in winning_team_ids]
    losing_team = [get_or_create_rating(pid) for pid in losing_team_ids]

    winning_team_ratings, losing_team_ratings = env.rate([winning_team, losing_team], ranks=[0, 1])

    for pid, rating in zip(winning_team_ids, winning_team_ratings):
        player_ratings[pid] = rating

    for pid, rating in zip(losing_team_ids, losing_team_ratings):
        player_ratings[pid] = rating

    # Save ratings to a file
    with open('ratings.pkl', 'wb') as f:
        pickle.dump(player_ratings, f)

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)