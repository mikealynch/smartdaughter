# -*- coding: utf-8 -*-
"""
Created on Sat Dec 14 12:06:14 2024

@author: MIke Lynch
"""
import streamlit as st
from dotenv import load_dotenv
import os
import openai
import replicate
from fpdf import FPDF
import requests
from io import BytesIO
import unicodedata
import random

# Load environment variables
load_dotenv()

# Set API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
replicate.api_token = os.getenv("REPLICATE_API_TOKEN")

# Normalize text to handle unsupported characters
def normalize_text(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode("latin-1")

# Summarize the story using OpenAI
def summarize_story_with_ai(story_text):
    """
    Generate a concise summary of the story using OpenAI.
    The summary is limited to 500 characters for use in the image prompt.
    """
    prompt = f"Select an important scene from this story and describe it in 200 characters or less. Use descriptive language optimized for Stable Diffusion:\n\n{story_text}"
    try:
        response = openai.ChatCompletion.create(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4",
        )
        summary = response["choices"][0]["message"]["content"]

        return summary.strip()
        
    except Exception as e:
        raise Exception(f"Error summarizing story: {e}")

# Generate an image using Replicate's Stable Diffusion
def generate_image(prompt):
    try:
        output = replicate.run(
            "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
            input={
                "width": 512,
                "height": 512,
                "prompt": prompt,
                "scheduler": "DPMSolverMultistep",
                "num_outputs": 1,
                "guidance_scale": 10,
                "num_inference_steps": 75,
            }
        )
        return output[0]  # Return the URL of the generated image
    except Exception as e:
        raise Exception(f"Error generating image: {e}")

# Wildcard Story Random Choices
people = ["a curious young scientist", "a friendly squishmallow", "a brave knight", "a mischievous gengar"]
places = ["an enchanted forest", "a futuristic city", "a magical castle", "a mysterious island"]
situations = ["discovering a hidden treasure", "solving a puzzling mystery", "making an unexpected friend", "saving the day from disaster"]

def generate_wildcard_prompt():
    person = random.choice(people)
    place = random.choice(places)
    situation = random.choice(situations)
    return f"Write a short, adventurous story for a 9-year-old about Eliana, and her adventures with {person} in {place}, who is {situation}. The story should be imaginative, exciting, and age-appropriate."

# Title and Introduction
st.title("SmartDaughter Story Generator")
st.markdown("""
Welcome to the **SmartDaughter Story Generator**! Click one of the buttons below to generate a unique story and illustration:
- **Dragon Story**: Generate a story about Eliana, the SeaWing-SandWing hybrid dragonet.
- **Wildcard Story**: Generate a story about Eliana's adventure with random characters, places, and situations.
""")

# Initialize variables for story and image
story = None
image_url = None

# Dragon Story Button
if st.button("Dragon Story"):
    with st.spinner("Generating your Dragon Story and illustration..."):
        story_prompt = """
        Write a short, adventurous story for a 9-year-old reader about Eliana, a brave SeaWing-SandWing hybrid dragonet. 
        Include themes of courage, discovery, and friendship. The story should be imaginative, exciting, and age-appropriate.
        """
        try:
            # Generate story
            chat_completion = openai.ChatCompletion.create(
                messages=[{"role": "user", "content": story_prompt}],
                model="gpt-4",
            )
            story = chat_completion["choices"][0]["message"]["content"]

            st.subheader("Your Dragon Story:")
            st.write(story)

            # Summarize the story for the illustration
            summary = summarize_story_with_ai(story)

            # Generate illustration
            image_prompt = f"A playful, imaginative children's illustration of: {summary}."
            image_url = generate_image(image_prompt)

            # Display illustration
            st.image(image_url, caption=f"Illustration of: {summary}")

        except Exception as e:
            st.error(f"An error occurred: {e}")

if st.button("Wildcard Story"):
    with st.spinner("Generating your Wildcard Story and illustration..."):
        story_prompt = generate_wildcard_prompt()
        try:
            # Generate story
            chat_completion = openai.ChatCompletion.create(
                messages=[{"role": "user", "content": story_prompt}],
                model="gpt-4",
            )
            story = chat_completion["choices"][0]["message"]["content"]

            st.subheader("Your Wildcard Story:")
            st.write(story)

            # Summarize the story for the illustration
            summary = summarize_story_with_ai(story)

            # Generate illustration
            image_prompt = f"A illustration of: {summary}. The illustration should look like it was made with colored pencils.  Elina is a 9 year old girl from Boston with brown hair and brown eyes. Her favorite color is orange."
            image_url = generate_image(image_prompt)

            # Display illustration
            st.image(image_url, caption=summary)

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Generate PDF
if story and image_url:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add the story to the PDF
    pdf.multi_cell(0, 10, normalize_text(story))

    # Add the illustration to the PDF
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image = BytesIO(response.content)
            temp_image_path = "temp_image.png"
            with open(temp_image_path, "wb") as f:
                f.write(image.getvalue())
            pdf.image(temp_image_path, x=10, y=pdf.get_y() + 10, w=100)
            os.remove(temp_image_path)
    except Exception as e:
        st.error(f"Could not fetch or add the image to the PDF: {e}")

    pdf_file = BytesIO()
    pdf_content = pdf.output(dest="S").encode("latin1")
    pdf_file.write(pdf_content)
    pdf_file.seek(0)

    # Allow the user to download the PDF
    st.download_button(
        label="Download Story as PDF",
        data=pdf_file,
        file_name="Generated_Adventure.pdf",
        mime="application/pdf",
    )
