from fastapi import FastAPI
from pydantic import BaseModel  
from transformers import GPT2Tokenizer, GPT2LMHeadModel

import os
import logging 
import sys 
import time
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger.setLevel(logging.INFO)


os.environ['CURL_CA_BUNDLE'] = ''
app = FastAPI()


tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')


class Item(BaseModel):  
    text: str  
  
@app.post("/infer")  
def infer(item: Item):
    
    _url = 'http://' + os.environ['VECTOR_DB_SERVICE_HOST']
    response = requests.get(_url + '/api/v1/collections') 
    logger.info(f"vector db response: {response.json()}")

    t = time.time()
    prompt = f"Instruct: {item.text}\nOutput:"
    inputs = tokenizer(prompt, return_tensors="pt", return_attention_mask=False)
    outputs = model.generate(**inputs, max_length=200)
    text = tokenizer.batch_decode(outputs)[0]
    logger.info(text)
    logger.info(f"inference took {int(time.time() - t)} secs")

    return {"result": text}  


