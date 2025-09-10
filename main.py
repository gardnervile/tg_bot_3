import os

folder = "quiz-questions"

for filename in os.listdir(folder):
    filepath = os.path.join(folder, filename)
    if os.path.isfile(filepath):
        with open(filepath, "r", encoding="KOI8-R") as f:
            print(f.read())