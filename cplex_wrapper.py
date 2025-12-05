import json
import sys
from collections import defaultdict
from loguru import logger
from datetime import datetime


class CplexWrapper:

    @staticmethod
    def read_data(path: str) -> dict:
        _data = defaultdict(str)
        try:
            with open(path, "r") as data_file:
                data = json.load(data_file)
            _data['start_planning_horizon'] = data['start_planning_horizon']
            _data['end_planning_horizon'] = data['end_planning_horizon']
            _data['breaks'] = data['breaks']
            _data['break_duration'] = data['break_duration']
            _data['break_length'] = data['break_length']
            _data['commercials'] = data['commercials']
            _data['name'] = data['name']
            _data['commercial_duration'] = data['commercial_duration']
            _data['commercial_copy'] = data['commercial_copy']
            _data['penalty'] = data['penalty']
            _data['competitors'] = data['competitors']
            _data['release_time'] = data['release_time']
            _data['due_time'] = data['due_time']
            _data['price'] = data['price']
            _data['reach'] = data['reach']
            _data['budget'] = data['budget']
            _data['required_reach'] = data['required_reach']

            return _data
        except (FileNotFoundError, FileExistsError) as exp:
            logger.exception(f"Error in Opening Data File!: {exp}")
            sys.exit(1)
        except KeyError as exp:
            logger.exception(f"Data File Structure is Not Correct!: {exp}")
            sys.exit(1)
        except Exception as exp:
            logger.exception(exp)
            sys.exit(1)

    @staticmethod
    def convert_commercial_duration(_generated_data: dict) -> dict:
        _generated_data['commercial_duration'] = [each_duration // 10
                                                  for each_duration in _generated_data['commercial_duration']]
        return _generated_data

    @staticmethod
    def convert_break_duration(_generated_data: dict) -> dict:
        _generated_data['break_duration'] = [each_duration // 10 for each_duration in _generated_data['break_duration']]
        return _generated_data

    @staticmethod
    def convert_break_length(_generated_data: dict) -> dict:
        start_planning_horizon = datetime.strptime(
            _generated_data['start_planning_horizon'], '%Y-%m-%d %H:%M:%S')
        for iter_break, each_break in enumerate(_generated_data["break_length"]):
            start_time_break = datetime.strptime(each_break['start'], "%Y-%m-%d %H:%M:%S")
            start_time = (start_time_break - start_planning_horizon).total_seconds()
            _generated_data["break_length"][iter_break]['start'] = int(start_time // 10)
            _generated_data["break_length"][iter_break]['end'] = int((start_time +
                                                                      _generated_data["break_duration"][
                                                                          iter_break]) // 10)
        return _generated_data

    @staticmethod
    def convert_due_time(_generated_data: dict) -> dict:
        start_planning_horizon = datetime.strptime(
            _generated_data['start_planning_horizon'], '%Y-%m-%d %H:%M:%S')
        for iter_due, each_due in enumerate(_generated_data['due_time']):
            converted_due_time = (datetime.strptime(each_due, "%Y-%m-%d %H:%M:%S") -
                                  start_planning_horizon).total_seconds()
            _generated_data['due_time'][iter_due] = int(converted_due_time // 10)
        return _generated_data

    @staticmethod
    def convert_release_time(_generated_data: dict) -> dict:
        start_planning_horizon = datetime.strptime(
            _generated_data['start_planning_horizon'], '%Y-%m-%d %H:%M:%S')
        for iter_rel, each_release in enumerate(_generated_data['release_time']):
            converted_release_time = (datetime.strptime(each_release, "%Y-%m-%d %H:%M:%S") -
                                      start_planning_horizon).total_seconds()
            _generated_data['release_time'][iter_rel] = int(converted_release_time // 10)
        return _generated_data

    @staticmethod
    def convert_time_scale(_generated_data: dict) -> dict:
        start = _generated_data['start_planning_horizon']
        end = _generated_data['end_planning_horizon']
        scale = (datetime.strptime(end, "%Y-%m-%d %H:%M:%S") - datetime.strptime(start, "%Y-%m-%d %H:%M:%S"))
        _generated_data['scale'] = int(scale.total_seconds() // 3600)
        return _generated_data

    @staticmethod
    def convert_budget_reach(_generated_data: dict) -> dict:
        for iter_budget, each_budget in enumerate(_generated_data['budget']):
            _generated_data['budget'][iter_budget] = each_budget / 100
        for iter_reach, each_reach in enumerate(_generated_data['required_reach']):
            _generated_data['required_reach'][iter_reach] = each_reach / 100
        return _generated_data

    @staticmethod
    def convert_price_reach(_generated_data: dict) -> dict:
        for iter_price, each_price in enumerate(_generated_data['price']):
            for __iter_price, __price in enumerate(each_price):
                _generated_data['price'][iter_price][__iter_price] = __price / 10
        for iter_reach, each_reach in enumerate(_generated_data['reach']):
            for __iter_reach, __reach in enumerate(each_reach):
                _generated_data['reach'][iter_reach][__iter_reach] = __reach / 10
        for iter_penalty, each_penalty in enumerate(_generated_data['penalty']):
            _generated_data['penalty'][iter_penalty] = each_penalty / 10
        return _generated_data


def cplex_wrapper(_generated_data: dict):
    converted_data = _generated_data
    converted_data = CplexWrapper.convert_time_scale(converted_data)
    converted_data = CplexWrapper.convert_break_length(converted_data)
    converted_data = CplexWrapper.convert_commercial_duration(converted_data)
    converted_data = CplexWrapper.convert_break_duration(converted_data)
    converted_data = CplexWrapper.convert_due_time(converted_data)
    converted_data = CplexWrapper.convert_release_time(converted_data)
    converted_data = CplexWrapper.convert_budget_reach(converted_data)
    converted_data = CplexWrapper.convert_price_reach(converted_data)
    return converted_data
