import wikipedia
import requests
from bs4 import BeautifulSoup
import random
from googlesearch import search
import chess
import chess.svg
import pyttsx3
import speech_recognition as sr
from pytube import YouTube
from summa.summarizer import summarize

# Initialize a global variable to keep track of the input method
current_input_method = "text"

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# ANSI escape code for text color (green)
GREEN_TEXT = "\033[92m"

# ANSI escape code for text color (reset)
RESET_TEXT = "\033[0m"

# Initialize the speech-to-text engine
recognizer = sr.Recognizer()

# Dictionary to map linguistic number names to numerical representation
number_names_dict = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
}

# Function to convert linguistic number names to numerical representation
def convert_linguistic_number_names(text):
    words = text.lower().split()
    converted_words = [number_names_dict[word] if word in number_names_dict else word for word in words]
    return " ".join(converted_words)
from playsound import playsound


def save_to_repository(content):
    if content is not None:
        with open("repository.txt", "a", encoding="utf-8") as file:
            file.write(content + "\n")
def listen_for_user_input():
    with sr.Microphone() as source:
        print("Listening... Please speak.")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        user_input = recognizer.recognize_google(audio).lower()
        print("You said:", user_input)  # Print the recognized speech for feedback
        user_input = convert_linguistic_number_names(user_input)  # Convert linguistic number names
        print("Converted input:", user_input)  # Print the converted input for feedback
        return user_input
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand what you said. Please try again.")
        return listen_for_user_input()
    except sr.RequestError:
        print("Sorry, there was an error with the speech recognition service.")
        return None

def listen_for_command():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.pause_threshold = 1  # Adjust the pause_threshold as needed
        audio = recognizer.listen(source)

    try:
        print("Processing your input...")
        command = recognizer.recognize_google(audio).lower()
        print(f"Your command: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand your speech.")
        return ""
    except sr.RequestError:
        print("Sorry, there was an error processing your request.")
        return ""

def read_from_repository():
    with open("conversational_data.txt", "r") as file:
        return file.read()

def search_books(query):
    api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get('items', [])
    return []


def get_book_summary(book_link):
    api_url = f"https://www.googleapis.com/books/v1/volumes/{book_link}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        book_info = data.get('volumeInfo', {})
        title = book_info.get('title', 'Title not available')
        authors = ", ".join(book_info.get('authors', ['Author not available']))
        description = book_info.get('description', 'No summary available.')
        link = book_info.get('canonicalVolumeLink', 'Link not available')
        return f"Book: {title}\nAuthors: {authors}\nLink: {link}\nSummary: {description}"
    return 'Failed to fetch book details.'

