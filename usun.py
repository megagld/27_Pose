import json
# jason = json.load("mydata.json")


with open("mydata.json", "r") as jsonfile:
    data = json.load(jsonfile)


print(type(data))
      