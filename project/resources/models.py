import pandas as pd  # Data manipulation
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

def train_model(path):
    df = pd.read_csv(path, encoding='utf-16')
    df = df.fillna('')

    # vectorization of data
    #vectorizer = CountVectorizer(min_df=2, max_df=0.7, max_features=4096, stop_words=stopwords.words('english'))
    vectorizer = CountVectorizer(ngram_range=(1,4), min_df=2, max_df=0.7, max_features=9096, stop_words=stopwords.words('english'))
    #v = CountVectorize
    posts = vectorizer.fit_transform(df['Sentence'].values.astype('U')).toarray()

    print('train')

    X_train, X_test, y_train, y_test = train_test_split(df.Sentence, df.Label, test_size=0.2)
   
    X_train_cv = vectorizer.fit_transform(X_train.values)
    X_train_np = X_train_cv.toarray()

    model = MultinomialNB()
    model.fit(X_train_cv, y_train)
    return model,vectorizer
    
def check(value, model, vectorizer):
    Sentence = [value]
    Sentence_count = vectorizer.transform(Sentence)
    return model.predict(Sentence_count)