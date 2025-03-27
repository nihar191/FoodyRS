from flask import Flask, render_template, request, redirect, url_for, flash
import pickle
import os
import numpy as np

app = Flask(__name__)
app.secret_key = "food_recommendation_secret_key"

# Create artifacts directory if it doesn't exist
os.makedirs('artifacts', exist_ok=True)

# Function to load pickle files
def load_data():
    try:
        food_list = pickle.load(open('artifacts/food_list.pkl', 'rb'))
        similarity = pickle.load(open('artifacts/similarity.pkl', 'rb'))
        return food_list, similarity
    except FileNotFoundError:
        return None, None

# Function to recommend foods
def recommend(food_name, food_df, similarity_matrix, min_rating=4.0, top_n=5):
    if food_name.lower() in food_df['Name'].str.lower().values:
        # Find index of exact match first
        index = food_df[food_df['Name'].str.lower() == food_name.lower()].index[0]
        distances = similarity_matrix[index]
        food_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:top_n+1]
        
        recommended_foods = []
        for i in food_list:
            food_idx = i[0]
            if food_df.iloc[food_idx]['Rating'] >= min_rating:
                recommended_foods.append({
                    'name': food_df.iloc[food_idx]['Name'],
                    'tags': food_df.iloc[food_idx]['tags'],
                    'rating': food_df.iloc[food_idx]['Rating']
                })
        
        return recommended_foods
    else:
        # Search by partial name match
        matching_foods = food_df[food_df['Name'].str.lower().str.contains(food_name.lower())]
        
        if not matching_foods.empty:
            # Filter by rating
            matching_foods = matching_foods[matching_foods['Rating'] >= min_rating]
            
            if not matching_foods.empty:
                # Sort by rating
                matching_foods = matching_foods.sort_values(by='Rating', ascending=False).head(top_n)
                
                recommended_foods = []
                for idx, row in matching_foods.iterrows():
                    recommended_foods.append({
                        'name': row['Name'],
                        'tags': row['tags'],
                        'rating': row['Rating']
                    })
                
                return recommended_foods
        
        # If no match found by name, try to find match in tags
        matching_tags = food_df[food_df['tags'].str.lower().str.contains(food_name.lower())]
        
        if not matching_tags.empty:
            # Filter by rating
            matching_tags = matching_tags[matching_tags['Rating'] >= min_rating]
            
            if not matching_tags.empty:
                # Sort by rating
                matching_tags = matching_tags.sort_values(by='Rating', ascending=False).head(top_n)
                
                recommended_foods = []
                for idx, row in matching_tags.iterrows():
                    recommended_foods.append({
                        'name': row['Name'],
                        'tags': row['tags'],
                        'rating': row['Rating']
                    })
                
                return recommended_foods
        
        return []

# Function to prepare star rating display information
def display_stars(rating):
    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.5
    
    return {
        'full': full_stars,
        'half': half_star,
        'empty': 5 - full_stars - (1 if half_star else 0)
    }

# Function to create tag list
def display_tags(tags_str):
    tags = tags_str.split()
    return tags[:5]  # Limit to 5 tags to avoid clutter

# Routes
@app.route('/')
def index():
    food_df, similarity_matrix = load_data()
    food_data_available = food_df is not None
    
    context = {
        'food_data_available': food_data_available,
        'showing_results': False,
        'search_query': '',
        'min_rating': 4.0,
        'num_results': 5
    }
    
    if food_data_available:
        # Sample categories for exploration
        categories = ["dessert", "chicken", "vegetarian", "spicy", "breakfast", "healthy", "quick"]
        context['categories'] = categories
    
    return render_template('index.html', **context)

@app.route('/search', methods=['POST'])
def search():
    food_df, similarity_matrix = load_data()
    food_data_available = food_df is not None
    
    context = {
        'food_data_available': food_data_available,
        'showing_results': True,
        'search_query': '',
        'min_rating': 4.0,
        'num_results': 5,
        'results': []
    }
    
    if not food_data_available:
        return render_template('index.html', **context)
    
    # Get search parameters
    search_query = request.form.get('search_query', '')
    min_rating = float(request.form.get('min_rating', 4.0))
    num_results = int(request.form.get('num_results', 5))
    
    # Update context
    context['search_query'] = search_query
    context['min_rating'] = min_rating
    context['num_results'] = num_results
    
    results = []
    if search_query:
        results = recommend(search_query, food_df, similarity_matrix, min_rating, num_results)
    
    # Process the results
    for result in results:
        result['stars'] = display_stars(result['rating'])
        result['tag_list'] = display_tags(result['tags'])
    
    context['results'] = results
    
    return render_template('index.html', **context)

@app.route('/category/<category>')
def category(category):
    food_df, similarity_matrix = load_data()
    food_data_available = food_df is not None
    
    context = {
        'food_data_available': food_data_available,
        'showing_results': True,
        'search_query': category,
        'min_rating': 4.0,
        'num_results': 5,
        'results': []
    }
    
    if not food_data_available:
        return render_template('index.html', **context)
    
    # Get results
    results = recommend(category, food_df, similarity_matrix, min_rating=4.0, top_n=5)
    
    # Process the results
    for result in results:
        result['stars'] = display_stars(result['rating'])
        result['tag_list'] = display_tags(result['tags'])
    
    context['results'] = results
    
    return render_template('index.html', **context)

if __name__ == '__main__':
    app.run(debug=True)