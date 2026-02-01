import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError

RANKING_URL = "https://www.10000recipe.com/ranking/home_new.html"


# 랭킹 레시피 -> recipe_id 수집
def get_recipe_ids_by_ranking():
    res = requests.session.get(RANKING_URL)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    recipe_ids = []
    for a in soup.select("a.common_sp_link"):
        href = a.get("href", "")
        if href.startswith("/recipe/"):
            recipe_ids.append(href.split("/")[-1])
    return list(dict.fromkeys(recipe_ids))