def get_wikipedia_summary(topic):
    try:
        page = wikipedia.page(topic)
        page_url = page.url

        # Get the full content of the Wikipedia page
        response = requests.get(page_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            page_content = "\n".join(paragraph.text for paragraph in paragraphs)

            content = f"Content from Wikipedia page '{page.title}':\n{page_content}"
            save_to_repository(content)
            return content
        else:
            return f"Failed to fetch Wikipedia content for '{topic}'."
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found. Please specify your query: {', '.join(e.options)}"
    except wikipedia.exceptions.PageError:
        return f"Page not found for '{topic}' on Wikipedia."

def scrape_website(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()
            content = f"Website content from '{url}': {text_content}"
            save_to_repository(content)
            return content
        else:
            return "Failed to fetch website content."
    except requests.exceptions.RequestException:
        return "Error: Could not connect to the website."

def get_number_of_sites():
    while True:
        try:
            num_results = int(input("How many resources do you want to refer to? "))
            if num_results > 0:
                return num_results
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_links_from_internet(query, num_results):
    try:
        if num_results > 11:
            # Try using Google as the primary browser for more than 11 websites
            links = []
            website_summaries = []
            for link in search(query, num_results, pause=2):
                links.append(link)
                summary = scrape_website(link)
                website_summaries.append(summary)

            if len(links) >= num_results:
                formatted_links = "\n".join(links[:num_results])
                limited_links = "\n".join(links[:11])  # Concatenate the first 11 links for repository storage
                save_to_repository(limited_links)  # Save the first 11 links to the repository
                if website_summaries:
                    save_to_repository('\n'.join(website_summaries[:11]))  # Save the first 11 website summaries to the repository
                return f"Links related to '{query}' (from Google):\n{formatted_links}"
            else:
                # If Google fails to provide enough results, try using Yahoo as a backup
                print("Google search failed to provide enough results. Attempting Yahoo Search as a backup...")
                return get_links_from_yahoo(query, num_results)
        else:
            # Use Yahoo as the primary browser for fewer than or equal to 11 websites
            yahoo_links = []
            website_summaries = []
            search_url = f"https://search.yahoo.com/search?p={query}"
            response = requests.get(search_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_='compTitle options-toggle')
                yahoo_links = [result.find('a')['href'] for result in results]

                for link in yahoo_links:
                    summary = scrape_website(link)
                    website_summaries.append(summary)

            if yahoo_links:
                formatted_links = "\n".join(yahoo_links[:num_results])
                limited_links = "\n".join(yahoo_links)  # Concatenate all links for repository storage
                save_to_repository(limited_links)  # Save all links to the repository
                if website_summaries:
                    save_to_repository('\n'.join(website_summaries))  # Save website summaries to the repository
                return f"Links related to '{query}' (from Yahoo):\n{formatted_links}"
            else:
                return f"No links found for '{query}' (from Yahoo)."
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not establish a network connection. Please check your internet connection.")
        return None
    except Exception as e:
        print(f"Both Google and Yahoo Search failed: {e}.")
        return None

def get_links_from_google(query, num_results):
    try:
        links = []
        website_summaries = []
        for link in search(query, num_results, pause=2, user_agent="Mozilla/5.0", api_key="AIzaSyC2DmE2P5xZuGtToLBA2Ny5ZTeN01Oe-us"):
            links.append(link)
            summary = scrape_website(link)
            website_summaries.append(summary)

        if links:
            formatted_links = "\n".join(links[:num_results])
            limited_links = "\n".join(links)  # Concatenate all links for repository storage
            save_to_repository(limited_links)  # Save all links to the repository
            if website_summaries:
                save_to_repository('\n'.join(website_summaries))  # Save website summaries to the repository
            return f"Links related to '{query}' (from Google):\n{formatted_links}"
        else:
            return f"No links found for '{query}' (from Google)."
    except Exception as e:
        return f"Google Search failed: {e}. No alternative search results available."

def get_links_from_yahoo(query, num_results):
    try:
        yahoo_links = []
        website_summaries = []
        search_url = f"https://search.yahoo.com/search?p={query}"
        response = requests.get(search_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='compTitle options-toggle')
            yahoo_links = [result.find('a')['href'] for result in results]

            for link in yahoo_links:
                summary = scrape_website(link)
                website_summaries.append(summary)

        if yahoo_links:
            formatted_links = "\n".join(yahoo_links[:num_results])
            limited_links = "\n".join(yahoo_links)  # Concatenate all links for repository storage
            save_to_repository(limited_links)  # Save all links to the repository
            if website_summaries:
                save_to_repository('\n'.join(website_summaries))  # Save website summaries to the repository
            return f"Links related to '{query}' (from Yahoo):\n{formatted_links}"
        else:
            return f"No links found for '{query}' (from Yahoo)."
    except Exception as e:
        return f"Yahoo Search failed: {e}. No alternative search results available."

def read_out_summary(summary):
    # Use the text-to-speech engine to read out the summary
    engine.say(summary)
    engine.runAndWait()

def listen_for_user_move():
    with sr.Microphone() as source:
        print("Listening... Please speak your move.")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        user_input = recognizer.recognize_google(audio).lower()
        print("You said:", user_input)  # Print the recognized speech for feedback
        user_input = convert_linguistic_number_names(user_input)  # Convert linguistic number names
        print("Converted input:", user_input)  # Print the converted input for feedback
        return user_input
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand what you said. Please try again.")
        return listen_for_user_move()
    except sr.RequestError:
        print("Sorry, there was an error with the speech recognition service.")
        return None
def play_chess():
    global current_input_method  # Add this line to use the global variable
    board = chess.Board()
    print("You are playing chess with the bot.")
    while not board.is_game_over():
        if board.turn == chess.WHITE:
            if current_input_method == "speech":
                # Ask for user input for the "from" square through speech
                print("Your turn. Please speak the 'from' square (e.g., 'e2').")
                from_square = listen_for_user_move()
                if from_square is None:
                    continue

                # Ask for user input for the "to" square through speech
                print("Your turn. Please speak the 'to' square (e.g., 'e4').")
                to_square = listen_for_user_move()
                if to_square is None:
                    continue

                user_input = from_square + to_square
            else:
                # Ask for user input through text
                user_input = input("Your turn. Please enter your move (in algebraic notation, e.g., e2e4): ").lower()

            move = user_input.strip()
            try:
                move = chess.Move.from_uci(move)
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print("Invalid move. Try again.")
            except ValueError:
                print("Invalid move. Try again.")
        else:
            legal_moves = list(board.legal_moves)
            move = random.choice(legal_moves)
            board.push(move)
            print(f"Bot's move: {move.uci()}")

        print(board)

    result = board.result()
    if result == "1-0":
        print("You win!")
    elif result == "0-1":
        print("Bot wins!")
    elif result == "1/2-1/2":
        print("It's a draw! Stalemate.")
    else:
        print("Game ended.")


def search_youtube_videos(query, num_results=10):
    api_url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": num_results,
        "key": "AIzaSyC2DmE2P5xZuGtToLBA2Ny5ZTeN01Oe-us",  # Replace this with your YouTube API key
    }

    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            video_items = data.get('items', [])
            video_ids = [item['id']['videoId'] for item in video_items]
            return video_ids
        except (KeyError, IndexError, ValueError):
            print("Failed to parse YouTube search results.")
            return []
    else:
        print(f"Failed to fetch YouTube search results. Status code: {response.status_code}")
        return []

# Function to get YouTube video details using pytube
def get_youtube_video_details(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        video = YouTube(url)
        title = video.title
        video_url = url
        description = video.description
        views = video.views
        publish_date = video.publish_date
        duration = video.length
        transcripts = video.captions.get_by_language_code('en') if video.captions else None
        return {
            "title": title,
            "video_url": video_url,
            "description": description,
            "views": views,
            "publish_date": publish_date,
            "duration": duration,
            "transcripts": transcripts,
        }
    except Exception as e:
        print(f"Failed to get video details for video ID: {video_id}. Error: {e}")
        return None

# Function to search for YouTube videos, get their details, and return a summary
def search_and_summarize_youtube_videos(query, num_results=10):
    video_ids = search_youtube_videos(query, num_results=num_results)
    if not video_ids:
        return f"No videos found for '{query}' on YouTube.", []

    summary = f"Videos related to '{query}':\n"
    video_details_list = []
    for idx, video_id in enumerate(video_ids, start=1):
        video_details = get_youtube_video_details(video_id)
        if video_details:
            video_details_list.append(video_details)
            summary += f"{idx}. Title: {video_details['title']}\nURL: {video_details['video_url']}\n"
            summary += f"Views: {video_details['views']}, Published on: {video_details['publish_date']}\n"
            summary += f"Duration: {video_details['duration']} seconds\n\n"

    return summary, video_details_list  # Return both the summary and the list of video details

def get_video_transcript(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        video = YouTube(url)
        transcripts = video.captions.get_by_language_code('en') if video.captions else None
        return transcripts
    except Exception as e:
        print(f"Failed to get video details for video ID: {video_id}. Error: {e}")
        return None

def summarize_video_transcripts(transcripts):
    if not transcripts:
        return "No transcript available."

    # Combine all the video transcripts into a single text
    all_transcripts = " ".join(transcripts)

    # Summarize the combined text Using Summa
    summary = summarize(all_transcripts, words=150)  # You can adjust the 'words' parameter as per your preference

    return summary
def process_command(command):
    if "bye" in command or "goodbye" in command:
        return "Goodbye! Have a great day."
    elif "input data" in command or "enter information" in command or "input web" in command:
        data = input("Please enter data: ")
        save_to_repository(data)
        return "Data saved to the repository."
    elif "talk" in command:
        return "Hello! How can I assist you?"
    elif "play chess" in command:
        play_chess()
        return "The chess game has ended. How else can I assist you?"
    elif "book summary" in command:
        query = command.replace("book summary", "").strip()
        books = search_books(query)
        if not books:
            return f"No books found for '{query}'."
        else:
            first_book_link = books[0]['id']
            summary = get_book_summary(first_book_link)

            # Ask the user if they want the book summary to be read out
            read_summary_response = input("Would you like me to read the book summary? (yes/no): ").strip().lower()
            if read_summary_response == "yes":
                read_out_summary(summary)
            return summary
    elif "search youtube" in command or "youtube video" in command:
        query = command.replace("search youtube", "").replace("youtube video", "").strip()
        num_results = get_number_of_sites()
        youtube_results, video_details_list = search_and_summarize_youtube_videos(query, num_results)
        print(youtube_results)

        # Ask the user how many videos they want to refer to
        while True:
            try:
                num_videos = int(input("How many videos do you want to refer to? "))
                if num_videos > 0 and num_videos <= len(video_details_list):
                    break
                else:
                    print("Please enter a valid number between 1 and the total number of videos.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        selected_summaries = video_details_list[:num_videos]

        for summary in selected_summaries:
            print(f"\nSummary for '{summary['title']}':")
            print(f"{summary['description']}")
            save_to_repository(summary['description'])  # Save the selected video summary to the repository

        return youtube_results
    else:
        query = command.replace("search", "").strip()
        if "wikipedia" in query:
            wikipedia_summary = get_wikipedia_summary(query)

            # Display the Wikipedia summary before reading it out
            print(wikipedia_summary)

            # Ask the user if they want the Wikipedia summary to be read out
            read_summary_response = input("Would you like me to read the Wikipedia summary? (yes/no): ").strip().lower()
            if read_summary_response == "yes":
                read_out_summary(wikipedia_summary)

            return wikipedia_summary
        else:
            num_results = get_number_of_sites()
            return get_links_from_internet(query, num_results)


def main():
    global current_input_method  # Add this line to use the global variable
    print("Welcome to Kush's magical chat bot!")
    while True:
        # Ask the user if they want to provide input through text or speech
        input_method = input("Do you want to provide input through text or speech? (text/speech): ").lower()

        if input_method not in ["text", "speech"]:
            print("Invalid input method. Please choose 'text' or 'speech'.")
            continue

        # Update the current input method based on user selection
        current_input_method = input_method

        if current_input_method == "text":
            user_input = input("How can I assist you? ").lower()
        elif current_input_method == "speech":
            user_input = listen_for_user_input()
            if user_input is None:
                continue
            print(f"User: {user_input}")

        # Ask for the response type: personal, general, or both
        response_type = input("Response type (personal/general/both): ").lower()

        if "personal repository" in response_type or "data storage" in response_type:
            personal_data = read_from_repository()
            print(personal_data)

        if "general" in response_type:
            while True:
                try:
                    num_videos_to_refer = int(input("How many resources do you want to refer to? "))
                    if num_videos_to_refer > 0:
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

            general_response, video_details_list = search_and_summarize_youtube_videos(user_input, num_videos_to_refer)

            if general_response is not None:
                print(general_response)
                save_to_repository(general_response)

                if "wikipedia" in user_input or "http" in user_input:
                    save_to_repository(general_response)

                # Ask the user if they want to get transcripts for any specific videos
                while True:
                    try:
                        num_videos = int(input("How many videos do you want to get transcripts for? "))
                        if num_videos > 0 and num_videos <= len(video_details_list):
                            break
                        else:
                            print("Please enter a valid number between 1 and the total number of videos.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")

                selected_indexes = []
                for i in range(num_videos):
                    while True:
                        try:
                            index = int(input(f"Enter the index of video {i+1}: "))
                            if index >= 1 and index <= len(video_details_list):
                                selected_indexes.append(index - 1)
                                break
                            else:
                                print("Please enter a valid index.")
                        except ValueError:
                            print("Invalid input. Please enter a number.")

                selected_summaries = [video_details_list[idx] for idx in selected_indexes]

                for summary in selected_summaries:
                    print(f"\nSummary for '{summary['title']}':")
                    print(f"{summary['description']}")
                    save_to_repository(summary['description'])  # Save the selected video summary to the repository

        if "play chess" in user_input:
            play_chess()

        if "bye" in user_input or "goodbye" in user_input:
            print("Goodbye for now! Can't wait to talk to you again!")
            break

if __name__ == "__main__":
    main()