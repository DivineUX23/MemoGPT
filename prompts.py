#TESTING PROMPT!

def test():
    audio = None
    summary = None    
    
    
    {"role": "system", "content": f"""Provide a single-phrase or single-word title that accurately captures the main theme or subject of this summary delimited by triple backticks ```{summary}```. Ensure the response consists only of the title, without any additional text or explanation. Title: """}
    

    
    {"role": "system", "content": f"""Based solely on this transcript: {audio} which contains sentence timestamps, speakers, and text, do the following:\
        
        1. Provide a short summary of the key points. Include timestamps in the summary to reference where details are derived from the transcript. Ensure the  summary directly addresses the core topics discussed in the transcript.\
        

        Present the summary in the format as the text in tripple astheric:\
        
        ***known for his work in existential philosophy and pioneering in the field of philosophy of mind. (9700)\

        Jaspers had a comprehensive impact on modern theology, psychiatric philosophy, and literature. (19892)\

        Timestamps:\

        * 9700: An influential German philosopher.\
        * 19892: Jaspers Impacts.***\

        
        2. Provide a single-phrase or single-word title that accurately captures the main theme or subject of the transcript delimited by triple backticks.\
        
    Provide your answer in JSON format with the following keys:\
    summary, title.\
         
    If the transcript is empty then simply write \"No transript provided."""}




        
    {"role": "system", "content": f"""Based solely on the transcript delimited by triple backticks below which contains sentence timestamps, speakers, and text, Provide a short summary of the key points.
     
        - Include the timestamps of the key points in parentheses.
        - Use triple asterisks to mark the summary.
        - Write "No transcript provided." if the transcript is empty.
        - Transcript: "This is an example of a transcript."

        Example 1:
        Transcript: "Hello, this is Alice from ABC company. I'm calling to confirm your appointment for tomorrow at 10 am. Please press 1 to confirm or 2 to reschedule."
        Summary: ***Alice from ABC company called to confirm an appointment for tomorrow at 10 am. (0-12)***
    
             
    Transcript: ```{audio}```
    """}

    "1. first find relevant quote as regrds teh qustion then use the quote to answer the question. Provide timestamp for each answer"

    f"""Summarize the transcript below in a few sentences.

    Include the timestamps of the key points in parentheses.
    Do not add or omit any information from the transcript.
    Transcript: {audio}
    Example 1: Transcript: “Hi, this is John from XYZ company. I'm calling to follow up on your order of 100 widgets. We have shipped your order today and you should receive it by next week. Please let me know if you have any questions or concerns.” Summary: ***John from XYZ company called to follow up on an order of 100 widgets. (0-10)

    The order was shipped today and expected to arrive by next week. (11-19)***"""


{"role": "system", "content": """System: Based solely on this transcript: {audio} which contains sentence timestamps, speakers, and text, do the following:\
- Provide a short summary of the key points. Include timestamps in the summary to reference where details are derived from the transcript. Ensure the summary directly addresses the core topics discussed in the transcript.\
- Provide a single-phrase or single-word title that accurately captures the main theme or subject of the transcript.\

User: Provide your answer in JSON format with the following keys: summary, title.\

System: If the transcript is empty then simply write "No transcript provided."\

Example 1:
Transcript: "Hi, this is John from XYZ company. I'm calling to follow up on your order of 100 widgets. We have shipped your order today and you should receive it by next week. Please let me know if you have any questions or concerns."\
Answer: {"summary": "***John from XYZ company called to follow up on an order of 100 widgets. (0-10)\n\nThe order was shipped today and expected to arrive by next week. (11-19)***", "title": "Order Confirmation"}"""
}

#REFRACTOR LIST
{"""
    Endpoints ---main
    
 Services:
    2. Audio upload and download and play---DONE!NOT TESTED
    3. Llama AI --- ---DONE-TESTED!!!
    4. Transcript--- ---DONE-TESTED!!!
    5. Tokenizers---DONE!NOT TESTED
    6. History, Continue_chat, delete, list ---DONE-TESTED!!!

 Api:
    2. Audio upload and download and play---DONE!NOT TESTED
    3. Llama AI --- ---DONE-TESTED!!!
    6. History, Continue_chat, delete, list ---DONE-TESTED!!!
 """
}

{   
    "We currently believe that the universe has been around for roughly 13.8 billion years. This estimation is based on a variety of data, including measurements of cosmic microwave background radiation left over from the Big Bang and observations of the rate at which galaxies are moving away from each other. Interestingly. To give a bit more color. While the matter and energy that make up the universe have been around for about 13.8 billion years, the universe itself as a concept may be much older or indeed timeless, depending on different interpretations of quantum gravity and string theories. And a little more info for the curious mind. Even though the universe is about 13.8 billion years old, we can see light from objects that are more than 13.8 billion light years away due to the constant expansion of the universe. Isn't that fascinating? In smile."
}