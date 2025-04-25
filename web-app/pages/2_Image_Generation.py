import streamlit as st
import requests
import matplotlib.pyplot as plt
import numpy as np
import time

from configs import *

from PIL import Image
image = Image.open("./img/sagemaker.png")
st.image(image, width=80)
st.header("Image Generation")
st.caption("Using Stable Diffusion model from Hugging Face")

with st.spinner("Retrieving configurations..."):

    all_configs_loaded = False

    while not all_configs_loaded:
        try:
            api_endpoint = get_parameter(key_txt2img_api_endpoint)
            sm_endpoint = get_parameter(key_txt2img_sm_endpoint)
            all_configs_loaded = True
        except:
            time.sleep(5)

    endpoint_name = st.sidebar.text_input("SageMaker Endpoint Name:",sm_endpoint)
    url = st.sidebar.text_input("API GW Url:",api_endpoint)


prompt = st.text_area("Input Image description:", """Dog in superhero outfit""")

if st.button("Generate image"):
    if endpoint_name == "" or prompt == "" or url == "":      
        st.error("Please enter a valid endpoint name, API gateway url and prompt!")
    else:
        with st.spinner("Wait for it..."):
            try:
                r = requests.post(url,json={"prompt":prompt,"endpoint_name":endpoint_name},timeout=180)
                data = r.json()
                image_array = data["image"]
                st.image(np.array(image_array))

            except requests.exceptions.ConnectionError as errc:
                st.error("Error Connecting:",errc)
                
            except requests.exceptions.HTTPError as errh:
                st.error("Http Error:",errh)
                
            except requests.exceptions.Timeout as errt:
                st.error("Timeout Error:",errt)    
                
            except requests.exceptions.RequestException as err:
                st.error("OOps: Something Else",err)                
                
        st.success("Done!")