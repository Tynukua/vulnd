import json
import re

def parse_openai_response(response):
    """
    Parses the JSON content from an OpenAI response.
    The response is expected to contain JSON enclosed in ```json``` markers.

    Args:
        response (str): The response string from OpenAI.

    Returns:
        dict: Parsed JSON data as a Python dictionary.
    """
    # Extract JSON content enclosed in ```json``` markers
    match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
    if match:
        json_content = match.group(1)
    else:
        json_content = response
    
    # Parse the JSON content
    while True:
        try:
            data = json.loads(json_content)
            return data
        except json.JSONDecodeError as e:
            pos = e.pos -1 
            if json_content[pos] == '"':
                json_content = json_content[:pos] + "\\" + json_content[pos:]
            else:
                raise ValueError(f"Invalid JSON format: {e}")

# Example usage
if __name__ == "__main__":
    openai_response = """
    Here is the data you requested:
    ```json
    {
        "quotes": [
            {"author": "Albert Einstein", "quote": "double quates :"TEST""},
            {"author": "Isaac Newton", "quote": "If I have seen further it is by standing on the shoulders of Giants."}
        ]
    }
    ```
    """
    try:
        parsed_data = parse_openai_response(openai_response)
        quotes = parsed_data.get("quotes", [])
        for quote in quotes:
            print(f"{quote['author']}: \"{quote['quote']}\"")
    except ValueError as e:
        print(f"Error: {e}")