def test():
    audio = None
    summary = None    
    
    
    {"role": "system", "content": f"""Provide a single-phrase or single-word title that accurately captures the main theme or subject of this summary delimited by triple backticks ```{summary}```. Ensure the response consists only of the title, without any additional text or explanation. Title: """}
    

    
    {"role": "system", "content": f"""Based solely on the transcript delimited by triple backticks which contains sentence timestamps, speakers, and text, do the following: 
        
        1. Provide a short summary of the key points. Include timestamps in the summary to reference where details are derived from the transcript. Ensure the summary directly addresses the core topics discussed in the transcript.\
        

        Present the summary in the format as the text in tripple astheric:
        
        ***known for his work in existential philosophy and pioneering in the field of philosophy of mind. (9700)

        Jaspers had a comprehensive impact on modern theology, psychiatric philosophy, and literature. (19892)

        Timestamps:

        * 9700: An influential German philosopher.
        * 19892: Jaspers Impacts.***\

        
        2. Provide a single-phrase or single-word title that accurately captures the main theme or subject of the transcript delimited by triple backticks.\
        
    Provide your answer in JSON format with the following keys: 
    summary, title.\
         
    If the transcript is empty then simply write \"No transript provided.\"\
         
    Transcript: ```{audio}```
    """}


    "1. first find relevant quote as regrds teh qustion then use the quote to answer the question. Provide timestamp for each answer"