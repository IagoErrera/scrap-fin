import sys
import pandas as pd
import matplotlib.pyplot as plt

from transformers import (
    AutoTokenizer,
    BertForSequenceClassification,
    pipeline,
)

finbert_pt_br_tokenizer = AutoTokenizer.from_pretrained("lucas-leme/FinBERT-PT-BR")
finbert_pt_br_model = BertForSequenceClassification.from_pretrained("lucas-leme/FinBERT-PT-BR")
finbert_pt_br_pipeline = pipeline(task='text-classification', model=finbert_pt_br_model, tokenizer=finbert_pt_br_tokenizer)

def get_index(text):
    chunks = get_chuncks(text)
    
    pred = finbert_pt_br_pipeline(chunks)

    positive = 0
    negative = 0
    neutral = 0
    for p in pred:
        if p['label'] == "POSITIVE": positive += 1
        elif p['label'] == "NEGATIVE": negative += 1
        else: neutral += 1
    
    if positive > negative: return 1
    elif negative > positive: return -1
    else: return 0

def get_chuncks(text, max_tokens=400, overlap=50):
    tokens = finbert_pt_br_tokenizer.tokenize(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk = tokens[start:end]
        chunks.append(finbert_pt_br_tokenizer.convert_tokens_to_string(chunk))
        start = end - overlap

    return chunks

path = sys.argv[1]

data = pd.read_csv(path)
# data = pd.read_csv('./fin_web_scrap//folha_p.csv')

data = data.dropna()

data['pubDate'] = pd.to_datetime(data['pubDate']) 
data['sentiment'] = data['paragraphs'].apply(get_index)

group_month_year = data.groupby([data['pubDate'].dt.month, data['pubDate'].dt.year])
dates_pair = group_month_year.groups.keys()

index_array = []
time_array = []
for date in dates_pair:
    group_data = group_month_year.get_group(date)
    index = group_data['sentiment'].sum() / group_data['sentiment'].count()
    index_array.append(index)
    
    time_str = f"{date[0] if date[0] > 9 else "0"+str(date[0])}-{date[1]}"
    time_array.append(time_str) 

plt.figure(figsize=(14, 7))
plt.plot(time_array, index_array)
plt.show()

export_date = {
    "time": time_array,
    "sentiment_index": index_array
}

export_df = pd.DataFrame(export_date)
export_df.to_csv('out.csv', index=False)