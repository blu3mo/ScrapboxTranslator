import tiktoken

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

# Splitting the titles into chunks that don't exceed the token limit
def split_titles(titles, max_tokens):
    """
    Splits the titles into chunks that don't exceed the token limit

    Args:
        titles (list): The list of titles to be split
        max_tokens (int): The max tokens to use for translation
    
    Returns:
        (list): A list of lists of titles
    """
    split_title_arrays = []
    current_title_set = []
    current_token_count = 0

    for title in titles:
        title_tokens = num_tokens_from_string(title)
        if current_token_count + title_tokens <= max_tokens:
            current_title_set.append(title)
            current_token_count += title_tokens
        else:
            split_title_arrays.append(current_title_set)
            current_title_set = [title]
            current_token_count = title_tokens

    if current_title_set:
        split_title_arrays.append(current_title_set)

    return split_title_arrays