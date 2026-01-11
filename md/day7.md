For today's challenge, we're building upon the app from Day 6 but this time we'll focus on **theming and layout**. We need to **transform the standard functional interface into a polished, branded experience using Streamlit's configuration and layout tools**. Once that's done, we will have a "Dark Mode" app with a clean sidebar navigation and custom color, creating a more professional look and feel.

---

### :material/settings: How It Works: Step-by-Step

Let's break down the specific changes regarding the visual design and structure.

#### 1. Global Styling (Theming)

To apply a custom look across the entire app without writing CSS, we can use Streamlit's native theming support by creating a `.streamlit/config.toml` file in our app's working directory.
```toml
# .streamlit/config.toml
[server]
enableStaticServing = true

[theme]
base = "dark"
primaryColor = "#1ed760"
backgroundColor = "#2a2a2a"
secondaryBackgroundColor = "#121212"
codeBackgroundColor = "#121212"
textColor = "#ffffff"
linkColor = "#1ed760"
borderColor = "#7c7c7c"
showWidgetBorder = true
baseRadius = "0.3rem"
buttonRadius = "full"
headingFontWeights = [600, 500, 500, 500, 500, 500]
headingFontSizes = ["3rem", "2.5rem", "2.25rem", "2rem", "1.5rem"]
chartCategoricalColors = ["#ffc862", "#2d46b9", "#b49bc8"]

[theme.sidebar]
backgroundColor = "#121212"
secondaryBackgroundColor = "#000000"
codeBackgroundColor = "#2a2a2a"
borderColor = "#696969"
```

* **`base = "dark"`**: Instantly flips the application to Dark Mode, changing defaults for text and backgrounds to be eye-friendly.
* **`primaryColor`**: Sets the accent color for interactive elements (like the "Generate" button and links). Here, it is set to a vibrant green (`#1ed760`).
* **`buttonRadius = "full"`**: Changes the geometry of buttons from standard rectangles to pill-shaped (fully rounded) buttons.
* **`[theme.sidebar]`**: A specific subsection that allows us to style the sidebar differently from the main body, creating visual separation.

#### 2. Layout Structure: The Sidebar

Instead of stacking everything vertically on the main page (as we did in Day 6), we move configuration options to a sidebar.
```python
# Input widgets for the main area
st.subheader(":material/input: Input content")
content = st.text_input("Content URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")

# Configuration widgets moved to the sidebar
with st.sidebar:
    st.title(":material/post: LinkedIn Post Generator v3")
    st.success("An app for generating LinkedIn post using content from input link.")
    tone = st.selectbox("Tone:", ["Professional", "Casual", "Funny"])
    word_count = st.slider("Approximate word count:", 50, 300, 100)
```

* **`with st.sidebar:`**: This context manager moves any widget defined inside it (Title, Tone, Slider) to a collapsible side panel, keeping the main work area clean.
* **`:material/post:`**: Streamlit supports Material Design icons directly in strings. This adds a relevant icon next to the title without needing image files.

#### 3. Progress Feedback with Status Container

When dealing with API calls or time-consuming operations, keeping users informed is crucial. We use `st.status()` to create an expandable container that shows real-time progress updates.
```python
with st.status("Starting engine...", expanded=True) as status:
    
    # Step 1: Construct Prompt
    st.write(":material/psychology: Thinking: Analyzing constraints and tone...")
    time.sleep(2)
    
    prompt = f"""..."""
    
    # Step 2: Call API
    st.write(":material/flash_on: Generating: contacting Snowflake Cortex...")
    time.sleep(2)
    
    response = call_cortex_llm(prompt)
    
    # Step 3: Update Status to Complete
    st.write(":material/check_circle: Post generation completed!")
    status.update(label="Post Generated Successfully!", state="complete", expanded=False)
```

* **`st.status()`**: Creates an animated status container that can display multiple progress steps. The `expanded=True` parameter ensures users can see what's happening in real-time.
* **`status.update()`**: Once processing completes, we update the status label and set `state="complete"` to show a green checkmark, while `expanded=False` collapses the details to keep the interface clean.
* **`time.sleep(2)`**: Adds a brief 2-second delay between steps. While the actual API call may happen quickly (especially with caching), these pauses make each stage visible, creating a more transparent and understandable experience. Without these delays, status updates might flash by too quickly to read. Feel free to remove these in your production app.

The combination of status updates and deliberate delays transforms what could be an opaque "loading" experience into an informative, step-by-step process that builds user confidence.

#### 4. Output Grouping and Visual Hierarchy

We organize the results to make the output distinct from the input and processing status.
```python
# Display Result
with st.container(border=True):
    st.subheader(":material/output: Generated post:")
    st.markdown(response)
```

* **`st.container(border=True)`**: Wraps the content inside a box with a visible border. This visually groups the "Result" as a distinct card, separating it from the processing logs or input fields.
* **`st.subheader(":material/output: ...")`**: Uses a distinct icon to signal to the user that this section contains the final deliverable.

When this code runs, you will see a sleek, dark-themed application where the controls are tucked away in the sidebar, progress updates keep you informed during processing, and the final AI output is presented in a clean, bordered card.

---

### :material/library_books: Resources
- [Streamlit Theming Guide](https://docs.streamlit.io/develop/concepts/configuration/theming)
- [config.toml Configuration](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
- [st.sidebar Documentation](https://docs.streamlit.io/develop/api-reference/layout/st.sidebar)
- [Material Icons in Streamlit](https://docs.streamlit.io/develop/api-reference/media/st.image#using-material-icons)
