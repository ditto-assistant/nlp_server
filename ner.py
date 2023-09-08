"""
Named Entity Recognition model.

author: Omar Barazanji

dataset:
https://raw.githubusercontent.com/Skuldur/virtual-assistant-tutorial/master/commands/play_commands.json

refs:
https://towardsdatascience.com/train-ner-with-custom-training-data-using-spacy-525ce748fab7
"""
from __future__ import unicode_literals, print_function
import json
import re

import random
from pathlib import Path
import spacy
from spacy.training.example import Example

from tqdm import tqdm

# which model to create
PLAY = 1
LIGHT = 0
TIMER = 0
NUM = 0

EPOCHS = 100

# def create_load_data():
# load in and organize data
if PLAY:
    with open("data/play_commands.json") as f:
        json_data = json.load(f)
if LIGHT:
    with open("data/light_commands.json") as f:
        json_data = json.load(f)
elif TIMER:
    with open("data/timer_commands.json") as f:
        json_data = json.load(f)
elif NUM:
    with open("data/numeric_commands.json") as f:
        json_data = json.load(f)

sentences = []
entities = []

for ndx, data in enumerate(json_data["training_data"]):
    if PLAY:
        words = data["words"]
        labels = data["labels"]

        ent_ndx = []
        for ndx, x in enumerate(labels):
            if "song" in x or "artist" in x or "playlist" in x:
                if "song" in x:
                    tag = "SONG"
                    ent_ndx.append([ndx, x])
                elif "artist" in x:
                    tag = "ARTIST"
                    ent_ndx.append([ndx, x])
                elif "playlist" in x:
                    tag = "PLAYLIST"
                    ent_ndx.append([ndx, x])

    if LIGHT:
        words = data["words"]
        labels = data["labels"]

        ent_ndx = []
        for ndx, x in enumerate(labels):
            if "lightname" in x:
                tag = "LIGHTNAME"
                ent_ndx.append([ndx, x])
            if "brightness" in x:
                tag = "BRIGHTNESS"
                ent_ndx.append([ndx, x])
            if "color" in x:
                tag = "COLOR"
                ent_ndx.append([ndx, x])
            if "command" in x:
                tag = "COMMAND"
                ent_ndx.append([ndx, x])

    elif TIMER:
        words = data["words"]
        labels = data["labels"]

        ent_ndx = []
        for ndx, x in enumerate(labels):
            if "second" in x or "minute" in x:
                if "second" in x:
                    tag = "SECOND"
                    ent_ndx.append([ndx, x])
                elif "minute" in x:
                    tag = "MINUTE"
                    ent_ndx.append([ndx, x])

    elif NUM:
        words = data["words"]
        labels = data["labels"]

        ent_ndx = []
        for ndx, x in enumerate(labels):
            if "numeric" in x:
                tag = "NUMERIC"
                ent_ndx.append([ndx, x])
            if "entity" in x:
                tag = "ENTITY"
                ent_ndx.append([ndx, x])

    sentence = ""
    for x in words:
        sentence += x + " "
    if (
        "(" in sentence
        or ")" in sentence
        or "+" in sentence
        or "?" in sentence
        or "[" in sentence
    ):
        continue

    ent = []
    curr_ndx = 0
    exiting = False
    for x in ent_ndx:
        word = words[x[0]]
        for match in re.finditer(word, sentence):
            beg = match.start()
            end = match.end()
            if end <= curr_ndx:
                exiting = True
            curr_ndx = end
            break
        if exiting:
            break
        ent.append((beg, end, x[1]))
    if exiting:
        continue
    sentences.append(sentence)
    entities.append(ent)


TRAIN_DATA = []

for sent, ent in zip(sentences, entities):
    ent_dict = dict()
    ent_dict["entities"] = ent
    TRAIN_DATA.append((sent, ent_dict))

# training time!
model = None
if PLAY:
    output_dir = Path("models/ner/play")
elif TIMER:
    output_dir = Path("models/ner/timer")
elif NUM:
    output_dir = Path("models/ner/numeric")
elif LIGHT:
    output_dir = Path("models/ner/light")

if model is not None:
    nlp = spacy.load(model)
    print("Loaded model '%s'" % model)
else:
    nlp = spacy.blank("en")
    print("Created blank 'en' model")

# set up the pipeline

if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
    # nlp.add_pipe(ner, last=True)
else:
    ner = nlp.get_pipe("ner")

for _, annotations in TRAIN_DATA:
    for ent in annotations.get("entities"):
        ner.add_label(ent[2])

other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
with nlp.disable_pipes(*other_pipes):  # only train NER
    optimizer = nlp.begin_training()
    for itn in range(EPOCHS):
        random.shuffle(TRAIN_DATA)
        losses = {}
        for text, annotations in tqdm(TRAIN_DATA):
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            nlp.update([example], drop=0.5, sgd=optimizer, losses=losses)
        print(losses)

if output_dir is not None:
    output_dir = Path(output_dir)
    if not output_dir.exists():
        output_dir.mkdir()
    nlp.to_disk(output_dir)
    print("Saved model to", output_dir)
