"""
Import Book Club Data from Excel Spreadsheet
Loads file Books of interest.xlsx into the database
"""

import pandas as pd
import database as db
import sys
import os

def import_from_excel(filepath: str):
    """Import books and members from the Excel spreadsheet"""
    
    print("Reading Excel file...")
    df = pd.read_excel(filepath, header=0)
    
    # Skip the first row (headers) and get actual data
    df = df.iloc[1:].reset_index(drop=True)
    
    # Clean column names
    df.columns = ['title', 'author', 'genre', 'added_by', 'top_prio', 'notes', 
                  'dom_plus1', 'emma_plus1', 'irsa_plus1', 'mahnoor_plus1', 'sylvia_plus1']
    
    # Remove rows with no title
    df = df[df['title'].notna()]
    
    print(f"\nFound {len(df)} books in spreadsheet")
    
    # Reset database
    print("\nResetting database...")
    db.reset_database()
    
    # Get unique members from "added_by" column
    members_from_added_by = df['added_by'].dropna().unique().tolist()
    
    # Members who have +1 columns (Dom, Emma, Irsa, Mahnoor, Sylvia)
    all_members = ['Dom', 'Emma', 'Irsa', 'Mahnoor', 'Sylvia']
    
    # Combine and deduplicate
    member_names = list(set(all_members + [m for m in members_from_added_by if m in all_members]))
    member_names.sort()
    
    print(f"\nAdding {len(member_names)} members: {', '.join(member_names)}")
    
    # Add members with default preferences
    # Can change these later in the app under "Manage Members"
    member_ids = {}
    for name in member_names:
        member_id = db.add_member(
            name=name,
            preferred_length=300,  # Default 300 pages
            liked_genres=['Fantasy', 'Science Fiction', 'Contemporary Fiction', 
                         'Mystery', 'Historical Fiction']  # Default broad preferences
        )
        member_ids[name] = member_id
        print(f" Added {name}")
    
    print(f"\nAdding {len(df)} books to pool...")
    
    # Import books
    books_added = 0
    books_skipped = 0
    
    for idx, row in df.iterrows():
        title = row['title']
        author = row['author'] if pd.notna(row['author']) else 'Unknown Author'
        
        # Setting a default genre for now because our spreadsheet doesnt have genres specified
        genre = row['genre'] if pd.notna(row['genre']) else 'Unspecified'
        
        # Get who suggested it
        suggested_by_name = row['added_by'] if pd.notna(row['added_by']) else None
        suggested_by_id = member_ids.get(suggested_by_name) if suggested_by_name else None
        
        # Default page count (can be updated later in the app)
        page_count = 300  # Default
        
        try:
            db.add_book(
                title=title,
                author=author,
                genre=genre,
                page_count=page_count,
                suggested_by=suggested_by_id
            )
            books_added += 1
            
            if books_added % 10 == 0:
                print(f"  Added {books_added} books...")
                
        except Exception as e:
            print(f"   Skipped '{title}': {e}")
            books_skipped += 1
    
    print(f"\nImport complete!")
    print(f"  Books added: {books_added}")
    print(f"  Books skipped: {books_skipped}")
    print(f"  Members: {len(member_names)}")
    
    print("\nNext steps:")
    print("  1. Run: streamlit run app.py")
    print("  2. Go to 'Manage Members' to update reading preferences")
    print("  3. Go to 'Manage Books' to:")
    print("     - Add missing genres (currently set to 'Unspecified')")
    print("     - Add page counts (currently default 300)")
    print("     - Add any books you've already read")
    print("  4. Go to 'Get Recommendations' to start choosing your next book!")
    
    return books_added, member_names

if __name__ == "__main__":
    # filepath = "/Users/irsaashraf/Desktop/Projects/Book Recommender/book-recommender"
    # if len(sys.argv) > 1:
    #     filepath = os.path.join(filepath, sys.argv[1])
    # else:
    # Default path for local development
    filepath = '/Users/irsaashraf/Desktop/Projects/Book Recommender/book-recommender/Books of interest.xlsx'
    
    try:
        import_from_excel(filepath)
    except FileNotFoundError:
        print(f"Error: Could not find file '{filepath}'")
        print("Usage: python import_bookclub_data.py <path_to_excel_file>")
    except Exception as e:
        print(f"Error importing data: {e}")
        import traceback
        traceback.print_exc()
