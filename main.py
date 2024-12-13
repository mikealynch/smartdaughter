import streamlit as st
from dotenv import load_dotenv
import os
import openai
from fpdf import FPDF
import requests
from io import BytesIO
import unicodedata
import random

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Normalize text to handle unsupported characters
def normalize_text(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode("latin-1")

# Extract an interesting part of the story for the illustration
def extract_key_scene(story_text):
    sentences = story_text.split(". ")
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in ["cave", "underwater", "shimmer", "adventure"]):
            return sentence.strip() + "."
    return sentences[0].strip() + "."

# Wildcard Story Random Choices
people = ["a curious young scientist", "a friendly robot", "a brave knight", "a talking cat"]
places = ["an enchanted forest", "a futuristic city", "a magical castle", "a mysterious island"]
situations = ["discovering a hidden treasure", "solving a puzzling mystery", "making an unexpected friend", "saving the day from disaster"]

def generate_wildcard_prompt():
    person = random.choice(people)
    place = random.choice(places)
    situation = random.choice(situations)
    return f"Write a short, adventurous story for a 9-year-old about {person} in {place}, who is {situation}. The story should be imaginative, exciting, and age-appropriate."

# Title and Introduction
st.title("SmartDaughter Story Generator by MIKEALYNCH")
st.markdown("""
Welcome to the **SmartDaughter Story Generator**! Click one of the buttons below to generate a unique story and illustration:
- **Dragon Story**: Explore adventures with Eliana, the brave SeaWing-SandWing hybrid dragonet.
- **Wildcard Story**: Create a fun story based on random characters, places, and situations!
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

            # Extract an interesting part of the story for the illustration
            key_scene = extract_key_scene(story)

            # Generate illustration
            image_prompt = f"""
            Create an illustration of the following scene:
            {key_scene}
            The style should be playful, imaginative, and age-appropriate for children, resembling a Saturday morning cartoon.
            """
            image_response = openai.Image.create(
                prompt=image_prompt,
                n=1,
                size="512x512",
            )
            image_url = image_response["data"][0]["url"]

            # Display illustration
            st.image(image_url, caption=f"Illustration of: {key_scene}")

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Wildcard Story Button
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

            # Generate illustration
            image_prompt = f"""
            Create an illustration of a scene from the following story:
            {story}
            The style should be playful, imaginative, and age-appropriate for children, resembling a Saturday morning cartoon.
            """
            image_response = openai.Image.create(
                prompt=image_prompt,
                n=1,
                size="512x512",
            )
            image_url = image_response["data"][0]["url"]

            # Display illustration
            st.image(image_url, caption="Illustration from Wildcard Story")

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
