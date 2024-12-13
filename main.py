import streamlit as st
from dotenv import load_dotenv
import os
import openai
from fpdf import FPDF
import requests
from io import BytesIO
import unicodedata

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Normalize text to handle unsupported characters
def normalize_text(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode("latin-1")

# Extract an interesting part of the story for the illustration
def extract_key_scene(story_text):
    """
    Extract a visually interesting part of the story for illustration.
    For simplicity, we use the first visually descriptive sentence. Eliana, is a SeaWing-SandWing hybrid dragonet.
    """
    sentences = story_text.split(". ")
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in ["cave", "underwater", "shimmer", "adventure"]):
            return sentence.strip() + "."
    return sentences[0].strip() + "."  # Default to the first sentence if no keywords are found

# Title and Introduction
st.title("SmartDaughter Story Generator by MIKEALYNCH")
st.markdown("""
Welcome to the **SmartDaughter Story Generator**! Here, you'll embark on amazing adventures with Eliana, 
the brave SeaWing-SandWing hybrid dragonet. Click the button below to generate a unique story and illustration!
""")

# Initialize variables for story and image
story = None
image_url = None

# Button for generating a story
if st.button("Generate Story"):
    with st.spinner("Generating your story and illustration..."):
        # AI prompt for story generation
        story_prompt = """
        Write a short, adventurous story for a 9-year-old reader about Eliana, a brave SeaWing-SandWing hybrid dragonet. 
        Include themes of courage, discovery, and friendship. The story should be imaginative, exciting, and age-appropriate.
        """
        try:
            # Generate story
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": story_prompt}],
                model="gpt-4",
            )
            story = chat_completion.choices[0].message.content

            st.subheader("Your Story:")
            st.write(story)

            # Extract an interesting part of the story for the illustration
            key_scene = extract_key_scene(story)

            # Update the image generation prompt
            image_prompt = f"""
            Create a illustration of the following scene:
            {key_scene}
            The style should be playful, imaginative, and age-appropriate for children. The style of illustration should be simple like a saturday morning children's cartoon. '
            """

            # Generate illustration
            image_response = client.images.generate(
                prompt=image_prompt,
                n=1,
                size="512x512",
            )

            # Access the URL of the generated image
            image_url = image_response.data[0].url

            # Display illustration
            st.image(image_url, caption=f"Illustration of: {key_scene}")

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
        # Fetch the image from the URL
        response = requests.get(image_url)
        if response.status_code == 200:
            image = BytesIO(response.content)

            # Save the image temporarily
            temp_image_path = "temp_image.png"
            with open(temp_image_path, "wb") as f:
                f.write(image.getvalue())

            # Add the image to the PDF
            pdf.image(temp_image_path, x=10, y=pdf.get_y() + 10, w=100)

            # Clean up temporary image file
            os.remove(temp_image_path)
    except Exception as e:
        st.error(f"Could not fetch or add the image to the PDF: {e}")

    # Save the PDF to a BytesIO object
    pdf_file = BytesIO()
    pdf_content = pdf.output(dest="S").encode("latin1")  # Get PDF content as a string
    pdf_file.write(pdf_content)  # Write content to BytesIO
    pdf_file.seek(0)  # Move the file pointer to the beginning

    # Allow the user to download the PDF
    st.download_button(
        label="Download Story as PDF",
        data=pdf_file,
        file_name="Eliana_Adventure.pdf",
        mime="application/pdf",
    )
