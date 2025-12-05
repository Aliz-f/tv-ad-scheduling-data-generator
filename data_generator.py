import json
import random
import sys
import string
from random import choice
from datetime import datetime, timedelta
from os import path, mkdir
from collections import defaultdict

import numpy as np
from loguru import logger

from cplex_wrapper import cplex_wrapper


class GenerateData:
    @staticmethod
    def read_config(config_path: str) -> dict:
        _data = defaultdict(str)
        try:
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
            _data['scale'] = config['scale']
            _data['name'] = config['name']
            _data['schedule_start_time'] = config['schedule_start_time']
            _data['schedule_end_time'] = config['schedule_end_time']
            _data['commercial_count'] = config['commercial_count']
            _data['commercial_duration'] = config['commercial_duration']
            _data['commercial_minimum_play'] = config['commercial_minimum_play']
            _data['commercial_maximum_play'] = config['commercial_maximum_play']
            _data['break_count'] = config['break_count']
            _data['break_duration'] = config['break_duration']
            _data['budget_chance'] = config['budget_chance']
            _data['reach_chance'] = config['reach_chance']
            _data['price_range'] = config['price_range']
            _data['reach_range'] = config['reach_range']
            _data['penalty'] = config['penalty']
            _data['competitors_count'] = config['competitors_count']

            return _data
        except (FileNotFoundError, FileExistsError) as exp:
            logger.exception(f"Error in Opening Config File!: {exp}")
            sys.exit(1)
        except KeyError as exp:
            logger.exception(f"Config File Structure is Not Correct!: {exp}")
            sys.exit(1)
        except Exception as exp:
            logger.exception(exp)
            sys.exit(1)

    @staticmethod
    def manage_break(_data: dict, _generated_data: dict) -> dict:
        break_count = choice(_data["break_count"])
        schedule_start_time = _data["schedule_start_time"]
        _generated_data['breaks'] = break_count
        _generated_data['break_duration'] = list()
        _generated_data['break_length'] = list()

        for iterator in range(break_count):
            break_duration = choice(_data["break_duration"])
            _generated_data['break_duration'].append(break_duration)
            try:
                previous_end_time = _generated_data['break_length'][-1]["end"]
            except (IndexError, KeyError):
                previous_end_time = schedule_start_time
            except Exception as exp:
                logger.exception(exp)
                sys.exit(1)
            end_time = (datetime.strptime(previous_end_time, '%Y-%m-%d %H:%M:%S') +
                        timedelta(seconds=break_duration)).strftime('%Y-%m-%d %H:%M:%S')
            _generated_data['break_length'].append(dict(start=previous_end_time, end=end_time))
        return _generated_data

    @staticmethod
    def manage_commercial(_data: dict, _generated_data: dict) -> dict:
        all_characters = list(string.ascii_uppercase)
        commercial_count = choice(_data['commercial_count'])
        _generated_data["commercials"] = commercial_count
        _generated_data["name"] = list()
        _generated_data["commercial_duration"] = list()
        _generated_data["commercial_copy"] = list()
        _generated_data["penalty"] = list()

        for iterator in range(commercial_count):
            name = choice(all_characters) + "-" + str(random.randint(1, 500))
            while name in _generated_data["name"]:
                name = choice(all_characters) + "-" + str(random.randint(1, 500))
            _generated_data["name"].append(name)
            _generated_data["commercial_duration"].append(choice(_data["commercial_duration"]))
            _generated_data["commercial_copy"].append(dict(
                max=choice(_data["commercial_maximum_play"]),
                min=choice(_data['commercial_minimum_play'])))
            _generated_data["penalty"].append(choice(_data["penalty"]))

        return _generated_data

    @staticmethod
    def manage_price_reach(_data: dict, _generated_data: dict) -> dict:
        max_position = max([each_duration // min(_generated_data['commercial_duration']) for
                            each_duration in _generated_data['break_duration']])
        price = list()
        reach = list()
        for break_iterator, each_duration in enumerate(_generated_data['break_duration']):
            each_price = np.zeros(max_position)
            each_reach = np.zeros(max_position)
            break_max_position = each_duration // min(_generated_data['commercial_duration'])
            random_price = choice(_data['price_range'])
            random_reach = choice(_data['reach_range'])
            for _iter in range(0, break_max_position // 2):
                each_price[_iter] = int(random_price)
                each_reach[_iter] = int(random_reach)
                random_price -= 1
                random_reach -= 1
            for _iter in range(break_max_position // 2, break_max_position):
                each_price[_iter] = int(random_price)
                each_reach[_iter] = int(random_reach)
                random_price += 1
                random_reach += 1
            price.append(each_price)
            reach.append(each_reach)
        _generated_data['price'] = np.array(price)
        _generated_data['reach'] = np.array(reach)
        return _generated_data

    @staticmethod
    def manage_commercial_time(_data: dict, _generated_data: dict) -> dict:
        try:
            start_range = _generated_data["break_length"][0]['start']
            end_range = _generated_data["break_length"][-1]['end']
        except (IndexError, KeyError) as exp:
            start_range = _data["schedule_start_time"]
            end_range = _data["schedule_end_time"]
        except Exception as exp:
            logger.exception(exp)
            sys.exit(-1)
        release_time_range = (((datetime.strptime(end_range, "%Y-%m-%d %H:%M:%S") -
                                datetime.strptime(start_range, "%Y-%m-%d %H:%M:%S")) * 0.75) +
                              datetime.strptime(start_range, "%Y-%m-%d %H:%M:%S"))
        break_start_times = [_generated_data['break_length'][each_start_time]['start'] for each_start_time in
                             range(len(_generated_data['break_length'][:2]))]
        duration = release_time_range.replace(microsecond=0) - datetime.strptime(start_range, "%Y-%m-%d %H:%M:%S")

        _generated_data['release_time'] = list()
        _generated_data['due_time'] = list()

        for iter_commercial in range(_generated_data['commercials']):
            needed_duration = (_generated_data['commercial_copy'][iter_commercial]['max'] *
                               _generated_data['commercial_duration'][iter_commercial])

            random_release_time = datetime.strptime(choice(break_start_times), "%Y-%m-%d %H:%M:%S")
            while (random_release_time + timedelta(seconds=needed_duration) >
                   datetime.strptime(end_range, "%Y-%m-%d %H:%M:%S")):
                random_release_time = datetime.strptime(choice(break_start_times), "%Y-%m-%d %H:%M:%S")
            _generated_data['release_time'].append(random_release_time.strftime("%Y-%m-%d %H:%M:%S"))

            due_time_duration = (datetime.strptime(end_range, "%Y-%m-%d %H:%M:%S") -
                                 (random_release_time + timedelta(seconds=needed_duration)))
            random_fraction = random.random()
            random_timedelta = due_time_duration * 2 * random_fraction
            random_due_time = random_release_time + timedelta(seconds=needed_duration) + random_timedelta
            random_due_time = random_due_time if (
                    random_due_time < datetime.strptime(end_range, "%Y-%m-%d %H:%M:%S")) else (
                datetime.strptime(end_range, "%Y-%m-%d %H:%M:%S"))
            random_due_time = random_due_time.replace(microsecond=0)
            _generated_data['due_time'].append(random_due_time.strftime("%Y-%m-%d %H:%M:%S"))
        return _generated_data

    @staticmethod
    def manage_competitors(_data: dict, _generated_data: dict) -> dict:
        _generated_data["competitors"] = set()
        while len(_generated_data["competitors"]) < _data["competitors_count"]:
            advertiser_1, advertiser_2 = choice(_generated_data['name']), choice(_generated_data['name'])
            ordered_pair = tuple(sorted([advertiser_1, advertiser_2]))
            if advertiser_1 != advertiser_2:
                _generated_data["competitors"].add(ordered_pair)

        _generated_data["competitors"] = list(_generated_data["competitors"])
        return _generated_data

    @staticmethod
    def manage_budget_reach(_data: dict, _generated_data: dict) -> dict:
        price_mean = int(np.mean(_generated_data['price'][_generated_data['price'] != 0])) + 1
        reach_mean = int(np.mean(_generated_data['reach'][_generated_data['reach'] != 0])) + 1
        _generated_data['budget'] = list()
        _generated_data['required_reach'] = list()
        for each_commercial in range(_generated_data['commercials']):
            mean = (_generated_data["commercial_copy"][each_commercial]['max'] +
                    _generated_data["commercial_copy"][each_commercial]['min']) // 2
            tmp_price = mean * _generated_data['commercial_duration'][each_commercial] * price_mean
            tmp_reach = mean * _generated_data['commercial_duration'][each_commercial] * reach_mean
            price_chance = choice(_data['budget_chance'])
            reach_chance = choice(_data['reach_chance'])
            select = choice([0, 1])
            if select == 0:
                budget = int(tmp_price + (price_chance / 100) * tmp_price)
                required_reach = int(tmp_reach - (reach_chance / 100) * tmp_reach)
            else:
                budget = int(tmp_price - ((price_chance - 10) / 100) * tmp_price)
                required_reach = int(tmp_reach - ((reach_chance - 10) / 100) * tmp_reach)
            _generated_data['budget'].append(budget)
            _generated_data['required_reach'].append(required_reach)
        return _generated_data


if __name__ == "__main__":
    generated_data = defaultdict(str)
    data = GenerateData.read_config("config.json")
    generated_data['start_planning_horizon'] = data['schedule_start_time']
    generated_data['end_planning_horizon'] = data['schedule_end_time']
    generated_data = GenerateData.manage_break(data, generated_data)
    generated_data = GenerateData.manage_commercial(data, generated_data)
    generated_data = GenerateData.manage_competitors(data, generated_data)
    generated_data = GenerateData.manage_commercial_time(data, generated_data)
    generated_data = GenerateData.manage_price_reach(data, generated_data)
    generated_data = GenerateData.manage_budget_reach(data, generated_data)
    generated_data['price'] = generated_data['price'].tolist()
    generated_data['reach'] = generated_data['reach'].tolist()

    if not path.exists('data'):
        mkdir('data')

    if not path.exists('data/data_nsga'):
        mkdir('data/data_nsga')

    with open(f'data/data_nsga/{data["scale"]}_{datetime.today().date()}_{data["name"]}.json', 'w') as gn_file:
        json.dump(generated_data, gn_file, indent=4)

    converted_data = cplex_wrapper(generated_data)

    if not path.exists('data/data_cplex'):
        mkdir('data/data_cplex')
    with open(f'data/data_cplex/{data["scale"]}_{datetime.today().date()}_{data["name"]}.json', 'w') as gn_file:
        json.dump(converted_data, gn_file, indent=4)
