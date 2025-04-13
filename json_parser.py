import json
import re

def parse_json_from_openapi_output(text):
    """
    Parse JSON content from OpenAPI output that might be formatted with markdown code blocks.
    Handles various edge cases including escape character issues.
    
    Args:
        text (str): The text containing JSON output, possibly wrapped in markdown code blocks
        
    Returns:
        dict/list: The parsed JSON object
        
    Raises:
        json.JSONDecodeError: If the extracted content is not valid JSON after all repairs
    """
    # Pattern to match ```json ... ``` blocks (or just ``` ... ```)
    json_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    
    # Try to find JSON blocks
    matches = re.findall(json_block_pattern, text)
    
    if matches:
        # Use the first match if found
        json_str = matches[0].strip()
    else:
        # If no markdown blocks found, assume the whole text might be JSON
        json_str = text.strip()
    
    # Fix common issues with escaped quotes
    json_str = fix_quote_escaping(json_str)
    
    # Handle other common formatting issues
    json_str = fix_common_formatting_issues(json_str)
    
    # Try parsing with different approaches if needed
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try alternative parsing approaches
        return fallback_json_parsing(json_str, e)

def fix_quote_escaping(json_str):
    """
    Fix issues with quote escaping that might appear in OpenAPI outputs.
    """
    # Replace incorrectly escaped quotes: \\" → \"
    json_str = re.sub(r'\\{2,}"', '\\"', json_str)
    
    # Replace """" (four quotes) with escaped quote: \"
    json_str = json_str.replace('""""', '\\"')
    
    # Replace triple quotes with single quotes where appropriate
    json_str = re.sub(r'"""([^"]*?)"""', r'"\1"', json_str)
    
    # Fix cases where quotes aren't properly escaped inside JSON strings
    # This is more complex and might need context-specific handling
    json_str = re.sub(r'(?<!")""(?!")', r'\\"', json_str)
    
    return json_str

def fix_common_formatting_issues(json_str):
    """
    Fix common JSON formatting issues found in OpenAPI outputs.
    """
    # Remove any BOM characters that might cause issues
    if json_str.startswith('\ufeff'):
        json_str = json_str[1:]
    
    # Fix trailing commas in objects and arrays (common mistake)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    
    # Fix missing commas between elements
    json_str = re.sub(r'"\s*}', '"}', json_str)  # Fix spacing issues
    json_str = re.sub(r'"\s*]', '"]', json_str)  # Fix spacing issues
    
    # Fix single quotes used instead of double quotes
    # This is risky and might cause issues with strings containing quotes
    # So we only do it if the JSON fails to parse with normal handling
    
    # Fix newline characters within string literals
    json_str = re.sub(r'(?<!\\)\\n', '\\\\n', json_str)
    
    # Handle potentially unquoted keys (common in JavaScript)
    json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)
    
    return json_str

def fallback_json_parsing(json_str, original_error):
    """
    Attempt fallback parsing methods if standard parsing fails.
    """
    # Try with single quotes converted to double quotes 
    # (only if parsing failed first - this can be risky)
    try:
        # This is a simplistic approach - in real code you'd need a more sophisticated
        # replacement that doesn't touch single quotes within double-quoted strings
        single_quote_fixed = re.sub(r"(?<![\\])(')(.*?)(?<![\\])(')", r'"\2"', json_str)
        return json.loads(single_quote_fixed)
    except:
        pass
    
    # Try with relaxed parsing via ast.literal_eval which is safer than eval
    try:
        import ast
        # Replace NaN, Infinity, -Infinity with valid JSON values
        cleaned = json_str.replace('NaN', 'null').replace('Infinity', '1e999').replace('-Infinity', '-1e999')
        # Try to evaluate as a Python literal
        return ast.literal_eval(cleaned)
    except:
        pass
    
    # If all else fails, raise the original error
    raise original_error

# Example usage
