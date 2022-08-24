def txt2list(filename):
    txt_file = open(filename, "r")
    file_content = txt_file.read()

    content_list = file_content.split("\n")
    txt_file.close()

    return content_list


def jaccard_similarity(word1, word2):
    word1 = set(word1)
    word2 = set(word2)
    #Find intersection of two sets
    nominator = word1.intersection(word2)

    #Find union of two sets
    denominator = word1.union(word2)

    #Take the ratio of sizes
    similarity = len(nominator)/len(denominator)
    
    return similarity
