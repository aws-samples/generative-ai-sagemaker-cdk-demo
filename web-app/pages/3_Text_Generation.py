import streamlit as st
import requests
import time

from configs import *

from PIL import Image
image = Image.open("./img/sagemaker.png")
st.image(image, width=80)
st.header("Text Generation")
st.caption("Using FLAN-T5-XL model from Hugging Face")

conversation = """Customer: Hi, my iPhone isn’t charging well, and the battery drains fast. I’ve tried different cables and adapters, but no luck.
Agent: Sorry to hear that. Check Settings > Battery for apps using lots of power.
Customer: Some apps are draining battery.
Agent: Force quit those apps by swiping up to close them.
Customer: Did that, but no improvement.
Agent: Let’s reset your settings: Settings > General > Reset > Reset All Settings. This won’t erase data.
Customer: Done. What next?
Agent: Restart your iPhone by holding the power button, slide to power off, then turn it back on.
Customer: Restarted, still not charging properly.
Agent: You should get a diagnostic test at an Apple Store or authorized service provider.
Customer: Do I need an appointment?
Agent: Yes, it’s best to book online or by phone to avoid waiting.
Customer: Will repairs cost me?
Agent: If under warranty, repairs are free; otherwise, you’ll pay.
Customer: How long will repairs take?
Agent: Usually 1-2 business days, depending on the issue.
Customer: Can I track the repair status?
Agent: Yes, online or by contacting the service center.
Customer: Thanks for your help.
Agent: You’re welcome! Let me know if you need anything else."""

with st.spinner("Retrieving configurations..."):

    all_configs_loaded = False

    while not all_configs_loaded:
        try:
            api_endpoint = get_parameter(key_txt2nlu_api_endpoint)
            sm_endpoint = get_parameter(key_txt2nlu_sm_endpoint)
            all_configs_loaded = True
        except:
            time.sleep(5)

    endpoint_name = st.sidebar.text_input("SageMaker Endpoint Name:",sm_endpoint)
    url = st.sidebar.text_input("API GW Url:",api_endpoint)

    context = st.text_area("Input Context:", conversation, height=300, max_chars=1700)


    queries = ("write a summary",
                "What steps were suggested to the customer to fix the issue?",
                "What is the overall sentiment and sentiment score of the conversation?")

    selection = st.selectbox(
        "Select a query:", queries)

    if st.button("Generate Response", key=selection):
        if endpoint_name == "" or selection == "" or url == "":        
            st.error("Please enter a valid endpoint name, API gateway url and prompt!")
        else:
            with st.spinner("Wait for it..."):
                try:
                    prompt = f"{context}\n{selection}"
                    r = requests.post(url,json={"prompt":prompt, "endpoint_name":endpoint_name},timeout=180)
                    data = r.json()
                    generated_text = data["generated_text"]
                    st.write(generated_text)
                    #st.write(data)
                    
                except requests.exceptions.ConnectionError as errc:
                    st.error("Error Connecting:",errc)
                    
                except requests.exceptions.HTTPError as errh:
                    st.error("Http Error:",errh)
                    
                except requests.exceptions.Timeout as errt:
                    st.error("Timeout Error:",errt)    
                    
                except requests.exceptions.RequestException as err:
                    st.error("OOps: Something Else",err)                
                                        
            st.success("Done!")

    query = st.text_area("Input Query:", "what do you suggest as next step for the customer?", height=100, max_chars=60)

    if st.button("Generate Response", key=query):
        if endpoint_name == "" or query == "" or url == "":        
            st.error("Please enter a valid endpoint name, API gateway url and query!")
        else:
            with st.spinner("Wait for it..."):
                try:
                    prompt = f"{context}\n{query}"
                    r = requests.post(url,json={"prompt":prompt, "endpoint_name":endpoint_name},timeout=180)
                    data = r.json()
                    generated_text = data["generated_text"]
                    st.write(generated_text)
                    #st.write(data)
                    
                except requests.exceptions.ConnectionError as errc:
                    st.error("Error Connecting:",errc)
                    
                except requests.exceptions.HTTPError as errh:
                    st.error("Http Error:",errh)
                    
                except requests.exceptions.Timeout as errt:
                    st.error("Timeout Error:",errt)    
                    
                except requests.exceptions.RequestException as err:
                    st.error("OOps: Something Else",err)                
                                
            st.success("Done!")
        
