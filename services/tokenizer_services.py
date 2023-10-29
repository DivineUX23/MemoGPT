import json
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize




#Tokenizing Transcript to fit LLama
def tokenizer(extracted_data: str):

    if isinstance(extracted_data, dict):
        extracted_data = json.dumps(extracted_data)

    print("Token count more = ", len(word_tokenize(extracted_data)))

    chunk_size = 3000 #problem with passing 3000 length to llama but not chatgpt3.5-turbo
    chucks = []
    sentences = sent_tokenize(extracted_data)
    current_chunk = ""

    for sentence in sentences:
        tokens = nltk.word_tokenize(sentence)

        if len(current_chunk.split()) + len(tokens) <= chunk_size:
            current_chunk += "" + sentence

        else:
            chucks.append(current_chunk.strip())
            current_chunk = sentence

        print(f"TOKEN LENT OF unsent CHUNK = \n\n{len(word_tokenize(str(current_chunk.strip())))}\n\n\n")

    if current_chunk:
        chucks.append(current_chunk.strip())
       
    print(chucks)
    return chucks
