import streamlit as st
import database as db
import recommender as rec
from typing import List

# Page config
st.set_page_config(
    page_title="Book Club Recommender",
    page_icon="📚",
    layout="wide"
)

# Initialize database
db.init_db()

# Title
st.title("📚 Book Club Recommender")
st.markdown("*A constraint-based filtering system for choosing your next read*")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Home", "Manage Members", "Manage Books", "Get Recommendations", "Reading History"]
)


# HOME PAGE

if page == "🏠 Home":
    st.header("Welcome to Book Club Recommender!")
    
    st.markdown("""
    This tool helps your book club choose what to read next using a smart filtering system.
    
    **How it works:**
    
    1. **Add Members** - Set up your book club members with their reading preferences
    2. **Add Books** - Build your book pool with suggestions from members
    3. **Set Vetoes** - Each member can veto one genre per round
    4. **Get Recommendations** - The system filters and scores books to find the best matches
    5. **Track History** - Keep track of what you've read
    
    **The Logic:**
    - **Hard filters**: Removes books already read, last 2 genres, and vetoed genres
    - **Soft scoring**: Ranks remaining books by genre match, length preference, member interest, and diversity
    
    ---
    
    **Quick Start:**
    1. Go to "Manage Members" and add your book club members
    2. Go to "Manage Books" and add books to your pool
    3. Go to "Get Recommendations" to see what you should read next!
    """)
    
    # Show stats
    members = db.get_members()
    books = db.get_books()
    history = db.get_reading_history()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Members", len(members))
    col2.metric("Books in Pool", len(books))
    col3.metric("Books Read", len(history))

# MANAGE MEMBERS PAGE

elif page == "Manage Members":
    st.header("Manage Book Club Members")
    
    # Show existing members
    members = db.get_members()
    
    if members:
        st.subheader("Current Members")
        for member in members:
            with st.expander(f"{member['name']}"):
                st.write(f"**Preferred Length:** {member['preferred_length']} pages")
                st.write(f"**Liked Genres:** {', '.join(member['liked_genres'])}")
    else:
        st.info("No members yet. Add your first member below!")
    
    # Add new member
    st.subheader("Add New Member")
    
    with st.form("add_member_form"):
        name = st.text_input("Name")
        preferred_length = st.number_input("Preferred Book Length (pages)", 
                                          min_value=100, max_value=1000, 
                                          value=300, step=50)
        
        # Genre selection
        common_genres = ["Fantasy", "Science Fiction", "Mystery", "Thriller", 
                        "Historical Fiction", "Contemporary Fiction", "Romance", 
                        "Horror", "Non-Fiction", "Biography", "Self-Help"]
        
        liked_genres = st.multiselect("Liked Genres", common_genres)
        
        submitted = st.form_submit_button("Add Member")
        
        if submitted:
            if name and liked_genres:
                db.add_member(name, preferred_length, liked_genres)
                st.success(f"Added {name} to the book club!")
                st.rerun()
            else:
                st.error("Please provide a name and at least one liked genre.")

# MANAGE BOOKS PAGE

elif page == "Manage Books":
    st.header("Manage Book Pool")
    
    # Show existing books
    books = db.get_books()
    
    if books:
        st.subheader(f"Current Pool ({len(books)} books)")
        
        # Filter options
        genre_filter = st.selectbox("Filter by Genre", ["All"] + sorted(list(set(b['genre'] for b in books))))
        
        filtered_books = books if genre_filter == "All" else [b for b in books if b['genre'] == genre_filter]
        
        for book in filtered_books:
            suggested_by = f" (suggested by {book['suggested_by_name']})" if book['suggested_by_name'] else ""
            st.write(f"**{book['title']}** by {book['author']} • {book['genre']} • {book['page_count']} pages{suggested_by}")
    else:
        st.info("No books in the pool yet. Add your first book below!")
    
    # Add new book
    st.subheader("Add New Book")
    
    members = db.get_members()
    
    with st.form("add_book_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Title")
            author = st.text_input("Author")
        
        with col2:
            genre = st.selectbox("Genre", 
                                ["Fantasy", "Science Fiction", "Mystery", "Thriller", 
                                 "Historical Fiction", "Contemporary Fiction", "Romance", 
                                 "Horror", "Non-Fiction", "Biography", "Self-Help"])
            page_count = st.number_input("Page Count", min_value=1, value=300)
        
        # Optional: who suggested this book
        suggested_by_options = ["None"] + [m['name'] for m in members]
        suggested_by_name = st.selectbox("Suggested By (Optional)", suggested_by_options)
        
        submitted = st.form_submit_button("Add Book")
        
        if submitted:
            if title and author:
                suggested_by_id = None
                if suggested_by_name != "None":
                    suggested_by_id = next(m['id'] for m in members if m['name'] == suggested_by_name)
                
                db.add_book(title, author, genre, page_count, suggested_by_id)
                st.success(f"Added '{title}' to the book pool!")
                st.rerun()
            else:
                st.error("Please provide title and author.")


