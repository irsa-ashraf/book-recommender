"""
Demo data loader for Book Club Recommender
Run this to populate the database with sample data for testing
"""

import database as db

def load_demo_data():
    """Load sample book club data"""
    
    print("Resetting database...")
    db.reset_database()
    
    print("Adding members...")
    # Add 4 members with different preferences
    members = [
        {
            'name': 'Alice',
            'preferred_length': 350,
            'liked_genres': ['Fantasy', 'Science Fiction', 'Thriller']
        },
        {
            'name': 'Bob',
            'preferred_length': 280,
            'liked_genres': ['Mystery', 'Historical Fiction', 'Thriller']
        },
        {
            'name': 'Carol',
            'preferred_length': 300,
            'liked_genres': ['Fantasy', 'Historical Fiction', 'Contemporary Fiction']
        },
        {
            'name': 'Dan',
            'preferred_length': 320,
            'liked_genres': ['Science Fiction', 'Non-Fiction', 'Fantasy']
        }
    ]
    
    member_ids = {}
    for member in members:
        member_id = db.add_member(
            member['name'],
            member['preferred_length'],
            member['liked_genres']
        )
        member_ids[member['name']] = member_id
        print(f"  Added {member['name']}")
    
    print("\nAdding books to pool...")
    # Add sample books
    books = [
        # Fantasy
        ('Project Hail Mary', 'Andy Weir', 'Science Fiction', 476, 'Alice'),
        ('The Name of the Wind', 'Patrick Rothfuss', 'Fantasy', 662, 'Carol'),
        ('Dune', 'Frank Herbert', 'Science Fiction', 688, 'Dan'),
        ('The Fifth Season', 'N.K. Jemisin', 'Fantasy', 512, 'Alice'),
        
        # Mystery/Thriller
        ('The Silent Patient', 'Alex Michaelides', 'Thriller', 336, 'Bob'),
        ('Gone Girl', 'Gillian Flynn', 'Mystery', 432, None),
        ('In the Woods', 'Tana French', 'Mystery', 464, 'Bob'),
        
        # Historical Fiction
        ('All the Light We Cannot See', 'Anthony Doerr', 'Historical Fiction', 531, 'Carol'),
        ('The Nightingale', 'Kristin Hannah', 'Historical Fiction', 440, None),
        ('The Book Thief', 'Markus Zusak', 'Historical Fiction', 584, 'Bob'),
        
        # Contemporary Fiction
        ('Where the Crawdads Sing', 'Delia Owens', 'Contemporary Fiction', 384, None),
        ('The Midnight Library', 'Matt Haig', 'Contemporary Fiction', 304, 'Carol'),
        ('Educated', 'Tara Westover', 'Non-Fiction', 334, 'Dan'),
        
        # More variety
        ('Sapiens', 'Yuval Noah Harari', 'Non-Fiction', 443, 'Dan'),
        ('The Hobbit', 'J.R.R. Tolkien', 'Fantasy', 310, None),
        ('Recursion', 'Blake Crouch', 'Science Fiction', 329, 'Alice'),
        ('The Seven Husbands of Evelyn Hugo', 'Taylor Jenkins Reid', 'Contemporary Fiction', 400, None),
        ('Mexican Gothic', 'Silvia Moreno-Garcia', 'Horror', 301, None),
        ('Circe', 'Madeline Miller', 'Fantasy', 400, 'Carol'),
        ('The Song of Achilles', 'Madeline Miller', 'Historical Fiction', 378, None),
    ]
    
    for title, author, genre, pages, suggested_by in books:
        suggested_by_id = member_ids.get(suggested_by) if suggested_by else None
        db.add_book(title, author, genre, pages, suggested_by_id)
        print(f"  Added '{title}'")
    
    print("\nAdding reading history...")
    # Simulate that they've read 2 books already
    all_books = db.get_books()
    
    # Round 1: The Midnight Library (Contemporary Fiction)
    book1 = next(b for b in all_books if b['title'] == 'The Midnight Library')
    db.mark_book_as_read(book1['id'], 1)
    print(f"  Round 1: {book1['title']} ({book1['genre']})")
    
    # Round 2: In the Woods (Mystery)
    book2 = next(b for b in all_books if b['title'] == 'In the Woods')
    db.mark_book_as_read(book2['id'], 2)
    print(f"  Round 2: {book2['title']} ({book2['genre']})")
    
    print("\nDemo data loaded successfully!")
    print("\nCurrent state:")
    print(f"  - 4 members")
    print(f"  - {len(books)} books in pool")
    print(f"  - 2 books read (Contemporary Fiction, Mystery)")
    print(f"  - Ready for Round 3 recommendations!")
    print("\nNow run: streamlit run app.py")

if __name__ == "__main__":
    load_demo_data()
