For today's challenge, our goal is to solve the Amnesia Problem in Streamlit apps. We need to understand why standard variables reset on every interaction and how to use Session State to preserve data. Once that's done, we will have a counter that actually remembers its value as you click buttons.

---

### :material/settings: How It Works: Step-by-Step

Streamlit runs your entire Python script from top to bottom every time you interact with a widget (like clicking a button). This creates a logic trap if you aren't careful.



#### 1. The Trap: Standard Variables

```python
with col1:
    st.header(":material/cancel: Standard Variable")
    
    # This line runs every time you click ANY button.
    count_wrong = 0 
    
    if st.button(":material/add:", key="std_plus"):
        count_wrong += 1  # Becomes 0 + 1 = 1

    st.metric("Standard Count", count_wrong)
```

* `count_wrong = 0`: This is the culprit. Every time the app reruns (which happens on every click), this line executes again, resetting the score to 0 immediately.
* `key="std_plus"`: We assign a unique ID to the button. If we didn't, Streamlit might get confused between the buttons in Column 1 and Column 2.

#### 2. The Fix: Initialization Pattern

```python
with col2:
    st.header(":material/check_circle: Session State")

    # 1. Initialization: Create the key only if it doesn't exist yet
    if "counter" not in st.session_state:
        st.session_state.counter = 0
```

* `st.session_state`: Think of this as a persistent dictionary that survives the app reruns.
* `if "counter" not in...`: This is the standard Session State Pattern. It ensures we set the start value to 0 only once. On the second run, Streamlit sees "counter" already exists and skips this block, preserving the current count.

#### 3. Modifying and Reading State

```python
    # 2. Modification: Update the dictionary value
    if st.button(":material/add:", key="state_plus"):
        st.session_state.counter += 1

    # 3. Read: Display the value
    st.metric("State Count", st.session_state.counter)
```

* `st.session_state.counter += 1`: Instead of modifying a temporary variable, we modify the value stored in the Session State dictionary.
* `st.metric(...)`: We read the value directly from state. Because the initialization block (Step 2) was skipped on this rerun, the value continues to grow rather than resetting.

This prepares us for the next step, which is applying this memory concept to our Chatbot so it remembers the conversation history.

---

### :material/library_books: Resources
- [Session State Documentation](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [Session State Guide](https://docs.streamlit.io/develop/concepts/architecture/session-state)
