import streamlit as st
import aisuite as ai
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import logging 
from youtube_transcript_api.formatters import TextFormatter
import yt_dlp
import json

# Set Streamlit page configuration
st.set_page_config(page_title="YouTube Video Summarizer", layout="wide")

# Sidebar for user inputs
client = ai.Client()
youtube_link = st.sidebar.text_input("Enter YouTube Video Link:")

# Summary length customization
summary_length = st.sidebar.select_slider(
    "Select Summary Length:", options=['Short', 'Medium', 'Long'], value='Medium'
)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_clip_metadata(video_url,download=False):
  """
  Extracts metadata for all clips within a YouTube video.

  Args:
    video_url: The URL of the YouTube video.

  Returns:
    A list of dictionaries containing the metadata for each clip.
  """
  ydl_opts = {
      'writeautomaticsub': True,  # Download subtitles if available
      'writesubtitles': True,      # Download subtitles in separate files
      'allsubtitles': True,       # Download all available subtitles
      'writeinfojson': True,      # Write metadata to a JSON file
      'no_warnings': True,       # Suppress warnings
      'quiet': True             # Suppress output
  }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info_dict = ydl.extract_info(video_url,download)

  # Get the list of clip information
  clip_info = info_dict.get('chapters')

  if clip_info:
    # Extract metadata for each clip
    clips = []
    for clip in clip_info:
      # Create a dictionary for clip metadata
      clip_metadata = {
          'title': clip.get('title'),
          'start_time': clip.get('start_time'),
          'end_time': clip.get('end_time'),
          'description': clip.get('description')
      }

      # Extract transcript if available
      if 'requested_subtitles' in info_dict:
        for lang, sub_info in info_dict['requested_subtitles'].items():
          if 'data' in sub_info:
            # Extract the text between the start and end time of the clip
            start_time_seconds = datetime.timedelta(seconds=clip['start_time']).total_seconds()
            end_time_seconds = datetime.timedelta(seconds=clip['end_time']).total_seconds()
            with open(sub_info['data'], 'r', encoding='utf-8') as f:
              transcript = f.read()
              transcript = transcript.split('\n')
              clip_transcript = [line for line in transcript if start_time_seconds <= datetime.timedelta(seconds=float(line.split(' --> ')[0])).total_seconds() <= end_time_seconds]
              clip_metadata['transcript'] = '\n'.join(clip_transcript)

      clips.append(clip_metadata)
 

    st.subheader("Detailed clip info:")
      # ℹ️ ydl.sanitize_info makes the info json-serializable
    #st.write(json.dumps(ydl.sanitize_info(info_dict)))
    st.download_button('Download metadata in json', json.dumps(ydl.sanitize_info(info_dict)), 'clips_metadata.json')
   
    return clips
  else:
    # No clips found in the video
    return []
# Define functions
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        #transcript_text = " ".join(segment["text"] for segment in transcript)
        formatter = TextFormatter()

        # .format_transcript(transcript) turns the transcript into a JSON string.
        text_formatted = formatter.format_transcript(transcript)


        transcript_text = ""
        for segment in transcript:
            transcript_text += f"{segment['text']}\n" 
            
     #transcript_text = transcript_to_text_area(video_id)       
        st.text_area("Transcript", text_formatted)
        st.write(f"Transcript: {len(transcript_text)} characters.")
        return transcript_text
    except Exception as e:
        st.sidebar.error(f"An error occurred: {e}")
        logging.debug(f"An error occurred while extracting transcript: {e}")
        return None
    
def generate_ollama_content(transcript_text, system_prompt, user_prompt):
    
    try:
        client.configure({"ollama" : {
        "api_key": "ollama",
        "base_url": "http://localhost:11434",
        "model": "ollama:llama3.2",
        }});


        ollama_model = "ollama:llama3.2"

        messages = [
            { "role": "system", "content": system_prompt },
            { "role": "user", "content": f"{user_prompt}\nTranscript: {transcript_text}\n"},
        ]
        

        response = client.chat.completions.create(model=ollama_model, messages=messages, temperature=0.75)
        print(response.choices[0].message.content)

     
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


# def generate_gemini_content(transcript_text, prompt, api_key):
#     try:
#         genai.configure(api_key=api_key)
#         model = genai.GenerativeModel("gemini-pro")
#         response = model.generate_content(prompt + transcript_text)
#         return response.text
#     except Exception as e:
#         st.error(f"An error occurred: {e}")
#         return None

def create_pdf(summary_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(72, 800, "Summary")
    text = c.beginText(40, 780)
    text.setFont("Helvetica", 12)
    for line in summary_text.split('\n'):
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# UI elements
st.title("YouTube Video Summarizer")

# Display video thumbnail
if youtube_link:
    video_id = youtube_link.split("=")[1]
    video_thumbnail = f"http://img.youtube.com/vi/{video_id}/0.jpg"
    st.image(video_thumbnail, caption="Video Thumbnail", use_container_width=True)
    clips = extract_clip_metadata(youtube_link)
    st.subheader("Detailed metadata:")
    
    # Print clip metadata
    # for clip in clips:
    #     st.write("Clip Title:", clip['title'])
    #     st.write("Start Time:", clip['start_time'])
    #     st.write("End Time:", clip['end_time'])
    #     st.write("Description:", clip['description'])
    #     # st.write("Transcript:", clip['transcript'])
    #     st.write("\n")
  #  st.download_button('Download summary in text', clips, 'clips_metadata.json')


# Process and display summary
if youtube_link and st.button("Get Detailed Notes"):

    transcript_text = extract_transcript_details(youtube_link)
    if transcript_text:
        system_prompt = """You are a YouTube video summarizer. Summarize the video content into key points within 5000 words."""
        user_prompt = f"Please generate a summary with key insights, key points, and important details from the video."
        summary = generate_ollama_content(transcript_text, system_prompt, user_prompt)
        if summary:
            st.success("Transcript extracted and summary generated successfully!")
            st.subheader("Detailed Notes:")
            st.write(summary)
            # PDF download
            pdf_bytes = create_pdf(summary)
            st.download_button(label="Download Summary as PDF",
                               data=pdf_bytes,
                               file_name="YouTube_Summary.pdf",
                               mime="application/pdf")
            

            st.download_button('Download summary in text', summary, 'summary.txt')
        else:
            st.error("Failed to generate summary.")
    else:
        st.error("Failed to extract transcript.")