# GET RECOMMENDATIONS PAGE

elif page == "Get Recommendations":
    st.header("Get Book Recommendations")
    
    members = db.get_members()
    books = db.get_books()
    
    if not members or not books:
        st.warning("Hold up! You need to add members and books before getting recommendations!")
        st.info("Go to 'Manage Members' and 'Manage Books' to set up your club.")
    else:
        current_round = db.get_current_round()
        st.subheader(f"Round {current_round}")
        
        # Show context
        last_2_genres = db.get_last_n_genres(2)
        if last_2_genres:
            st.info(f"**Last genres read:** {', '.join(last_2_genres)} (will be excluded)")
        
        # Veto section
        st.subheader("Set Vetoes for This Round")
        st.markdown("Each member can veto one genre they don't want to read this round.")
        
        vetoes = db.get_vetoes(current_round)
        available_genres = rec.get_genres_from_pool()
        
        veto_cols = st.columns(len(members))
        for idx, member in enumerate(members):
            with veto_cols[idx]:
                st.write(f"**{member['name']}**")
                current_veto = next((v for v in vetoes if v == member.get('veto')), None)
                
                veto_genre = st.selectbox(
                    f"Veto genre",
                    ["None"] + available_genres,
                    key=f"veto_{member['id']}"
                )
                
                if st.button(f"Save", key=f"save_veto_{member['id']}"):
                    if veto_genre != "None":
                        db.add_veto(member['id'], veto_genre, current_round)
                        st.success(f"Saved veto for {member['name']}")
                        st.rerun()
        
        # Show current vetoes
        if vetoes:
            st.write(f"**Current vetoes:** {', '.join(vetoes)}")
        
        st.divider()
        
        # Get recommendations
        if st.button("Get Recommendations", type="primary"):
            recommendations = rec.get_recommendations(top_n=10)
            
            if not recommendations:
                st.error("No eligible books found! Try adjusting your vetoes or adding more books to the pool.")
            else:
                st.success(f"Found {len(recommendations)} recommendations!")
                
                for idx, book in enumerate(recommendations, 1):
                    with st.expander(f"#{idx} - {book['title']} (Score: {book['score']}/100)"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Author:** {book['author']}")
                            st.write(f"**Genre:** {book['genre']}")
                            st.write(f"**Length:** {book['page_count']} pages")
                            if book['suggested_by_name']:
                                st.write(f"**Suggested by:** {book['suggested_by_name']}")
                        
                        with col2:
                            st.metric("Total Score", f"{book['score']}/100")
                            
                            breakdown = book['score_breakdown']
                            st.write("**Score Breakdown:**")
                            st.write(f"Genre Match: {breakdown['genre_match']:.1f}")
                            st.write(f"Length: {breakdown['length_preference']:.1f}")
                            st.write(f"Interest: {breakdown['member_interest']:.1f}")
                            st.write(f"Diversity: {breakdown['diversity_bonus']:.1f}")
                        
                        # Option to mark as chosen
                        if st.button(f"We chose this book!", key=f"choose_{book['id']}"):
                            db.mark_book_as_read(book['id'], current_round)
                            st.success(f"Marked '{book['title']}' as Round {current_round} pick!")
                            st.balloons()
                            st.rerun()


# READING HISTORY PAGE

elif page == "📊 Reading History":
    st.header("Reading History")
    
    history = db.get_reading_history()
    
    if not history:
        st.info("No books read yet! Use 'Get Recommendations' to choose your first book.")
    else:
        st.subheader(f"Books Read: {len(history)}")
        
        for entry in history:
            st.write(f"**Round {entry['round_number']}:** {entry['title']} by {entry['author']} ({entry['genre']}, {entry['page_count']} pages)")
        
        # Genre breakdown
        st.divider()
        st.subheader("Genre Distribution")
        
        genre_counts = {}
        for entry in history:
            genre_counts[entry['genre']] = genre_counts.get(entry['genre'], 0) + 1
        
        for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
            st.write(f"{genre}: {count} book(s)")


# FOOTER

st.sidebar.divider()
st.sidebar.markdown("""
**Book Club Recommender**  
Built with constraint-based filtering  

[GitHub](https://github.com/yourusername/book-club-recommender) • [Blog Post](https://yoursubstack.com)
""")

# Reset database option (for testing)
if st.sidebar.button("!! Reset Database", help="Deletes all data"):
    if st.sidebar.checkbox("I'm sure"):
        db.reset_database()
        st.sidebar.success("Database reset!")
        st.rerun()
