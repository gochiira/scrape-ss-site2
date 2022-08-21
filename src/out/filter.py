from typing import List, Union
import csv
import neologdn
import os
import re


def get_serifus_by_character_name(
    files: List[str],
    names: List[str]
) -> List[str]:
    out_texts: List[str] = []
    for file in files:
        with open(file, "r", encoding="utf8") as f:
            texts = f.read()
        # 正規表現で台詞を抽出
        character_groups = re.finditer(
            f'({"|".join(names)})'+'「(.{1,})」',
            texts
        )
        character_text_groups: List[str] = [
            g.group(2) for g in character_groups
        ]
        # 複数行跨っている台詞を分割
        character_text_split: List[List[str]] = [
            s.split("。")
            for s in character_text_groups
        ]
        # 二次配列を一次配列に変換
        character_text: List[str] = sum(character_text_split, [])
        character_text = [c for c in character_text if c != ""]
        # 余計な文字除去
        character_text = [
            filter_text(text, ["...", "…", "●｀ε´●", "/", "♪", "―"])
            for text in character_text
        ]
        # 気持ちだけ正規化する
        character_text = [
            neologdn.normalize(text)
            for text in character_text
        ]
        # 5文字以上の文章だけ取ってくる
        character_text = [
            text for text in character_text
            if len(text) >= 5
        ]
        out_texts.extend(character_text)
    return out_texts


def filter_text(text: str, ng_words: List[str]) -> str:
    for word in ng_words:
        text = text.replace(word, "")
    return text


if __name__ == "__main__":
    files = [f for f in os.listdir("./") if f.endswith(".txt")]
    character_sets = [
        ["chino", "チノ", "ちの"],
        ["cocoa", "ココア", "ここあ"],
        ["rize", "リゼ", "りぜ"],
        ["syaro", "シャロ", "しゃろ"],
        ["chiya", "千夜", "ちや"],
        ["maya", "マヤ", "まや"],
        ["megu", "メグ", "めぐ"],
    ]
    out: List[List[Union[int, str]]] = []
    for i, c_set in enumerate(character_sets):
        texts = get_serifus_by_character_name(files, c_set[1:])
        for t in texts:
            out.append([i, t])
    with open('out.tsv', mode='w', newline='', encoding='utf-8') as fo:
        tsv_writer = csv.writer(fo, delimiter='\t')
        tsv_writer.writerows(out)
