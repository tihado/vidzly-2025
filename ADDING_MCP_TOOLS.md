# Adding a New MCP Tool

This guide will walk you through creating and integrating a new MCP (Model Context Protocol) tool into the Vidzly application.

## Overview

MCP tools in this project are Python functions that can be exposed through Gradio's MCP server. Each tool is a standalone function that performs a specific task and can be used by AI agents or directly through the Gradio interface.

## Step-by-Step Guide

### Step 1: Create the Tool Function

Create a new Python file in the `src/app/mcps/` directory. Name it descriptively (e.g., `word_reverser.py`, `text_analyzer.py`).

**Example: Creating `word_reverser.py`**

```python
def word_reverser(text):
    """
    Reverse the order of words in a given text.

    Args:
        text (str): The input text to reverse

    Returns:
        str: The text with words in reverse order
    """
    words = text.split()
    reversed_words = ' '.join(reversed(words))
    return reversed_words
```

**Key Requirements:**

- The function should have a clear, descriptive name
- Include a docstring explaining what the function does
- Document all parameters in the docstring
- Document the return value
- Keep the function focused on a single task

### Step 2: Import the Tool in `app.py`

Open `src/app/app.py` and add an import statement at the top:

```python
from mcps.word_reverser import word_reverser
```

### Step 3: Create a Gradio Interface

In `app.py`, within the `with gr.Tab("MCP Tools"):` block, add a new tab for your tool:

```python
with gr.Tab("Demo Word Reverser"):
    gr.Interface(
        fn=word_reverser,
        inputs=[gr.Textbox("Hello world from Vidzly")],
        outputs=[gr.Textbox()],
        title="Word Reverser",
        description="Enter text to reverse the order of words.",
        api_name="word_reverser",
    )
```

**Gradio Interface Parameters:**

- `fn`: Your tool function
- `inputs`: List of Gradio input components (e.g., `gr.Textbox()`, `gr.Number()`, `gr.Slider()`)
- `outputs`: List of Gradio output components
- `title`: Display title for the interface
- `description`: Helpful description for users
- `api_name`: Unique API endpoint name (used for MCP server)

### Step 4: Test Your Tool

1. Run the application:

   ```bash
   poetry run python src/app/app.py
   ```

2. Navigate to the "MCP Tools" tab in the web interface
3. Click on your new tool's tab
4. Test the tool with various inputs
5. Verify the MCP server exposes your tool correctly

## Complete Example

Here's a complete example showing how the existing `letter_counter` tool is implemented:

**File: `src/app/mcps/letter_counter.py`**

```python
def letter_counter(word, letter):
    """
    Count the number of occurrences of a letter in a word or text.

    Args:
        word (str): The input text to search through
        letter (str): The letter to search for

    Returns:
        str: A message indicating how many times the letter appears
    """
    word = word.lower()
    letter = letter.lower()
    count = word.count(letter)
    return count
```

**Integration in `app.py`:**

```python
from mcps.letter_counter import letter_counter

# ... inside the MCP Tools tab ...
with gr.Tab("Demo Letter Counter"):
    gr.Interface(
        fn=letter_counter,
        inputs=[gr.Textbox("strawberry"), gr.Textbox("r")],
        outputs=[gr.Textbox()],
        title="Letter Counter",
        description="Enter text and a letter to count how many times the letter appears in the text.",
        api_name="predict",
    )
```

## Best Practices

1. **Function Design:**

   - Keep functions pure when possible (no side effects)
   - Handle edge cases and invalid inputs gracefully
   - Return meaningful error messages if needed

2. **Documentation:**

   - Write clear docstrings with parameter descriptions
   - Include examples in docstrings if helpful
   - Use type hints if possible (optional but recommended)

3. **Naming:**

   - Use descriptive function names (e.g., `word_reverser` not `rev`)
   - Use descriptive file names matching the function name
   - Use clear `api_name` values for MCP endpoints

4. **Testing:**

   - Test with various inputs including edge cases
   - Verify the tool works both in the Gradio UI and via MCP
   - Check that error handling works correctly

5. **Gradio Components:**
   - Choose appropriate input/output components:
     - `gr.Textbox()` for text input/output
     - `gr.Number()` for numeric values
     - `gr.Slider()` for numeric ranges
     - `gr.Checkbox()` for boolean values
     - `gr.Dropdown()` for selections
   - Provide default values in inputs for better UX

## Advanced: Multiple Parameters

If your tool requires multiple parameters, simply add them to your function signature and corresponding Gradio inputs:

```python
def text_processor(text, operation, case_sensitive):
    """
    Process text with various operations.

    Args:
        text (str): The input text
        operation (str): Operation to perform ('upper', 'lower', 'reverse')
        case_sensitive (bool): Whether operations should be case sensitive

    Returns:
        str: Processed text
    """
    # Implementation here
    pass
```

```python
gr.Interface(
    fn=text_processor,
    inputs=[
        gr.Textbox("Hello World"),
        gr.Dropdown(["upper", "lower", "reverse"]),
        gr.Checkbox(False)
    ],
    outputs=[gr.Textbox()],
    title="Text Processor",
    description="Process text with various operations.",
    api_name="text_processor",
)
```

## Troubleshooting

- **Import errors:** Make sure your function is in the `src/app/mcps/` directory and the import path matches
- **MCP not exposing tool:** Verify `api_name` is unique and the function is properly defined
- **Type errors:** Ensure your function's return type matches the Gradio output component type
- **UI not showing:** Check that the tab is properly nested within `with gr.Tab("MCP Tools"):`

