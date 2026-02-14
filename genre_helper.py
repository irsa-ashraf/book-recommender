"""
Genre Helper - Assign genres to imported books
After importing from Excel, use this to fill in missing genres
"""

import database as db

# Common genre keywords to help with classification
GENRE_KEYWORDS = {
    'Fantasy': ['magic', 'dragon', 'wizard', 'witch', 'fantasy', 'realm', 'enchant', 
                'sorcerer', 'fae', 'basilisk', 'alchemy', 'bewitched'],
    'Science Fiction': ['sci-fi', 'space', 'station', 'future', 'atmosphere', 'mistborn'],
    'Mystery': ['murder', 'detective', 'clue', 'mystery', 'suspect', 'investigation'],
    'Thriller': ['dark', 'lies', 'lying', 'secret', 'shadow', 'vanishing'],
    'Historical Fiction': ['war', 'empire', 'history', 'lessons', 'past', 'raven scholar'],
    'Contemporary Fiction': ['modern', 'contemporary', 'never told you', 'lovers', 'beauty'],
    'Romance': ['love', 'kiss', 'heart', 'lovers', 'mate'],
    'Horror': ['horror', 'dark', 'blood', 'death', 'damned'],
    'Literary Fiction': ['picture', 'dorian', 'kafka', 'steinbeck', 'wilde'],
    'Non-Fiction': ['advice', 'unsolicited', 'lessons'],
}

def suggest_genre(title: str, author: str = '') -> str:
    '''
    Suggest a genre based on keywords in title/author
    '''

    title_lower = title.lower()
    author_lower = author.lower()
    combined = f"{title_lower} {author_lower}"
    
    # Check for keyword matches
    scores = {}
    for genre, keywords in GENRE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in combined)
        if score > 0:
            scores[genre] = score
    
    if scores:
        # Return genre with highest score
        best_genre = max(scores, key=scores.get)
        return best_genre
    
    return 'Unspecified'


def update_book_genres():
    '''
    Interactive genre assignment for books with 'Unspecified' genre
    '''

    books = db.get_books()
    
    # Filter books with Unspecified genre
    unspecified = [b for b in books if b['genre'] == 'Unspecified']
    
    if not unspecified:
        print("✅ All books have genres assigned!")
        return
    
    print(f"\n📚 Found {len(unspecified)} books without genres")
    print("Let's assign them!\n")
    
    # Get all unique genres from books that DO have genres
    existing_genres = list(set(b['genre'] for b in books if b['genre'] != 'Unspecified'))
    
    # Add common genres
    all_genres = sorted(list(set(existing_genres + list(GENRE_KEYWORDS.keys()))))
    
    print("Available genres:")
    for i, genre in enumerate(all_genres, 1):
        print(f"  {i}. {genre}")
    print(f"  {len(all_genres) + 1}. [Enter custom genre]")
    print()
    
    updated = 0
    
    for book in unspecified:
        print(f"\n{'='*60}")
        print(f"{book['title']}")
        print(f"   by {book['author']}")
        if book['suggested_by_name']:
            print(f"   (suggested by {book['suggested_by_name']})")
        
        # Suggest a genre based on keywords
        suggested = suggest_genre(book['title'], book['author'])
        if suggested != 'Unspecified':
            print(f"\nSuggested genre: {suggested}")
        
        print(f"\nSelect genre (1-{len(all_genres) + 1}), or press Enter to skip:")
        
        choice = input("> ").strip()
        
        if not choice:
            print("  Skipped")
            continue
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(all_genres):
                selected_genre = all_genres[choice_num - 1]
            elif choice_num == len(all_genres) + 1:
                custom_genre = input("Enter custom genre: ").strip()
                if custom_genre:
                    selected_genre = custom_genre
                else:
                    print("  Skipped")
                    continue
            else:
                print("  Invalid choice, skipped")
                continue
        except ValueError:
            print("  Invalid input, skipped")
            continue
        
        # Update in database
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("UPDATE books SET genre = %s WHERE id = %s", 
                  (selected_genre, book['id']))
        conn.commit()
        conn.close()
        
        print(f"  ✓ Set to: {selected_genre}")
        updated += 1
    
    print(f"\n{'='*60}")
    print(f"\nUpdated {updated} books")
    print(f"   {len(unspecified) - updated} books still need genres")

def batch_update_page_counts():
    '''
    Batch update page counts for all books
    '''

    books = db.get_books()
    
    print(f"\nUpdating page counts for {len(books)} books")
    print("You can update these individually in the app later,")
    print("or enter them here.\n")
    
    updated = 0
    
    for book in books:
        if book['page_count'] != 300:  # Skip if already updated
            continue
            
        print(f"\n📖 {book['title']} by {book['author']}")
        print(f"   Current: {book['page_count']} pages (default)")
        
        page_input = input("Enter page count (or press Enter to keep default): ").strip()
        
        if page_input:
            try:
                pages = int(page_input)
                if pages > 0:
                    conn = db.get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE books SET page_count = %s WHERE id = %s", 
                              (pages, book['id']))
                    conn.commit()
                    conn.close()
                    print(f"  ✓ Updated to {pages} pages")
                    updated += 1
            except ValueError:
                print("  Invalid number, skipped")
    
    print(f"\nUpdated {updated} books")


if __name__ == "__main__":
    print("="*60)
    print("BOOK CLUB GENRE & PAGE COUNT HELPER")
    print("="*60)
    
    while True:
        print("\nWhat would you like to do?")
        print("  1. Assign genres to books")
        print("  2. Update page counts")
        print("  3. Exit")
        
        choice = input("\n> ").strip()
        
        if choice == '1':
            update_book_genres()
        elif choice == '2':
            batch_update_page_counts()
        elif choice == '3':
            print("\nDone! Run: streamlit run app.py")
            break
        else:
            print("Invalid choice")
