import random

adjectives = [
    "Magnificent",
    "Exquisite",
    "Radiant",
    "Splendid",
    "Majestic",
    "Elegant",
    "Sublime",
    "Resplendent",
    "Impeccable",
    "Opulent",
    "Grandiose",
    "Stupendous",
    "Glorious",
    "Enchanting",
    "Effervescent",
]

animals = [
    "Swan",
    "Lynx",
    "Eagle",
    "Tiger",
    "Panda",
    "Shark",
    "Zebra",
    "Horse",
    "Crane",
    "Whale",
    "Otter",
    "Gecko",
    "Koala",
    "Bison",
    "Ibex",
]

trees = [
    "Maple",
    "Birch",
    "Oak",
    "Elm",
    "Ash",
    "Pine",
    "Cedar",
    "Fir",
    "Beech",
    "Palm",
    "Spruce",
    "Larch",
    "Alder",
    "Willow",
    "Ebony",
]


def generate_unique_name():
    adjective = random.choice(adjectives)
    noun = random.choice(animals + trees)
    number = random.randint(100, 999)
    return f"{adjective} {noun} {number}"
