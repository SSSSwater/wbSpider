import random

def try_sample_from_list(list, count):
    if len(list) <= count:
        return list
    else:
        return random.sample(list, count)

def rand_probability(prob):
    if random.random() < prob:
        return True
    else:
        return False
def rand_probability_list(prob, count):
    list = []
    for i in range(count):
        list.append(rand_probability(prob))
    return list