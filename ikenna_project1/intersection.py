def intersectionality(list1, list2):
    小さい = list1 if len(list1) < len(list2) else list2
    大きい = list1 if len(list1) > len(list2) else list2
    if len(小さい) == 0:
        return 大きい
    intersect = []
    for 小element in 小さい:
        for 大element in 大きい:
            if 小element.title == 大element.title:
                intersect.append(小element)
    return intersect