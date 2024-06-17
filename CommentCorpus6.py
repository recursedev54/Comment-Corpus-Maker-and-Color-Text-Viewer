import requests
from bs4 import BeautifulSoup
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from datetime import datetime
import math
import re
import sys
from collections import Counter
import threading
import os
from ursina import Ursina, Text, camera, Button, color
from panda3d.core import LVecBase4f

def get_wikipedia_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching page: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    content = []
    
    for paragraph in soup.select('p'):
        content.append(paragraph.text.strip())
    
    return content

def save_content_to_text(content, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for paragraph in content:
            file.write(paragraph + "\n")

def save_content_to_csv(content, filename):
    df = pd.DataFrame(content, columns=["Content"])
    df.to_csv(filename, index=False)

def scrape_wikipedia_content():
    url = entry_url.get()
    if not url:
        messagebox.showerror("Error", "Please enter a Wikipedia URL")
        return
    
    try:
        content = get_wikipedia_content(url)
        display_content(content)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        global text_filename
        global csv_filename
        text_filename = f"wikipedia_content_{timestamp}.txt"
        csv_filename = f"wikipedia_content_{timestamp}.csv"
        
        save_content_to_text(content, text_filename)
        save_content_to_csv(content, csv_filename)
        
        messagebox.showinfo("Success", f"Content saved to {text_filename} and {csv_filename}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def display_content(content):
    text_content.delete(1.0, tk.END)
    for paragraph in content:
        text_content.insert(tk.END, paragraph + "\n\n")

def load_text_file():
    filename = filedialog.askopenfilename(
        title="Open Text File",
        filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
    )
    if filename:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read().splitlines()
            display_colored_content(content)

def display_colored_content(content):
    full_text = "\n\n".join(content)
    colorize_text(full_text)

# Function to display colored text using Ursina
def display_colored_text(text, position, color_value):
    color_value = LVecBase4f(color_value[0]/255, color_value[1]/255, color_value[2]/255, 1)
    Text(text=text, position=position, color=color_value)

def count_syllables(word):
    # A very basic syllable counter
    return max(1, len(re.findall(r'[aeiouy]+', word, re.IGNORECASE)))

def renyi_entropy(text, alpha):
    # Count the occurrences of each character in the text
    freqs = Counter(text)
    # Calculate the probability of each character
    probs = [float(freq) / len(text) for freq in freqs.values()]
    # Calculate Rényi entropy
    entropy = 1 / (1 - alpha) * math.log2(sum(p**alpha for p in probs))
    return entropy

def generate_rgb_code(entropy):
    # Extract the digits after the decimal point
    digits = str(entropy - int(entropy))[2:8]
    # Generate RGB code if digits are not empty
    if digits and len(digits) >= 6:
        rgb_code = tuple(int(digits[i:i+2], 16) for i in range(0, 6, 2))
    else:
        rgb_code = (0, 0, 0)  # Default to black if no valid digits
    return rgb_code

def colorize_text(sentence):
    # Split the sentence into words
    words = sentence.split()
    x, y = -0.7, 0.4  # Ursina coordinates for positioning text
    processed_words = set()  # Keep track of processed words
    for i, word in enumerate(words):
        if word in processed_words:  # Skip if word already processed as part of a pair
            continue
        if len(word) > 5:
            # For long words, calculate Rényi entropy individually
            word_entropy = renyi_entropy(word, alpha=16)
            rgb_code = generate_rgb_code(word_entropy)
            display_colored_text(word, (x, y), rgb_code)
            y -= 0.05
            if y < -0.4:
                y = 0.4
                x += 0.3
            processed_words.add(word)  # Mark word as processed
        elif i == len(words) - 1:
            # For the last word, calculate Rényi entropy
            word_entropy = renyi_entropy(word, alpha=16)
            rgb_code = generate_rgb_code(word_entropy)
            display_colored_text(word, (x, y), rgb_code)
            y -= 0.05
            if y < -0.4:
                y = 0.4
                x += 0.3
        else:
            # For short words, combine them into pairs
            word_pair = word + ' ' + words[i + 1]
            pair_entropy = renyi_entropy(word_pair, alpha=16)
            rgb_code = generate_rgb_code(pair_entropy)
            display_colored_text(word_pair, (x, y), rgb_code)
            y -= 0.05
            if y < -0.4:
                y = 0.4
                x += 0.3
            processed_words.add(word)  # Mark first word of pair as processed
            processed_words.add(words[i + 1])  # Mark second word of pair as processed

# Ursina app function to run in the main thread
def ursina_app():
    app = Ursina()
    camera.orthographic = True
    camera.fov = 1.5
    Button(text='Load Text File', scale=(0.3, 0.1), position=(0.65, 0.45), on_click=load_text_file)
    app.run()

def launch_ursina():
    root.destroy()  # Close the tkinter window before starting Ursina
    ursina_app()

if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    root.title("Wikipedia Scraper")

    # Set the main window to full screen
    root.geometry("800x600")  # Set a default size (width x height)
    root.state('zoomed')  # Make the window full screen

    # Create a notebook (tabs)
    notebook = ttk.Notebook(root)
    notebook.pack(pady=0, expand=True)

    # Create frames for each tab
    frame_entry = ttk.Frame(notebook)
    frame_display = ttk.Frame(notebook)
    frame_colored = ttk.Frame(notebook)

    frame_entry.pack(fill='both', expand=True)
    frame_display.pack(fill='both', expand=True)
    frame_colored.pack(fill='both', expand=True)

    # Add frames to notebook
    notebook.add(frame_entry, text='Enter Link')
    notebook.add(frame_display, text='Scraped Content')
    notebook.add(frame_colored, text='Colored Content')

    # Widgets for the entry tabk
    label_url = ttk.Label(frame_entry, text="Wikipedia URL:")
    label_url.pack(pady=0)

    entry_url = ttk.Entry(frame_entry, width=100)
    entry_url.pack(pady=0)

    button_scrape = ttk.Button(frame_entry, text="Scrape Content", command=scrape_wikipedia_content)
    button_scrape.pack(pady=0)

    # Widgets for the display tab
    label_content = ttk.Label(frame_display, text="Scraped Content:")
    label_content.pack(pady=0)

    text_content = scrolledtext.ScrolledText(frame_display, wrap=tk.WORD)
    text_content.pack(fill='both', expand=True, padx=10, pady=10)

    # Button to launch Ursina app
    button_launch_ursina = ttk.Button(frame_colored, text="Launch Colored Text Viewer", command=launch_ursina)
    button_launch_ursina.pack(pady=20)

    root.mainloop()
