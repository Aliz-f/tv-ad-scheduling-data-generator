import random
import numpy as np
import json


def generate_data(commercials, breaks, time_scale, competitors=[]):
    commercials = commercials
    breaks = breaks
    time_scale = time_scale  # Second

    duration_random = [15, 30]
    copy_random = [1, 2, 3, 4, 5, 6]
    breaks_random = [60, 90]
    penalty_random = [10, 12, 15, 8, 9, 11]
    #TODO: reduce price and reach (price per second & reach per second)
    price_random = [4, 5, 6, 7, 8, 9]
    reach_random = [4, 5, 6, 7, 8, 9]
    budget_random = [580, 600, 800, 900, 700, 500, 960, 1200, 1350, 1400, 1700, 1600, 1500]
    required_reach_random = [270, 380, 490, 395, 473, 150, 100, 170, 200, 210]

    # --------------------------------------- commercial ---------------------------------------------------
    commercial_duration = [random.choice(duration_random) for i in range(commercials)]
    commercial_copy = []
    for i in range(commercials):
        tmp = dict()
        max_copy = max(random.choice(copy_random), 2)
        min_copy = max_copy
        while min_copy >= max_copy:
            min_copy = min(max_copy, random.choice(copy_random))

        tmp = {
            "max": max_copy,
            "min": min_copy
        }
        commercial_copy.append(tmp)

    # --------------------------------------- breaks ---------------------------------------------------
    break_duration = [random.choice(breaks_random) for j in range(breaks)]
    break_length = []
    time_duration = 0
    for j in range(breaks):
        tmp = dict()
        duration = break_duration[j]
        tmp = {
            "start": time_duration,
            "end": time_duration + duration
        }
        time_duration += time_scale
        break_length.append(tmp)

    # --------------------------------------- price ---------------------------------------------------
    tmp = list()
    for j in range(breaks):
        tmp.append(break_duration[j] // min(commercial_duration))
    max_poistion_in_break = max(tmp)
    price_tmp = list()
    for j in range(breaks):
        tmp = list()
        for i in range(max_poistion_in_break-2):
            num = random.choice(price_random)
            while num == max(price_random):
                num = random.choice(price_random)
            tmp.append(num)

        tmp.insert(0, max(price_random))
        tmp.append(max(price_random))
        price_tmp.append(tmp)

    price = np.array(price_tmp)

    # ------------------- budget, required_reach, due_time, release_time, penalty ----------------
    penalty = [random.choice(penalty_random) for i in range(commercials)]
    budget = [random.choice(budget_random) for i in range(commercials)]
    required_reach = [random.choice(required_reach_random) for i in range(commercials)]
    competitors = competitors

    # --------------------------------------- reach ---------------------------------------------------
    reach_tmp = list()
    for j in range(breaks):
        tmp = list()
        for i in range(max_poistion_in_break-2):
            num = random.choice(reach_random)
            while num == max(reach_random):
                num = random.choice(reach_random)
            tmp.append(num)

        tmp.insert(0, max(reach_random))
        tmp.append(max(reach_random))
        reach_tmp.append(tmp)

    reach = np.array(reach_tmp)

    # --------------------------------------- due time ---------------------------------------------------
    due_time_random = list()
    release_time_random = list()
    due_time = []
    release_time = []
    start_time = break_length[0]["start"]
    end_time = break_length[-1]["end"]

    for j in range(breaks):
        if start_time + time_scale <= break_length[j]["end"] <= end_time:
            due_time_random.append(break_length[j]["end"])
        if 0 <= break_length[j]["start"] < break_length[-1]["start"]:
            release_time_random.append(break_length[j]["start"])

    for i in range(commercials):
        _due = random.choice(due_time_random)
        _release = random.choice(release_time_random)
        due_time.append(_due)
        while _release > _due:
            _release = random.choice(release_time_random)
        release_time.append(_release)

    data = {
        "commercials": commercials,
        "breaks": breaks,
        "time_scale": time_scale,
        "commercial_duration": commercial_duration,
        "commercial_copy": commercial_copy,
        "break_duration": break_duration,
        "break_length": break_length,
        "price": price.tolist(),
        "penalty": penalty,
        "budget": budget,
        "required_reach": required_reach,
        "reach": reach.tolist(),
        "due_time": due_time,
        "release_time": release_time,
        "competitors": competitors
    }
    with open("generated_data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)


if __name__ == "__main__":
    generate_data(
        commercials=5,
        breaks=3,
        time_scale=3600,
        competitors=[]
    )
    print("DONE")
