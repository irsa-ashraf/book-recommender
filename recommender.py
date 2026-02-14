from typing import List, Dict
import database as db

# Scoring weights (must sum to 1.0)
WEIGHTS = {
    'genre_match': 0.4,
    'length_preference': 0.2,
    'member_interest': 0.3,
    'diversity_bonus': 0.1
}

def get_recommendations(top_n: int = 10) -> List[Dict]:
    """
    Get top N book recommendations based on filtering and scoring.
    
    Returns list of books with their scores and reasoning.
    """

    # Get current data
    all_books = db.get_books()
    members = db.get_members()
    reading_history = db.get_reading_history()
    current_round = db.get_current_round()
    
    # STEP 1: Apply hard constraints
    eligible_books = apply_hard_constraints(
        all_books, 
        reading_history, 
        current_round
        )
    
    if not eligible_books:
        return []
    
    # STEP 2: Score each eligible book
    scored_books = []

    for book in eligible_books:
        score, breakdown = calculate_book_score(book, members, reading_history)
        scored_books.append({
            **book,
            'score': score,
            'score_breakdown': breakdown
        })
    
    # Sort by score descending
    scored_books.sort(key=lambda x: x['score'], reverse=True)
    
    return scored_books[:top_n]


def apply_hard_constraints(all_books: List[Dict], 
                           reading_history: List[Dict],
                           current_round: int) -> List[Dict]:
    """
    Apply hard filters: remove books that violate must-have rules.
    
    Filters:
    1. Not already read
    2. Not in the last 2 genres
    3. Not in vetoed genres for this round
    """

    eligible = []
    
    # Get read book IDs
    read_book_ids = {item['book_id'] for item in reading_history}
    
    # Get last 2 genres read
    last_2_genres = db.get_last_n_genres(2)
    
    # Get vetoed genres for current round
    vetoed_genres = db.get_vetoes(current_round)
    
    for book in all_books:
        # Filter 1: Not already read
        if book['id'] in read_book_ids:
            continue
        
        # Filter 2: Not in last 2 genres
        if book['genre'] in last_2_genres:
            continue
        
        # Filter 3: Not vetoed
        if book['genre'] in vetoed_genres:
            continue
        
        eligible.append(book)
    
    return eligible


def calculate_book_score(book: Dict, members: List[Dict], 
                        reading_history: List[Dict]) -> tuple:
    """
    Calculate weighted score for a book based on soft preferences.
    
    Returns: (total_score, breakdown_dict)
    """

    breakdown = {}
    
    # Component 1: Genre Match Score
    genre_match = calculate_genre_match(book, members)
    breakdown['genre_match'] = genre_match
    
    # Component 2: Length Preference Score
    length_score = calculate_length_preference(book, members)
    breakdown['length_preference'] = length_score
    
    # Component 3: Member Interest Score
    interest_score = calculate_member_interest(book, members)
    breakdown['member_interest'] = interest_score
    
    # Component 4: Diversity Bonus
    diversity = calculate_diversity_bonus(book, reading_history)
    breakdown['diversity_bonus'] = diversity
    
    # Calculate weighted total
    total_score = (
        WEIGHTS['genre_match'] * genre_match +
        WEIGHTS['length_preference'] * length_score +
        WEIGHTS['member_interest'] * interest_score +
        WEIGHTS['diversity_bonus'] * diversity
    )
    
    return round(total_score, 2), breakdown


def calculate_genre_match(book: Dict, members: List[Dict]) -> float:
    """
    Score based on how many members like this genre.
    
    Returns: 0-100
    """
    
    if not members:
        return 50.0
    
    members_who_like = sum(
        1 for member in members 
        if book['genre'] in member['liked_genres']
    )
    
    return (members_who_like / len(members)) * 100


def calculate_length_preference(book: Dict, members: List[Dict]) -> float:
    """
    Score based on distance from ideal length.
    
    Returns: 0-100
    """

    if not members:
        return 50.0
    
    # Get median preferred length
    preferred_lengths = [m['preferred_length'] for m in members]
    preferred_lengths.sort()
    n = len(preferred_lengths)
    
    if n % 2 == 0:
        ideal_length = (preferred_lengths[n//2 - 1] + preferred_lengths[n//2]) / 2
    else:
        ideal_length = preferred_lengths[n//2]
    
    # Calculate distance penalty (1 point per 5 pages away)
    distance = abs(book['page_count'] - ideal_length)
    penalty = distance / 5
    
    score = max(0, 100 - penalty)
    return score


def calculate_member_interest(book: Dict, members: List[Dict]) -> float:
    """
    Score based on whether a member suggested this book.
    
    Returns: 0-100
    """

    if book['suggested_by'] is not None:
        return 100.0
    else:
        return 50.0


def calculate_diversity_bonus(book: Dict, reading_history: List[Dict]) -> float:
    """
    Reward genres not read recently (beyond the last 2 constraint).
    
    Returns: 0-100
    """

    if not reading_history:
        return 100.0
    
    # Count how many books ago we read this genre
    books_since = 0
    for entry in reading_history:
        if entry['genre'] == book['genre']:
            break
        books_since += 1
    else:
        # Never read this genre
        return 100.0
    
    # Scoring tiers
    if books_since >= 5:
        return 100.0
    elif books_since >= 3:
        return 70.0
    else:
        return 0.0


def get_genres_from_pool() -> List[str]:
    """Get unique list of all genres in the book pool"""

    books = db.get_books()
    genres = list(set(book['genre'] for book in books))
    return sorted(genres)
