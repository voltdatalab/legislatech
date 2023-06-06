import openai
import os       # ler variaveis de ambiente

def summarize(text, token_key):
    print(" - Summarizando texto")
    text = text[:1000] + '...' if len(text) > 1000 else text
    openai.api_key = token_key

    model_engine = "text-davinci-003"
    prompt = "Please summarize in native language the following text in up to 130 characters:\n" + text + "\n\nSummary:"
    # prompt = "Summarize the main points in up to 130 characters in the following text:" + text

    try:
        # Generate a response
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )
        response = completion.choices[0].text
        return response

    except Exception as e:
        print(e)
        if type(e) == openai.error.RateLimitError:
            print("You exceeded your current quota,")
            print("please wait a few minutes and try again.")

        return ''