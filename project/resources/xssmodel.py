import pandas as pd #Data manipulation
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB



def check(value):
    df = pd.read_csv(r'D:\project\resources\xss.csv',encoding='utf-16')

    df = df.fillna('')

    # vectorization of data

    vectorizer = CountVectorizer( min_df=2, max_df=0.7, max_features=4096, stop_words=stopwords.words('english'))
    posts = vectorizer.fit_transform(df['Sentence'].values.astype('U')).toarray()

    # split train test data

    X_train, X_test, y_train, y_test = train_test_split(df.Sentence, df.Label, test_size=0.2)

    v=CountVectorizer()
    X_train_cv = v.fit_transform(X_train.values)
    X_train_np=X_train_cv.toarray()

    model = MultinomialNB()

    model.fit(X_train_cv, y_train)

    X_test_cv=v.transform(X_test)

    y_pred=model.predict(X_test_cv)

    Sentence=[value]
    Sentence_count= v.transform(Sentence)
    return model.predict(Sentence_count)
