import json
'''
Loads Named Entity Recognition (NER) training data to generate new samples.
'''


class NERDataGenerator:
    '''
    NER Dataset Generator class for loading, expanding, and saving new training samples.
    '''

    def __init__(self) -> None:
        self.__load_data()

    def __load_data(self):
        try:
            self.ner_light_data = json.load(open('light_commands.json'))
            self.ner_numeric_data = json.load(open('numeric_commands.json'))
            self.ner_play_data = json.load(open('play_commands.json'))
            self.ner_timer_data = json.load(open('timer_commands.json'))
            self.ner_weather_data = json.load(open('weather_commands.json'))
        except BaseException as e:
            print('Error loading data...')
            print(e)
