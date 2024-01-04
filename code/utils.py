import base64
import os
import time
import urllib.parse

import pandas as pd
from cryptography.fernet import Fernet
from openai import OpenAI
from pyhtml2pdf import converter
from tqdm.auto import tqdm


def encrypt_api_key(key: str, password: str) -> str:
    cipher = Fernet(password)
    encrypted_key = cipher.encrypt(key.encode())
    return encrypted_key.decode()

def decrypt_api_key(filename: str = "api.txt") -> str:
    with open('api.txt', 'r') as file:
        password = file.readline().strip()
        password = base64.b64decode(password.encode('utf-8'))
        encrypted_key = file.readline().strip()

    cipher = Fernet(password)
    decrypted_key = cipher.decrypt(encrypted_key.encode())
    return decrypted_key.decode()

def find_wiki_url(name):
    actors = pd.read_csv("./data/actors_list.csv")
    actor_data = actors[actors.name == name]

    if len(actor_data) >= 2:
        print("동명이인이 존재합니다. 나무위키 문서 URL을 직접 입력해주세요.")
    elif len(actor_data) == 0:
        print(f"배우 목록에 존재하지 않는 이름: {name}")
    else:
        actor_url = actors[actors.name == name].iloc[0].wiki
        return actor_url

def create_pdf(name, full_url=None, replace=False):
    base_url = "https://namu.wiki"
    save_dir = "./data"

    if not full_url:
        url = find_wiki_url(name)
        if not url:
            return None
        full_url = urllib.parse.urljoin(base_url, url)
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if replace or f"{name}.pdf" not in os.listdir(save_dir):
        converter.convert(full_url, f"{save_dir}/{name}.pdf")
        print(f"Created {name}.pdf")
    else:
        print("File already exsits.")
