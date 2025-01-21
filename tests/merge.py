def merge_to_str(l: list[int]) -> list[str]:
    sorted_l = sorted(l)
    if not sorted_l:
        return []

    result = []
    start = sorted_l[0]
    end = sorted_l[0]

    for num in sorted_l[1:]:
        if num == end + 1:
            end = num
        else:
            if start == end:
                result.append(str(start))
            else:
                result.append(f"{start}-{end}")
            start = num
            end = num

    if start == end:
        result.append(str(start))
    else:
        result.append(f"{start}-{end}")

    return result


def sort_by_range(ranges: list[str]) -> list[str]:
    def get_range_size(r: str) -> int:
        if '-' in r:
            start, end = map(int, r.split('-'))
            return end - start + 1
        return 1

    return sorted(ranges, key=get_range_size)


if __name__ == '__main__':
    with open('need_to_reupload.txt', 'r') as f:
        l = [int(line.strip()) for line in f.readlines()]
    l = list(set(l))
    print(sort_by_range(merge_to_str(l)))
