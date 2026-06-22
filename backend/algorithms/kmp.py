def kmp_steps(text: str, pattern: str):
    steps = []
    #Creating lps table
    lps = [0]*len(pattern)
    length = 0
    i = 1
    while i<len(pattern):
        steps.append(
            {
                "phase": "build_lps",
                "message": f"Compare pattern[{i}] with pattern[{length}]",
                "i": i,
                "j": length,
                "lps": lps.copy()

            }
        )
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length-1]
        else:
            lps[i]=0
            i += 1
    # Search set up
    i = 0
    j = 0
    matches = []
    while i < len(text):
        steps.append(
            {
                "phase": "search",
                "message": f"Compare text[{i}] with pattern[{j}]",
                "i": i,
                "j": j,
                "lps": lps.copy(),
                "matches": matches.copy()

            }
        )
        
        # If characters match, both indexs move forward
        if text[i] == pattern[j]:
            i+=1
            j+=1
        if j == len(pattern):
            # If fully matched pattern found, the index of the starting point is at i-j
            matches.append(i-j)
            steps.append(
                {
                    "phase": "match",
                    "message": f"pattern found at index {i-j}",
                    "i": i,
                    "j": j,
                    "lps": lps.copy(),
                    "matches": matches.copy()

                }
            )
            # Continue search for potiential matches
            j = lps[j-1]
        elif i < len(text) and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1         
    return steps
steps = kmp_steps("ABABDABACDABABCABAB", "ABABCABAB")

for step in steps:
    print(step["message"])

def kmp_contains(text: str, pattern: str) -> bool:
    if pattern == "":
        return True

    text = text.lower()
    pattern = pattern.lower()

    lps = [0] * len(pattern)
    length = 0
    i = 1

    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1

    i = 0
    j = 0

    while i < len(text):
        if text[i] == pattern[j]:
            i += 1
            j += 1

        if j == len(pattern):
            return True
        elif i < len(text) and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return False