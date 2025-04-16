import pandas as pd

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

# Coloque os arquivos aqui
files = ['data_analysis/folha_2018-2020.csv', 'data_analysis/g1_2017_2023.csv', 'data_analysis/estadao_2017-2022.csv']

for i, path in enumerate(files):
  if i == 0: data = pd.read_csv(path)
  else: data = pd.concat([data, pd.read_csv(path)])

data = data.dropna()
data = data.drop(data[data['pubDate'] == "#"].index)

data['pubDate'] = data['pubDate'].apply(lambda s: s if not 'T' in s else s.split('T')[0])
data['pubDate'] = pd.to_datetime(data['pubDate'], format='%Y-%m-%d')
data['sentiment'] = data['paragraphs'].apply(get_index)

group_month_year = data.groupby([data['pubDate'].dt.month, data['pubDate'].dt.year])
dates_pair = group_month_year.groups.keys()

index_array = []
time_array = []
count_array = []
count_positive_array = []
count_negative_array = []
count_neutral_array = []
for date in dates_pair:
    group_data = group_month_year.get_group(date)
    index = group_data['sentiment'].sum() / group_data['sentiment'].count()
    index_array.append(index)

    count_array.append(group_data['sentiment'].count())

    positive_count = (group_data['sentiment'] == 1).sum()
    negative_count = (group_data['sentiment'] == -1).sum()
    neutral_count = (group_data['sentiment'] == 0).sum()
    count_positive_array.append(positive_count)
    count_negative_array.append(negative_count)
    count_neutral_array.append(neutral_count)

    time_str = f"{date[0] if date[0] > 9 else '0'+str(date[0])}-{date[1]}"
    time_array.append(time_str)

export_date = {
    "time": time_array,
    "sentiment_index": index_array,
    "count": count_array,
    "positive_count": count_positive_array,
    "negative_count": count_negative_array,
    "neutral_count": count_neutral_array,
}

export_df = pd.DataFrame(export_date)
export_df['time'] = pd.to_datetime(export_df['time'], format='%m-%Y')
export_df = export_df.sort_values(by='time').reset_index(drop=True)
export_df.to_csv('out.csv', index=False)