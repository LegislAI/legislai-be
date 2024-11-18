import json
import random

import spacy
from lime.lime_text import LimeTextExplainer
from spacy.tokens import Doc
from spacy.tokens import DocBin


def split_text(input_file, output_file):
    with open(input_file, "r", encoding="utf8") as f:
        data = [json.loads(line) for line in f]

        split_entries = []
        for entry in data:
            text = entry.get("text", "")
            label = entry.get("label", "")

            text_lines = text.split("\n")

            for line in text_lines:
                line = line.strip()  # Remove extra whitespace
                if line:  # Ignore empty lines
                    split_entries.append({"text": line, "label": label})

    with open(output_file, "w", encoding="utf8") as f_out:
        for entry in split_entries:
            f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")


split_text("./bin/input.jsonl", "./bin/output.jsonl")


def split_dataset(input_file, train_file, dev_file, train_ratio=0.8):
    with open(input_file, "r", encoding="utf8") as f:
        data = [json.loads(line) for line in f]

    random.shuffle(data)
    split_idx = int(len(data) * train_ratio)
    train_data = data[:split_idx]
    dev_data = data[split_idx:]

    with open(train_file, "w", encoding="utf8") as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(dev_file, "w", encoding="utf8") as f:
        for item in dev_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


split_dataset(
    "./bin/output.jsonl", "./bin/train.jsonl", "./bin/dev.jsonl", train_ratio=0.8
)

nlp = spacy.blank("pt")


def remove_stopwords(text):
    doc = nlp(text)
    filtered_words = [
        token.text for token in doc if not token.is_stop and not token.is_punct
    ]  # Filtra stop words e pontuação
    return " ".join(filtered_words)


doccano_file_train = "./bin/train.jsonl"
doccano_file_test = "./bin/dev.jsonl"
doccano_file_all = "./bin/input.jsonl"


def convert_doccano_to_spacy(doccano_file, output_file):
    db = DocBin()
    with open(doccano_file, "r", encoding="utf8") as f:
        for line in f:
            data = json.loads(line)
            text = data["text"]
            labels = data["label"]

            filtered_text = remove_stopwords(text)

            doc = nlp.make_doc(filtered_text)
            cats = {}

            if isinstance(labels, list):
                for label in labels:
                    cats[label] = 1.0
            else:
                cats[labels] = 1.0

            doc.cats = cats
            db.add(doc)

    db.to_disk(output_file)


convert_doccano_to_spacy(doccano_file_train, "spacy_data_train.spacy")
convert_doccano_to_spacy(doccano_file_test, "spacy_data_dev.spacy")
convert_doccano_to_spacy(doccano_file_all, "spacy_data_all.spacy")


stopwords = nlp.Defaults.stop_words

# Exportar as stopwords para um ficheiro de texto
with open("stopwords.txt", "w", encoding="utf-8") as f:
    for stopword in sorted(stopwords):
        f.write(stopword + "\n")

from spacy.language import Language

category_keywords = {"Código do Trabalho e Processo do Trabalho": ["patrão", "chefe"]}

Doc.set_extension("is_keyword", default=False, force=True)
Doc.set_extension("keyword_category", default=None, force=True)


@Language.component("keyword_component")
def keyword_component(doc):
    for cat, keywords in category_keywords.items():
        for token in doc:
            if token.text.lower() in keywords:
                token._.is_keyword = True
                token._.keyword_category = cat
    return doc


nlp.add_pipe("keyword_component", last=True)
