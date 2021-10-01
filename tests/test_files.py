data_dict = {}
strategies = {
    '海龟交易法则',
    '放量上涨',
    '突破平台',
    '均线多头',
    '无大幅回撤',
    '停机坪',
    '回踩年线',
}
root_path = "/Users/runyunyao/Documents/Code/PythonProjects/Sequoia/0915/"

data_set = []
for strategy in strategies:
    path = root_path + strategy + ".ini"
    with open(path, "r") as f:
        for line in f:
            data = line[:-1].replace('\'', '').replace(' ', '').split(',')
            if data_dict.get(data[0]):
                data_dict[data[0]] = [data_dict[data[0]][0]+1, data[1]]
            else:
                data_dict[data[0]] = [1, data[1]]

for id in data_dict:
    if data_dict.get(id)[0] > 2:
        data_set.append([id, data_dict[id][1]])

for data in data_set:
    print(data)



