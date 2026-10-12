from ollama import chat

def run_basic_extraction():

    try:
        with open("brief.txt", "r", encoding="utf-8") as file:
            brief_text = file.read()
    except FileNotFoundError:
        print("Error: Could not find 'brief.txt'. Please ensure it exists.")
        return

    prompt = f"""
    Please read the following text and produce software requirements from it.    
    Text:
    {brief_text}
    """
    
    print("Calling Qwen model... (this might take a moment)")

    response = chat(
        model="qwen3:8b", 
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    output_text = response.message.content


    with open("robot requirements.txt", "w", encoding="utf-8") as out_file:
        out_file.write(output_text)
    print("Extraction complete. Output saved to 'robot requirements.txt'.")
    print("Please run this a few times to check if the output is consistent.")

if __name__ == "__main__":
    run_basic_extraction()