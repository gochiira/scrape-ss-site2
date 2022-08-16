from typing import List
import os
import re


def filter_text(text: str, ng_words: List[str]) -> str:
    for word in ng_words:
        text = text.replace(word, "")
    return text


files = [f for f in os.listdir("./") if f.endswith(".txt")]
chino_texts = []

for file in files:
    with open(file, "r", encoding="utf8") as f:
        texts = f.read()
    chino_groups = re.finditer('(チノ|ちの)「(.{1,})」', texts)
    chino_text = [g.group(2) for g in chino_groups]
    chino_text = [
        filter_text(text, ["…", "●｀ε´●", "/", "♪", "―"])
        for text in chino_text
    ]
    chino_text = [text for text in chino_text if len(text) >= 3]
    chino_texts.extend(chino_text)

with open("chino_serif.txt", "w", encoding="utf8") as f:
    for text in chino_texts:
        f.write(text + "\n")
