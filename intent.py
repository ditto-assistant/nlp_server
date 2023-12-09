"""
Intent recognition train / test framework for Ditto Assistant.

author: Omar Barazanji
date: 4/1/2023
"""

import spacy
import pandas as pd
from matplotlib import pyplot as plt
import os
import dill as pickle
import numpy as np
import tensorflow as tf
from nltk import word_tokenize
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from tensorflow.keras import backend as K
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from word2number import w2n
import logging

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

log = logging.getLogger("intent")
logging.basicConfig(level=logging.DEBUG)

# get arg for train or test
import sys

TRAIN = False
if len(sys.argv) > 1:
    if str(sys.argv[1]).lower() == "train":
        TRAIN = True

class IntentRecognition:
    def __init__(self, train=0):
        self.train = train
        log.info("Fitting Neurons...")
        if train:
            self.__load_data()
            self.__transform_data()
            self.__create_train_models()
        else:
            self.__load_intent_models()
            self.__load_ner_models()

    def __load_intent_models(self):
        try:
            self.category_model = tf.keras.models.load_model("models/category.model")
            self.subcategory_model = tf.keras.models.load_model(
                "models/subcategory.model"
            )
            self.action_model = tf.keras.models.load_model("models/action.model")
            self.cat_labels = list(np.load("data/intent-resources/cat_labels.npy"))
            self.subcat_labels = list(
                np.load("data/intent-resources/subcat_labels.npy")
            )
            self.action_labels = list(
                np.load("data/intent-resources/action_labels.npy")
            )
            self.vectorizer = pickle.load(open("vectorizers/tfidf.pickle", "rb"))
            self.stemmer = SnowballStemmer("english")
            self.lemmatizer = WordNetLemmatizer()
        except BaseException as e:
            log.info(e)
            log.info("\n[Unable to load intent model and its resources...]\n")

    def __load_ner_models(self):
        try:
            self.ner_play = spacy.load("models/ner/play")
            self.ner_timer = spacy.load("models/ner/timer")
            self.ner_numeric = spacy.load("models/ner/numeric")
            self.ner_light = spacy.load("models/ner/light")
            self.ner_name = spacy.load("models/ner/name")
        except:
            log.info("\n[Unable to locate one or more NER models...]\n")
            self.ner_play, self.ner_timer, self.ner_numeric, self.ner_light = (
                [],
                [],
                [],
                [],
            )

    def __load_data(self):
        self.df = pd.read_csv("data/dataset_ditto.csv")
        self.cat_strarr, self.subcat_strarr, self.action_str_arr, self.prompt_strarr = (
            [],
            [],
            [],
            [],
        )
        for sample in self.df.iterrows():
            self.cat_strarr.append(str(sample[1].Category).lower())
            self.subcat_strarr.append(str(sample[1].Subcategory).lower())
            self.action_str_arr.append(str(sample[1].Action).lower())
            self.prompt_strarr.append(str(sample[1].Sentence).lower())

    def __transform_data(self):
        # load stemmer
        self.stemmer = SnowballStemmer("english")
        # load lemmatizer
        self.lemmatizer = WordNetLemmatizer()

        log.info("\n[Tokenizing...]\n")
        tokenized_prompts = list(
            map(lambda prompt: word_tokenize(prompt), self.prompt_strarr)
        )

        log.info("\n[Stemming and lemmatizing...]\n")
        prompts_stem_lem = []
        for tok_prompt in tokenized_prompts:
            stem_lem_arr = []
            for tok in tok_prompt:
                stem_lem_arr.append(self.lemmatizer.lemmatize(self.stemmer.stem(tok)))
            prompts_stem_lem.append(stem_lem_arr)
        tokenized_prompts = prompts_stem_lem

        log.info("\n[Vectorizing...]\n")
        # vectorize sentence arrays
        self.vectorizer = TfidfVectorizer(analyzer=lambda x: x)
        self.x_vector = self.vectorizer.fit_transform(tokenized_prompts)
        log.info("\nVectorized Shape: ", self.x_vector.shape, "\n")

        if not os.path.exists("vectorizers"):
            os.mkdir("vectorizers")
        pickle.dump(self.vectorizer, open("vectorizers/tfidf.pickle", "wb"))

        # convert to Dense format (X vector)
        self.x = self.x_vector.todense()

        # create 3 Y arrays for each intent model
        self.cat_labels, self.subcat_labels, self.action_labels = (
            list(set(self.cat_strarr)),
            list(set(self.subcat_strarr)),
            list(set(self.action_str_arr)),
        )
        self.y_cat, self.y_subcat, self.y_action = [], [], []
        for cat_label, subcat_label, action_label in zip(
            self.cat_strarr, self.subcat_strarr, self.action_str_arr
        ):
            onehot = np.zeros(len(self.cat_labels))
            onehot[self.cat_labels.index(cat_label)] = 1
            self.y_cat.append(onehot)
            onehot = np.zeros(len(self.subcat_labels))
            onehot[self.subcat_labels.index(subcat_label)] = 1
            self.y_subcat.append(onehot)
            onehot = np.zeros(len(self.action_labels))
            onehot[self.action_labels.index(action_label)] = 1
            self.y_action.append(onehot)
        self.y_cat, self.y_subcat, self.y_action = (
            np.array(self.y_cat),
            np.array(self.y_subcat),
            np.array(self.y_action),
        )

        # cache data
        np.save("data/intent-resources/cat_labels.npy", np.array(self.cat_labels))
        np.save("data/intent-resources/subcat_labels.npy", np.array(self.subcat_labels))
        np.save("data/intent-resources/action_labels.npy", np.array(self.action_labels))

    def __create_train_models(self, epochs=100):
        xtrain_cat, xtest_cat, ytrain_cat, ytest_cat = train_test_split(
            self.x, self.y_cat, train_size=0.9
        )
        xtrain_subcat, xtest_subcat, ytrain_subcat, ytest_subcat = train_test_split(
            self.x, self.y_subcat, train_size=0.9
        )
        xtrain_action, xtest_action, ytrain_action, ytest_action = train_test_split(
            self.x, self.y_action, train_size=0.9
        )

        self.category_model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(units=16, activation="relu"),
                tf.keras.layers.Dense(units=len(self.cat_labels), activation="softmax"),
            ]
        )
        self.subcategory_model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(units=16, activation="relu"),
                tf.keras.layers.Dense(
                    units=len(self.subcat_labels), activation="softmax"
                ),
            ]
        )
        self.action_model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(units=16, activation="relu"),
                tf.keras.layers.Dense(
                    units=len(self.action_labels), activation="softmax"
                ),
            ]
        )

        log.info("\n[Training Category Model...]\n")
        self.cat_callback = tf.keras.callbacks.EarlyStopping(monitor="loss", patience=3)
        self.category_model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics="accuracy"
        )
        self.category_model.fit(
            xtrain_cat,
            ytrain_cat,
            batch_size=32,
            epochs=epochs,
            callbacks=[self.cat_callback],
        )
        ypreds_cat = self.category_model.predict(xtest_cat)
        ypreds_cat_ = []
        for pred in ypreds_cat:
            onehot = np.zeros(len(pred))
            onehot[np.argmax(pred)] = 1
            ypreds_cat_.append(onehot)
        accuracy_cat = accuracy_score(ytest_cat, ypreds_cat_)
        log.info(f"\n[Category Model Accuracy: {accuracy_cat}]\n")
        # save as Keras model for local instance
        self.category_model.save("models/category.model")
        log.info("\n[Model saved to models/category.model]\n")

        log.info("\n[Training Subcategory Model...]\n")
        self.subcat_callback = tf.keras.callbacks.EarlyStopping(
            monitor="loss", patience=3
        )
        self.subcategory_model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics="accuracy"
        )
        self.subcategory_model.fit(
            xtrain_subcat,
            ytrain_subcat,
            batch_size=32,
            epochs=epochs,
            callbacks=[self.subcat_callback],
        )
        ypreds_subcat = self.subcategory_model.predict(xtest_subcat)
        ypreds_subcat_ = []
        for pred in ypreds_subcat:
            onehot = np.zeros(len(pred))
            onehot[np.argmax(pred)] = 1
            ypreds_subcat_.append(onehot)
        accuracy_subcat = accuracy_score(ytest_subcat, ypreds_subcat_)
        log.info(f"\n[Subcategory Model Accuracy: {accuracy_subcat}]\n")
        # save as Keras model for local instance
        self.subcategory_model.save("models/subcategory.model")
        log.info("\n[Model saved to models/subcategory.model]\n")

        log.info("\n[Training Action Model...]\n")
        self.action_callback = tf.keras.callbacks.EarlyStopping(
            monitor="loss", patience=3
        )
        self.action_model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics="accuracy"
        )
        self.action_model.fit(
            xtrain_action,
            ytrain_action,
            batch_size=32,
            epochs=epochs,
            callbacks=[self.action_callback],
        )
        ypreds_action = self.action_model.predict(xtest_action)
        ypreds_action_ = []
        for pred in ypreds_action:
            onehot = np.zeros(len(pred))
            onehot[np.argmax(pred)] = 1
            ypreds_action_.append(onehot)
        accuracy_action = accuracy_score(ytest_action, ypreds_action_)
        log.info(f"\n[Action Model Accuracy: {accuracy_action}]\n")
        # save as Keras model for local instance
        self.action_model.save("models/action.model")
        log.info("\n[Model saved to models/action.model]\n")

        log.info(
            f"\n[Category: {accuracy_cat}, Subcategory: {accuracy_subcat}, Action: {accuracy_action}]\n"
        )

    def prompt(self, prompt):
        prompt_tokenized = word_tokenize(prompt.lower())
        stem_lem = []
        for tok in prompt_tokenized:
            stem_lem.append(self.lemmatizer.lemmatize(self.stemmer.stem(tok)))
        prompt_tokenized = stem_lem
        prompt_vectorized = self.vectorizer.transform([prompt_tokenized]).todense()
        cat_pred = self.category_model.predict(prompt_vectorized)
        subcat_pred = self.subcategory_model.predict(prompt_vectorized)
        action_pred = self.action_model.predict(prompt_vectorized)
        category = self.cat_labels[np.argmax(cat_pred)]
        subcategory = self.subcat_labels[np.argmax(subcat_pred)]
        action = self.action_labels[np.argmax(action_pred)]
        K.clear_session()
        response = '{"category" : "%s", "sub_category" : "%s", "action" : "%s"}' % (
            category,
            subcategory,
            action,
        )
        log.info(response)
        return response

    def prompt_ner_play(self, sentence):
        artist = ""
        song = ""
        playlist = ""
        reply = self.ner_play(sentence)
        for ent in reply.ents:
            if "song" in ent.label_:
                song += ent.text + " "
            if "artist" in ent.label_:
                artist += ent.text + " "
            if "playlist" in ent.label_:
                playlist += ent.text + " "
        response = '{"song" : "%s", "artist" : "%s", "playlist" : "%s"}' % (
            song,
            artist,
            playlist,
        )
        return response

    def prompt_ner_timer(self, sentence):
        second = ""
        minute = ""
        reply = self.ner_timer(sentence)
        # log.info(reply.ents)
        for ent in reply.ents:
            if "second" in ent.label_:
                second += ent.text + " "
            elif "minute" in ent.label_:
                minute += ent.text + " "
        # log.info(second, minute)
        try:
            if "second" in second:
                second = "1"  # user said 'a' second
            if "minute" in minute:
                minute = "1"  # user said 'a' minute
            if not second == "1" and not second == "":
                second = w2n.word_to_num(second.strip())
            if not minute == "1" and not minute == "":
                minute = w2n.word_to_num(minute.strip())
            # log.info(second, minute)

        except:
            log.info("\n[word2num error]\n")
            second = second
            minute = minute
        response = '{"second" : "%s", "minute" : "%s"}' % (second, minute)
        return response

    def prompt_ner_numeric(self, sentence):
        numeric = ""
        entity = ""
        reply = self.ner_numeric(sentence)
        for ent in reply.ents:
            if "numeric" in ent.label_:
                numeric += ent.text + " "
            if "entity" in ent.label_:
                entity += ent.text + " "
        try:
            numeric = w2n.word_to_num(numeric.strip())
        except:
            numeric = numeric
        response = '{"numeric" : "%s", "entity" : "%s"}' % (numeric, entity)
        return response

    def prompt_ner_light(self, sentence):
        lightname = ""
        brightness = ""
        color = ""
        command = ""
        reply = self.ner_light(sentence)
        for ent in reply.ents:
            if "lightname" in ent.label_:
                lightname += ent.text + " "
            if "brightness" in ent.label_:
                brightness += ent.text + " "
            if "color" in ent.label_:
                color += ent.text + " "
            if "command" in ent.label_:
                command += ent.text + " "
            try:
                brightness = w2n.word_to_num(brightness.strip())
            except:
                brightness = brightness
        response = (
            '{"lightname" : "%s", "brightness" : "%s", "color" : "%s", "command" : "%s"}'
            % (lightname, brightness, color, command)
        )
        return response

    def prompt_ner_name(self, sentence):
        entity = ""
        reply = self.ner_name(sentence)
        for ent in reply.ents:
            if "entity" in ent.label_:
                entity += ent.text + " "
        response = '{"name" : "%s"}' % (entity)
        return response


if __name__ == "__main__":
    intent = IntentRecognition(train=TRAIN)
