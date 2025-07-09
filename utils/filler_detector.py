FILLERS = ["um", "uh", "like", "you know", "so", "basically", "actually"]

def count_fillers(text):
    words = text.lower().split()
    return {f: words.count(f) for f in FILLERS if words.count(f) > 0}
