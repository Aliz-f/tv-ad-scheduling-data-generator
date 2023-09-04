from loguru import logger
import json
from random import choice, uniform, randint
import numpy as np
from datetime import datetime


def read_config(config_path: str) -> tuple:
    try:
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
            config_time_scale = config['config__time_scale']
            config_break_count = config['config__break_count']
            config_break_length = config['config__break_length']
            config__commercial_duration = config["config__commercial_duration"]
            config__commercial_count = config["config__commercial_count"]
            config__commercial_min_count = config["config__commercial_min_count"]
            config__commercial_max_count = config["config__commercial_max_count"]
            budget_chance = config["config__budget_chance"]
            config__penalty_random = config['config__penalty_random']

            return config_time_scale, config_break_count, config_break_length, \
                config__commercial_duration, config__commercial_count,\
                config__commercial_min_count, config__commercial_max_count,budget_chance,\
                config__penalty_random
    except Exception as exp:
        logger.exception(exp)


def manage_breaks(config_break_count, config_break_length, config_commercial_duration):
    try:
        count = choice(config_break_count)
        length = []
        position = []
        mean_count_for_commercials = 0
        for i in range(count):
            each_length = choice(config_break_length)
            length.append(each_length)
            position.append(each_length // min(config_commercial_duration))
            mean_count_for_commercials += (each_length // max(config_commercial_duration) +
                                           each_length // min(config_commercial_duration)) // 2

        return count, length, mean_count_for_commercials, position
    except Exception as exp:
        logger.exception(exp)


def manage_reach_price(breaks: dict, max_position: int) -> np.array:
    tmp_reach = list()
    tmp_price = list()
    for key, value in breaks.items():
        for each_break in range(value['count']):
            tmp = list()
            for i in range(value['positions'][each_break]):
                half = value['positions'][each_break] // 2
                if i < half:
                    tmp.append(max_position + 1-i)
                else:
                    if value['positions'][each_break] < max_position:
                        tmp.append((i-max_position+1)+max_position+max_position+1 - value['positions'][each_break])
                    else:
                        tmp.append((i-max_position+1)+max_position+1)
            while len(tmp) < max_position:
                tmp.append(0)
            random = uniform(1, 1.9)
            tmp_reach.append([int(random * t) for t in tmp])
            tmp_price.append([int(3.5 * random * t) for t in tmp])

    price = np.array(tmp_price)
    reach = np.array(tmp_reach)
    return reach, price


def manage_commercial(commercial_count: list, commercial_min_count: list, commercial_max_count: list,
                      commercial_duration: list) -> dict:
    count = choice(commercial_count)
    commercial = {
        "count": count,
        "list": []
    }
    for i in range(count):
        commercial["list"].append(
            {"max": choice(commercial_max_count), "min": choice(commercial_min_count),
             'duration': choice(commercial_duration)}
        )
    return commercial


def manage_break_length(breaks: dict, time_scale: int) -> list:
    end_time = 0
    break_length = []
    for key, value in breaks.items():
        scale = int(key-1) * 3600
        count = value['count']
        for each_count in range(value['count']):
            if each_count <= count // 4:
                start_time = randint(scale + 0, scale + 900)
                end_time = value['length'][each_count] + start_time
            elif count // 4 < each_count <= count // 2:
                start_time = randint(scale + 900, scale + 1800)
                end_time = value['length'][each_count] + start_time
            elif count // 2 < each_count <= count // (3/4):
                start_time = randint(scale + 1800, scale + 2700)
                end_time = value['length'][each_count] + start_time
            elif count // (3/4) < each_count <= count:
                start_time = randint(scale + 2700, scale + 3450)
                end_time = value['length'][each_count] + start_time
            break_length.append(
                {
                    "start": start_time,
                    "end": end_time
                 }
            )
    return break_length


def manage_budget(price: np.array, commercial: dict, budget_chance: list, reach: np.array):
    price_mean = int(np.mean(price[price != 0]))+1
    reach_mean = int(np.mean(reach[reach != 0]))+1
    for each_comm in commercial['list']:
        mean = (each_comm['max'] + each_comm['min']) // 2
        tmp_price = mean * each_comm['duration'] * price_mean
        tmp_reach = mean * each_comm['duration'] * reach_mean
        chance = randint(0, 1)
        if chance == 0:
            price_chance = choice(budget_chance)
            budget = int(tmp_price - (price_chance / 100) * tmp_price)
        else:
            price_chance = choice(budget_chance)
            budget = int(tmp_price + (price_chance / 100) * tmp_price)
        chance = randint(0, 1)
        if chance == 0:
            reach_chance = choice(budget_chance)
            required_reach = int(tmp_reach + (reach_chance / 100) * tmp_reach)
        else:
            reach_chance = choice(budget_chance)
            required_reach = int(tmp_reach - (reach_chance / 100) * tmp_reach)

        each_comm['budget'] = budget
        each_comm['required_reach'] = required_reach
    return commercial


def manage_time(commercial: dict, break_length: list):
    start_time = break_length[0]['start']
    end_time = break_length[-1]['end']

    for i in range(commercial['count']):
        if i < commercial['count'] // 2:
            commercial['list'][i]["due_time"] = break_length[-1]['end']
            commercial['list'][i]["release_time"] = 0
        elif commercial['count'] // 2 <= i < commercial['count'] // (3/4):
            tmp = randint(0, (end_time // 4))
            commercial['list'][i]["due_time"] = tmp + end_time // (3/4)
            commercial['list'][i]["release_time"] = tmp
        else:
            tmp = randint(0, (end_time * 0.4))
            commercial['list'][i]["due_time"] = int(tmp + end_time * 0.6)
            commercial['list'][i]["release_time"] = tmp
    return commercial


if __name__ == "__main__":
    breaks = dict()
    time_scale, break_count, break_length_list, commercial_duration_list, commercial_count, commercial_min_count,\
        commercial_max_count, budget_chance, penalty_choice = read_config("config_small.json")

    for iter in range(1, time_scale+1):
        breaks[iter] = {}
        breaks[iter]["count"], breaks[iter]["length"], breaks[iter]["mean_count_commercial"],\
            breaks[iter]["positions"] =\
            manage_breaks(break_count, break_length_list, commercial_duration_list)

    max_position = max(break_length_list) // min(commercial_duration_list)
    reach, price = manage_reach_price(breaks, max_position)
    commercial = manage_commercial(commercial_count, commercial_min_count, commercial_max_count,
                                   commercial_duration_list)
    break_length = manage_break_length(breaks, time_scale)
    commercial = manage_budget(price, commercial, budget_chance, reach)
    commercial = manage_time(commercial, break_length)
    penalty = list()
    for each in range(commercial['count']):
        penalty.append(
            choice(penalty_choice)
        )
    break_count = 0
    break_duration = list()
    _break_length = list()
    for each in breaks.values():
        break_count += each['count']
        for i in each['length']:
            break_duration.append(i)
    for each in break_length:
        _break_length.append(
            {
                "start": each['start'],
                "end": each['end']
            }
        )
    _due_time = list()
    _release_time = list()
    _budget = list()
    _required_reach = list()
    commercial_duration = list()
    commercial_copy = list()
    for each in commercial['list']:
        commercial_duration.append(each['duration'])
        commercial_copy.append(
            {
                "max": each['max'],
                "min": each['min']
            }
        )
        _budget.append(
            each['budget']
        )
        _required_reach.append(
            each['required_reach']
        )
        _due_time.append(
            each['due_time']
        )
        _release_time.append(
            each['release_time']
        )

    data = {
        "commercials": commercial['count'],
        "breaks": break_count,
        "time_scale": time_scale,
        "commercial_duration": commercial_duration,
        "commercial_copy": commercial_copy,
        "break_duration": break_duration,
        "break_length": _break_length,
        "price": price.tolist(),
        "penalty": penalty,
        "budget": _budget,
        "required_reach": _required_reach,
        "reach": reach.tolist(),
        "due_time": _due_time,
        "release_time": _release_time,
        "competitors": []
    }

    with open(f"data/small_data_{datetime.now()}.json", "w") as json_file:
        json.dump(data, json_file, indent=4)